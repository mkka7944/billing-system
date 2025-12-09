#!/usr/bin/env python3
"""
Advanced Survey Extractor v5 (Deep Drill Fix)
- FIX: Aggressively hunts for 'Answers' in multiple possible keys (json/table/str).
- FIX: Force-parses stringified JSON to ensure nested fields appear as columns.
- Strategy: Scrape by District -> Sync one by one.
"""

import requests
import csv
import os
import time
import re
import json
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse, urljoin

# -----------------------------
# USER CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "..", "outputs", "scraped_data")
AREAS_CSV = os.path.join(BASE_DIR, "..", "inputs", "config_files", "areas_export.csv")

LOGIN_URL = "https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/login"
GET_SURVEY_URL = "https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/autoform/get-item-listing"
BASE_HOST = "https://suthra.punjab.gov.pk"

# Credentials
CNIC = "3840111639195"
PASSWORD = "1975@MuhammadHassanTMT"
USER_TYPE = "HRMIS_USER"

# Networking
PAGE_SIZE = 50
REQUEST_RETRIES = 3
SESSION_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'Origin': 'https://suthra.punjab.gov.pk',
    'Referer': 'https://suthra.punjab.gov.pk/survey-app/view/survey-submissions',
}

# Standard Columns required by API
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
    if not os.path.exists(path):
        print(f"❌ Error: areas_export.csv not found at: {path}")
        return []
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

def clean_surveyor_name(rec):
    raw_name = rec.get("added_by")
    if isinstance(raw_name, str) and not raw_name.isdigit():
        return raw_name.strip()
    composite = rec.get("added_by_str", "")
    if composite:
        clean = re.split(r'[/(\-]', composite)[0]
        return clean.strip()
    return ""

# -----------------------------
# LOGIN & FETCH
# -----------------------------
def do_login():
    s = requests.Session()
    s.headers.update(SESSION_HEADERS)
    try:
        print("🔑 Authenticating with Portal...", end="\r")
        resp = s.post(LOGIN_URL, json={"cnic": CNIC, "password": PASSWORD, "user_type": USER_TYPE}, timeout=25)
        resp.raise_for_status()
        token = resp.json().get("data", {}).get("token")
        if not token: raise RuntimeError("Token not found")
        s.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Authentication Successful!       ")
        return s
    except Exception as e:
        raise RuntimeError(f"Login failed: {e}")

