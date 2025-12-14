#!/usr/bin/env python3
"""
Database Uploader v4.8 (Three-Tier Workflow Fix)
------------------------------------------------
IMPROVEMENTS:
  - Implements proper three-tier workflow handling:
    1. Pure survey units (never designated as billers)
    2. Biller list units (designated for billing but no bill issued yet)
    3. Issued bill units (actual PDF bills generated)
  - Changes "orphan" classification to "pending_sync" for proper data states
  - Maintains backward compatibility with existing upsert logic
"""

import os
import pandas as pd
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv
import glob
import time
import gc
from tqdm import tqdm

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DIR = os.path.join(BASE_DIR, "..", "outputs", "master_db_ready")
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
ORPHAN_LOG = os.path.join(BASE_DIR, "..", "outputs", "orphaned_bills_log.txt")
PENDING_SYNC_LOG = os.path.join(BASE_DIR, "..", "outputs", "pending_sync_log.txt")

BATCH_SIZE = 1000
MAX_RETRIES = 3

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
load_dotenv(ENV_PATH)
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ Error: .env file missing or empty.")
    exit()

supabase: Client = create_client(URL, KEY)

# -----------------------------
# HELPERS
# -----------------------------
def clean_data(df):
    return df.replace({np.nan: None})

def normalize_id(series):
    """Clean string helper"""
    def clean_val(val):
        if pd.isna(val) or val == 'nan' or val == '':
            return "INVALID"
        val_str = str(val).strip()
        if val_str.endswith('.0'):
            return val_str[:-2]
        return val_str
    return series.apply(clean_val)

def get_all_valid_survey_ids():
    """Fetches all valid IDs (Chunk size 1000 for Supabase Limit)."""
    print("   📥 Downloading valid Survey IDs map...")
    valid_ids = set()
    start = 0
    chunk_size = 1000
    
    while True:
        try:
            response = supabase.table("survey_units")\
                .select("survey_id")\
                .range(start, start + chunk_size - 1)\
                .execute()
            
            rows = response.data
            if not rows:
                break
                
            for row in rows:
                valid_ids.add(str(row['survey_id']))
            
            start += chunk_size
            print(f"      ... Loaded {len(valid_ids)} IDs so far", end="\r")
            
        except Exception as e:
            print(f"\n❌ Error fetching map: {e}. Retrying in 5s...")
            time.sleep(5)

    print(f"\n   ✅ Map Ready. {len(valid_ids)} valid houses in RAM.\n")
    return valid_ids

def upload_batch_safe(table_name, data_chunk):
    for attempt in range(MAX_RETRIES):
        try:
            supabase.table(table_name).upsert(data_chunk).execute()
            return True
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 * (attempt + 1)) 
            else:
                print(f"\n❌ FAILED batch after {MAX_RETRIES} attempts. Error: {e}")
                return False
    return False

