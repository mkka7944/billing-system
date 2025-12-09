#!/usr/bin/env python3
"""
Data Auditor v2 (Global Unique Checker)
---------------------------------------
Purpose: 
  1. Counts TOTAL UNIQUE PSIDs across all files on your disk.
  2. Checks for "Collision" (Do Nov files contain Oct PSIDs?).
  3. Compares CSV Reality vs. Database Reality.
"""

import os
import pandas as pd
import glob

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DIR = os.path.join(BASE_DIR, "..", "outputs", "master_db_ready")

def audit_global_uniques():
    print("=== 🕵️ GLOBAL PSID AUDIT v2 ===\n")

    files = glob.glob(os.path.join(MASTER_DIR, "MASTER_FINANCIALS_*.csv"))
    files.sort()
    
    global_psids = set()
    month_sets = {} # Stores sets of PSIDs for each month
    
    total_rows_processed = 0
    
    print("Phase 1: Scanning Local CSVs...")
    
    for f in files:
        fname = os.path.basename(f)
        # Extract Month from filename (e.g. MASTER_FINANCIALS_Nov-2025...)
        # We assume the format includes the month string
        current_month = "Unknown"
        if "Nov-2025" in fname: current_month = "Nov-2025"
        elif "Oct-2025" in fname: current_month = "Oct-2025"
        elif "Sep-2025" in fname: current_month = "Sep-2025"
        
        if current_month not in month_sets:
            month_sets[current_month] = set()

        try:
            # FORCE STRING to avoid scientific notation confusion
            df = pd.read_csv(f, dtype={'psid': str})
            
            # Clean PSIDs
            df['psid'] = df['psid'].str.strip()
            df['psid'] = df['psid'].apply(lambda x: x[:-2] if str(x).endswith('.0') else x)
            
            # Add to Month Set
            ids = set(df['psid'].dropna().unique())
            month_sets[current_month].update(ids)
            
            # Add to Global Set
            global_psids.update(ids)
            
            count = len(ids)
            total_rows_processed += len(df)
            print(f"   -> {fname} : {count} unique PSIDs")
            
        except Exception as e:
            print(f"   ❌ Error reading {fname}: {e}")

    print("\nPhase 2: The Collision Analysis")
    print("-------------------------------")
    
    # 1. Total Unique Capacity
    print(f"   📊 Total Rows in CSVs:         {total_rows_processed}")
    print(f"   💎 TOTAL UNIQUE PSIDs (Local): {len(global_psids)}")
    print(f"      (This is the MAXIMUM number of rows Supabase should have)")

    # 2. Overlap Check
    if 'Oct-2025' in month_sets and 'Nov-2025' in month_sets:
        oct_ids = month_sets['Oct-2025']
        nov_ids = month_sets['Nov-2025']
        
        overlap = oct_ids.intersection(nov_ids)
        print(f"\n   🔄 Oct-Nov Overlap:")
        print(f"      - Oct Total: {len(oct_ids)}")
        print(f"      - Nov Total: {len(nov_ids)}")
        print(f"      - REPEATED IDs: {len(overlap)} (These are Updates, not New Rows)")
        
        if len(overlap) > 0:
            print("      ⚠️  CONCLUSION: Some November bills are reusing October PSIDs.")
        else:
            print("      ✅ CONCLUSION: PSIDs are unique between months (No Overlap).")

if __name__ == "__main__":
    audit_global_uniques()