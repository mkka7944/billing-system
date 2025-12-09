#!/usr/bin/env python3
"""
Universal Bill Extractor v10 (Final Production)
- Architecture: Fresh Session Isolation (prevents data mixing).
- Fixes: Hybrid Data Keys, Magic Category Key, Context Switching.
- Output: Auto-Sorted, Month-Filtered, with Sequential Serial Numbers.
"""

import requests
import csv
import os
import time
import pandas as pd
from datetime import datetime
from urllib.parse import urljoin
import config

# --- CONSTANTS ---
LOGIN_URL = "https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/login"
SWITCH_URL = "https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/hrmis/set-active-designation"
GET_DATA_URL = "https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/autoform/get-item-listing"
BASE_HOST = "https://suthra.punjab.gov.pk"

PAGE_SIZE = 250
REQUEST_RETRIES = 3
SESSION_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/96.0.4664.110 Safari/537.36',
    'Content-Type': 'application/json',
    'Origin': BASE_HOST,
    'Referer': f"{BASE_HOST}/suthra-billing/view/suthra-punjab-bills",
}

CHANNEL_MAP = {"1": "1Bill", "2": "BOP OTC", "0": "OTC/Cash"}

# Full Columns for API Request
FULL_DISPLAY_COLUMNS = [
    {"key": "sr_no", "column": True, "value": "Sr#"}, {"key": "print_serial", "column": True, "value": "PDF JOB ID"},
    {"key": "psid", "column": True, "value": "PSID"}, {"key": "month_str", "column": True, "value": "Month"},
    {"key": "attached_department_id", "column": True, "value": "WMC"}, {"key": "division_id", "column": True, "value": "Division"},
    {"key": "district_id", "column": True, "value": "District"}, {"key": "tehsil_id", "column": True, "value": "Tehsil"},
    {"key": "office_id", "column": True, "value": "Office"}, {"key": "uc_id", "column": True, "value": "UC"},
    {"key": "biller_category_id", "column": True, "value": "Billing Category"}, {"key": "amount", "column": True, "value": "Amount"},
    {"key": "fine", "column": True, "value": "Fine"}, {"key": "bill_url", "column": True, "value": "Bill PDF"},
    {"key": "channel", "column": True, "value": "Channel"}, {"key": "paid_date", "column": True, "value": "Paid Date"},
    {"key": "paid_amount", "column": True, "value": "Paid Amount"}, {"key": "status", "column": True, "value": "Status"},
    {"key": "active", "column": True, "value": "Active"}, {"key": "action", "column": True, "value": "Action"}
]

# --- COLUMN DEFINITIONS ---
COLS_CSV = [
    "Sr#", "PSID", "Month", "WMC", "Division", "District", "Tehsil", "Office", 
    "UC", "Billing Category", "Amount", "Fine", "Bill PDF", "Channel", 
    "Paid Date", "Paid Amount", "Status", "Active"
]

COLS_EXCEL = [
    "Sr#", "PSID", "Month", "Office", "UC", "Billing Category", 
    "Amount", "Fine", "Channel", "Paid Date", "Paid Amount", "Active"
]

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def build_full_url(fragment):
    if not fragment or not isinstance(fragment, str): return ""
    fragment = fragment.strip()
    if fragment.startswith(("http://", "https://")): return fragment
    return urljoin(BASE_HOST, fragment)

def create_fresh_session(profile_key):
    creds = config.CREDENTIALS.get(profile_key)
    if "YOUR_" in creds["CNIC"]:
        print(f"❌ SKIPPING {profile_key}: Credentials not set in config.py")
        return None

    print(f"   🔑 Logging in Identity: {profile_key}...")
    s = requests.Session()
    s.headers.update(SESSION_HEADERS)
    
    try:
        payload = {"cnic": creds["CNIC"], "password": creds["PASSWORD"], "user_type": creds["USER_TYPE"]}
        resp = s.post(LOGIN_URL, json=payload, timeout=25)
        resp.raise_for_status()
        token = resp.json().get("data", {}).get("token")
        if not token: raise RuntimeError("No token returned.")
        s.headers.update({"Authorization": f"Bearer {token}"})
        print("      ✅ Login Success!")
        return s
    except Exception as e:
        print(f"      ❌ Login Failed: {e}")
        return None