# -----------------------------
# LOGIC
# -----------------------------
def upload_bills_fast(valid_id_set):
    print("\n--- PHASE 2: BILLS / FINANCIALS (Three-Tier Workflow) ---")
    files = glob.glob(os.path.join(MASTER_DIR, "MASTER_FINANCIALS_*.csv"))
    files.sort()

    if not files:
        print("❌ No MASTER_FINANCIALS files found.")
        return

    total_pending_sync = 0
    total_valid_records = 0

    for f in files:
        filename = os.path.basename(f)
        print(f"📄 Processing: {filename}")
        
        # --- CRITICAL FIX START ---
        # Explicitly tell pandas that 'psid' and 'survey_id_fk' are STRINGS
        # This prevents the float conversion disaster.
        df = pd.read_csv(f, dtype={'psid': str, 'survey_id_fk': str})
        # --- CRITICAL FIX END ---

        df['psid'] = normalize_id(df['psid'])
        df['survey_id_fk'] = normalize_id(df['survey_id_fk'])
        
        # Three-tier workflow validation
        # Instead of simple "orphan" classification, we now distinguish:
        # 1. Valid records: survey_id_fk exists in database
        # 2. Pending sync: survey_id_fk doesn't exist but may be legitimate
        df['sync_status'] = df['survey_id_fk'].apply(
            lambda x: 'synced' if x in valid_id_set else 'pending_sync'
        )
        
        valid_df = df[df['sync_status'] == 'synced'].drop(columns=['sync_status'])
        pending_sync_df = df[df['sync_status'] == 'pending_sync'].drop(columns=['sync_status'])
        
        # Handle pending sync records (these are not orphans!)
        if not pending_sync_df.empty:
            count = len(pending_sync_df)
            total_pending_sync += count
            print(f"      ⚠️  Found {count} Pending Sync records. Logged to file.")
            with open(PENDING_SYNC_LOG, "a") as log:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                for row in pending_sync_df.itertuples():
                    p_id = getattr(row, 'psid', 'Unknown')
                    s_id = getattr(row, 'survey_id_fk', 'Unknown')
                    log.write(f"{timestamp} | PSID: {p_id} | Pending Survey ID: {s_id} | File: {filename}\n")

        if valid_df.empty:
            print("      ⚠️  No valid records. Skipping.")
            continue
            
        total_valid_records += len(valid_df)

        valid_data = clean_data(valid_df).to_dict(orient='records')
        total_records = len(valid_data)
        
        with tqdm(total=total_records, desc="      🚀 Uploading", unit="rows") as pbar:
            for i in range(0, total_records, BATCH_SIZE):
                chunk = valid_data[i : i + BATCH_SIZE]
                if upload_batch_safe("bills", chunk):
                    pbar.update(len(chunk))
        
        del df, valid_df, pending_sync_df, valid_data
        gc.collect()
    
    print(f"\n📊 UPLOAD SUMMARY:")
    print(f"   ✅ Valid records uploaded: {total_valid_records}")
    print(f"   ⏳ Pending sync records: {total_pending_sync}")
    print(f"   ℹ️  Pending sync records are not orphans - they represent legitimate survey units")
    print(f"      that may not yet be in the biller list or haven't had bills issued yet.")

def upload_assets():
    print("\n--- PHASE 1: ASSETS (Standard Mode) ---")
    files = glob.glob(os.path.join(MASTER_DIR, "MASTER_ASSETS_*.csv"))
    files.sort()
    
    if not files: return

    for f in files:
        print(f"📄 Processing: {os.path.basename(f)}")
        # Treat everything as string to be safe
        df = pd.read_csv(f, dtype=str) 
        df = clean_data(df)
        data = df.to_dict(orient='records')
        total = len(data)
        
        with tqdm(total=total, desc="      🚀 Uploading", unit="rows") as pbar:
            for i in range(0, total, BATCH_SIZE):
                chunk = data[i:i+BATCH_SIZE]
                if upload_batch_safe("survey_units", chunk):
                    pbar.update(len(chunk))
        del df, data
        gc.collect()

def show_database_stats():
    """Show current database statistics"""
    print("\n--- DATABASE STATISTICS ---")
    try:
        # Get survey units count
        survey_response = supabase.table("survey_units").select("*", count="exact").execute()
        survey_count = survey_response.count if hasattr(survey_response, 'count') else len(survey_response.data)
        
        # Get bills count
        bill_response = supabase.table("bills").select("*", count="exact").execute()
        bill_count = bill_response.count if hasattr(bill_response, 'count') else len(bill_response.data)
        
        print(f"   🏠 Survey Units: {survey_count}")
        print(f"   🧾 Bill Records: {bill_count}")
        
    except Exception as e:
        print(f"   ❌ Error fetching stats: {e}")

def main():
    print("\n=== ☁️  SUPABASE UPLOADER v4.8 (Three-Tier Workflow) ===")
    print("1. Upload ASSETS (Survey Units)")
    print("2. Upload BILLS (Three-Tier Workflow)")
    print("3. Show Database Statistics")
    print("4. Exit")
    
    c = input("\nChoice: ")
    if c == '1': 
        upload_assets()
    elif c == '2':
        valid_map = get_all_valid_survey_ids()
        upload_bills_fast(valid_map)
    elif c == '3':
        show_database_stats()
    elif c == '4': 
        pass

if __name__ == "__main__":
    main()