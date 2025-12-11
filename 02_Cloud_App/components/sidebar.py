import streamlit as st
from services import auth
from utils.notifications import get_unread_notification_count

# Global variable to store user's preferred navigation layout
if 'nav_layout' not in st.session_state:
    st.session_state.nav_layout = 'default'  # default, compact, expanded

def render_sidebar():
    """
    Renders the consistent sidebar with user info and navigation.
    Implements AppSheet-like hierarchical navigation with primary and menu navigation.
    Supports customizable navigation options.
    """
    user = auth.get_current_user()
    
    with st.sidebar:
        st.image("assets/logo.png", use_container_width=True) if "logo" in st.query_params else st.title("Suthra Punjab")
        
        st.markdown("---")
        
        if user:
            st.write(f"**👤 {user['name']}**")
            st.caption(f"Role: {user['role']}")
            st.caption(f"City: {user['city'] or 'All'}")
            
            # Show notification count (will silently fail if notifications table doesn't exist)
            try:
                unread_count = get_unread_notification_count(user['id'])
                if unread_count > 0:
                    st.markdown(f"🔔 **Notifications:** {unread_count} unread")
            except:
                # Silently ignore notification errors
                pass
            
            st.markdown("---")
            
            # CUSTOMIZATION OPTIONS
            with st.expander("⚙️ Navigation Settings", expanded=False):
                nav_layout = st.radio(
                    "Layout Style",
                    options=["Default", "Compact", "Expanded"],
                    index=["Default", "Compact", "Expanded"].index(st.session_state.nav_layout.capitalize()),
                    key="nav_layout_radio"
                )
                
                # Update session state
                st.session_state.nav_layout = nav_layout.lower()
                
                # Option to expand all sections by default
                expand_all = st.checkbox("Expand all sections by default", key="expand_all_nav")
                
                # Reset to default
                if st.button("Reset to Default"):
                    st.session_state.nav_layout = 'default'
                    st.rerun()
            
            # PRIMARY NAVIGATION - Main app sections
            st.subheader("🧭 Primary Navigation")
            
            # Dashboard (accessible to all users)
            st.page_link("pages/01_Dashboard.py", label="📊 Dashboard", icon="📊")
            
            # Bills Management (accessible to all users)
            st.page_link("pages/02_Bills_Browser.py", label="💰 Bills", icon="💰")
            
            # Survey Units (accessible to all users)
            st.page_link("pages/04_Survey_Units.py", label="🏠 Survey Units", icon="🏠")
            
            # Tickets (accessible to all users)
            st.page_link("pages/05_Ticket_Center.py", label="🎫 Tickets", icon="🎫")
            
            # Locations (accessible to all users)
            st.page_link("pages/06_Locations.py", label="📍 Locations", icon="📍")
            
            # COLLAPSIBLE MENU SECTIONS
            # Admin Section
            if user['role'] in ['admin', 'manager']:
                with st.expander("🔐 Admin Tools", expanded=expand_all):
                    st.page_link("pages/03_Staff_Manager.py", label="👥 Staff Manager", icon="👥")
                    st.page_link("pages/08_Bulk_Operations.py", label="⚡ Bulk Ops", icon="⚡")
            
            # Reports Section
            with st.expander("📈 Reports & Analytics", expanded=expand_all):
                st.page_link("pages/07_Reports.py", label="📈 Reports", icon="📈")
                # Additional report links can be added here
                if st.button("📋 Bill Status Report", key="ref_bill_status_report"):
                    st.switch_page("pages/07_Reports.py")
                
                if st.button("💵 Payment Summary", key="ref_payment_summary"):
                    st.switch_page("pages/07_Reports.py")
            
            # Notifications Section
            with st.expander("🔔 Communications", expanded=expand_all):
                st.page_link("pages/09_Notifications.py", label="🔔 Notifications", icon="🔔")
                # Additional communication links can be added here
            
            # Reference Views Section
            with st.expander("📚 Reference", expanded=expand_all):
                # Quick reference links for common data
                if st.button("📋 Bill Status Types", key="ref_bill_status"):
                    st.switch_page("pages/07_Reports.py")
                
                if st.button("🧾 Payment Methods", key="ref_payment_methods"):
                    st.switch_page("pages/07_Reports.py")
                
                if st.button("📍 Location Codes", key="ref_location_codes"):
                    st.switch_page("pages/06_Locations.py")
                
                if st.button("👥 User Roles", key="ref_user_roles"):
                    st.switch_page("pages/03_Staff_Manager.py")
            
            st.markdown("---")
            
            # DEEP LINKING SECTION
            st.subheader("🔗 Quick Links")
            # These are contextual links that can be used for deep linking
            if st.button("🆕 Create New Bill", key="deep_link_new_bill"):
                st.switch_page("pages/02_Bills_Browser.py")
            
            if st.button("➕ Add Survey Unit", key="deep_link_add_unit"):
                st.switch_page("pages/04_Survey_Units.py")
            
            if st.button("✏️ New Ticket", key="deep_link_new_ticket"):
                st.switch_page("pages/05_Ticket_Center.py")
            
            st.markdown("---")
            
            # User Actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            
            with col2:
                if st.button("🚪 Logout", use_container_width=True):
                    auth.logout()
        else:
            st.info("Please log in to continue.")
            
        st.markdown("---")
        st.caption("v2.0.0 | Billing System")