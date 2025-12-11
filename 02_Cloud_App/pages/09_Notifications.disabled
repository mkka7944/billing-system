"""
Notifications Page for the Billing System
Provides interface for viewing and managing notifications
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from services import auth
from components import sidebar
from utils.session import check_session_timeout, update_last_activity
from utils.notifications import get_user_notifications, mark_notification_as_read, mark_all_notifications_as_read, delete_notification, get_unread_notification_count

# --- Page Setup ---
st.set_page_config(page_title="Notifications", layout="wide")

# Check session timeout
check_session_timeout()

# Render sidebar and check auth
sidebar.render_sidebar()
auth.require_auth()

# Update last activity
update_last_activity()

# Get current user
user = auth.get_current_user()
if not user:
    st.error("User not found")
    st.stop()

st.title("🔔 Notifications")

# --- Notification Controls ---
col1, col2, col3 = st.columns(3)

with col1:
    unread_count = get_unread_notification_count(user['id'])
    st.metric("Unread Notifications", unread_count)

with col2:
    if st.button("_mark all as read", type="secondary"):
        if mark_all_notifications_as_read(user['id']):
            st.success("All notifications marked as read")
            st.rerun()
        else:
            st.error("Failed to mark notifications as read")

with col3:
    st.info("Notifications are automatically marked as read when viewed")

st.markdown("---")

# --- Fetch Notifications ---
notifications = get_user_notifications(user['id'], limit=100)

if not notifications:
    st.info("You have no notifications")
else:
    # Convert to DataFrame for easier handling
    df = pd.DataFrame(notifications)
    
    # Add readable timestamp
    df['timestamp'] = pd.to_datetime(df['created_at']).dt.strftime("%Y-%m-%d %H:%M")
    
    # Add icon column
    icon_map = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    df['icon'] = df['type'].map(icon_map).fillna("ℹ️")
    
    # Add status column
    df['status'] = df['is_read'].apply(lambda x: "Read" if x else "Unread")
    
    # Filter options
    st.subheader("Filter Notifications")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        type_filter = st.multiselect(
            "Notification Type",
            ["info", "success", "warning", "error"],
            default=["info", "success", "warning", "error"]
        )
    
    with filter_col2:
        status_filter = st.radio("Read Status", ["All", "Read", "Unread"], horizontal=True)
    
    # Apply filters
    filtered_df = df.copy()
    
    if type_filter:
        filtered_df = filtered_df[filtered_df['type'].isin(type_filter)]
    
    if status_filter == "Read":
        filtered_df = filtered_df[filtered_df['is_read'] == True]
    elif status_filter == "Unread":
        filtered_df = filtered_df[filtered_df['is_read'] == False]
    
    # Display statistics
    st.subheader(f"Showing {len(filtered_df)} of {len(df)} notifications")
    
    # Display notifications
    if filtered_df.empty:
        st.info("No notifications match your filters")
    else:
        # Group by date
        filtered_df['date'] = pd.to_datetime(filtered_df['created_at']).dt.date
        grouped = filtered_df.groupby('date')
        
        for date, group in grouped:
            st.markdown(f"### 📅 {date.strftime('%A, %B %d, %Y')}")
            
            for _, notification in group.iterrows():
                # Style based on notification type and read status
                bg_color = {
                    "info": "#e3f2fd" if notification['is_read'] else "#bbdefb",
                    "success": "#e8f5e9" if notification['is_read'] else "#c8e6c9",
                    "warning": "#fff3e0" if notification['is_read'] else "#ffe0b2",
                    "error": "#ffebee" if notification['is_read'] else "#ffcdd2"
                }.get(notification['type'], "#f5f5f5")
                
                border_left = {
                    "info": "4px solid #2196f3",
                    "success": "4px solid #4caf50",
                    "warning": "4px solid #ff9800",
                    "error": "4px solid #f44336"
                }.get(notification['type'], "4px solid #9e9e9e")
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; border-left: {border_left}; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="font-size: 1.2em; margin-bottom: 5px;">
                                <strong>{notification['icon']}</strong> {notification['message']}
                            </div>
                            {f"<div style='font-size: 0.9em; color: #666; margin-top: 5px;'>Related to: {notification['related_entity']} #{notification['entity_id']}</div>" if notification['related_entity'] else ""}
                        </div>
                        <div style="text-align: right; font-size: 0.8em; color: #666;">
                            {notification['timestamp']}
                            <br/>
                            <span style="background-color: {'#e0e0e0' if notification['is_read'] else '#2196f3'}; color: {'#666' if notification['is_read'] else 'white'}; padding: 2px 6px; border-radius: 10px;">
                                {notification['status']}
                            </span>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                        <button onclick="deleteNotification({notification['id']})" style="background-color: #f44336; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
                            Delete
                        </button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Mark as read when viewed
                if not notification['is_read']:
                    mark_notification_as_read(notification['id'])
        
        # Export options
        st.markdown("---")
        st.subheader("Export Notifications")
        
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            if st.button("📥 Export All Notifications (CSV)"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"notifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with export_col2:
            if st.button("🗑️ Clear All Notifications"):
                st.warning("This feature is not yet implemented. Please delete notifications individually.")

# --- Help Section ---
with st.expander("ℹ️ About Notifications"):
    st.markdown("""
    ### Notification System
    
    **Types of Notifications:**
    - ℹ️ **Info**: General information and updates
    - ✅ **Success**: Successful operations and completions
    - ⚠️ **Warning**: Warnings and cautions
    - ❌ **Error**: Errors and failures
    
    **How It Works:**
    - Notifications are automatically marked as read when you view them
    - You can manually mark all notifications as read
    - Unread notifications are highlighted in the sidebar
    
    **Best Practices:**
    - Regularly check your notifications for important updates
    - Delete notifications you no longer need to keep your inbox clean
    """)