def fetch_survey_page(session, page, size, district_id, tehsil_id, uc_id):
    payload = {
        "slug": "survey-submissions", "page": page, "size": size, 
        "displayedColumnsAll": DISPLAY_COLUMNS_ALL,
        "filters_data": {
            "district_id": str(district_id or ""), 
            "tehsil_id": str(tehsil_id or ""), 
            "uc_id": str(uc_id or "")
        },
        "id": "0", "search_keyword": "", 
        "requesting_url": "/survey-app/view/survey-submissions", 
        "sorting": "", "user_type": "contractor", "plateform": "web"
    }
    for attempt in range(REQUEST_RETRIES):
        try:
            r = session.post(GET_SURVEY_URL, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            time.sleep(1)
    return {}

def extract_records_from_response(data):
    if not data: return []
    payload = data.get("data", data)
    if isinstance(payload, dict):
        for key in ("listings", "items", "records", "data"):
            if isinstance(payload.get(key), list): return payload[key]
    return payload if isinstance(payload, list) else []

# -----------------------------
# DATA PROCESSOR (Deep Drill Logic)
# -----------------------------
def flatten_record(rec, district_name, tehsil_name, uc_name):
    flat = {
        "Survey ID": rec.get("id") or rec.get("survey_id"),
        "Surveyor Name": clean_surveyor_name(rec),
        "Survey Timestamp": rec.get("added_date_time"),
        "GPS Coordinates": rec.get("location"),
        "District": district_name,
        "Tehsil": tehsil_name,
        "Union Council": uc_name,
        "UC Type": rec.get("uc_type"),
    }
    
    # Images
    urls = extract_attachment_urls_from_record(rec)
    flat["Image URLs"] = " | ".join(urls)
    
    # --- DEEP DRILL FOR ANSWERS ---
    # Try all possible keys where answers might hide
    answers = rec.get("answers_json") or rec.get("answers_table") or rec.get("answers")
    
    # If it's a string that looks like a dict, try to parse it
    if isinstance(answers, str) and answers.strip().startswith("{"):
        try:
            answers = json.loads(answers)
        except:
            pass # Keep as string if parse fails

    # Case A: Dictionary (Ideal)
    if isinstance(answers, dict):
        for k, v in answers.items():
            clean_key = k.replace("_", " ").title()
            # Handle if value is a list or dict
            if isinstance(v, (dict, list)): v = str(v)
            flat[clean_key] = str(v).strip()
            
    # Case B: Pipe Separated String (Legacy)
    elif isinstance(answers, str) and "|" in answers:
        parts = answers.split("|")
        for part in parts:
            if ":" in part:
                k, v = part.split(":", 1)
                flat[k.strip()] = v.strip()
            else:
                flat["Additional Info"] = flat.get("Additional Info", "") + " " + part.strip()
    
    return flat

# -----------------------------
# MAIN WORKFLOW
# -----------------------------
def main():
    print("================================================")
    print("   Advanced Survey Extractor v5 (Deep Drill)    ")
    print("================================================\n")
    ensure_dir(OUTPUT_FOLDER)
    
    areas = read_areas_csv(AREAS_CSV)
    if not areas: return

    print("Selection Mode:")
    print("  1) Enter specific area_id (Manual)")
    print("  2) Interactive Menu (Batch Mode)")
    mode = input("Choose mode (1/2) [1]: ").strip() or "1"
    
    target_areas_list = []

    if mode == "1":
        area_id_in = input("Enter area_id (UC/MC ID): ").strip()
        found = next((a for a in areas if a.get("area_id") == area_id_in), None)
        if found: target_areas_list = [found]
        else: target_areas_list = [{"area_id": area_id_in, "area_name": f"Area_{area_id_in}", "district_name": "Unknown", "tehsil_name": "Unknown"}]
    else:
        # Full Menu Logic
        districts = sorted(list({(a["district_id"], a["district_name"]) for a in areas}), key=lambda x: x[1])
        for i, d in enumerate(districts, 1): print(f"{i}. {d[1]}")
        di = int(input(f"Select District (1-{len(districts)}): ")) - 1
        d_id, d_name = districts[di]
        
        tehsils = sorted(list({(a["tehsil_id"], a["tehsil_name"]) for a in areas if a["district_id"] == d_id}), key=lambda x: x[1])
        print(f"\nDistrict: {d_name}")
        print("0. ALL TEHSILS")
        for i, t in enumerate(tehsils, 1): print(f"{i}. {t[1]}")
        ti = int(input(f"Select Tehsil (0-{len(tehsils)}): "))
        
        if ti == 0:
            target_areas_list = [a for a in areas if a["district_id"] == d_id]
        else:
            t_id, t_name = tehsils[ti - 1]
            ucs = [a for a in areas if a["district_id"] == d_id and a["tehsil_id"] == t_id]
            print(f"\nTehsil: {t_name}")
            print("0. ALL UCs")
            for i, u in enumerate(ucs, 1): print(f"{i}. {u['area_name']} ({u['area_id']})")
            ui = int(input(f"Select UC (0-{len(ucs)}): "))
            if ui == 0: target_areas_list = ucs
            else: target_areas_list = [ucs[ui - 1]]

    max_recs = input("Max records PER AREA (Enter for all): ").strip()
    max_limit = int(max_recs) if max_recs else float('inf')

    session = do_login()
    print("\n🚀 STARTING EXTRACTION PIPELINE...\n")
    
    MASTER_DATA = []
    total_areas = len(target_areas_list)
    grand_total_records = 0
    start_time_global = time.time()

    for idx, area in enumerate(target_areas_list, 1):
        d_name = area.get('district_name', 'Unknown')
        t_name = area.get('tehsil_name', 'Unknown')
        u_name = area.get('area_name', f"Area_{area.get('area_id')}")
        u_id = area.get('area_id')
        
        print(f"[{idx}/{total_areas}] Initializing: {u_name}...")
        
        area_folder = os.path.join(OUTPUT_FOLDER, sanitize_filename(d_name), sanitize_filename(t_name))
        ensure_dir(area_folder)
        
        fetched_count = 0
        page = 1
        area_records_raw = []
        start_time_area = time.time()
        
        while fetched_count < max_limit:
            print(f"   ⏳ Page {page}: Fetched {len(area_records_raw)} records...", end="\r")
            data = fetch_survey_page(session, page, PAGE_SIZE, area.get("district_id"), area.get("tehsil_id"), u_id)
            recs = extract_records_from_response(data)
            if not recs: break
            
            area_records_raw.extend(recs)
            fetched_count += len(recs)
            page += 1
            time.sleep(0.2)
        
        print(" " * 60, end="\r")
        
        if not area_records_raw:
            print(f"   ⚠️ No records found for {u_name}.")
            continue
            
        processed_area_data = []
        for raw in area_records_raw:
            final_d = raw.get('districts.district_id.name', d_name)
            final_t = raw.get('tehsils.tehsil_id.name', t_name)
            final_u = raw.get('sw_areas.uc_id.name', u_name)
            flat_row = flatten_record(raw, final_d, final_t, final_u)
            processed_area_data.append(flat_row)

        MASTER_DATA.extend(processed_area_data)
        grand_total_records += len(processed_area_data)
        elapsed_area = round(time.time() - start_time_area, 2)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        safe_u_name = sanitize_filename(u_name)
        df_area = pd.DataFrame(processed_area_data)
        filename = os.path.join(area_folder, f"Survey_{safe_u_name}_{timestamp}.xlsx")
        df_area.to_excel(filename, index=False)
        
        print(f"   ------------------------------------------------")
        print(f"   ✅ COMPLETED: {u_name}")
        print(f"   📄 Records:   {len(processed_area_data)}")
        print(f"   ⏱️ Time:      {elapsed_area}s")
        print(f"   💾 Saved to:  .../{os.path.basename(filename)}")
        print(f"   ------------------------------------------------\n")

    if MASTER_DATA:
        print("\n🔗 Generating Combined Master File (Please wait)...")
        df_master = pd.DataFrame(MASTER_DATA)
        df_master.insert(0, "Sr#", range(1, len(df_master) + 1))
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        master_filename = os.path.join(OUTPUT_FOLDER, f"COMBINED_SURVEY_MASTER_{timestamp}.xlsx")
        
        if "Survey Timestamp" in df_master.columns:
             df_master.sort_values(by="Survey Timestamp", ascending=False, inplace=True)

        df_master.to_excel(master_filename, index=False)
        
        elapsed_global = round((time.time() - start_time_global) / 60, 2)
        
        print("\n================================================")
        print("🎉 MISSION ACCOMPLISHED")
        print(f"📄 Grand Total Records:    {grand_total_records}")
        print(f"💾 MASTER FILE:            {master_filename}")
        print("================================================")
    else:
        print("\n⚠️ No data collected.")

if __name__ == "__main__":
    main()