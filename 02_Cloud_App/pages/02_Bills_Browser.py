import streamlit as st
import pandas as pd
import plotly.express as px
from services import auth, repository
from components import sidebar, data_grid
from utils.session import check_session_timeout, update_last_activity
from utils.exporters import download_button_csv, download_button_excel
from components.pagination import paginate_data

# --- Setup ---
st.set_page_config(page_title="Bills Browser", layout="wide")

# --- Load Custom CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    local_css("assets/style.css")
    local_css("assets/mobile.css")
except FileNotFoundError:
    pass # CSS might be missing in dev

# Check session timeout
check_session_timeout()

sidebar.render_sidebar()
auth.require_auth()

# Update last activity
update_last_activity()

st.title("🧾 Bills Browser")

# --- Filters ---
with st.expander("🔎 Advanced Filters", expanded=True):
    c1, c2, c3 = st.columns(3)
    status_filter = c1.multiselect("Payment Status", ["PAID", "UNPAID", "ARREARS"], default=["PAID", "UNPAID"])
    
    # Date range filters
    start_date = c2.date_input("Start Date", pd.Timestamp.now() - pd.Timedelta(days=30))
    end_date = c3.date_input("End Date", pd.Timestamp.now())
    
    # Additional filters
    col1, col2 = st.columns(2)
    channel_filter = col1.multiselect("Payment Channel", ["1Bill", "BOP OTC", "OTC/Cash"])
    min_amount = col2.number_input("Minimum Amount", min_value=0, value=0)
    
# --- Data ---
with st.spinner("Loading bills..."):
    # Construct filters
    filters = {}
    # Repo currently supports simple equality. For 'IN' or range, we might filter in Pandas or extend repo.
    # For now, fetch all and filter in Pandas for robustness of 'IN' logic without complex repository code yet
    df = repository.fetch_data("bills")

if not df.empty:
    # Apply Python-side filtering for complex logic not yet in generic repo
    if status_filter:
        df = df[df['payment_status'].isin(status_filter)]
    
    # Apply date filters if columns exist
    if 'uploaded_at' in df.columns:
        df['uploaded_at'] = pd.to_datetime(df['uploaded_at'])
        mask = (df['uploaded_at'].dt.date >= start_date) & (df['uploaded_at'].dt.date <= end_date)
        df = df[mask]
    
    # Apply channel filter
    if channel_filter and 'channel' in df.columns:
        df = df[df['channel'].isin(channel_filter)]
    
    # Apply minimum amount filter
    if 'amount_due' in df.columns:
        df = df[df['amount_due'] >= min_amount]
        
    # --- Analytics for filtered view ---
    st.markdown("### Snapshot")
    m1, m2, m3 = st.columns(3)
    m1.metric("Visible Records", len(df))
    m2.metric("Total Due", f"PKR {df['amount_due'].sum():,.0f}")
    m3.metric("Avg Amount", f"PKR {df['amount_due'].mean():,.0f}")
    
    # Export options
    st.subheader("📤 Export Options")
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    with exp_col1:
        download_button_csv(df, "bills_export.csv", "📥 Download CSV")
    with exp_col2:
        download_button_excel(df, "bills_export.xlsx", "📊 Download Excel")
    with exp_col3:
        st.info("Select records below to export specific items")
    
    # --- Grid with Pagination ---
    st.subheader("Bill Records")
    
    # Show paginated data
    paginated_bills = paginate_data(df.to_dict('records'), page_size=100, key_prefix="bills_browser")
    if paginated_bills:
        paginated_df = pd.DataFrame(paginated_bills)
        selected = data_grid.display_aggrid(paginated_df, selection_mode="multiple")
        
        if selected:
            st.write(f"Selected {len(selected)} bills")
            # Add 'Action' buttons here later (e.g. "Mark Paid")
            
            # Export selected records
            if st.button("📤 Export Selected Records"):
                selected_df = pd.DataFrame(selected)
                download_button_csv(selected_df, "selected_bills.csv", "Download Selected CSV")
    else:
        st.info("No bills found matching criteria.")

else:
    st.info("No bills found matching criteria.")