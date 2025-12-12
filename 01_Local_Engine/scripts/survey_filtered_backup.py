#!/usr/bin/env python3
"""
Advanced Survey Extractor v5 (Deep Drill Fix) - PAGINATION VERSION
- Reads survey data by fetching a specified number of pages
- Outputs to Excel with clickable image URLs
- FIX: Aggressively hunts for 'Answers' in multiple possible keys (json/table/str).
- FIX: Force-parses stringified JSON to ensure nested fields appear as columns.
- Strategy: Direct fetch from Sargodha District/Sargodha Tehsil using CSV data.
"""

import requests
import csv
import os
import time
import re
import json
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from tqdm import tqdm
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
PAGE_SIZE = 250  # Increased from 50 to 250 records per page
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

def create_clickable_link(url, link_text="View Image"):
    """Create Excel clickable hyperlink formula"""
    if not url:
        return ""
    # Escape any quotes in the URL
    escaped_url = url.replace('"', '""')
    return f'=HYPERLINK("{escaped_url}", "{link_text}")'

def split_timestamp(timestamp):
    """Split timestamp into separate date and time components"""
    if not timestamp:
        return "", ""
    
    # Handle various timestamp formats
    try:
        # Try to parse the timestamp
        # Common formats: "YYYY-MM-DD HH:MM:SS" or "DD/MM/YYYY HH:MM:SS"
        if ' ' in timestamp:
            date_part, time_part = timestamp.split(' ', 1)
            return date_part, time_part
        else:
            # If no space, assume it's just a date
            return timestamp, ""
    except:
        # If parsing fails, return as-is
        return timestamp, ""

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

def fetch_survey_page(session, page, size, district_id, tehsil_id):
    payload = {
        "slug": "survey-submissions", "page": page, "size": size, 
        "displayedColumnsAll": DISPLAY_COLUMNS_ALL,
        "filters_data": {
            "district_id": str(district_id or ""), 
            "tehsil_id": str(tehsil_id or "")
        },
        "id": "0", "search_keyword": "", 
        "requesting_url": "/survey-app/view/survey-submissions", 
        "sorting": "", "user_type": "contractor", "plateform": "web"
    }
    
    for attempt in range(REQUEST_RETRIES):
        try:
            # Increase timeout to 60 seconds to handle slow responses
            r = session.post(GET_SURVEY_URL, json=payload, timeout=60)
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
        # If we didn't find any of the expected keys, let's check all keys
        for key, value in payload.items():
            if isinstance(value, list) and len(value) > 0:
                # Let's check if this looks like survey data
                if isinstance(value[0], dict) and ('id' in value[0] or 'survey_id' in value[0]):
                    return value
    return payload if isinstance(payload, list) else []
# -----------------------------
# FIND SARGODHA IDS
# -----------------------------
def find_sargodha_ids(areas):
    """Find Sargodha district and tehsil IDs from the areas data"""
    # Find Sargodha district
    sargodha_district = None
    for area in areas:
        if "sargodha" in area.get("district_name", "").lower():
            sargodha_district = area
            break
    
    if not sargodha_district:
        print("⚠️ Sargodha district not found in areas data")
        return None, None
    
    district_id = sargodha_district.get("district_id")
    district_name = sargodha_district.get("district_name")
    
    # Find Sargodha tehsil within the district
    sargodha_tehsil = None
    for area in areas:
        if (area.get("district_id") == district_id and 
            "sargodha" in area.get("tehsil_name", "").lower()):
            sargodha_tehsil = area
            break
    
    if not sargodha_tehsil:
        print("⚠️ Sargodha tehsil not found in areas data")
        return district_id, None
    
    tehsil_id = sargodha_tehsil.get("tehsil_id")
    tehsil_name = sargodha_tehsil.get("tehsil_name")
    
    print(f"📍 Found: {district_name} (ID: {district_id}) / {tehsil_name} (ID: {tehsil_id})")
    return district_id, tehsil_id

