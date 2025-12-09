import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import time
import pandas as pd

# ---------------------------------------------------------
# 1. CONFIG & SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="Suthra Punjab Ops", page_icon="🇵🇰", layout="wide")

# Load Environment Variables
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    st.error("❌ API Keys missing. Check .env file.")
    st.stop()

# Initialize Database
@st.cache_resource
def init_db():
    return create_client(url, key)

supabase = init_db()

# ---------------------------------------------------------
# 2. SESSION STATE
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS
# ---------------------------------------------------------
def login_user(username, password):
    try:
        response = supabase.table("staff").select("*").eq("username", username).eq("password", password).execute()
        if response.data:
            user = response.data[0]
            if user['is_active']:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = user['role']
                st.session_state["user_name"] = user['full_name']
                st.success("Login Successful!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("🚫 Account Locked.")
        else:
            st.error("❌ Invalid Credentials")
    except Exception as e:
        st.error(f"Error: {e}")

def logout():
    st.session_state["logged_in"] = False
    st.rerun()

# ---------------------------------------------------------
# 4. LOGIN SCREEN
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🇵🇰 Suthra Punjab")
        st.caption("Operations Management System")
        st.markdown("---")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Log In", use_container_width=True):
            login_user(username, password)
    st.stop()

# ---------------------------------------------------------
# 5. DASHBOARD (Authenticated)
# ---------------------------------------------------------
# --- SIDEBAR ---
with st.sidebar:
    st.header("🏛️ Menu") 
    st.write(f"**User:** {st.session_state['user_name']}")
    st.caption(f"**Role:** {st.session_state['user_role']}")
    st.markdown("---")
    
    menu = st.radio("Navigate", ["Dashboard", "Search Consumer", "My Route", "Staff Manager"])
    
    st.markdown("---")
    if st.button("Logout", type="secondary"):
        logout()

# --- PAGE: DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Operations Overview")
    
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_month = st.selectbox("Select Billing Month", ["Nov-2025", "Oct-2025", "Sep-2025"])
    
    try:
        # A. Issued
        res_total = supabase.table("bills").select("psid", count="exact").eq("bill_month", selected_month).execute()
        count_issued = res_total.count
        
        # B. Paid
        res_paid = supabase.table("bills").select("psid", count="exact").eq("bill_month", selected_month).eq("payment_status", "PAID").execute()
        count_paid = res_paid.count
        
        if count_issued > 0:
            recovery_pct = (count_paid / count_issued) * 100
        else:
            recovery_pct = 0
            
    except Exception as e:
        st.error(f"Data Error: {e}")
        count_issued, count_paid, recovery_pct = 0, 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Issued Bills", f"{count_issued:,}")
    m2.metric("Recovered", f"{count_paid:,}")
    m3.metric("Recovery %", f"{recovery_pct:.2f}%")

# --- PAGE: SEARCH CONSUMER ---
elif menu == "Search Consumer":
    st.title("🔍 Search Consumer")
    
    # 1. Search Bar
    search_term = st.text_input("Search by Name, Mobile, Survey ID, or PSID:", placeholder="e.g. 03001234567 or Ali").strip()
    
    if search_term:
        results = []
        
        # LOGIC: 
        # If input is long digits (20) -> It's likely a PSID.
        # If input is digits (11) -> Mobile.
        # If input is digits (<8) -> Survey ID.
        # Else -> Name.
        
        try:
            if len(search_term) == 20 and search_term.isdigit():
                # PSID Search (Go to Bills -> Get Survey ID -> Get Unit)
                st.caption("Searching by PSID...")
                bill_res = supabase.table("bills").select("survey_id_fk").eq("psid", search_term).execute()
                if bill_res.data:
                    sid = bill_res.data[0]['survey_id_fk']
                    res = supabase.table("survey_units").select("*").eq("survey_id", sid).execute()
                    results = res.data
            else:
                # General Search (Name/Mobile/ID)
                # We use .or_() to search multiple columns at once
                query_str = f"billing_consumer_name.ilike.%{search_term}%,billing_mobile.eq.{search_term},survey_id.eq.{search_term}"
                res = supabase.table("survey_units").select("*").or_(query_str).limit(10).execute()
                results = res.data
        
        except Exception as e:
            st.error(f"Search Error: {e}")

        # 2. Display Results
        if not results:
            st.warning("No consumer found.")
        
        elif len(results) == 1:
            # Exact Match -> Show Profile Directly
            unit = results[0]
            survey_id = unit['survey_id']
            
            # --- PROFILE HEADER ---
            st.markdown("---")
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(f"🏠 {unit.get('billing_consumer_name', 'Unknown')}")
                st.write(f"**ID:** {survey_id}")
                st.write(f"**Address:** {unit.get('billing_address', 'N/A')}")
                st.write(f"**Mobile:** {unit.get('billing_mobile', 'N/A')}")
                st.write(f"**Type:** {unit.get('unit_specific_type', 'N/A')} ({unit.get('survey_category', '-')})")
            
            with c2:
                # Status Badge
                is_active = unit.get('is_active_portal', 'True')
                if str(is_active) == 'True':
                    st.success("Active Unit")
                else:
                    st.error("Inactive")

            # --- FINANCIAL HISTORY ---
            st.markdown("#### 📜 Bill History")
            try:
                # Fetch Bills
                bills_res = supabase.table("bills")\
                    .select("bill_month, amount_due, payment_status, paid_date, amount_paid, psid")\
                    .eq("survey_id_fk", survey_id)\
                    .order("bill_month", desc=True)\
                    .execute()
                
                if bills_res.data:
                    df_bills = pd.DataFrame(bills_res.data)
                    # Color the status
                    def highlight_status(val):
                        color = '#d4edda' if val == 'PAID' else '#f8d7da' # Green vs Red
                        return f'background-color: {color}'
                    
                    st.dataframe(
                        df_bills.style.applymap(highlight_status, subset=['payment_status']),
                        use_container_width=True,
                        column_config={
                            "bill_month": "Month",
                            "amount_due": "Due",
                            "payment_status": "Status",
                            "paid_date": "Paid On",
                            "amount_paid": "Paid Amt",
                            "psid": "PSID"
                        }
                    )
                else:
                    st.info("No bill history found.")
            except Exception as e:
                st.error("Could not load bills.")

            # --- LAZY LOADING VISUALS ---
            st.markdown("#### 📍 Visuals & Location")
            
            # 1. Map Expander
            with st.expander("🗺️ View Location on Map"):
                lat = unit.get('gps_lat')
                lng = unit.get('gps_long')
                if lat and lng and lat != 'None':
                    try:
                        map_data = pd.DataFrame({'lat': [float(lat)], 'lon': [float(lng)]})
                        st.map(map_data)
                    except:
                        st.warning("Invalid GPS Data.")
                else:
                    st.info("GPS Coordinates not available.")

            # 2. Image Expander (Lazy Load)
            with st.expander("📸 View Site Images"):
                img_url = unit.get('image_portal_url')
                if img_url and img_url != "None":
                    # Handle multiple images separated by pipe |
                    urls = img_url.split(" | ")
                    
                    cols = st.columns(len(urls))
                    for idx, url in enumerate(urls):
                        with cols[idx]:
                            st.image(url, use_container_width=True, caption=f"Image {idx+1}")
                else:
                    st.info("No images uploaded.")

        else:
            # Multiple Results -> Show Table
            st.info(f"Found {len(results)} matches. Please copy the Exact ID to search.")
            df_res = pd.DataFrame(results)
            st.dataframe(
                df_res[['survey_id', 'billing_consumer_name', 'billing_mobile', 'uc_name']],
                use_container_width=True
            )

# --- PAGE: STAFF ---
elif menu == "Staff Manager":
    st.title("👥 Staff Roster")
    st.info("Module coming soon...")