#!/usr/bin/env python3
"""
Final Survey Extractor with CSV and Excel Export (Batch Support)

- This script performs all the original data extraction tasks.
- It saves the results in TWO formats:
  1. A standard CSV file with the full image URLs.
  2. A user-friendly Excel file (.xlsx) where the image URLs are replaced with
     clickable hyperlinks displaying the Survey ID and sequence number.
- UPDATED: Supports batch downloading (District/Tehsil wise) and custom folder organization.
"""

import requests
import csv
import os
import time
import re
import json
from datetime import datetime
from urllib.parse import urlparse, urljoin
import pandas as pd 

# -----------------------------
# USER CONFIG - adjust if needed
# -----------------------------
OUTPUT_FOLDER = r"F:\Billing-Main\Python-Scripts\Output"
AREAS_CSV = os.path.join(OUTPUT_FOLDER, "areas_export.csv")
LOGIN_URL = "https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/login"
GET_SURVEY_URL = "https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/autoform/get-item-listing"
BASE_HOST = "https://suthra.punjab.gov.pk"

# Credentials
CNIC = "3840111639195"
PASSWORD = "1975@MuhammadHassanTMT"
USER_TYPE = "HRMIS_USER"

# Networking defaults
PAGE_SIZE = 50
REQUEST_RETRIES = 3
REQUEST_DELAY = 0.5
SESSION_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'Origin': 'https://suthra.punjab.gov.pk',
    'Referer': 'https://suthra.punjab.gov.pk/survey-app/view/survey-submissions',
}


# The exact displayedColumnsAll used in the browser (kept identical)
DISPLAY_COLUMNS_ALL = [
    {"key":"sr_no","column":True,"value":"Sr#"}, {"key":"added_by","column":True,"value":"Submitted By"},
    {"key":"id","column":True,"value":"Survey ID"}, {"key":"district_id","column":True,"value":"District"},
    {"key":"tehsil_id","column":True,"value":"Tehsil"}, {"key":"uc_type","column":True,"value":"UC Type"},
    {"key":"village_id","column":True,"value":"Village/Beat"}, {"key":"uc_id","column":True,"value":"UC"},
    {"key":"location","column":True,"value":"Location"}, {"key":"answers_table","column":True,"value":"Answers"},
    {"key":"billers_list","column":True,"value":"Total Billers"}, {"key":"new_str","column":True,"value":"Attachment"},
    {"key":"added_by_str","column":False,"value":"Added By"}, {"key":"added_date_time","column":False,"value":"Added Date&Time"},
    {"key":"app_version","column":True,"value":"App Version"}, {"key":"action","column":True,"value":"Action"},
]


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def sanitize_filename(name):
    if not isinstance(name, str): name = str(name)
    name = re.sub(r'[/\\]', '-', name)
    return re.sub(r'[:*?"<>|]', '', name)

def read_areas_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def build_full_attachment_url(fragment):
    if not fragment: return None
    fragment = fragment.strip().replace('public//', 'public/')
    if fragment.startswith(("http://", "https://")):
        return fragment
    return urljoin(BASE_HOST, f"/suthra-punjab/backend/public{fragment}")

def extract_attachment_urls_from_record(rec):
    urls = []
    att_field = rec.get("attachment") or rec.get("new_str") or ""
    if isinstance(att_field, str):
        hrefs = re.findall(r"href=['\"](.*?)['\"]", att_field)
        if hrefs:
            for h in hrefs: urls.append(build_full_attachment_url(h))
        else:
            parts = [p.strip() for p in att_field.split(",") if p.strip()]
            for p in parts: urls.append(build_full_attachment_url(p))
    return [u for u in urls if u]

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

