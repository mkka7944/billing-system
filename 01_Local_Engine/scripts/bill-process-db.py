#!/usr/bin/env python3
"""
------------------------------------------------------------------------
   MASTER CLEANER & MERGER (biller-process-db.py)
------------------------------------------------------------------------
   Purpose: 
     1. Reads 'Survey Master Excel' (Physical Assets).
     2. Reads 'Biller List CSV' (Financials & People).
     3. Merges them into two final Database-Ready files:
        - MASTER_ASSETS_MERGED (The Unit Profile)
        - MASTER_FINANCIALS (The Money Ledger)
   
   Key Features:
     - Splits 'GPS Coordinates' into Lat/Long.
     - Maps 'Type' (Barber/Bakery) and 'Surveyor Name'.
     - Cleans Urdu, PSIDs, and Financial Dashes.
------------------------------------------------------------------------
"""

import pandas as pd
import os
import glob
import sys
import logging

# -----------------------------
# CONFIGURATION
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_SURVEY_DIR = os.path.join(BASE_DIR, "..", "inputs", "survey_dumps")
INPUT_BILLER_DIR = os.path.join(BASE_DIR, "..", "inputs", "excel_dumps")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "outputs", "master_db_ready")

# Create Output Folder
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Logging Setup
LOG_FILE = os.path.join(OUTPUT_DIR, "process_log.txt")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# -----------------------------
# COLUMN MAPPINGS
# -----------------------------

# 1. Survey Excel Map (Source Header -> Final DB Column)
SURVEY_MAP = {
    "Survey ID": "survey_id",
    "Surveyor Name": "surveyor_name",
    "Survey Timestamp": "survey_timestamp",
    "Tehsil": "city_district",
    "Union Council": "uc_name",
    "UC Type": "uc_type",
    "Image URLs": "image_portal_url",
    "Type": "unit_specific_type",       # e.g. Barber shops
    "Level": "survey_category",         # e.g. Small
    "Name": "survey_consumer_name",     # The name written by Surveyor
    "Mobile Num": "survey_mobile",
    "Address": "survey_address",
    "House Type": "house_type",
    "Water Connection": "water_connection",
    "Area": "size_marla"                # Mapping Area to Size
    # GPS is handled via logic
}

# 2. Biller CSV Map (Source Header -> Final DB Column)
BILLER_ASSET_MAP = {
    "Survey ID": "survey_id",
    "Name": "billing_consumer_name",    # The Active Name
    "Mobile": "billing_mobile",
    "Address": "billing_address",
    "Status": "is_active_portal"
}

BILLER_FINANCE_MAP = {
    "Biller PSID": "psid",
    "Survey ID": "survey_id_fk",
    "Monthly Fee": "monthly_fee",
    "Balance": "arrears",
    "Total Payable": "amount_due"
}

# -----------------------------
# CLEANING FUNCTIONS
# -----------------------------

def clean_currency(val):
    """Converts '-' or empty to 0. Removes commas."""
    if pd.isna(val): return 0
    s = str(val).strip()
    if s in ["-", "", "nan", "None"]: return 0
    try:
        return int(float(s.replace(",", "")))
    except:
        return 0

def clean_text_id(val):
    """Ensures IDs are clean strings (no .0 artifacts)."""
    if pd.isna(val): return ""
    s = str(val).strip()
    if s.endswith(".0"): s = s[:-2]
    return s

def split_gps(val):
    """Splits '32.098,72.687' into (32.098, 72.687)."""
    if pd.isna(val): return None, None
    s = str(val).strip()
    parts = s.split(',')
    if len(parts) >= 2:
        return parts[0].strip(), parts[1].strip()
    return None, None

# -----------------------------
# MAIN LOGIC
# -----------------------------

