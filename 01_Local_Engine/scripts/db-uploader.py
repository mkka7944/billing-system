#!/usr/bin/env python3
"""
Database Uploader v4.5 (Robust Speed Mode)
------------------------------------------
Features:
  - Pre-flight Foreign Key Validation (RAM-based)
  - Automatic Network Retries (3 attempts per batch)
  - Progress Bars (tqdm)
  - Orphan Logging
"""

import os
import pandas as pd
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv
import glob
import time
import gc
from tqdm import tqdm  # pip install tqdm

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DIR = os.path.join(BASE_DIR, "..", "outputs", "master_db_ready")
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
ORPHAN_LOG = os.path.join(BASE_DIR, "..", "outputs", "orphaned_bills_log.txt")

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
    """Replaces NaNs with None for JSON compatibility."""
    return df.replace({np.nan: None})

def normalize_id(series):
    """
    Ensures IDs are clean strings. 
    Handles cases where Excel saved '123' as '123.0'.
    Handles alphanumeric IDs safely.
    """
    def clean_val(val):
        if pd.isna(val) or val == 'nan' or val == '':
            return "INVALID"
        val_str = str(val).strip()
        # If it looks like a float "123.0", fix it
        if val_str.endswith('.0'):
            return val_str[:-2]
        return val_str

    return series.apply(clean_val)

def get_all_valid_survey_ids():
    """Fetches all valid IDs efficiently."""
    print("   📥 Downloading valid Survey IDs map (Guest List)...")
    valid_ids = set()
    start = 0
    chunk_size = 2000 
    
    # Simple spinner loop
    while True:
        try:
            # We fetch only the ID column to keep it fast
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
    """Tries to upload a batch, retries on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            supabase.table(table_name).upsert(data_chunk).execute()
            return True
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                # print(f"      ⚠️ Network blip. Retrying ({attempt+1}/{MAX_RETRIES})...")
                time.sleep(2 * (attempt + 1)) 
            else:
                print(f"\n❌ FAILED batch after {MAX_RETRIES} attempts. Error: {e}")
                return False
    return False

# -----------------------------
# LOGIC
# -----------------------------
def upload_bills_fast(valid_id_set):
    print("\n--- PHASE 2: BILLS / FINANCIALS (Speed Mode) ---")
    files = glob.glob(os.path.join(MASTER_DIR, "MASTER_FINANCIALS_*.csv"))
    files.sort()

    if not files:
        print("❌ No MASTER_FINANCIALS files found.")
        return

    for f in files:
        filename = os.path.basename(f)
        print(f"📄 Processing: {filename}")
        
        # 1. Load Data
        df = pd.read_csv(f)
        
        # Normalize IDs
        df['survey_id_fk'] = normalize_id(df['survey_id_fk'])
        
        # 2. Local Validation (The Speed Trick)
        # Check which IDs exist in our Valid Set
        df['is_valid'] = df['survey_id_fk'].isin(valid_id_set)
        
        valid_df = df[df['is_valid']].drop(columns=['is_valid'])
        orphan_df = df[~df['is_valid']].drop(columns=['is_valid'])
        
        # 3. Handle Orphans (Log them, don't crash)
        if not orphan_df.empty:
            count = len(orphan_df)
            print(f"      ⚠️  Found {count} Orphans (Missing Houses). Logging to file...")
            
            with open(ORPHAN_LOG, "a") as log:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                for row in orphan_df.itertuples():
                    # Safely get attributes
                    p_id = getattr(row, 'psid', 'Unknown')
                    s_id = getattr(row, 'survey_id_fk', 'Unknown')
                    log.write(f"{timestamp} | PSID: {p_id} | Missing Survey ID: {s_id} | File: {filename}\n")

        if valid_df.empty:
            print("      ⚠️  No valid records in this file. Skipping.")
            continue

        # 4. Upload Valid Data
        valid_data = clean_data(valid_df).to_dict(orient='records')
        total_records = len(valid_data)
        
        # Progress Bar
        with tqdm(total=total_records, desc="      🚀 Uploading", unit="rows") as pbar:
            for i in range(0, total_records, BATCH_SIZE):
                chunk = valid_data[i : i + BATCH_SIZE]
                success = upload_batch_safe("bills", chunk)
                
                if success:
                    pbar.update(len(chunk))
                else:
                    print("      ❌ Critical Batch Failure. Stopping this file.")
                    break
        
        # Cleanup Memory
        del df, valid_df, orphan_df, valid_data
        gc.collect()

def upload_assets():
    print("\n--- PHASE 1: ASSETS (Standard Mode) ---")
    files = glob.glob(os.path.join(MASTER_DIR, "MASTER_ASSETS_*.csv"))
    files.sort()
    
    if not files:
        print("❌ No MASTER_ASSETS files found.")
        return

    for f in files:
        print(f"📄 Processing: {os.path.basename(f)}")
        
        # Force string type for Phone Numbers/CNICs to prevent data loss
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

# -----------------------------
# MAIN
# -----------------------------
def main():
    print("\n=== ☁️  SUPABASE UPLOADER v4.5 (Robust) ===")
    print("1. Upload ASSETS (Survey Units)")
    print("2. Upload BILLS (Fast Validation)")
    print("3. Exit")
    
    c = input("\nChoice: ")
    if c == '1': 
        upload_assets()
    elif c == '2':
        # Download map only once
        valid_map = get_all_valid_survey_ids()
        upload_bills_fast(valid_map)
    elif c == '3': 
        print("Bye.")

if __name__ == "__main__":
    main()