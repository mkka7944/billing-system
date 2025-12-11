import streamlit as st
from services import auth
from utils.notifications import get_unread_notification_count

def render_sidebar():
    """
    Renders the consistent sidebar with user info and navigation.
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
            if st.button("🚪 Logout", use_container_width=True):
                auth.logout()
        else:
            st.info("Please log in to continue.")
            
        st.markdown("---")
        st.caption("v2.0.0 | Billing System")