def fetch_survey_page(session, page, size, district_id, tehsil_id, uc_id):
    payload = {
        "slug": "survey-submissions", "page": page, "size": size, "displayedColumnsAll": DISPLAY_COLUMNS_ALL,
        "filters_data": {"district_id": str(district_id or ""), "tehsil_id": str(tehsil_id or ""), "uc_id": str(uc_id or "")},
        "id": "0", "search_keyword": "", "requesting_url": "/survey-app/view/survey-submissions", "sorting": "", "user_type": "contractor", "plateform": "web"
    }
    for attempt in range(REQUEST_RETRIES):
        try:
            r = session.post(GET_SURVEY_URL, json=payload, timeout=30)
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
# SAVE RESULTS FUNCTIONS
# -----------------------------
# Updated to accept 'target_folder' argument
def save_results_csv(rows, district_name, tehsil_name, uc_name, target_folder):
    if not rows: return
    s_district, s_tehsil, s_uc = sanitize_filename(district_name), sanitize_filename(tehsil_name), sanitize_filename(uc_name)
    filename = os.path.join(target_folder, f"survey_{s_district}_{s_tehsil}_{s_uc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    fieldnames = [
        "survey_id", "added_by", "added_date_time", "uc_name",
        "location", "possible_address", "billing_category", "type",
        "attachments_urls"
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)
    print(f"✅ CSV saved → {filename}")

# Updated to accept 'target_folder' argument
def save_results_excel(rows, district_name, tehsil_name, uc_name, target_folder):
    if not rows: return
    s_district, s_tehsil, s_uc = sanitize_filename(district_name), sanitize_filename(tehsil_name), sanitize_filename(uc_name)
    filename = os.path.join(target_folder, f"survey_{s_district}_{s_tehsil}_{s_uc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

    excel_data = [row.copy() for row in rows]
    
    for row in excel_data:
        survey_id = row.get('survey_id')
        urls_str = row.get('attachments_urls', '')
        if urls_str and survey_id:
            urls = urls_str.split('|')
            hyperlinks = []
            for i, url in enumerate(urls, 1):
                friendly_name = f"{survey_id}_{i}"
                hyperlinks.append(f'=HYPERLINK("{url}", "{friendly_name}")')
            row['attachments_urls'] = ", ".join(hyperlinks)
            
    fieldnames = [
        "survey_id", "added_by", "added_date_time", "uc_name",
        "location", "possible_address", "billing_category", "type",
        "attachments_urls"
    ]
    
    df = pd.DataFrame(excel_data, columns=fieldnames)
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"✅ Excel saved → {filename}")

