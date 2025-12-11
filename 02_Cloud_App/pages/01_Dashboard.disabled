import streamlit as st
import pandas as pd
import plotly.express as px
from services import auth, repository
from components import metrics, sidebar
from utils.session import check_session_timeout, update_last_activity
from utils.exporters import download_button_csv, download_button_excel, export_bill_summary
from components.pagination import paginate_data

# --- Setup ---
st.set_page_config(page_title="Dashboard", layout="wide")

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

st.title("📊 Executive Dashboard")

# Add date range filters
st.sidebar.subheader("Filters")
start_date = st.sidebar.date_input("Start Date", pd.Timestamp.now() - pd.Timedelta(days=30))
end_date = st.sidebar.date_input("End Date", pd.Timestamp.now())

# Add refresh button
if st.sidebar.button("🔄 Refresh Data"):
    # Clear cache to force refresh
    repository.fetch_data.clear()
    st.rerun()

# --- Data Fetching ---
with st.spinner("Refreshing analytics..."):
    # Fetch high-level stats (could be optimized with RPC calls in Supabase)
    # For now, fetching full tables for prototype, restrict columns for perf in prod
    bills_df = repository.fetch_data("bills", columns="id, payment_status, amount_due, created_at, paid_amount, fine")
    staff_df = repository.fetch_data("staff", columns="id, is_active, role")
    tickets_df = repository.fetch_data("tickets", columns="ticket_id, status, priority, created_at")
    
    # Apply date filters if data is available
    if not bills_df.empty and 'created_at' in bills_df.columns:
        # Convert to datetime if needed
        bills_df['created_at'] = pd.to_datetime(bills_df['created_at'])
        mask = (bills_df['created_at'].dt.date >= start_date) & (bills_df['created_at'].dt.date <= end_date)
        bills_df = bills_df[mask]

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    metrics.kpi_card("Total Bills", len(bills_df))
with col2:
    rev = bills_df[bills_df['payment_status'] == 'PAID']['amount_due'].sum() if not bills_df.empty else 0
    metrics.kpi_card("Revenue Collected", f"PKR {rev:,.0f}")
with col3:
    pending = len(tickets_df[tickets_df['status'] == 'OPEN']) if not tickets_df.empty else 0
    metrics.kpi_card("Open Tickets", pending, delta=f"{pending} active", color="inverse")
with col4:
    active_staff = len(staff_df[staff_df['is_active']]) if not staff_df.empty else 0
    metrics.kpi_card("Active Staff", active_staff)

st.markdown("---")

# --- Charts ---
chart_tabs = st.tabs(["Payment Status", "Ticket Summary", "Collection Trends", "Staff Distribution"])

with chart_tabs[0]:
    st.subheader("💵 Payment Status Distribution")
    if not bills_df.empty:
        status_counts = bills_df['payment_status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig_pie = px.pie(status_counts, values='Count', names='Status', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No billing data.")

with chart_tabs[1]:
    st.subheader("🎫 Ticket Summary")
    if not tickets_df.empty:
        ticket_counts = tickets_df['status'].value_counts().reset_index()
        ticket_counts.columns = ['Status', 'Count']
        fig_bar = px.bar(ticket_counts, x='Status', y='Count', color='Status')
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Priority distribution
        st.subheader("Priority Distribution")
        priority_counts = tickets_df['priority'].value_counts().reset_index()
        priority_counts.columns = ['Priority', 'Count']
        fig_pie2 = px.pie(priority_counts, values='Count', names='Priority', hole=0.4)
        st.plotly_chart(fig_pie2, use_container_width=True)
    else:
        st.info("No ticket data.")

with chart_tabs[2]:
    st.subheader("📈 Collection Trends")
    if not bills_df.empty and 'created_at' in bills_df.columns:
        # Group by date and sum payments
        daily_collections = bills_df[bills_df['payment_status'] == 'PAID'].copy()
        daily_collections['date'] = pd.to_datetime(daily_collections['created_at']).dt.date
        daily_summary = daily_collections.groupby('date')['amount_due'].sum().reset_index()
        
        fig_trend = px.line(daily_summary, x='date', y='amount_due', title='Daily Collections')
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No collection data available.")

with chart_tabs[3]:
    st.subheader("👥 Staff Distribution")
    if not staff_df.empty:
        role_counts = staff_df['role'].value_counts().reset_index()
        role_counts.columns = ['Role', 'Count']
        fig_roles = px.bar(role_counts, x='Role', y='Count', color='Role')
        st.plotly_chart(fig_roles, use_container_width=True)
    else:
        st.info("No staff data.")

st.markdown("---")

# --- Data Tables with Pagination ---
tab1, tab2, tab3 = st.tabs(["Bills Summary", "Tickets", "Staff"])

with tab1:
    st.subheader("📋 Bills Data")
    if not bills_df.empty:
        # Show export buttons
        summary_df = export_bill_summary(bills_df)
        col1, col2 = st.columns(2)
        with col1:
            download_button_csv(summary_df, "bill_summary.csv", "📥 Download CSV Summary")
        with col2:
            download_button_excel(summary_df, "bill_summary.xlsx", "📊 Download Excel Summary")
        
        # Show paginated data
        paginated_bills = paginate_data(bills_df.to_dict('records'), page_size=50, key_prefix="bills")
        if paginated_bills:
            st.dataframe(pd.DataFrame(paginated_bills), use_container_width=True)
    else:
        st.info("No billing data.")

with tab2:
    st.subheader("📋 Tickets Data")
    if not tickets_df.empty:
        # Show export buttons
        col1, col2 = st.columns(2)
        with col1:
            download_button_csv(tickets_df, "tickets.csv", "📥 Download CSV")
        with col2:
            download_button_excel(tickets_df, "tickets.xlsx", "📊 Download Excel")
        
        # Show paginated data
        paginated_tickets = paginate_data(tickets_df.to_dict('records'), page_size=50, key_prefix="tickets")
        if paginated_tickets:
            st.dataframe(pd.DataFrame(paginated_tickets), use_container_width=True)
    else:
        st.info("No ticket data.")

with tab3:
    st.subheader("📋 Staff Data")
    if not staff_df.empty:
        # Show export buttons
        col1, col2 = st.columns(2)
        with col1:
            download_button_csv(staff_df, "staff.csv", "📥 Download CSV")
        with col2:
            download_button_excel(staff_df, "staff.xlsx", "📊 Download Excel")
        
        # Show paginated data
        paginated_staff = paginate_data(staff_df.to_dict('records'), page_size=50, key_prefix="staff")
        if paginated_staff:
            st.dataframe(pd.DataFrame(paginated_staff), use_container_width=True)
    else:
        st.info("No staff data.")

st.subheader("Recent Activity")
st.caption("Real-time feed of system events.")
# Placeholder for activity feed
st.text("• System initialization complete.")