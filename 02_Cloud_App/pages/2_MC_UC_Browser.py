# pages/2_MC_UC_Browser.py
import streamlit as st
import pandas as pd
from components.auth import enforce_auth
from components.db import supabase
from utils.session import check_session_timeout, update_last_activity
from utils.exporters import download_button_csv, download_button_excel
from components.pagination import paginate_data

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

enforce_auth() # All logged-in users can access this page

# Update last activity
update_last_activity()

st.title("🧭 MC/UC Browser")

# --- Filters ---
try:
    locations = pd.DataFrame(supabase.table('unique_locations').select('*').execute().data)
    selected_city = st.selectbox("City", sorted(locations['city_district'].unique()))
    ucs_in_city = sorted(locations[locations['city_district'] == selected_city]['uc_name'].unique())
    selected_uc = st.selectbox("Union Council", ucs_in_city)
except Exception as e:
    st.error(f"Could not load locations: {e}"); st.stop()

# --- Data Display using st.dataframe with on_select ---
consumers_res = supabase.table('survey_units').select('*').eq('uc_name', selected_uc).execute()
df_consumers = pd.DataFrame(consumers_res.data)

st.subheader(f"Consumers in {selected_uc}")

# Export options
st.subheader("📤 Export Options")
exp_col1, exp_col2 = st.columns(2)
with exp_col1:
    download_button_csv(df_consumers, f"consumers_{selected_uc}.csv", "📥 Download CSV")
with exp_col2:
    download_button_excel(df_consumers, f"consumers_{selected_uc}.xlsx", "📊 Download Excel")

# Show paginated data
paginated_consumers = paginate_data(df_consumers.to_dict('records'), page_size=50, key_prefix="consumers")
if paginated_consumers:
    paginated_df = pd.DataFrame(paginated_consumers)
    selection = st.dataframe(
        paginated_df[['survey_id', 'billing_consumer_name', 'billing_mobile', 'survey_address']],
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No consumers found.")
    st.stop()

# --- Detail View ---
if selection.selection['rows']:
    selected_index = selection.selection['rows'][0]
    # Adjust index for pagination
    adjusted_index = (st.session_state.get("consumers_current_page", 1) - 1) * 50 + selected_index
    if adjusted_index < len(df_consumers):
        selected_consumer = df_consumers.iloc[adjusted_index].to_dict()
        
        st.markdown("---")
        st.subheader(f"Details for: {selected_consumer['survey_id']}")
        
        main_cols = st.columns(2)
        with main_cols[0]:
            st.write(f"**Name:** {selected_consumer.get('billing_consumer_name')}")
            st.write(f"**Mobile:** {selected_consumer.get('billing_mobile')}")
            st.write(f"**Address:** {selected_consumer.get('billing_address')}")
            if selected_consumer.get('image_portal_url'):
                st.image(selected_consumer.get('image_portal_url'), caption="Site Image")
            else:
                st.info("No image available.")
        
        with main_cols[1]:
            lat, lng = selected_consumer.get('gps_lat'), selected_consumer.get('gps_long')
            if lat and lng and lat not in ['None', ''] and lng not in ['None', '']:
                try:
                    st.map(pd.DataFrame({'lat': [float(lat)], 'lon': [float(lng)]}))
                except:
                    st.info("Invalid GPS data.")
            else: 
                st.info("No GPS data.")