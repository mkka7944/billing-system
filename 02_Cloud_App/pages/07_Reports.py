"""
Comprehensive Reporting Module for the Billing System
Provides detailed analytics and exportable reports
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from services import auth, repository
from components import sidebar
from utils.session import check_session_timeout, update_last_activity
from utils.exporters import download_button_csv, download_button_excel, export_bill_summary, export_consumer_summary
from components.pagination import paginate_data

# --- Page Setup ---
st.set_page_config(page_title="Reports & Analytics", layout="wide")

# Check session timeout
check_session_timeout()

# Render sidebar and check auth
sidebar.render_sidebar()
auth.require_auth()

# Update last activity
update_last_activity()

st.title("📈 Reports & Analytics")

# --- Report Filters ---
with st.expander("🔍 Report Filters", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["Billing Summary", "Consumer Analysis", "Payment Trends", "Staff Performance", "Ticket Analysis"]
        )
        
        start_date = st.date_input(
            "Start Date",
            datetime.now() - timedelta(days=30)
        )
    
    with col2:
        group_by = st.selectbox(
            "Group By",
            ["None", "City/District", "Union Council", "Payment Status", "Month"]
        )
        
        end_date = st.date_input(
            "End Date",
            datetime.now()
        )
    
    with col3:
        st.write("Additional Options")
        show_charts = st.checkbox("Show Charts", value=True)
        export_format = st.radio("Export Format", ["CSV", "Excel"])

# --- Data Fetching Based on Report Type ---
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_report_data(report_type, start_date, end_date):
    """Fetch data based on report type and date range"""
    try:
        if report_type == "Billing Summary":
            # Fetch bills with all relevant columns
            bills_df = repository.fetch_data(
                "bills", 
                columns="psid, bill_month, survey_id_fk, monthly_fee, arrears, amount_due, payment_status, paid_date, paid_amount, fine, channel, uploaded_at"
            )
            
            # Apply date filter
            if not bills_df.empty and 'uploaded_at' in bills_df.columns:
                bills_df['uploaded_at'] = pd.to_datetime(bills_df['uploaded_at'])
                mask = (bills_df['uploaded_at'].dt.date >= start_date) & (bills_df['uploaded_at'].dt.date <= end_date)
                bills_df = bills_df[mask]
                
            return bills_df
            
        elif report_type == "Consumer Analysis":
            # Fetch survey units
            consumers_df = repository.fetch_data(
                "survey_units",
                columns="survey_id, surveyor_name, survey_timestamp, city_district, uc_name, unit_specific_type, survey_category, billing_consumer_name, billing_mobile, billing_address, house_type, water_connection, size_marla, gps_lat, gps_long, is_active_portal"
            )
            
            # Apply date filter if timestamp column exists
            if not consumers_df.empty and 'survey_timestamp' in consumers_df.columns:
                consumers_df['survey_timestamp'] = pd.to_datetime(consumers_df['survey_timestamp'])
                mask = (consumers_df['survey_timestamp'].dt.date >= start_date) & (consumers_df['survey_timestamp'].dt.date <= end_date)
                consumers_df = consumers_df[mask]
                
            return consumers_df
            
        elif report_type == "Payment Trends":
            # Fetch bills with payment information
            bills_df = repository.fetch_data(
                "bills",
                columns="psid, bill_month, survey_id_fk, amount_due, payment_status, paid_date, paid_amount, uploaded_at"
            )
            
            # Apply date filter
            if not bills_df.empty and 'uploaded_at' in bills_df.columns:
                bills_df['uploaded_at'] = pd.to_datetime(bills_df['uploaded_at'])
                mask = (bills_df['uploaded_at'].dt.date >= start_date) & (bills_df['uploaded_at'].dt.date <= end_date)
                bills_df = bills_df[mask]
                
            return bills_df
            
        elif report_type == "Staff Performance":
            # Fetch staff and related ticket data
            staff_df = repository.fetch_data("staff", columns="id, username, full_name, role, assigned_city, is_active")
            tickets_df = repository.fetch_data("tickets", columns="ticket_id, reported_by_staff_id, status, priority, created_at")
            
            return staff_df, tickets_df
            
        elif report_type == "Ticket Analysis":
            # Fetch tickets with all relevant columns
            tickets_df = repository.fetch_data(
                "tickets",
                columns="ticket_id, reported_by_staff_id, status, title, description, priority, category, created_at, updated_at, resolved_at, resolved_by_staff_id"
            )
            
            # Apply date filter
            if not tickets_df.empty and 'created_at' in tickets_df.columns:
                tickets_df['created_at'] = pd.to_datetime(tickets_df['created_at'])
                mask = (tickets_df['created_at'].dt.date >= start_date) & (tickets_df['created_at'].dt.date <= end_date)
                tickets_df = tickets_df[mask]
                
            return tickets_df
            
    except Exception as e:
        st.error(f"Error fetching report data: {str(e)}")
        return pd.DataFrame()

# --- Generate Report Based on Type ---
def generate_billing_summary_report(bills_df, group_by_option):
    """Generate billing summary report"""
    if bills_df.empty:
        st.warning("No billing data available for the selected period.")
        return pd.DataFrame(), {}
    
    # Apply grouping if selected
    if group_by_option == "City/District":
        # Would need to join with survey_units to get city info
        pass
    elif group_by_option == "Payment Status":
        summary = bills_df.groupby('payment_status').agg({
            'amount_due': ['count', 'sum', 'mean'],
            'paid_amount': 'sum'
        }).round(2)
        
        # Flatten column names
        summary.columns = ['_'.join(col).strip() for col in summary.columns]
        summary = summary.reset_index()
        
        return summary, {}
        
    elif group_by_option == "Month":
        # Extract month from bill_month column
        if 'bill_month' in bills_df.columns:
            summary = bills_df.groupby('bill_month').agg({
                'amount_due': ['count', 'sum', 'mean'],
                'paid_amount': 'sum'
            }).round(2)
            
            # Flatten column names
            summary.columns = ['_'.join(col).strip() for col in summary.columns]
            summary = summary.reset_index()
            
            return summary, {}
    
    # Overall summary
    total_bills = len(bills_df)
    total_amount = bills_df['amount_due'].sum()
    paid_amount = bills_df[bills_df['payment_status'] == 'PAID']['paid_amount'].sum()
    collection_rate = (paid_amount / total_amount * 100) if total_amount > 0 else 0
    
    summary_stats = {
        "Total Bills": total_bills,
        "Total Amount Due": f"PKR {total_amount:,.2f}",
        "Total Amount Collected": f"PKR {paid_amount:,.2f}",
        "Collection Rate": f"{collection_rate:.2f}%"
    }
    
    # Payment status breakdown
    status_breakdown = bills_df['payment_status'].value_counts().reset_index()
    status_breakdown.columns = ['Payment Status', 'Count']
    
    return status_breakdown, summary_stats

def generate_consumer_analysis_report(consumers_df, group_by_option):
    """Generate consumer analysis report"""
    if consumers_df.empty:
        st.warning("No consumer data available for the selected period.")
        return pd.DataFrame(), {}
    
    # Summary statistics
    total_consumers = len(consumers_df)
    active_consumers = consumers_df['is_active_portal'].sum() if 'is_active_portal' in consumers_df.columns else 0
    inactive_consumers = total_consumers - active_consumers
    
    summary_stats = {
        "Total Consumers": total_consumers,
        "Active Consumers": active_consumers,
        "Inactive Consumers": inactive_consumers,
        "Activation Rate": f"{(active_consumers/total_consumers*100):.2f}%" if total_consumers > 0 else "0%"
    }
    
    # Group by option
    if group_by_option == "City/District" and 'city_district' in consumers_df.columns:
        city_summary = consumers_df.groupby('city_district').agg({
            'survey_id': 'count',
            'is_active_portal': 'sum'
        }).reset_index()
        
        city_summary.columns = ['City/District', 'Total Consumers', 'Active Consumers']
        city_summary['Inactive Consumers'] = city_summary['Total Consumers'] - city_summary['Active Consumers']
        
        return city_summary, summary_stats
        
    elif group_by_option == "Union Council" and 'uc_name' in consumers_df.columns:
        uc_summary = consumers_df.groupby('uc_name').agg({
            'survey_id': 'count',
            'is_active_portal': 'sum'
        }).reset_index()
        
        uc_summary.columns = ['Union Council', 'Total Consumers', 'Active Consumers']
        uc_summary['Inactive Consumers'] = uc_summary['Total Consumers'] - uc_summary['Active Consumers']
        
        return uc_summary, summary_stats
    
    # Default: return basic summary
    basic_summary = pd.DataFrame([{
        "Metric": "Total Consumers",
        "Value": total_consumers
    }])
    
    return basic_summary, summary_stats

# --- Main Report Generation ---
if st.button("Generate Report", type="primary"):
    with st.spinner("Generating report..."):
        # Fetch data based on report type
        if report_type in ["Billing Summary", "Payment Trends"]:
            data = fetch_report_data(report_type, start_date, end_date)
        elif report_type == "Consumer Analysis":
            data = fetch_report_data(report_type, start_date, end_date)
        elif report_type == "Ticket Analysis":
            data = fetch_report_data(report_type, start_date, end_date)
        elif report_type == "Staff Performance":
            staff_data, tickets_data = fetch_report_data(report_type, start_date, end_date)
        
        # Generate report based on type
        if report_type == "Billing Summary":
            report_df, summary_stats = generate_billing_summary_report(data, group_by)
        elif report_type == "Consumer Analysis":
            report_df, summary_stats = generate_consumer_analysis_report(data, group_by)
        else:
            report_df = data if not isinstance(data, tuple) else data[0]
            summary_stats = {}
        
        # Display summary statistics
        if summary_stats:
            st.subheader("📊 Summary Statistics")
            cols = st.columns(len(summary_stats))
            for i, (key, value) in enumerate(summary_stats.items()):
                with cols[i]:
                    st.metric(label=key, value=value)
        
        # Display charts if enabled
        if show_charts and not report_df.empty:
            st.subheader("📈 Data Visualization")
            
            # Create appropriate chart based on data
            if 'Count' in report_df.columns:
                fig = px.bar(report_df, x=report_df.columns[0], y='Count', 
                           title=f"{report_type} - Count by {report_df.columns[0]}")
                st.plotly_chart(fig, use_container_width=True)
            elif len(report_df.columns) > 1:
                # Try to create a meaningful chart
                numeric_cols = report_df.select_dtypes(include=['number']).columns
                if len(numeric_cols) >= 2:
                    fig = px.scatter(report_df, x=numeric_cols[0], y=numeric_cols[1],
                                   title=f"{report_type} - Data Scatter Plot")
                    st.plotly_chart(fig, use_container_width=True)
        
        # Display data table with pagination
        st.subheader("📋 Report Data")
        if not report_df.empty:
            # Export buttons
            col1, col2 = st.columns(2)
            with col1:
                if export_format == "CSV":
                    download_button_csv(report_df, f"{report_type.replace(' ', '_').lower()}_report.csv", 
                                      f"📥 Download {report_type} (CSV)")
                else:
                    download_button_excel(report_df, f"{report_type.replace(' ', '_').lower()}_report.xlsx", 
                                        f"📊 Download {report_type} (Excel)")
            
            # Show paginated data
            paginated_data = paginate_data(report_df.to_dict('records'), page_size=100, key_prefix="report")
            if paginated_data:
                st.dataframe(pd.DataFrame(paginated_data), use_container_width=True)
        else:
            st.info("No data to display for this report.")

# --- Pre-built Reports Section ---
st.markdown("---")
st.subheader("📚 Pre-built Reports")

# Quick report buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💰 Monthly Collection Report"):
        st.info("Monthly Collection Report would be generated here.")
    
    if st.button("👥 New Consumers Report"):
        st.info("New Consumers Report would be generated here.")

with col2:
    if st.button("🎫 Ticket Resolution Report"):
        st.info("Ticket Resolution Report would be generated here.")
    
    if st.button("📱 Field Visit Report"):
        st.info("Field Visit Report would be generated here.")

with col3:
    if st.button("⚙️ System Usage Report"):
        st.info("System Usage Report would be generated here.")
    
    if st.button("🏆 Staff Performance Report"):
        st.info("Staff Performance Report would be generated here.")

st.info("Click 'Generate Report' above with your selected filters to create custom reports.")