# -----------------------------
# DATA PROCESSOR (Deep Drill Logic)
# -----------------------------
def flatten_record(rec, district_name, tehsil_name, uc_name):
    # Parse GPS coordinates into separate lat/long columns for mymapp
    gps_coords = rec.get("location", "")
    latitude = ""
    longitude = ""
    if gps_coords and "," in gps_coords:
        try:
            lat_str, long_str = gps_coords.split(",", 1)
            latitude = lat_str.strip()
            longitude = long_str.strip()
        except:
            pass  # Keep empty if parsing fails
    
    flat = {
        "Survey ID": rec.get("id") or rec.get("survey_id"),
        "Surveyor Name": clean_surveyor_name(rec),
        "Latitude": latitude,
        "Longitude": longitude,
        "District": district_name,
        "Tehsil": tehsil_name,
        "Union Council": uc_name,
        "UC Type": rec.get("uc_type"),
    }    
    # Split timestamp into date and time
    timestamp = rec.get("added_date_time", "")
    date_part, time_part = split_timestamp(timestamp)
    flat["Survey Date"] = date_part
    flat["Survey Time"] = time_part
    
    # Images - Extract URLs
    urls = extract_attachment_urls_from_record(rec)
    flat["Image URLs"] = " | ".join(urls)
    
    # Create separate clickable link columns for up to 3 images (for Excel only)
    for i in range(3):
        if i < len(urls):
            flat[f"Clickable Image {i+1}"] = create_clickable_link(urls[i], f"Image {i+1}")
        else:
            flat[f"Clickable Image {i+1}"] = ""
    
    # Create separate URL columns for up to 4 images (for CSV only)
    for i in range(4):
        if i < len(urls):
            flat[f"Image URL {i+1}"] = urls[i]
        else:
            flat[f"Image URL {i+1}"] = ""
    
    # --- DEEP DRILL FOR ANSWERS ---
    # Try all possible keys where answers might hide
    answers = rec.get("answers_json") or rec.get("answers_table") or rec.get("answers")
    
    # If it's a string that looks like a dict, try to parse it
    if isinstance(answers, str) and answers.strip().startswith("{"):
        try:
            answers = json.loads(answers)
        except:
            pass # Keep as string if parse fails

    # Initialize consumer type as unknown
    consumer_type = "Unknown"
    
    # Case A: Dictionary (Ideal)
    if isinstance(answers, dict):
        for k, v in answers.items():
            clean_key = k.replace("_", " ").title()
            # Handle if value is a list or dict
            if isinstance(v, (dict, list)): v = str(v)
            flat[clean_key] = str(v).strip()
            
            # Determine consumer type based on house type or type field
            if k.lower() == "house type":
                consumer_type = "Domestic"  # If house type field exists, it's domestic
            elif k.lower() == "type" and str(v).strip().lower() not in ["", "house", "residential"]:
                consumer_type = "Commercial"  # If type field exists and is not residential, it's commercial
                
    # Case B: Pipe Separated String (Legacy)
    elif isinstance(answers, str) and "|" in answers:
        parts = answers.split("|")
        for part in parts:
            if ":" in part:
                k, v = part.split(":", 1)
                flat[k.strip()] = v.strip()
                
                # Determine consumer type based on house type or type field
                if k.lower().strip() == "house type":
                    consumer_type = "Domestic"  # If house type field exists, it's domestic
                elif k.lower().strip() == "type" and v.strip().lower() not in ["", "house", "residential"]:
                    consumer_type = "Commercial"  # If type field exists and is not residential, it's commercial
            else:
                flat["Additional Info"] = flat.get("Additional Info", "") + " " + part.strip()
    
    # Add the consumer type column
    flat["Consumer Type"] = consumer_type
    
    return flat