def switch_context(session, designation_id, city_name):
    print(f"   🔀 Switching Context for {city_name} (Designation: {designation_id})...")
    payload = {"designation_id": designation_id}
    try:
        r = session.post(SWITCH_URL, json=payload, timeout=20)
        r.raise_for_status()
        print(f"      ✅ Context Switched.")
        return True
    except Exception as e:
        print(f"      ❌ Context Switch Failed: {e}")
        return False

def extract_records_from_response(data):
    if not data: return []
    payload = data.get("data", data)
    if isinstance(payload, dict):
        for key in ("listings", "items", "records", "data"):
            if isinstance(payload.get(key), list): return payload[key]
    return payload if isinstance(payload, list) else []

def fetch_bills(session, job_details, status_arg):
    city = job_details['city_name']
    final_status = status_arg.upper()
    target_office = job_details.get('office_id', "")
    
    des_id = job_details.get('designation_id')
    if des_id:
        if not switch_context(session, des_id, city):
            return []

    print(f"   📡 Fetching [{final_status}] bills for -> {city}...")
    
    all_records = []
    page = 1
    
    while True:
        payload = {
            "slug": "suthra-punjab-bills", 
            "id": "0", "page": page, "size": PAGE_SIZE,
            "search_keyword": "", "sorting": "",
            "requesting_url": "/suthra-billing/view/suthra-punjab-bills",
            "displayedColumnsAll": FULL_DISPLAY_COLUMNS,
            "filters_data": {
                "status": final_status,
                "division_id": job_details['division_id'],
                "district_id": job_details['district_id'],
                "office_id": target_office, "uc_id": "", "active": ""
            },
            "user_type": "contractor", "plateform": "web"
        }
        
        success = False
        for _ in range(REQUEST_RETRIES):
            try:
                r = session.post(GET_DATA_URL, json=payload, timeout=45)
                r.raise_for_status()
                items = extract_records_from_response(r.json())
                if not items: success = True; break
                all_records.extend(items)
                print(f"      Page {page}: Fetched {len(items)} records...")
                page += 1
                success = True; break
            except Exception as e:
                print(f"      ⚠️ Retry: {e}")
                time.sleep(2)
        
        if not success or not items: break
            
    return all_records

