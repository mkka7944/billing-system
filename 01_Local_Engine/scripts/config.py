"""
Global Configuration for SGWMC Billing System
"""
import os

# ====================================================
# 1. CREDENTIALS
# ====================================================
CREDENTIALS = {
    "PROFILE_SARGODHA": {
        "CNIC": "3840111639195",
        "PASSWORD": "1975@MuhammadHassanTMT",  # <--- UPDATE THIS
        "USER_TYPE": "HRMIS_USER"
    },
    "PROFILE_KB": {
        "CNIC": "3230307561839",   # <--- UPDATE THIS
        "PASSWORD": "Sac@1235", # <--- UPDATE THIS
        "USER_TYPE": "HRMIS_USER"
    }
}

# ====================================================
# 2. TARGET JOBS
# ====================================================
TARGET_JOBS = [
    {
        "city_name": "Sargodha",
        "profile": "PROFILE_SARGODHA", 
        "division_id": "9",
        "district_id": "32",
        "office_id": "",         # Vacuum Mode
        "designation_id": None   
    },
    {
        "city_name": "Khushab",
        "profile": "PROFILE_KB", 
        "division_id": "9",
        "district_id": "",       # Vacuum Mode (Relies on Switch)
        "office_id": "",         
        "designation_id": 160449 # <--- Mapped to 712 Records
    },
    {
        "city_name": "Bhalwal",
        "profile": "PROFILE_KB", 
        "division_id": "9",
        "district_id": "",       # Vacuum Mode (Relies on Switch)
        "office_id": "",         
        "designation_id": 160443 # <--- Mapped to 404 Records
    }
]

# ====================================================
# 3. PATHS
# ====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "outputs", "scraped_data")
AREAS_CSV_PATH = os.path.join(BASE_DIR, "..", "inputs", "config_files", "areas_export.csv")