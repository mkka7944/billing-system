#!/usr/bin/env python3
"""
Data Auditor (The Detective)
----------------------------
Purpose: Analyzes your Master CSVs to find:
  1. Scientific Notation Corruption in PSIDs.
  2. Duplicate PSIDs (Data Collisions).
  3. Orphan Counts (Bills with no House).
"""

import os
import pandas as pd
import glob

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DIR = os.path.join(BASE_DIR, "..", "outputs", "master_db_ready")

def audit_files():
    print("=== 🕵️ DATA DETECTIVE REPORT ===\n")

    # 1. LOAD ASSET IDS (The "Truth")
    asset_files = glob.glob(os.path.join(MASTER_DIR, "MASTER_ASSETS_*.csv"))
    valid_assets = set()
    print("Phase 1: Loading Asset Register...")
    for f in asset_files:
        try:
            df = pd.read_csv(f, dtype=str)
            ids = set(df['survey_id'].unique())
            valid_assets.update(ids)
            print(f"   -> {os.path.basename(f)}: Found {len(ids)} unique houses.")
        except:
            print(f"   ❌ Error reading {os.path.basename(f)}")
    
    print(f"   ✅ TOTAL KNOWN HOUSES: {len(valid_assets)}\n")

    # 2. AUDIT FINANCIAL FILES
    bill_files = glob.glob(os.path.join(MASTER_DIR, "MASTER_FINANCIALS_*.csv"))
    bill_files.sort()
    
    print("Phase 2: Auditing Financial Files...")
    for f in bill_files:
        fname = os.path.basename(f)
        print(f"\n📄 File: {fname}")
        
        try:
            df = pd.read_csv(f, dtype=str) # Read as string to detect format issues
            total_rows = len(df)
            
            # CHECK A: Scientific Notation
            # Look for "E+" or "." in PSID
            bad_psids = df[df['psid'].str.contains('E\+', case=False, na=False) | df['psid'].str.contains('\.', na=False)]
            bad_count = len(bad_psids)
            
            # CHECK B: Duplicates
            unique_psids = df['psid'].nunique()
            duplicate_count = total_rows - unique_psids
            
            # CHECK C: Orphans
            # How many Survey IDs in this bill file are NOT in the valid_assets set?
            df['is_orphan'] = ~df['survey_id_fk'].isin(valid_assets)
            orphan_count = df['is_orphan'].sum()
            
            print(f"   Total Rows:      {total_rows}")
            print(f"   ---------------------------")
            
            if bad_count > 0:
                print(f"   ❌ CORRUPTED PSIDs (Scientific Notation): {bad_count}  <-- CRITICAL ERROR")
            else:
                print(f"   ✅ PSID Format:  Clean")
                
            if duplicate_count > 0:
                print(f"   ⚠️  Duplicate PSIDs: {duplicate_count} (Rows sharing same PSID)")
            else:
                print(f"   ✅ Duplicates:   None")
                
            if orphan_count > 0:
                print(f"   ⚠️  Orphans:         {orphan_count} (Bill exists, House missing in Asset File)")
            else:
                print(f"   ✅ Orphans:      None")
                
        except Exception as e:
            print(f"   ❌ CRITICAL: Could not read file. {e}")

if __name__ == "__main__":
    audit_files()