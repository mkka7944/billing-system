#!/usr/bin/env python3
"""
Universal Bill Extractor v6 (The Context Switcher)
- Feature: Logic to "Switch Designation" (Clock In) for Khushab/Bhalwal.
- Logic: Uses 'designation_id' from config to change active office.
- Core: Uses V2/V5 extraction method (Vacuum Mode).
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

# Full Columns list (V2 Standard)
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

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def build_full_url(fragment):
    if not fragment or not isinstance(fragment, str): return ""
    fragment = fragment.strip()
    if fragment.startswith(("http://", "https://")): return fragment
    return urljoin(BASE_HOST, fragment)

def do_login(profile_key):
    creds = config.CREDENTIALS.get(profile_key)
    if "YOUR_" in creds["CNIC"]:
        print(f"❌ SKIPPING {profile_key}: Credentials not set in config.py")
        return None

    print(f"🔑 Logging in Identity: {profile_key}...")
    s = requests.Session()
    s.headers.update(SESSION_HEADERS)
    
    try:
        payload = {"cnic": creds["CNIC"], "password": creds["PASSWORD"], "user_type": creds["USER_TYPE"]}
        resp = s.post(LOGIN_URL, json=payload, timeout=25)
        resp.raise_for_status()
        token = resp.json().get("data", {}).get("token")
        if not token: raise RuntimeError("No token returned.")
        s.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Login Success!")
        return s
    except Exception as e:
        print(f"❌ Login Failed for {profile_key}: {e}")
        return None

def switch_context(session, designation_id, city_name):
    """Hits the API to change the Active Office/Designation"""
    print(f"   🔀 Switching Context for {city_name} (Designation: {designation_id})...")
    payload = {"designation_id": designation_id}
    try:
        r = session.post(SWITCH_URL, json=payload, timeout=20)
        r.raise_for_status()
        print(f"   ✅ Context Switched Successfully.")
        return True
    except Exception as e:
        print(f"   ❌ Context Switch Failed: {e}")
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
    
    # 1. SWITCH CONTEXT IF NEEDED
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
            "id": "0", 
            "page": page, 
            "size": PAGE_SIZE,
            "search_keyword": "",
            "sorting": "",
            "requesting_url": "/suthra-billing/view/suthra-punjab-bills",
            "displayedColumnsAll": FULL_DISPLAY_COLUMNS,
            "filters_data": {
                "status": final_status,
                "division_id": job_details['division_id'],
                "district_id": job_details['district_id'], # Blank for KB, Filled for Sargodha
                "office_id": job_details['office_id'],     # Always Blank
                "uc_id": "", 
                "active": ""
            },
            "user_type": "contractor", 
            "plateform": "web"
        }
        
        success = False
        for _ in range(REQUEST_RETRIES):
            try:
                r = session.post(GET_DATA_URL, json=payload, timeout=45)
                r.raise_for_status()
                items = extract_records_from_response(r.json())
                
                if not items:
                    success = True; break
                
                all_records.extend(items)
                print(f"      Page {page}: Fetched {len(items)} records...")
                page += 1
                success = True; break
            except Exception as e:
                print(f"      ⚠️ Retry: {e}")
                time.sleep(2)
        
        if not success or not items: break
            
    return all_records

def process_and_save(raw_records, city_name, status):
    if not raw_records:
        print(f"   ⚠️ No records to save for {city_name}.")
        return

    print(f"   ⚙️ Generating Excel/CSV for {len(raw_records)} records...")
    
    processed_rows = []
    for i, rec in enumerate(raw_records, 1):
        def get_n(d, path):
            keys = path.split('.')
            val = d
            for k in keys: val = val.get(k, {})
            return val if isinstance(val, (str, int, float)) else ""

        p_date = rec.get("paid_date")
        if p_date:
            try: p_date = datetime.strptime(p_date, '%Y-%m-%d').strftime('%b %d, %Y')
            except: pass
            
        row = {
            "Sr#": i,
            "PSID": rec.get("psid"),
            "Month": rec.get("month_str"),
            "City": city_name,
            "Office": get_n(rec, "new_offices.office_id.name"),
            "UC": get_n(rec, "sw_areas.uc_id.name"),
            "Amount": rec.get("amount"),
            "Fine": rec.get("fine"),
            "Bill PDF": build_full_url(rec.get("bill_url")),
            "Channel": CHANNEL_MAP.get(str(rec.get("channel")), "Unknown"),
            "Paid Date": p_date,
            "Paid Amount": rec.get("paid_amount"),
            "Status": rec.get("status"),
        }
        processed_rows.append(row)

    df = pd.DataFrame(processed_rows)
    ensure_dir(config.OUTPUT_DIR)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f"{city_name}_{status}_{timestamp}"
    
    csv_path = os.path.join(config.OUTPUT_DIR, f"{base_name}_Master.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    xlsx_path = os.path.join(config.OUTPUT_DIR, f"{base_name}_Report.xlsx")
    try:
        if "Month" in df.columns and not df["Month"].isnull().all():
            unique_months = df["Month"].dropna().unique()
            with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
                for month in unique_months:
                    sheet_name = str(month).replace("/", "-")[:30] 
                    df[df["Month"] == month].to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"   📊 Excel Saved ({len(unique_months)} Sheets): {os.path.basename(xlsx_path)}")
        else:
            df.to_excel(xlsx_path, sheet_name="All_Data", index=False)
            print(f"   📊 Excel Saved (Single Sheet): {os.path.basename(xlsx_path)}")

    except Exception as e:
        print(f"   ❌ Excel Error: {e}")

def main():
    print("=== Universal Bill Extractor v6 (Context Switcher) ===")
    status_input = input("Status to fetch (PAID/UNPAID) [PAID]: ").strip() or "PAID"
    
    jobs_by_profile = {}
    for job in config.TARGET_JOBS:
        p = job['profile']
        if p not in jobs_by_profile: jobs_by_profile[p] = []
        jobs_by_profile[p].append(job)
    
    for profile_key, jobs in jobs_by_profile.items():
        print(f"\n🔄 Switching to Profile: {profile_key}")
        session = do_login(profile_key)
        if not session: continue
        
        for job in jobs:
            print(f"--- Processing {job['city_name']} ---")
            raw_data = fetch_bills(session, job, status_input)
            process_and_save(raw_data, job['city_name'], status_input)

    print("\n🎉 All jobs completed.")

if __name__ == "__main__":
    main()