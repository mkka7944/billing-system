#!/usr/bin/env python3
"""
Database Uploader v4.0 (Pre-Flight Validation)
----------------------------------------------
Purpose: Uploads Bills at maximum speed.
Strategy: 
  1. Downloads ALL valid Survey IDs from Supabase first.
  2. Filters CSVs locally (RAM) to remove Orphans.
  3. Uploads only valid data in fast batches.
  4. Saves orphans to log file.
"""

import os
import pandas as pd
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv
import glob
import time

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DIR = os.path.join(BASE_DIR, "..", "outputs", "master_db_ready")
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
ORPHAN_LOG = os.path.join(BASE_DIR, "..", "outputs", "orphaned_bills_log.txt")

BATCH_SIZE = 1000

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
load_dotenv(ENV_PATH)
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ Error: .env file missing.")
    exit()

supabase: Client = create_client(URL, KEY)

# -----------------------------
# HELPERS
# -----------------------------
def get_all_valid_survey_ids():
    """
    Fetches ALL existing survey_ids from the database to create a local whitelist.
    Handles pagination because Supabase limits fetch to 1000 rows per request.
    """
    print("   📥 Downloading valid Survey IDs from Database (for validation)...")
    valid_ids = set()
    start = 0
    chunk_size = 1000
    
    while True:
        # Fetch only the ID column to be fast
        response = supabase.table("survey_units").select("survey_id").range(start, start + chunk_size - 1).execute()
        rows = response.data
        
        if not rows:
            break
            
        for row in rows:
            valid_ids.add(str(row['survey_id']))
            
        start += chunk_size
        print(f"      ... Fetched {len(valid_ids)} IDs so far", end="\r")
        
    print(f"\n   ✅ Validation Map Ready. Found {len(valid_ids)} valid houses.\n")
    return valid_ids

def clean_data(df):
    return df.replace({np.nan: None})

def log_orphans_bulk(orphan_list, filename):
    """Writes a list of orphans to file efficiently"""
    if not orphan_list: return
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    with open(ORPHAN_LOG, "a") as f:
        for item in orphan_list:
            f.write(f"{timestamp} | PSID: {item['psid']} | Missing Survey ID: {item['survey_id']} | File: {filename}\n")

# -----------------------------
# FAST UPLOAD LOGIC
# -----------------------------
def upload_bills_fast(valid_id_set):
    print("\n--- PHASE 2: FINANCIALS (High Speed Mode) ---")
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
        df['psid'] = df['psid'].astype(str)
        df['survey_id_fk'] = df['survey_id_fk'].astype(str)
        if 'is_duplicate' in df.columns:
            df['is_duplicate'] = df['is_duplicate'].replace({np.nan: False})
        
        total_rows = len(df)
        
        # 2. Local Validation (The Speed Trick)
        print("      🔍 Validating IDs locally...")
        
        # Split into Valid and Invalid
        # We use a simple apply/lambda to check if ID exists in our set
        df['is_valid'] = df['survey_id_fk'].apply(lambda x: x in valid_id_set)
        
        valid_df = df[df['is_valid'] == True].drop(columns=['is_valid'])
        orphan_df = df[df['is_valid'] == False].drop(columns=['is_valid'])
        
        # 3. Log Orphans
        if not orphan_df.empty:
            print(f"      ⚠️  Found {len(orphan_df)} Orphans (Skipping upload, logging to text file).")
            orphans_to_log = [{'psid': row.psid, 'survey_id': row.survey_id_fk} for row in orphan_df.itertuples()]
            log_orphans_bulk(orphans_to_log, filename)
        
        # 4. Batch Upload Valid Data
        valid_data = clean_data(valid_df).to_dict(orient='records')
        count_valid = len(valid_data)
        
        print(f"      🚀 Uploading {count_valid} clean records...")
        
        for i in range(0, count_valid, BATCH_SIZE):
            chunk = valid_data[i : i + BATCH_SIZE]
            try:
                supabase.table("bills").upsert(chunk).execute()
                pct = int(((i + BATCH_SIZE) / count_valid) * 100)
                print(f"         [{min(100, pct)}%] Batch sent.")
            except Exception as e:
                print(f"         ❌ Critical Network Error on batch: {e}")
                # We don't need rescue mode here because we KNOW the IDs are valid.
                # If this fails, it's strictly an internet connection drop.
        
        print("      ✨ Done.")

# -----------------------------
# ASSETS (Standard Upload)
# -----------------------------
def upload_assets():
    # Assets don't have Foreign Keys to check, so they use standard upload
    # reusing the logic from v3 but simplified for brevity in this answer
    print("\n--- PHASE 1: ASSETS (Standard) ---")
    files = glob.glob(os.path.join(MASTER_DIR, "MASTER_ASSETS_*.csv"))
    if not files: return

    for f in files:
        print(f"📄 Processing: {os.path.basename(f)}")
        df = pd.read_csv(f, dtype=str)
        if 'gps_lat' in df.columns: df['gps_lat'] = df['gps_lat'].replace({'None': None})
        df = clean_data(df)
        data = df.to_dict(orient='records')
        
        for i in range(0, len(data), BATCH_SIZE):
            chunk = data[i:i+BATCH_SIZE]
            try:
                supabase.table("survey_units").upsert(chunk).execute()
                print(f"      Batch {i}-{i+len(chunk)} sent.")
            except Exception as e:
                print(f"      ❌ Error: {e}")

# -----------------------------
# MAIN
# -----------------------------
def main():
    print("\n=== ☁️  CLOUD UPLOADER v4.0 (Speed Mode) ===")
    print("1. Upload ASSETS (Standard)")
    print("2. Upload BILLS (Fast Validation)")
    print("3. Exit")
    
    c = input("Choice: ")
    if c == '1': 
        upload_assets()
    elif c == '2':
        # Fetch map once, use for all files
        valid_map = get_all_valid_survey_ids()
        upload_bills_fast(valid_map)
    elif c == '3': 
        pass

if __name__ == "__main__":
    main()