def process_merge(survey_path, biller_path, billing_month):
    survey_file = os.path.basename(survey_path)
    biller_file = os.path.basename(biller_path)
    
    logging.info(f"\n🚀 STARTING MERGE PROCESS")
    logging.info(f"   Input Survey: {survey_file}")
    logging.info(f"   Input Biller: {biller_file}")
    logging.info(f"   Billing Month: {billing_month}")

    # --- STEP 1: PROCESS SURVEY DATA (The Assets) ---
    logging.info("   ⏳ Loading Survey Master Excel...")
    try:
        df_survey = pd.read_excel(survey_path, dtype=str)
    except Exception as e:
        logging.error(f"   ❌ Failed to read Excel: {e}")
        return

    # A. Split GPS
    if "GPS Coordinates" in df_survey.columns:
        logging.info("      📍 Splitting GPS Coordinates...")
        gps_split = df_survey["GPS Coordinates"].apply(split_gps)
        df_survey['gps_lat'] = gps_split.apply(lambda x: x[0])
        df_survey['gps_long'] = gps_split.apply(lambda x: x[1])
        df_survey['gps_full_string'] = df_survey["GPS Coordinates"]

    # B. Rename Columns
    df_survey.rename(columns=SURVEY_MAP, inplace=True)
    
    # Keep only mapped columns + GPS
    keep_cols = list(SURVEY_MAP.values()) + ['gps_lat', 'gps_long', 'gps_full_string']
    # Filter columns that actually exist
    final_cols_survey = [c for c in keep_cols if c in df_survey.columns]
    df_survey = df_survey[final_cols_survey]

    logging.info(f"      ✅ Loaded {len(df_survey)} physical assets.")

    # --- STEP 2: PROCESS BILLER DATA (The Updates & Money) ---
    logging.info("   ⏳ Loading Biller List CSV...")
    try:
        df_biller = pd.read_csv(biller_path, encoding='utf-8-sig', dtype=str)
    except:
        df_biller = pd.read_csv(biller_path, encoding='cp1252', dtype=str)

    # Clean IDs
    if "Survey ID" in df_biller.columns:
        df_biller["Survey ID"] = df_biller["Survey ID"].apply(clean_text_id)
    if "Biller PSID" in df_biller.columns:
        df_biller["Biller PSID"] = df_biller["Biller PSID"].apply(clean_text_id)

    # --- STEP 3: GENERATE ASSETS MERGED FILE ---
    # We take the Survey Data as the Base.
    # We Left Join the Biller Data (Name/Mobile) onto it.
    
    # Prepare Biller subset for merging
    biller_cols_to_use = [k for k in BILLER_ASSET_MAP.keys() if k in df_biller.columns]
    df_biller_assets = df_biller[biller_cols_to_use].copy()
    df_biller_assets.rename(columns=BILLER_ASSET_MAP, inplace=True)
    
    # Deduplicate Biller Assets (One status per house)
    df_biller_assets.drop_duplicates(subset=['survey_id'], keep='last', inplace=True)

    # MERGE: Survey (Left) + Biller (Right) on survey_id
    logging.info("   🔗 Merging Assets...")
    df_final_assets = pd.merge(df_survey, df_biller_assets, on='survey_id', how='left')

    # Status Cleanup
    if 'is_active_portal' in df_final_assets.columns:
        df_final_assets['is_active_portal'] = df_final_assets['is_active_portal'].replace(
            {'1': 'True', '0': 'False', 'Active': 'True', np.nan: 'False'}
        )

    # SAVE ASSETS FILE
    asset_filename = f"MASTER_ASSETS_MERGED_{survey_file.replace('.xlsx', '')}.csv"
    asset_save_path = os.path.join(OUTPUT_DIR, asset_filename)
    df_final_assets.to_csv(asset_save_path, index=False, encoding='utf-8-sig')
    logging.info(f"      💾 Saved Assets: {asset_filename}")

    # --- STEP 4: GENERATE FINANCIALS FILE ---
    logging.info("   💰 Processing Financials...")
    
    # Prepare Financials
    fin_cols = [k for k in BILLER_FINANCE_MAP.keys() if k in df_biller.columns]
    df_fin = df_biller[fin_cols].copy()
    df_fin.rename(columns=BILLER_FINANCE_MAP, inplace=True)

    # Clean Money
    for col in ['monthly_fee', 'arrears', 'amount_due']:
        if col in df_fin.columns:
            df_fin[col] = df_fin[col].apply(clean_currency)

    # Inject Meta
    df_fin['bill_month'] = billing_month
    df_fin['payment_status'] = 'UNPAID'
    
    # Duplicate Flagging
    df_fin['is_duplicate'] = df_fin.duplicated(subset=['survey_id_fk'], keep=False)

    # SAVE FINANCIALS FILE
    fin_filename = f"MASTER_FINANCIALS_{billing_month}_{biller_file}"
    fin_save_path = os.path.join(OUTPUT_DIR, fin_filename)
    df_fin.to_csv(fin_save_path, index=False, encoding='utf-8-sig')
    logging.info(f"      💾 Saved Financials: {fin_filename}")

    logging.info("   ✨ Batch Complete.")

# -----------------------------
# MENU SYSTEM
# -----------------------------
def main():
    print("==========================================")
    print("   MASTER DATA MERGER (biller-process-db)")
    print("==========================================\n")

    # 1. Select Survey File
    survey_files = glob.glob(os.path.join(INPUT_SURVEY_DIR, "*.xlsx"))
    if not survey_files:
        logging.error("No Survey Excel files found in inputs/survey_dumps/")
        return

    print("Step 1: Select SURVEY MASTER File (The Assets)")
    for i, f in enumerate(survey_files, 1):
        print(f"  {i}. {os.path.basename(f)}")
    
    try:
        s_idx = int(input("Selection: ")) - 1
        survey_target = survey_files[s_idx]
    except: return

    # 2. Select Biller File
    biller_files = glob.glob(os.path.join(INPUT_BILLER_DIR, "*.csv"))
    biller_files.sort()
    if not biller_files:
        logging.error("No Biller CSV files found in inputs/excel_dumps/")
        return

    print("\nStep 2: Select BILLER LIST File (The Data to Merge)")
    for i, f in enumerate(biller_files, 1):
        print(f"  {i}. {os.path.basename(f)}")
    
    try:
        b_idx = int(input("Selection: ")) - 1
        biller_target = biller_files[b_idx]
    except: return

    # 3. Input Month
    print("\nStep 3: Enter Billing Month")
    month = input("Format (e.g. Sep-2025): ").strip()
    if not month: return

    # 4. Run
    process_merge(survey_target, biller_target, month)

if __name__ == "__main__":
    import numpy as np # Import locally to avoid top-level dependency issues if not installed
    main()