def process_data(raw_records, city_name, status, target_month):
    if not raw_records: return None

    # The Magic Key from V2 logic
    cat_key = "biller_categories.bill_category_id.category,' ', sub_category, ' ',billing_category"

    rows = []
    for i, rec in enumerate(raw_records, 1):
        
        # Hybrid Extractor (Tries Flat Key, then Nested Key)
        def get_n(d, path):
            if path in d: return d[path] # Try Flat
            keys = path.split('.')
            val = d
            for k in keys: 
                if isinstance(val, dict): val = val.get(k, {})
                else: return ""
            if isinstance(val, (str, int, float)): return val
            return ""

        raw_date = rec.get("paid_date", "")
        pretty_date = ""
        if raw_date:
            try: pretty_date = datetime.strptime(raw_date, '%Y-%m-%d').strftime('%b %d, %Y')
            except: pretty_date = raw_date

        row = {
            "Sr#": i, # Temporary, re-indexed at end
            "PSID": rec.get("psid"),
            "Month": rec.get("month_str"),
            "WMC": get_n(rec, "attached_departments.attached_department_id.name"),
            "Division": get_n(rec, "divisions.division_id.name"),
            "District": get_n(rec, "districts.district_id.name"),
            "Tehsil": get_n(rec, "tehsils.tehsil_id.name"),
            "Office": get_n(rec, "new_offices.office_id.name"),
            "UC": get_n(rec, "sw_areas.uc_id.name"),
            
            # Use Magic Key for Category
            "Billing Category": rec.get(cat_key) or rec.get("biller_category_id"),
            
            "Amount": rec.get("amount"),
            "Fine": rec.get("fine"),
            "Bill PDF": build_full_url(rec.get("bill_url")),
            "Channel": CHANNEL_MAP.get(str(rec.get("channel")), "Unknown"),
            "Paid Date": pretty_date,
            "raw_date": raw_date, # For sorting
            "Paid Amount": rec.get("paid_amount"),
            "Status": rec.get("status"),
            "Active": rec.get("active"),
            "City": city_name
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # 2. Filter by Month
    if target_month:
        original_count = len(df)
        df = df[df['Month'].str.lower() == target_month.lower()]
        print(f"      🔎 Filtered by Month '{target_month}': {original_count} -> {len(df)} records.")
        if len(df) == 0: return None

    # 3. Sort by Paid Date (Newest First)
    if "raw_date" in df.columns:
        df = df.sort_values(by="raw_date", ascending=False)
    
    # 4. Generate Clean Sequential Serial Numbers
    df['Sr#'] = range(1, len(df) + 1)
    
    return df

def save_files(df, city_name, status, target_month):
    ensure_dir(config.OUTPUT_DIR)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    month_label = target_month.replace(" ", "_") if target_month else "ALL_HISTORY"
    base_name = f"{city_name}_{status}_{month_label}_{timestamp}"
    
    csv_path = os.path.join(config.OUTPUT_DIR, f"{base_name}_Full.csv")
    csv_cols = [c for c in COLS_CSV if c in df.columns]
    df[csv_cols].to_csv(csv_path, index=False, encoding='utf-8-sig')

    xlsx_path = os.path.join(config.OUTPUT_DIR, f"{base_name}_Report.xlsx")
    excel_cols = [c for c in COLS_EXCEL if c in df.columns]
    
    try:
        df[excel_cols].to_excel(xlsx_path, index=False, sheet_name=city_name)
        print(f"      💾 Saved: {os.path.basename(xlsx_path)}")
        print(f"      💾 Saved: {os.path.basename(csv_path)}")
    except Exception as e:
        print(f"      ❌ Save Failed: {e}")

def main():
    print("=== Universal Bill Extractor v10 (Final Production) ===")
    status_input = input("Status to fetch (PAID/UNPAID) [PAID]: ").strip() or "PAID"
    month_input = input("Filter by Month (e.g. 'Nov 2025') or Enter for All: ").strip()
    
    master_df_list = []

    for job in config.TARGET_JOBS:
        city = job['city_name']
        profile = job['profile']
        
        print(f"\n🚀 Starting Job: {city}")
        
        session = create_fresh_session(profile)
        if not session: continue
            
        raw_data = fetch_bills(session, job, status_input)
        
        df = process_data(raw_data, city, status_input, month_input)
        
        if df is not None and not df.empty:
            save_files(df, city, status_input, month_input)
            master_df_list.append(df)
        else:
            print("      ⚠️ No records found (Check Status/Month filter).")

        session.close()
        print(f"   🔒 Session closed for {city}.")

    # --- GRAND MERGE LOGIC ---
    if master_df_list:
        print("\n🔗 Merging all cities into one Master File...")
        master_df = pd.concat(master_df_list, ignore_index=True)
        
        # Sort again by date
        if "raw_date" in master_df.columns:
            master_df = master_df.sort_values(by="raw_date", ascending=False)
        
        # RE-INDEX SERIAL NUMBERS FOR MASTER FILE
        master_df['Sr#'] = range(1, len(master_df) + 1)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        month_label = month_input.replace(" ", "_") if month_input else "ALL_HISTORY"
        combined_name = f"COMBINED_ALL_CITIES_{status_input}_{month_label}_{timestamp}"
        
        # Save Combined CSV
        csv_path = os.path.join(config.OUTPUT_DIR, f"{combined_name}_Full.csv")
        csv_cols = [c for c in COLS_CSV if c in master_df.columns]
        if "City" in master_df.columns: csv_cols.insert(2, "City") 
        master_df[csv_cols].to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # Save Combined Excel
        xlsx_path = os.path.join(config.OUTPUT_DIR, f"{combined_name}_Report.xlsx")
        excel_cols = [c for c in COLS_EXCEL if c in master_df.columns]
        if "City" in master_df.columns: excel_cols.insert(2, "City")
        master_df[excel_cols].to_excel(xlsx_path, index=False, sheet_name="All Cities")
        
        print(f"🎉 GRAND TOTAL: {len(master_df)} Records Saved to:")
        print(f"   -> {os.path.basename(xlsx_path)}")

    print("\n✅ Script Finished.")

if __name__ == "__main__":
    main()