# -----------------------------
# MAIN WORKFLOW
# -----------------------------
def main():
    print("=== Final Survey Extractor (Batch Support) ===\n")
    
    # 1. Ask for Output Path
    user_path = input(f"Enter Output Folder Path (Press Enter for default: {OUTPUT_FOLDER}): ").strip()
    
    # Handle "Copy as path" quotes
    if len(user_path) >= 2 and user_path.startswith('"') and user_path.endswith('"'):
        user_path = user_path[1:-1]
    
    base_output_folder = user_path if user_path else OUTPUT_FOLDER
    ensure_dir(base_output_folder)
    print(f"📂 Saving files to root: {base_output_folder}\n")

    if not os.path.exists(AREAS_CSV):
        print(f"{AREAS_CSV} not found. Please place your areas_export.csv file there."); return

    areas = read_areas_csv(AREAS_CSV)

    print("Selection Mode:")
    print("  1) Enter specific area_id (Manual)")
    print("  2) Interactive Menu (Supports Batch Download)")
    mode = input("Choose mode (1/2) [1]: ").strip() or "1"
    
    target_areas_list = []

    if mode == "1":
        area_id_in = input("Enter area_id (UC/MC ID): ").strip()
        found = next((a for a in areas if a.get("area_id") == area_id_in), None)
        if found:
            target_areas_list = [found]
        else:
            print("Warning: area_id not found in CSV. Proceeding with raw ID.")
            target_areas_list = [{"area_id": area_id_in, "area_name": f"area_{area_id_in}", "district_name": "Unknown_District", "tehsil_name": "Unknown_Tehsil"}]
    else:
        # DISTRICT SELECTION
        districts = sorted(list({(a["district_id"], a["district_name"]) for a in areas}), key=lambda x: x[1])
        for i, d in enumerate(districts, 1): print(f"{i}. {d[1]}")
        di = int(input(f"Select District (1-{len(districts)}): ")) - 1
        district_id, district_name = districts[di]

        # TEHSIL SELECTION
        tehsils = sorted(list({(a["tehsil_id"], a["tehsil_name"]) for a in areas if a["district_id"] == district_id}), key=lambda x: x[1])
        print(f"\nDistrict: {district_name}")
        print("0. ALL TEHSILS (Entire District)")
        for i, t in enumerate(tehsils, 1): print(f"{i}. {t[1]}")
        
        ti_input = int(input(f"Select Tehsil (0-{len(tehsils)}): "))
        
        if ti_input == 0:
            # Get ALL UCs in District
            target_areas_list = [a for a in areas if a["district_id"] == district_id]
            print(f"Selected entire district: {len(target_areas_list)} Areas found.")
        else:
            tehsil_id, tehsil_name = tehsils[ti_input - 1]
            
            # UC SELECTION
            ucs = [a for a in areas if a["district_id"] == district_id and a["tehsil_id"] == tehsil_id]
            print(f"\nTehsil: {tehsil_name}")
            print("0. ALL UCs/MCs (Entire Tehsil)")
            for i, u in enumerate(ucs, 1): print(f"{i}. {u['area_name']} (id={u['area_id']})")
            
            ui_input = int(input(f"Select UC/MC (0-{len(ucs)}): "))
            
            if ui_input == 0:
                target_areas_list = ucs
                print(f"Selected entire tehsil: {len(target_areas_list)} Areas found.")
            else:
                target_areas_list = [ucs[ui_input - 1]]

    max_input = input("Max records PER AREA (leave blank for all): ").strip()
    max_records_per_area = int(max_input) if max_input else float('inf')

    session = do_login()
    print("✅ Logged in. Starting Batch Process...\n")

    # -----------------------------
    # BATCH PROCESSING LOOP
    # -----------------------------
    total_areas = len(target_areas_list)
    
    for idx, current_area in enumerate(target_areas_list, 1):
        d_name = current_area.get('district_name', 'Unknown')
        t_name = current_area.get('tehsil_name', 'Unknown')
        u_name = current_area.get('area_name', f"Area_{current_area.get('area_id')}")
        
        print(f"[{idx}/{total_areas}] Processing: {d_name} -> {t_name} -> {u_name} ...")

        # Create District Sub-folder
        district_folder = os.path.join(base_output_folder, sanitize_filename(d_name))
        ensure_dir(district_folder)

        all_records, page, total_fetched = [], 1, 0
        while total_fetched < max_records_per_area:
            # print(f"   Fetching page {page}...") # Optional: uncomment for verbosity
            data = fetch_survey_page(session, page, PAGE_SIZE, current_area.get("district_id"), current_area.get("tehsil_id"), current_area["area_id"])
            page_records = extract_records_from_response(data)
            if not page_records: break
            for rec in page_records:
                if total_fetched >= max_records_per_area: break
                all_records.append(rec); total_fetched += 1
            page += 1; time.sleep(REQUEST_DELAY)

        if not all_records: 
            print(f"   ⚠️ No records found for {u_name}.")
            continue

        # Prepare Data
        first_rec = all_records[0]
        # Fallback to CSV names if API names missing
        final_district_name = first_rec.get('districts.district_id.name', d_name)
        final_tehsil_name = first_rec.get('tehsils.tehsil_id.name', t_name)
        final_area_name = first_rec.get('sw_areas.uc_id.name', u_name)

        results_for_output = []
        for rec in all_records:
            sid = rec.get("id") or rec.get("survey_id")
            answers_data = rec.get("answers_json", {})
            row = {
                "survey_id": sid, "added_by": rec.get("added_by_str"), "added_date_time": rec.get("added_date_time"),
                "uc_name": final_area_name, "location": rec.get("location"),
                "possible_address": answers_data.get('address'), "billing_category": answers_data.get('area'), "type": answers_data.get('house_type'),
            }
            att_urls = extract_attachment_urls_from_record(rec)
            row["attachments_urls"] = "|".join(att_urls)
            results_for_output.append(row)

        # Save to District Folder
        save_results_csv(results_for_output, final_district_name, final_tehsil_name, final_area_name, district_folder)
        save_results_excel(results_for_output, final_district_name, final_tehsil_name, final_area_name, district_folder)
        
    print("\n✅ All selected areas processed.")

if __name__ == "__main__":
    main()