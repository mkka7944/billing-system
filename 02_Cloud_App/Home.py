import streamlit as st
from services.db import supabase
import pandas as pd

st.title("Suthra Punjab Operations Center")
st.write("Welcome to the Waste Management & Billing System")

# Function to get total number of bills
@st.cache_data(ttl=60)
def get_total_bills():
    try:
        response = supabase.table("bills").select("count", count="exact").execute()
        return response.count if hasattr(response, 'count') else len(response.data)
    except Exception as e:
        st.error(f"Error fetching total bills: {str(e)}")
        return 0

# Function to get survey count for each city
@st.cache_data(ttl=60)
def get_survey_count_by_city():
    try:
        response = supabase.table("survey_units").select("city_district").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            survey_counts = df.groupby('city_district').size().reset_index(name='survey_count')
            return survey_counts
        return pd.DataFrame(columns=['city_district', 'survey_count'])
    except Exception as e:
        st.error(f"Error fetching survey counts: {str(e)}")
        return pd.DataFrame(columns=['city_district', 'survey_count'])

# Function to get total paid amount
@st.cache_data(ttl=60)
def get_total_paid_amount():
    try:
        # Use the correct column name: amount_paid
        response = supabase.table("bills").select("amount_paid").eq("payment_status", "PAID").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Convert "amount_paid" to numeric, handling any non-numeric values
            df["amount_paid"] = pd.to_numeric(df["amount_paid"], errors='coerce')
            total_paid = df["amount_paid"].sum()
            return total_paid
        return 0.0
    except Exception as e:
        st.error(f"Error fetching total paid amount: {str(e)}")
        return 0.0

# Display metrics
st.subheader("System Metrics")

# Create three columns for the KPIs
col1, col2, col3 = st.columns(3)

# Get data
total_bills = get_total_bills()
total_paid = get_total_paid_amount()
survey_data = get_survey_count_by_city()

# Display KPIs
with col1:
    st.metric(label="Total Bills", value=total_bills)

with col2:
    st.metric(label="Total Paid Amount", value=f"₨{total_paid:,.2f}")

with col3:
    st.metric(label="Cities with Surveys", value=survey_data['city_district'].nunique() if not survey_data.empty else 0)

# Display survey counts by city
if not survey_data.empty:
    st.subheader("Surveys by City")
    st.dataframe(survey_data.rename(columns={'city_district': 'City', 'survey_count': 'Survey Count'}), width='stretch')
else:
    st.subheader("Surveys by City")
    st.write("No survey data available.")

st.markdown("""
This is a fresh start for the billing system with default Streamlit pages.
""")