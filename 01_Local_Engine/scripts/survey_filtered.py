#!/usr/bin/env python3
"""
Advanced Survey Extractor v6 - Multi-District/Tehsil Support
- Reads survey data by fetching a specified number of pages
- Processes multiple district/tehsil combinations:
  1. District Khushab (16) / Tehsil Khushab (133)
  2. District Sargodha (32) / Tehsil Sargodha (143)
  3. District Sargodha (32) / Tehsil Bhalwal (139)
- Outputs separate Excel/CSV files for each combination
- Outputs to Excel with clickable image URLs
- FIX: Aggressively hunts for 'Answers' in multiple possible keys (json/table/str).
- FIX: Force-parses stringified JSON to ensure nested fields appear as columns.
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

# District/Tehsil combinations to process
DISTRICT_TEHSIL_COMBINATIONS = [
    {"district_id": 16, "tehsil_id": 133, "district_name": "Khushab", "tehsil_name": "Khushab"},
    {"district_id": 32, "tehsil_id": 143, "district_name": "Sargodha", "tehsil_name": "Sargodha"},
    {"district_id": 32, "tehsil_id": 139, "district_name": "Sargodha", "tehsil_name": "Bhalwal"}
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
        # First check for the known path 'listings' which is where survey data is located
        if isinstance(payload.get("listings"), list): return payload["listings"]
        
        # Then check other possible keys
        for key in ("items", "records", "data"):
            if isinstance(payload.get(key), list): return payload[key]
        
        # If we didn't find any of the expected keys, let's check all keys
        for key, value in payload.items():
            if isinstance(value, list) and len(value) > 0:
                # Let's check if this looks like survey data
                if isinstance(value[0], dict) and ('id' in value[0] or 'survey_id' in value[0]):
                    return value
    return payload if isinstance(payload, list) else []

# -----------------------------
# NEW FUNCTION TO GET TOTAL RECORDS COUNT
# -----------------------------
def get_total_records_count(session, district_id, tehsil_id):
    """Get the total number of records available for a district/tehsil combination"""
    try:
        # Request just the first page with a small size (10) to quickly get pagination info
        data = fetch_survey_page(session, 1, 10, district_id, tehsil_id)
        if data and isinstance(data, dict):
            # Look for pagination info in various possible locations in the response
            payload = data.get("data", data)
            if isinstance(payload, dict):
                # Check for totalInDB field which contains the total record count
                if "totalInDB" in payload:
                    return payload["totalInDB"]
                
                # Check for pagination information first
                if "pagination" in payload and isinstance(payload["pagination"], dict):
                    pagination = payload["pagination"]
                    # Look for totalPages or similar pagination info
                    for key in ("totalPages", "total_pages", "lastPage", "last_page"):
                        if key in pagination:
                            total_pages = pagination[key]
                            # Calculate total records based on pages and page size
                            return total_pages * PAGE_SIZE
                    
                    # Look for total records count directly
                    for key in ("total", "count", "totalCount", "recordCount", "total_records"):
                        if key in pagination:
                            return pagination[key]
                        
                # Check for total count in the main payload
                for key in ("total", "count", "totalCount", "recordCount", "total_records"):
                    if key in payload:
                        return payload[key]
                        
    except Exception as e:
        print(f"   ⚠️ Could not determine total records: {e}")
    return None

def process_district_tehsil_combination(session, district_id, tehsil_id, district_name, tehsil_name, num_pages, fetch_all=False):
    """Process a single district/tehsil combination and return the data"""
    first_page_data = None
    first_page_records = None
    
    if fetch_all:
        print(f"\n🚀 FETCHING ALL DATA FROM {district_name.upper()} DISTRICT/{tehsil_name.upper()} TEHSIL...")
        # Try to determine total records/pages
        total_records = get_total_records_count(session, district_id, tehsil_id)
        if total_records:
            # Calculate required pages (rounding up)
            calculated_pages = (total_records + PAGE_SIZE - 1) // PAGE_SIZE
            print(f"   📊 Total records available: {total_records} ({calculated_pages} pages needed)")
            num_pages = calculated_pages
        else:
            print(f"   ⚠️ Could not determine total records. Will fetch pages dynamically until no more data.")
            # Fetch first page to check pagination info
            first_page_data = fetch_survey_page(session, 1, PAGE_SIZE, district_id, tehsil_id)
            first_page_records = extract_records_from_response(first_page_data)
            
            if not first_page_records:
                print(f"   ⚠️ No records found on first page.")
                return []
            
            # Try to get pagination info from first page
            total_pages = None
            if first_page_data and isinstance(first_page_data, dict):
                payload = first_page_data.get("data", first_page_data)
                if isinstance(payload, dict) and "pagination" in payload:
                    pagination = payload["pagination"]
                    for key in ("totalPages", "total_pages", "lastPage", "last_page"):
                        if key in pagination:
                            total_pages = pagination[key]
                            break
            
            if total_pages:
                print(f"   📊 Total pages available: {total_pages}")
                num_pages = total_pages
            else:
                # If we still can't determine total pages, we'll fetch incrementally
                print(f"   ⚠️ Could not determine total pages. Will fetch incrementally until no more data.")
                num_pages = 1000  # Reasonable upper limit for incremental fetching
    else:
        print(f"\n🚀 FETCHING DATA FROM {district_name.upper()} DISTRICT/{tehsil_name.upper()} TEHSIL FOR {num_pages} PAGES...\n")
    
    area_records_raw = []
    
    # Fetch specified number of pages
    print(f"   📥 Fetching up to {num_pages} pages of data...")
    total_records_fetched = 0
    
    # Create a progress bar for pages
    with tqdm(total=num_pages, desc="   📄 Fetching pages", leave=True) as page_bar:
        for page in range(1, num_pages + 1):
            page_bar.set_description(f"   📄 Fetching page {page}/{num_pages}")
            
            # Use first page data if we already fetched it for pagination info
            if fetch_all and page == 1 and first_page_records:
                recs = first_page_records
            else:
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
        print(f"   ⚠️ No records found for {district_name} District/{tehsil_name} Tehsil.")
        return []
        
    processed_area_data = []
    for raw in area_records_raw:
        # Extract location information from the record
        uc_name = raw.get('sw_areas.uc_id.name', 'Unknown UC')
        
        flat_row = flatten_record(raw, district_name, tehsil_name, uc_name)
        processed_area_data.append(flat_row)
    
    if not processed_area_data:
        print(f"   ⚠️ No records found for {district_name} District/{tehsil_name} Tehsil.")
        return []
        
    return processed_area_data

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

    # Initialize consumer type as domestic by default
    consumer_type = "Domestic"
    
    # Track if we have house type and type fields
    house_type_value = ""
    type_value = ""
    
    # Case A: Dictionary (Ideal)
    if isinstance(answers, dict):
        for k, v in answers.items():
            clean_key = k.replace("_", " ").title()
            # Handle if value is a list or dict
            if isinstance(v, (dict, list)): v = str(v)
            flat[clean_key] = str(v).strip()
            
            # Capture house type and type field values for consumer classification
            if k.lower() == "house type":
                house_type_value = str(v).strip()
            elif k.lower() == "type":
                type_value = str(v).strip().lower()
                
        # Apply the simplified consumer type logic:
        # - If House Type field is empty -> Commercial
        # - If House Type field contains any value -> Domestic
        if house_type_value == '' or house_type_value.lower() == 'nan' or house_type_value.lower() == 'none':
            consumer_type = "Commercial"
        else:
            consumer_type = "Domestic"
                
    # Case B: Pipe Separated String (Legacy)
    elif isinstance(answers, str) and "|" in answers:
        parts = answers.split("|")
        house_type_value = ""
        type_value = ""
        
        for part in parts:
            if ":" in part:
                k, v = part.split(":", 1)
                flat[k.strip()] = v.strip()
                
                # Capture house type and type field values for consumer classification
                if k.lower().strip() == "house type":
                    house_type_value = v.strip()
                elif k.lower().strip() == "type":
                    type_value = v.strip().lower()
            else:
                flat["Additional Info"] = flat.get("Additional Info", "") + " " + part.strip()
                
        # Apply the simplified consumer type logic:
        # - If House Type field is empty -> Commercial
        # - If House Type field contains any value -> Domestic
        if house_type_value == '' or house_type_value.lower() == 'nan' or house_type_value.lower() == 'none':
            consumer_type = "Commercial"
        else:
            consumer_type = "Domestic"
    
    # Add the consumer type column
    flat["Consumer Type"] = consumer_type
    
    return flat

# -----------------------------
# MAIN WORKFLOW
# -----------------------------

def save_data_to_files(data, district_name, tehsil_name):
    """Save data to separate Excel and CSV files"""
    if not data:
        print(f"   ⚠️ No data to save for {district_name} District/{tehsil_name} Tehsil.")
        return
        
    print(f"\n🔗 Generating Files for {district_name} District/{tehsil_name} Tehsil (Please wait)...")
    df = pd.DataFrame(data)
    df.insert(0, "Sr#", range(1, len(df) + 1))
    
    # Use descriptive filename based on district/tehsil
    filename_base = f"{district_name.upper()}_{tehsil_name.upper()}_SURVEY_DATA"
    
    # Sort by Survey Date if available
    if "Survey Date" in df.columns:
         df.sort_values(by=["Survey Date", "Survey Time"], ascending=False, inplace=True)
    
    # Create Excel file with clickable links
    excel_filename = os.path.join(OUTPUT_FOLDER, f"{filename_base}.xlsx")
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=f'{district_name} {tehsil_name} Survey Data')
    
    # Create CSV file with separate image URL columns and no clickable links
    csv_filename = os.path.join(OUTPUT_FOLDER, f"{filename_base}.csv")
    
    # Remove clickable link columns for CSV and exclude the combined "Image URLs" column
    csv_columns = [col for col in df.columns if not col.startswith("Clickable Image") and col != "Image URLs"]
    df_csv = df[csv_columns]
    
    # Reorder columns to put Image URL columns at the end
    image_url_columns = [col for col in csv_columns if col.startswith("Image URL")]
    other_columns = [col for col in csv_columns if not col.startswith("Image URL")]
    reordered_columns = other_columns + image_url_columns
    df_csv = df_csv[reordered_columns]        
    
    # Add error handling for file writing
    try:
        df_csv.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    except PermissionError:
        print(f"⚠️ Permission denied when writing CSV file: {csv_filename}")
        print("   Please close any applications that might be using this file and try again.")
        print("   Common causes: Excel has the file open, or Google Drive is syncing the file.")
        return
    except Exception as e:
        print(f"⚠️ Error writing CSV file: {e}")
        return
    
    print(f"   📄 Records:   {len(data)}")
    print(f"   💾 EXCEL FILE: {excel_filename}")
    print(f"   💾 CSV FILE:   {csv_filename}")

def main():
    print("================================================")
    print("   Advanced Survey Extractor v6 (MULTI-DISTRICT)   ")
    print("================================================\n")
    ensure_dir(OUTPUT_FOLDER)
    
    # Read areas data from CSV
    areas = read_areas_csv(AREAS_CSV)
    if not areas:
        print("❌ Error: Could not read areas data")
        return
    
    # Get user choice for download mode
    print("Download Options:")
    print("1. Download specific number of pages")
    print("2. Download ALL available data")
    choice = input("Select option (1 or 2): ").strip()
    
    fetch_all = False
    num_pages = 5  # Default
    
    if choice == "2":
        fetch_all = True
        print("Selected: Download ALL available data")
    else:
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
    
    # Process each district/tehsil combination
    all_processed_data = []
    
    for combo in DISTRICT_TEHSIL_COMBINATIONS:
        district_id = combo["district_id"]
        tehsil_id = combo["tehsil_id"]
        district_name = combo["district_name"]
        tehsil_name = combo["tehsil_name"]
        
        print(f"\n{'='*50}")
        print(f"Processing: {district_name} District/{tehsil_name} Tehsil")
        print(f"{'='*50}")
        
        # Process this combination
        processed_data = process_district_tehsil_combination(
            session, district_id, tehsil_id, district_name, tehsil_name, num_pages, fetch_all)
        
        # Save separate files for this combination
        save_data_to_files(processed_data, district_name, tehsil_name)
        
        # Add to master collection
        all_processed_data.extend(processed_data)
    
    # Create combined master files
    if all_processed_data:
        print("\n" + "="*50)
        print("GENERATING COMBINED MASTER FILES")
        print("="*50)
        
        print("\n🔗 Generating Combined Master Files (Please wait)...")
        df_master = pd.DataFrame(all_processed_data)
        df_master.insert(0, "Sr#", range(1, len(df_master) + 1))
        
        # Use fixed filename for master files
        fixed_name = "ALL_DISTRICTS_TEHSILS_MASTER"
        
        # Sort by Survey Date if available
        if "Survey Date" in df_master.columns:
             df_master.sort_values(by=["Survey Date", "Survey Time"], ascending=False, inplace=True)
        
        # Create Excel file with clickable links
        excel_filename = os.path.join(OUTPUT_FOLDER, f"{fixed_name}.xlsx")
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            df_master.to_excel(writer, index=False, sheet_name='All Districts Tehsils Survey Data')
        
        # Create CSV file with separate image URL columns and no clickable links
        csv_filename = os.path.join(OUTPUT_FOLDER, f"{fixed_name}.csv")
        
        # Remove clickable link columns for CSV and exclude the combined "Image URLs" column
        csv_columns = [col for col in df_master.columns if not col.startswith("Clickable Image") and col != "Image URLs"]
        df_csv = df_master[csv_columns]
        
        # Reorder columns to put Image URL columns at the end
        image_url_columns = [col for col in csv_columns if col.startswith("Image URL")]
        other_columns = [col for col in csv_columns if not col.startswith("Image URL")]
        reordered_columns = other_columns + image_url_columns
        df_csv = df_csv[reordered_columns]        
        
        # Add error handling for file writing
        try:
            df_csv.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        except PermissionError:
            print(f"⚠️ Permission denied when writing CSV file: {csv_filename}")
            print("   Please close any applications that might be using this file and try again.")
            print("   Common causes: Excel has the file open, or Google Drive is syncing the file.")
            return
        except Exception as e:
            print(f"⚠️ Error writing CSV file: {e}")
            return
        
        print("\n" + "="*50)
        print("🎉 MISSION ACCOMPLISHED")
        if fetch_all:
            print(f"📄 Grand Total Records: {len(all_processed_data)} (ALL available data downloaded)")
        else:
            print(f"📄 Grand Total Records: {len(all_processed_data)}")
            print(f"📄 Pages Fetched:       {num_pages} pages ({PAGE_SIZE} records per page)")
        print(f"💾 MASTER EXCEL FILE:   {excel_filename}")
        print(f"💾 MASTER CSV FILE:     {csv_filename}")
        print("="*50)
    else:
        print("\n⚠️ No data collected from any district/tehsil combination.")

if __name__ == "__main__":
    main()