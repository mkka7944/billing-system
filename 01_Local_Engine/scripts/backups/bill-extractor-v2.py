#!/usr/bin/env python3
"""
Suthra Punjab Bill Extractor (Definitive CSV v4 - Corrected)

- This is the final, definitive version of the bill extractor.
- FIX: Re-added the missing 'urljoin' import to prevent the NameError crash.
- Correctly formats the 'Paid Date' to the required 'Month Day, Year' format.
- Updates the 'Channel' translation map to use the exact text from the portal.
"""

import requests
import csv
import os
import time
import re
from datetime import datetime
from urllib.parse import urljoin # <-- THE MISSING IMPORT IS NOW ADDED

# -----------------------------
# CONFIGURATION
# -----------------------------
OUTPUT_FOLDER = r"F:\Billing-Main\Python-Scripts\Output"
LOGIN_URL = "https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/login"
GET_DATA_URL = "https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/autoform/get-item-listing"
BASE_HOST = "https://suthra.punjab.gov.pk"

# Credentials
CNIC = "3840111639195"
PASSWORD = "1975@MuhammadHassanTMT"
USER_TYPE = "HRMIS_USER"

# --- FIXED Division and District IDs for this login ---
FIXED_DIVISION_ID = "9"
FIXED_DISTRICT_ID = "32"

# --- OPTIMIZED Performance Settings ---
PAGE_SIZE = 250
REQUEST_RETRIES = 3
REQUEST_DELAY = 0.7
SESSION_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'Origin': 'https://suthra.punjab.gov.pk',
    'Referer': 'https://suthra.punjab.gov.pk/suthra-billing/view/suthra-punjab-bills',
}

# --- Data Translation Dictionaries ---
CHANNEL_MAP = {
    "1": "1Bill",
    "2": "BOP OTC",
    "0": "OTC/Cash",
}
ACTIVE_MAP = {
    1: "Active",
    0: "Inactive",
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def sanitize_filename(name):
    if not isinstance(name, str): name = str(name)
    return re.sub(r'[\\/*?:"<>|]', "", name)

def build_full_url(fragment):
    if not fragment or not isinstance(fragment, str): return ""
    fragment = fragment.strip()
    if fragment.startswith(("http://", "https://")):
        return fragment
    return urljoin(BASE_HOST, fragment)

# -----------------------------
# LOGIN & FETCH
# -----------------------------
def do_login():
    s = requests.Session()
    s.headers.update(SESSION_HEADERS)
    try:
        resp = s.post(LOGIN_URL, json={"cnic": CNIC, "password": PASSWORD, "user_type": USER_TYPE}, timeout=25)
        resp.raise_for_status()
        token = resp.json().get("data", {}).get("token")
        if not token: raise RuntimeError("Token not found in login response")
        s.headers.update({"Authorization": f"Bearer {token}"})
        return s
    except Exception as e:
        raise RuntimeError(f"Login failed: {e}")

def fetch_bills_page(session, page, size, status):
    full_display_columns = [
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
    payload = {
        "slug": "suthra-punjab-bills", "id": "0", "page": page, "search_keyword": "",
        "requesting_url": "/suthra-billing/view/suthra-punjab-bills",
        "displayedColumnsAll": full_display_columns, "size": size, "sorting": "",
        "filters_data": {
            "status": status, "division_id": FIXED_DIVISION_ID, "district_id": FIXED_DISTRICT_ID,
            "office_id": "", "uc_id": "", "active": ""
        },
        "user_type": "contractor", "plateform": "web"
    }
    for attempt in range(REQUEST_RETRIES):
        try:
            r = session.post(GET_DATA_URL, json=payload, timeout=45)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"Fetch page {page} attempt {attempt+1} failed: {e}")
            time.sleep(2)
    raise RuntimeError(f"Failed fetching page {page}")

def extract_records_from_response(data):
    if not data: return []
    payload = data.get("data", data)
    if isinstance(payload, dict):
        for key in ("listings", "items", "records", "data"):
            if isinstance(payload.get(key), list): return payload[key]
    return payload if isinstance(payload, list) else []

# -----------------------------
# SAVE RESULTS FUNCTION (CSV ONLY)
# -----------------------------
def save_results_csv(rows, status):
    if not rows:
        print("⚠️ No rows to save.")
        return
    ensure_dir(OUTPUT_FOLDER)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_part = sanitize_filename(f"bills_sargodha_division_{status}_{timestamp}")
    filename = os.path.join(OUTPUT_FOLDER, f"{filename_part}.csv")

    fieldnames = [
        "Sr#", "PSID", "Month", "WMC", "Division", "District", "Tehsil",
        "Office", "UC", "Billing Category", "Amount", "Fine", "Bill PDF",
        "Channel", "Paid Date", "Paid Amount", "Status", "Active"
    ]
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"✅ Raw CSV file saved (perfect for Excel Power Query) → {filename}")

