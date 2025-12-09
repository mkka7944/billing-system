# pages/2_MC_UC_Browser.py
import streamlit as st
import pandas as pd
from components.auth import enforce_auth
from components.db import supabase

enforce_auth() # All logged-in users can access this page

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
selection = st.dataframe(
    df_consumers[['survey_id', 'billing_consumer_name', 'billing_mobile', 'survey_address']],
    on_select="rerun",
    selection_mode="single-row",
    hide_index=True,
    use_container_width=True
)

# --- Detail View ---
if selection.selection['rows']:
    selected_index = selection.selection['rows'][0]
    selected_consumer = df_consumers.iloc[selected_index].to_dict()
    
    st.markdown("---")
    st.subheader(f"Details for: {selected_consumer['survey_id']}")
    
    main_cols = st.columns(2)
    with main_cols[0]:
        st.write(f"**Name:** {selected_consumer.get('billing_consumer_name')}")
        st.write(f"**Mobile:** {selected_consumer.get('billing_mobile')}")
        st.write(f"**Address:** {selected_consumer.get('billing_address')}")
        st.image(selected_consumer.get('image_portal_url'), caption="Site Image")
    
    with main_cols[1]:
        lat, lng = selected_consumer.get('gps_lat'), selected_consumer.get('gps_long')
        if lat and lng and lat not in ['None', '']:
            st.map(pd.DataFrame({'lat': [float(lat)], 'lon': [float(lng)]}))
        else: st.info("No GPS data.")