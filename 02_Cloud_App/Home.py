import streamlit as st
import time
from services import auth
from components import sidebar
from utils.session import check_session_timeout, update_last_activity

# --- Page Config ---
st.set_page_config(
    page_title="Suthra Punjab Operations",
    page_icon="🇵🇰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load Custom CSS ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # Silently ignore if CSS files are missing
        pass
    except Exception as e:
        # Silently ignore any other CSS loading errors
        pass

try:
    local_css("assets/style.css")
    local_css("assets/mobile.css")
except:
    # Silently ignore CSS loading errors
    pass

# --- Main App Logic ---
def main():
    
    # Check session timeout
    check_session_timeout()
    
    # Update last activity
    update_last_activity()
    
    # Render Sidebar (always, but state aware)
    sidebar.render_sidebar()
    
    if not st.session_state.get("logged_in"):
        # Login View
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🇵🇰 Suthra Punjab Login")
            st.markdown("Please sign in to access the operations dashboard.")
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Sign In", type="primary", use_container_width=True):
                    if auth.login(username, password):
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
    else:
        # Welcome View
        st.title(f"Welcome, {st.session_state['user_name']}!")
        
        st.info("👈 Use the *sidebar navigation* to access specific modules.")
        
        st.markdown("""
        ### Quick Stats
        - **System Status**: 🟢 Online
        - **Your Role**: `{}`
        - **Assigned Area**: `{}`
        """.format(
            st.session_state.get('user_role'), 
            st.session_state.get('assigned_city') or 'Global'
        ))
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("#### Recent Updates")
            st.write("- System maintenance scheduled for Sunday.")
            st.write("- New report module available.")
            
        with col2:
            if st.button("Go to Dashboard ➡", type="primary"):
                st.switch_page("pages/01_Dashboard.py")

if __name__ == "__main__":
    main()