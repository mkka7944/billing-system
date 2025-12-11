# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time

from components.auth import enforce_auth
from components.db import supabase

enforce_auth(admin_only=True)

st.title("📊 Operations Dashboard")

# --- KPI Section (Unchanged) ---
# ...

st.markdown("---")

# --- Custom Bill Query Tool ---
st.subheader("Custom Bill Query")

try:
    locations_res = supabase.table('unique_locations').select('city_district').execute()
    tehsils = sorted(list(set([loc['city_district'] for loc in locations_res.data])))
except Exception as e:
    st.error(f"Could not load Tehsil list: {e}")
    tehsils = []

with st.form("bill_query_form"):
    st.write("Select filters to query the bills database.")
    
    query_cols = st.columns(3)
    selected_tehsil = query_cols[0].selectbox("Tehsil / Office", options=["All Tehsils"] + tehsils)
    query_start_date = query_cols[1].date_input("Start Date", datetime.now().date() - timedelta(days=30))
    query_end_date = query_cols[2].date_input("End Date", datetime.now().date())

    status_options = ["PAID", "UNPAID", "ARREARS"]
    selected_statuses = st.multiselect("Payment Status", options=status_options, default=["PAID"])

    submitted = st.form_submit_button("Run Query")

if submitted:
    if not selected_statuses:
        st.warning("Please select at least one payment status.")
    else:
        with st.spinner("Building and running your query..."):
            try:
                # --- ROBUST DATE/TIME HANDLING ---
                # Combine date from picker with time to create full timestamps
                # This ensures we get all records from the start of the first day to the end of the last day.
                start_timestamp = datetime.combine(query_start_date, time.min).isoformat()
                end_timestamp = datetime.combine(query_end_date, time.max).isoformat()
                
                # --- Start building the query ---
                query = supabase.table("bills").select("*", count='exact') \
                    .gte('uploaded_at', start_timestamp) \
                    .lte('uploaded_at', end_timestamp) \
                    .in_('payment_status', selected_statuses)
                
                unit_ids_to_filter = None
                
                if selected_tehsil != "All Tehsils":
                    units_res = supabase.table("survey_units").select("survey_id").eq("city_district", selected_tehsil).execute()
                    if units_res.data:
                        unit_ids_to_filter = [unit['survey_id'] for unit in units_res.data]
                        query = query.in_("survey_id_fk", unit_ids_to_filter)
                    else:
                        st.info(f"No survey units found for Tehsil '{selected_tehsil}'. Query will likely return no results.")
                        # Create an impossible condition to ensure no bills are returned
                        query = query.in_("survey_id_fk", ["nonexistent_id"])

                # Execute the final query
                results = query.execute()
                
                with st.expander("🔍 Query Details", expanded=True):
                    st.write(f"**Time Range:** `{start_timestamp}` to `{end_timestamp}`")
                    st.write(f"**Tehsil Filter:** `{selected_tehsil}`")
                    if unit_ids_to_filter is not None:
                         st.write(f"Found `{len(unit_ids_to_filter)}` survey units to filter by.")
                    st.write(f"**Status Filter:** `{selected_statuses}`")
                    st.write(f"**Database Response:** Found **{results.count}** matching bills.")

                if results.data:
                    df_results = pd.DataFrame(results.data)
                    st.dataframe(df_results, use_container_width=True)
                # The 'No bills found' message will now appear below the debug details
                else:
                    st.info("ℹ️ No bills found for the selected criteria.")
            
            except Exception as e:
                st.error(f"An error occurred while querying the database: {e}")