# -----------------------------
# MAIN WORKFLOW
# -----------------------------
def main():
    print("=== Suthra Punjab Bill Extractor (Definitive CSV v4) ===\n")

    status = input("Enter Bill Status (e.g., Paid, Un-paid) [Paid]: ").strip().upper() or "PAID"
    max_input = input("Max records to fetch (leave blank for all): ").strip()
    max_records = int(max_input) if max_input else float('inf')

    session = do_login()
    print("\n✅ Logged in.\n")

    all_records, page, total_fetched = [], 1, 0
    while total_fetched < max_records:
        print(f"Fetching page {page} (up to {PAGE_SIZE} records)...")
        data = fetch_bills_page(session, page, PAGE_SIZE, status)
        page_records = extract_records_from_response(data)
        if not page_records:
            print("No more records found.")
            break
        
        for rec in page_records:
            all_records.append(rec)
            total_fetched += 1
            if total_fetched >= max_records: break
        
        if total_fetched >= max_records:
            print(f"Reached max records limit of {max_records}.")
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    if not all_records:
        print("\n⚠️ No records were fetched for the given criteria.")
        return

    print(f"\nTotal records fetched: {len(all_records)}. Transforming data for CSV export...")
    
    results_for_csv = []
    for i, rec in enumerate(all_records, 1):
        channel_code = str(rec.get("channel", ""))
        channel_text = CHANNEL_MAP.get(channel_code, "Unknown")
        
        active_code = rec.get("active")
        active_text = ACTIVE_MAP.get(active_code, active_code)

        paid_date_raw = rec.get("paid_date")
        paid_date_formatted = ""
        if paid_date_raw:
            try:
                date_obj = datetime.strptime(paid_date_raw, '%Y-%m-%d')
                paid_date_formatted = date_obj.strftime('%b %d, %Y')
            except (ValueError, TypeError):
                paid_date_formatted = paid_date_raw

        transformed_row = {
            "Sr#": i,
            "PSID": rec.get("psid"),
            "Month": rec.get("month_str"),
            "WMC": rec.get("attached_departments.attached_department_id.name"),
            "Division": rec.get("divisions.division_id.name"),
            "District": rec.get("districts.district_id.name"),
            "Tehsil": rec.get("tehsils.tehsil_id.name"),
            "Office": rec.get("new_offices.office_id.name"),
            "UC": rec.get("sw_areas.uc_id.name"),
            "Billing Category": rec.get("biller_categories.bill_category_id.category,' ', sub_category, ' ',billing_category"),
            "Amount": rec.get("amount"),
            "Fine": rec.get("fine"),
            "Bill PDF": build_full_url(rec.get("bill_url")),
            "Channel": channel_text,
            "Paid Date": paid_date_formatted,
            "Paid Amount": rec.get("paid_amount"),
            "Status": rec.get("status"),
            "Active": active_text
        }
        results_for_csv.append(transformed_row)

    save_results_csv(results_for_csv, status)
    
    print("\n✅ Extraction finished.")

if __name__ == "__main__":
    main()