# -----------------------------
# MAIN WORKFLOW
# -----------------------------
def main():
    print("================================================")
    print("   Advanced Survey Extractor v5 (SARGODHA ONLY)   ")
    print("================================================\n")
    ensure_dir(OUTPUT_FOLDER)
    
    # Read areas data from CSV
    areas = read_areas_csv(AREAS_CSV)
    if not areas:
        print("❌ Error: Could not read areas data")
        return
    
    # Find Sargodha district and tehsil IDs
    print("🔍 Looking for Sargodha district/tehsil in areas data...")
    district_id, tehsil_id = find_sargodha_ids(areas)
    
    if not district_id:
        print("❌ Error: Could not find Sargodha district")
        return
    
    if not tehsil_id:
        print("❌ Error: Could not find Sargodha tehsil")
        return
    
    # Get the number of pages to fetch
    pages_input = input("Enter number of pages to fetch (e.g., 5 for 1250 records): ").strip()
    try:
        num_pages = int(pages_input)
        if num_pages <= 0:
            print("Invalid number of pages. Using default of 5 pages.")
            num_pages = 5
    except ValueError:
        print("Invalid input. Using default of 5 pages.")
        num_pages = 5

    session = do_login()
    print(f"\n🚀 FETCHING DATA FROM SARGODHA DISTRICT/TEHSIL FOR {num_pages} PAGES...\n")
    
    MASTER_DATA = []
    grand_total_records = 0
    start_time_global = time.time()
    
    print("Processing: Sargodha District/Sargodha Tehsil...")
    
    area_records_raw = []
    start_time_area = time.time()
    
    # Fetch specified number of pages from Sargodha District/Sargodha Tehsil
    print(f"   📥 Fetching {num_pages} pages of data...")
    total_records_fetched = 0
    area_records_raw = []
    
    # Create a progress bar for pages
    with tqdm(total=num_pages, desc="   📄 Fetching pages", leave=True) as page_bar:
        for page in range(1, num_pages + 1):
            page_bar.set_description(f"   📄 Fetching page {page}/{num_pages}")
            
            data = fetch_survey_page(session, page, PAGE_SIZE, district_id, tehsil_id)
            recs = extract_records_from_response(data)
            
            if not recs: 
                print(f"   ⚠️ No more records found on page {page}")
                break
            
            area_records_raw.extend(recs)
            total_records_fetched += len(recs)
            page_bar.update(1)
            time.sleep(0.2)
    
    print()  # New line after progress updates
    
    if not area_records_raw:
        print("   ⚠️ No records found for Sargodha District/Sargodha Tehsil.")
        return
        
    processed_area_data = []
    for raw in area_records_raw:
        # Extract location information from the record
        district_name = raw.get('districts.district_id.name', 'Sargodha')
        tehsil_name = raw.get('tehsils.tehsil_id.name', 'Sargodha')
        uc_name = raw.get('sw_areas.uc_id.name', 'Unknown UC')
        
        flat_row = flatten_record(raw, district_name, tehsil_name, uc_name)
        processed_area_data.append(flat_row)
    
    if not processed_area_data:
        print("   ⚠️ No records found for Sargodha District/Sargodha Tehsil.")
        return
        
    MASTER_DATA.extend(processed_area_data)
    grand_total_records += len(processed_area_data)
    elapsed_area = round(time.time() - start_time_area, 2)
    
    print("   ------------------------------------------------")
    print("   ✅ COMPLETED: Sargodha District/Sargodha Tehsil")
    print(f"   📄 Records:   {len(processed_area_data)}")
    print(f"   ⏱️ Time:      {elapsed_area}s")
    print("   ------------------------------------------------\n")

    if MASTER_DATA:
        print("\n🔗 Generating Combined Master Files (Please wait)...")
        df_master = pd.DataFrame(MASTER_DATA)
        df_master.insert(0, "Sr#", range(1, len(df_master) + 1))
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sort by Survey Date if available
        if "Survey Date" in df_master.columns:
             df_master.sort_values(by=["Survey Date", "Survey Time"], ascending=False, inplace=True)
        
        # Create Excel file with clickable links
        excel_filename = os.path.join(OUTPUT_FOLDER, f"SARGODHA_SURVEY_MASTER_{num_pages}Pages_{timestamp}.xlsx")
        df_master.to_excel(excel_filename, index=False)
        
        # Create CSV file with separate image URL columns and no clickable links
        csv_filename = os.path.join(OUTPUT_FOLDER, f"SARGODHA_SURVEY_MASTER_{num_pages}Pages_{timestamp}.csv")
        
        # Remove clickable link columns for CSV and exclude the combined "Image URLs" column
        csv_columns = [col for col in df_master.columns if not col.startswith("Clickable Image") and col != "Image URLs"]
        df_csv = df_master[csv_columns]
        
        # Reorder columns to put Image URL columns at the end
        image_url_columns = [col for col in csv_columns if col.startswith("Image URL")]
        other_columns = [col for col in csv_columns if not col.startswith("Image URL")]
        reordered_columns = other_columns + image_url_columns
        df_csv = df_csv[reordered_columns]        
        df_csv.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        elapsed_global = round((time.time() - start_time_global) / 60, 2)
        
        print("\n================================================")
        print("🎉 MISSION ACCOMPLISHED")
        print(f"📄 Grand Total Records: {grand_total_records}")
        print(f"📄 Pages Fetched:       {num_pages} pages ({PAGE_SIZE} records per page)")
        print(f"💾 EXCEL FILE:          {excel_filename}")
        print(f"💾 CSV FILE:            {csv_filename}")
        print("================================================")
    else:
        print("\n⚠️ No data collected.")

if __name__ == "__main__":
    main()