import streamlit as st
from services import auth

def render_sidebar():
    """
    Renders the consistent sidebar with user info and navigation.
    """
    user = auth.get_current_user()
    
    with st.sidebar:
        st.image("assets/logo.png", use_container_width=True) if st.sidebar.query_params.get("logo") else st.title("Suthra Punjab")
        
        st.markdown("---")
        
        if user:
            st.write(f"**👤 {user['name']}**")
            st.caption(f"Role: {user['role']}")
            st.caption(f"City: {user['city'] or 'All'}")
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                auth.logout()
        else:
            st.info("Please log in to continue.")
            
        st.markdown("---")
        st.caption("v2.0.0 | Billing System")
