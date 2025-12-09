import requests
import config # Uses your config credentials

# SETTINGS FOR KHUSHAB DIAGNOSTIC
PROFILE = "PROFILE_KB"
OFFICE_ID = "9956"  # Khushab Office from Sniffer
DISTRICT_ID = "16"  # Khushab District
STATUS = "Paid"     # Title Case from Sniffer

def debug():
    print(f"🕵️ DEBUG MODE: Testing {PROFILE}...")
    
    # 1. LOGIN
    creds = config.CREDENTIALS[PROFILE]
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/96.0.4664.110 Safari/537.36',
        'Content-Type': 'application/json',
        'Origin': 'https://suthra.punjab.gov.pk',
        'Referer': 'https://suthra.punjab.gov.pk/suthra-billing/view/suthra-punjab-bills'
    })
    
    login_payload = {"cnic": creds["CNIC"], "password": creds["PASSWORD"], "user_type": creds["USER_TYPE"]}
    r = s.post("https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/login", json=login_payload)
    token = r.json().get("data", {}).get("token")
    if not token:
        print("❌ Login Failed:", r.text)
        return
    s.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Login Success. Token obtained.")

    # 2. SEND EXACT SNIFFER PAYLOAD
    payload = {
        "slug": "suthra-punjab-bills",
        "id": "0",
        "page": 1,
        "size": 10, # Small size just to check connection
        "search_keyword": "",
        "requesting_url": "/suthra-billing/view/suthra-punjab-bills",
        "displayedColumnsAll": [{"key": "psid", "column": True, "value": "PSID"}],
        "filters_data": {
            "status": STATUS,  # "Paid"
            "division_id": "9",
            "district_id": DISTRICT_ID, # 16
            "office_id": OFFICE_ID, # 9956
            "uc_id": "",
            "active": ""
        },
        "user_type": "contractor",
        "plateform": "web"
    }
    
    print("\n📨 Sending Payload:")
    print(payload)
    
    # 3. PRINT RAW RESPONSE
    r = s.post("https://suthra.punjab.gov.pk/suthra-punjab/backend/public/api/autoform/get-item-listing", json=payload)
    
    print("\n📩 SERVER RESPONSE (RAW):")
    print("------------------------------------------------")
    print(r.text[:2000]) # Print first 2000 chars
    print("------------------------------------------------")

if __name__ == "__main__":
    debug()