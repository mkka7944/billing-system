"""
Bulk Operations Page for the Billing System
Provides interface for bulk data manipulation
"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime
from services import auth, repository
from components import sidebar
from utils.session import check_session_timeout, update_last_activity
from utils.bulk_operations import bulk_update_records, bulk_delete_records, bulk_insert_records, bulk_payment_status_update, bulk_consumer_status_update, validate_bulk_operation
from utils.exporters import download_button_csv

# --- Page Setup ---
st.set_page_config(page_title="Bulk Operations", layout="wide")

# Check session timeout
check_session_timeout()

# Render sidebar and check auth
sidebar.render_sidebar()
auth.require_auth()

# Only admins can access bulk operations
user = auth.get_current_user()
if user and user.get('role') not in ['MANAGER', 'HEAD']:
    st.error("🚫 Access denied. Only managers and head administrators can perform bulk operations.")
    st.stop()

# Update last activity
update_last_activity()

st.title("⚙️ Bulk Operations")

# --- Operation Type Selection ---
operation_type = st.radio(
    "Select Operation Type",
    ["Bulk Update Payment Status", "Bulk Update Consumer Status", "Bulk Import Data", "Bulk Export Data"]
)

st.markdown("---")

# --- Bulk Update Payment Status ---
if operation_type == "Bulk Update Payment Status":
    st.subheader("💳 Bulk Update Payment Status")
    
    # File upload for bill IDs
    uploaded_file = st.file_uploader("Upload CSV with Bill PSIDs", type=["csv"])
    
    if uploaded_file:
        # Read uploaded file
        df = pd.read_csv(uploaded_file)
        st.write(f"Loaded {len(df)} records")
        st.dataframe(df.head(10))
        
        # Payment status update options
        col1, col2, col3 = st.columns(3)
        with col1:
            new_status = st.selectbox("New Payment Status", ["PAID", "UNPAID", "ARREARS"])
        with col2:
            paid_date = st.date_input("Payment Date", datetime.now())
        with col3:
            paid_amount = st.number_input("Payment Amount", min_value=0.0, value=0.0)
        
        # Confirm operation
        if st.button("🔄 Update Payment Status", type="primary"):
            if "psid" not in df.columns:
                st.error("CSV must contain a 'psid' column with bill identifiers")
                st.stop()
            
            bill_ids = df["psid"].tolist()
            with st.spinner(f"Updating {len(bill_ids)} bills..."):
                result = bulk_payment_status_update(
                    bill_ids, 
                    new_status, 
                    paid_date.strftime("%Y-%m-%d") if paid_date else None,
                    paid_amount if paid_amount > 0 else None
                )
                
                st.success(f"✅ Updated {result['success']} bills, {result['failed']} failed")
                
                # Show failed records if any
                if result['failed'] > 0:
                    st.warning(f"{result['failed']} records failed to update. Check logs for details.")

# --- Bulk Update Consumer Status ---
elif operation_type == "Bulk Update Consumer Status":
    st.subheader("👥 Bulk Update Consumer Status")
    
    # File upload for consumer IDs
    uploaded_file = st.file_uploader("Upload CSV with Consumer Survey IDs", type=["csv"])
    
    if uploaded_file:
        # Read uploaded file
        df = pd.read_csv(uploaded_file)
        st.write(f"Loaded {len(df)} records")
        st.dataframe(df.head(10))
        
        # Consumer status update options
        is_active = st.radio("Set Consumer Status", ["Active", "Inactive"]) == "Active"
        
        # Confirm operation
        if st.button("🔄 Update Consumer Status", type="primary"):
            if "survey_id" not in df.columns:
                st.error("CSV must contain a 'survey_id' column with consumer identifiers")
                st.stop()
            
            consumer_ids = df["survey_id"].tolist()
            with st.spinner(f"Updating {len(consumer_ids)} consumers..."):
                result = bulk_consumer_status_update(consumer_ids, is_active)
                
                st.success(f"✅ Updated {result['success']} consumers, {result['failed']} failed")
                
                # Show failed records if any
                if result['failed'] > 0:
                    st.warning(f"{result['failed']} records failed to update. Check logs for details.")

# --- Bulk Import Data ---
elif operation_type == "Bulk Import Data":
    st.subheader("📥 Bulk Import Data")
    
    # Select table to import into
    table_name = st.selectbox("Select Table", ["survey_units", "bills", "staff", "tickets"])
    
    # File upload
    uploaded_file = st.file_uploader("Upload CSV Data", type=["csv"])
    
    if uploaded_file:
        # Read uploaded file
        df = pd.read_csv(uploaded_file)
        st.write(f"Loaded {len(df)} records")
        st.dataframe(df.head(10))
        
        # Show column mapping options
        st.subheader("Column Mapping")
        st.info("Map your CSV columns to database columns:")
        
        # Get table schema information
        column_mapping = {}
        for col in df.columns:
            db_col = st.text_input(f"CSV Column '{col}' → Database Column", value=col)
            column_mapping[col] = db_col
        
        # Validate before import
        if st.button("🔍 Validate Data"):
            # Convert DataFrame to records
            records = df.rename(columns=column_mapping).to_dict('records')
            
            # Validate records
            errors = validate_bulk_operation(table_name, "insert", records)
            
            if errors:
                st.error(f"Validation failed with {len(errors)} errors:")
                for error in errors[:10]:  # Show first 10 errors
                    st.write(f"- {error}")
                if len(errors) > 10:
                    st.write(f"... and {len(errors) - 10} more errors")
            else:
                st.success("✅ Data validation passed!")
        
        # Confirm import
        if st.button("🚀 Import Data", type="primary"):
            # Convert DataFrame to records
            records = df.rename(columns=column_mapping).to_dict('records')
            
            # Validate records
            errors = validate_bulk_operation(table_name, "insert", records)
            
            if errors:
                st.error(f"Cannot import due to validation errors:")
                for error in errors[:10]:
                    st.write(f"- {error}")
                st.stop()
            
            # Perform bulk insert
            with st.spinner(f"Importing {len(records)} records..."):
                result = bulk_insert_records(table_name, records)
                
                st.success(f"✅ Imported {result['success']} records, {result['failed']} failed")
                
                # Show failed records if any
                if result['failed'] > 0:
                    st.warning(f"{result['failed']} records failed to import. Check logs for details.")

# --- Bulk Export Data ---
elif operation_type == "Bulk Export Data":
    st.subheader("📤 Bulk Export Data")
    
    # Select table to export from
    table_name = st.selectbox("Select Table to Export", ["survey_units", "bills", "staff", "tickets", "compliance_visits"])
    
    # Add filters
    st.subheader("Filter Options")
    col1, col2 = st.columns(2)
    
    with col1:
        limit_records = st.number_input("Limit Records (0 for all)", min_value=0, value=1000)
    
    with col2:
        order_by = st.selectbox("Order By", ["created_at", "id", "updated_at"])
    
    # Add custom filters
    st.subheader("Custom Filters")
    filter_col = st.text_input("Column Name")
    filter_val = st.text_input("Filter Value")
    
    filters = {}
    if filter_col and filter_val:
        filters[filter_col] = filter_val
    
    # Preview data
    if st.button("🔍 Preview Data"):
        with st.spinner("Fetching data..."):
            if limit_records > 0:
                # Fetch limited data
                df = repository.fetch_data(table_name, order_by=order_by)
                if not df.empty:
                    df = df.head(limit_records)
            else:
                # Fetch all data
                df = repository.fetch_data(table_name, order_by=order_by)
            
            # Apply filters
            if filters:
                for col, val in filters.items():
                    if col in df.columns:
                        df = df[df[col] == val]
            
            st.write(f"Previewing {len(df)} records")
            st.dataframe(df.head(20))
            
            # Export button
            if not df.empty:
                st.subheader("Export Options")
                filename = f"{table_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                download_button_csv(df, filename, "📥 Download CSV Export")

st.info("💡 Tip: Always backup your data before performing bulk operations!")

# --- Help Section ---
with st.expander("ℹ️ Help & Guidelines"):
    st.markdown("""
    ### Bulk Operations Guide
    
    **Before You Begin:**
    - Ensure you have the necessary permissions
    - Backup critical data before bulk operations
    - Test with small datasets first
    
    **File Formats:**
    - CSV files only
    - First row should contain column headers
    - Required columns vary by operation type
    
    **Best Practices:**
    - Validate data before importing
    - Monitor progress during long operations
    - Check results after completion
    
    **Troubleshooting:**
    - If operations fail, check the error messages
    - Contact system administrator for persistent issues
    """)