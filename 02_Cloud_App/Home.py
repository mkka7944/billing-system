import streamlit as st
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import only what we need, with fallback for missing modules
try:
    from services import repository
except ImportError:
    repository = None

try:
    from components import sidebar
except ImportError:
    sidebar = None

# --- Page Config ---
st.set_page_config(
    page_title="Suthra Punjab Operations",
    page_icon="🇵🇰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Modern Dark Theme CSS ---
def inject_custom_css():
    """Inject modern dark theme with rounded corners and gradients"""
    st.markdown("""
    <style>
    /* Global Dark Theme */
    :root {
        --bg-primary: #0d1117;
        --bg-secondary: #161b22;
        --bg-tertiary: #1c2128;
        --bg-card: #21262d;
        --border-color: #30363d;
        --text-primary: #e6edf3;
        --text-secondary: #7d8590;
        --accent-purple: #8b5cf6;
        --accent-blue: #3b82f6;
        --accent-green: #10b981;
        --accent-orange: #f59e0b;
        --accent-red: #ef4444;
        --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-card: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.5);
        --shadow-glow: 0 0 20px rgba(139, 92, 246, 0.3);
        /* Subtle hover effect colors */
        --hover-subtle: rgba(139, 92, 246, 0.1);
        --hover-subtle-blue: rgba(59, 130, 246, 0.1);
        --hover-subtle-green: rgba(16, 185, 129, 0.1);
    }
    
    /* Main App Background */
    .stApp {
        background: var(--bg-primary);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600;
    }
    
    p, span, div {
        color: var(--text-secondary);
    }
    
    /* Metric Cards - Modern Glass Morphism */
    [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
        border-color: var(--accent-purple);
    }
    
    [data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Buttons - Modern with Gradient */
    .stButton > button {
        background: var(--gradient-primary);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-md);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
    }
    
    .stButton > button:disabled {
        background: var(--bg-tertiary);
        color: var(--text-secondary);
        cursor: not-allowed;
    }
    
    /* Expander - Modern Card Style */
    .streamlit-expanderHeader {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        color: var(--text-primary) !important;
        font-weight: 600;
        padding: 1rem;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--hover-subtle);
    }
    
    .streamlit-expanderContent {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 0 0 12px 12px;
        border-top: none;
    }
    
    /* Info/Warning Boxes */
    .stAlert {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        border-left: 4px solid var(--accent-blue);
        padding: 1rem;
    }
    
    .stAlert:hover {
        background: var(--hover-subtle-blue);
    }
    
    /* Dataframe/Tables */
    [data-testid="stDataFrame"] {
        background: var(--bg-card);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: var(--shadow-md);
    }
    
    /* Plotly Charts */
    .js-plotly-plot {
        border-radius: 16px;
        background: var(--bg-card) !important;
        padding: 1rem;
        box-shadow: var(--shadow-md);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--accent-purple) !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent-purple);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #9d6fff;
    }
    
    /* Custom Card Class */
    .modern-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }
    
    .modern-card:hover {
        background: var(--hover-subtle);
        border-color: var(--accent-purple);
        box-shadow: var(--shadow-lg);
    }
    
    /* Activity Item */
    .activity-item {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--accent-purple);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }
    
    .activity-item:hover {
        background: var(--hover-subtle);
        transform: translateX(4px);
        border-left-color: var(--accent-blue);
    }
    
    /* Header Gradient */
    .header-gradient {
        background: var(--gradient-primary);
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        box-shadow: var(--shadow-lg), var(--shadow-glow);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .header-gradient::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .header-gradient h1 {
        color: white !important;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        position: relative;
        z-index: 1;
    }
    
    .header-gradient p {
        color: rgba(255, 255, 255, 0.9) !important;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        position: relative;
        z-index: 1;
    }
    
    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- Main App Logic ---
def main():
    
    # TEMPORARY: Skip authentication for development focus on Home.py
    # Comment out these lines when authentication is needed
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = True
        st.session_state['user_name'] = 'Developer'
        st.session_state['user_role'] = 'admin'
        st.session_state['assigned_city'] = 'Development'
    
    # Check session timeout
    # check_session_timeout()  # Disabled for development
    
    # Update last activity
    # update_last_activity()  # Disabled for development
    
    # Render Sidebar (always, but state aware)
    if sidebar:
        sidebar.render_sidebar()
    
    # --- ENHANCED HOME PAGE ---
    render_home_page()


def render_home_page():
    """Modern dark-themed home page with sleek design"""
    
    # Consolidated Header with User Info and Time/Date
    st.markdown("""
    <div class='header-gradient'>
        <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;'>
            <div>
                <h1 style='margin: 0 0 0.5rem 0;'>🇵🇰 Suthra Punjab Operations Center</h1>
                <p style='margin: 0;'>Waste Management & Billing System</p>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;'>Welcome, <span style='background: linear-gradient(135deg, #ffffff, #e0e0ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>{}</span>!</div>
                <div style='font-size: 0.9rem; margin-bottom: 0.5rem;'>Role: <strong style='color: #d0c0ff;'>{}</strong> | Location: <strong style='color: #c0d0ff;'>{}</strong></div>
                <div style='display: flex; gap: 1rem; justify-content: flex-end;'>
                    <div style='background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 8px;'>
                        <div style='font-size: 0.75rem; opacity: 0.8;'>CURRENT TIME</div>
                        <div style='font-size: 1.1rem; font-weight: 600;'>⏰ {}</div>
                    </div>
                    <div style='background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 8px;'>
                        <div style='font-size: 0.75rem; opacity: 0.8;'>TODAY'S DATE</div>
                        <div style='font-size: 1.1rem; font-weight: 600;'>📅 {}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """.format(
        st.session_state.get('user_name', 'User'),
        st.session_state.get('user_role', 'N/A').upper(),
        st.session_state.get('assigned_city', 'N/A'),
        datetime.now().strftime("%I:%M %p"),
        datetime.now().strftime("%b %d, %Y")
    ), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Modern Section Header
    st.markdown("""
    <div style='margin: 2rem 0 1.5rem 0;'>
        <h2 style='margin: 0; font-size: 1.75rem;'>📊 System Overview</h2>
        <p style='margin: 0.25rem 0 0 0; color: var(--text-secondary);'>Real-time metrics and performance indicators</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Loading system metrics..."):
        # Fetch real data from database
        try:
            if repository:
                bills_df = repository.fetch_data("bills", columns="id, payment_status, amount_due, created_at")
                staff_df = repository.fetch_data("staff", columns="id, is_active, role")
                tickets_df = repository.fetch_data("tickets", columns="ticket_id, status, priority")
            else:
                # Use empty dataframes if repository not available
                bills_df = pd.DataFrame()
                staff_df = pd.DataFrame()
                tickets_df = pd.DataFrame()
            
            # Calculate metrics
            total_bills = len(bills_df) if not bills_df.empty else 0
            paid_bills = len(bills_df[bills_df['payment_status'] == 'PAID']) if not bills_df.empty else 0
            pending_bills = len(bills_df[bills_df['payment_status'] == 'UNPAID']) if not bills_df.empty else 0
            total_revenue = bills_df[bills_df['payment_status'] == 'PAID']['amount_due'].sum() if not bills_df.empty else 0
            
            active_staff = len(staff_df[staff_df['is_active']]) if not staff_df.empty else 0
            open_tickets = len(tickets_df[tickets_df['status'] == 'OPEN']) if not tickets_df.empty else 0
            
        except Exception as e:
            st.warning(f"Could not load live data. Showing sample metrics. Error: {e}")
            total_bills = 1250
            paid_bills = 890
            pending_bills = 360
            total_revenue = 2450000
            active_staff = 24
            open_tickets = 15
    
    # KPI Cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    with kpi1:
        st.metric(
            label="💳 Total Bills",
            value=f"{total_bills:,}",
            delta=f"+{int(total_bills * 0.08)} this week"
        )
    
    with kpi2:
        st.metric(
            label="✅ Paid Bills",
            value=f"{paid_bills:,}",
            delta=f"{(paid_bills/total_bills*100):.1f}% collection" if total_bills > 0 else "0%"
        )
    
    with kpi3:
        st.metric(
            label="⏳ Pending Bills",
            value=f"{pending_bills:,}",
            delta=f"-{int(pending_bills * 0.05)} cleared",
            delta_color="inverse"
        )
    
    with kpi4:
        st.metric(
            label="💰 Revenue Collected",
            value=f"PKR {total_revenue/1000000:.2f}M",
            delta="+12.5% vs last month"
        )
    
    with kpi5:
        st.metric(
            label="👥 Active Staff",
            value=f"{active_staff}",
            delta=f"{open_tickets} open tickets"
        )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Charts Section with Modern Headers
    st.markdown("""
    <div style='margin: 2rem 0 1.5rem 0;'>
        <h2 style='margin: 0; font-size: 1.75rem;'>📈 Analytics & Insights</h2>
        <p style='margin: 0.25rem 0 0 0; color: var(--text-secondary);'>Visual representation of key metrics</p>
    </div>
    """, unsafe_allow_html=True)
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("<h3 style='font-size: 1.25rem; margin-bottom: 1rem;'>Payment Status Distribution</h3>", unsafe_allow_html=True)
        
        # Create pie chart
        payment_data = pd.DataFrame({
            'Status': ['Paid', 'Pending', 'Overdue'],
            'Count': [paid_bills, pending_bills, int(pending_bills * 0.3)]
        })
        
        fig_pie = px.pie(
            payment_data,
            values='Count',
            names='Status',
            color='Status',
            color_discrete_map={'Paid': '#10b981', 'Pending': '#f59e0b', 'Overdue': '#ef4444'},
            hole=0.5
        )
        fig_pie.update_layout(
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e6edf3', size=12),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, width='stretch')
    
    with chart_col2:
        st.markdown("<h3 style='font-size: 1.25rem; margin-bottom: 1rem;'>Weekly Collection Trend</h3>", unsafe_allow_html=True)
        
        # Create line chart
        dates = pd.date_range(end=datetime.now(), periods=7).strftime('%a')
        trend_data = pd.DataFrame({
            'Day': dates,
            'Revenue': [350000 + i*25000 for i in range(7)]
        })
        
        fig_line = px.area(
            trend_data,
            x='Day',
            y='Revenue',
            markers=True
        )
        fig_line.update_traces(
            line_color='#8b5cf6',
            fillcolor='rgba(139, 92, 246, 0.2)',
            line_width=3,
            marker=dict(size=8, color='#8b5cf6')
        )
        fig_line.update_layout(
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e6edf3', size=12),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(48, 54, 61, 0.5)',
                zeroline=False
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(48, 54, 61, 0.5)',
                zeroline=False
            ),
            hovermode='x unified'
        )
        st.plotly_chart(fig_line, width='stretch')
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Quick Actions & Activity with Modern Headers
    action_col1, action_col2 = st.columns([1, 1])
    
    with action_col1:
        st.markdown("""
        <div style='margin-bottom: 1.5rem;'>
            <h2 style='margin: 0; font-size: 1.75rem;'>⚡ Quick Actions</h2>
            <p style='margin: 0.25rem 0 0 0; color: var(--text-secondary);'>Navigate to key system modules</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class='modern-card' style='background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6;'>
            <div style='display: flex; align-items: center; gap: 0.75rem;'>
                <div style='font-size: 1.5rem;'>📌</div>
                <div>
                    <strong style='color: #3b82f6;'>Development Mode</strong>
                    <p style='margin: 0.25rem 0 0 0; font-size: 0.875rem;'>Pages are temporarily disabled. Focus on Home.py development.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        action1, action2 = st.columns(2)
        with action1:
            if st.button("📊 View Dashboard", use_container_width=True, disabled=True):
                st.info("Dashboard page is temporarily disabled")
            if st.button("💳 Browse Bills", use_container_width=True, disabled=True):
                st.info("Bills page is temporarily disabled")
            if st.button("📋 Survey Units", use_container_width=True, disabled=True):
                st.info("Survey page is temporarily disabled")
        
        with action2:
            if st.button("👥 Manage Staff", use_container_width=True, disabled=True):
                st.info("Staff page is temporarily disabled")
            if st.button("🎫 View Tickets", use_container_width=True, disabled=True):
                st.info("Tickets page is temporarily disabled")
            if st.button("📈 Generate Reports", use_container_width=True, disabled=True):
                st.info("Reports page is temporarily disabled")
    
    with action_col2:
        st.markdown("""
        <div style='margin-bottom: 1.5rem;'>
            <h2 style='margin: 0; font-size: 1.75rem;'>🔔 Recent Activity</h2>
            <p style='margin: 0.25rem 0 0 0; color: var(--text-secondary);'>Latest system events and updates</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Activity Feed
        activities = [
            {"time": "5 min ago", "icon": "💳", "text": "New bill payment received - PKR 2,500"},
            {"time": "12 min ago", "icon": "🎫", "text": "Ticket #TK-1234 was resolved"},
            {"time": "25 min ago", "icon": "👤", "text": "New staff member registered"},
            {"time": "1 hour ago", "icon": "📊", "text": "Monthly report generated"},
            {"time": "2 hours ago", "icon": "📋", "text": "Survey completed for UC-North"},
        ]
        
        for activity in activities:
            st.markdown(f"""
            <div class='activity-item'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='display: flex; align-items: center; gap: 0.75rem;'>
                        <span style='font-size: 1.25rem;'>{activity['icon']}</span>
                        <span style='color: var(--text-primary); font-weight: 500;'>{activity['text']}</span>
                    </div>
                    <small style='color: var(--text-secondary); font-size: 0.75rem;'>{activity['time']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Modern Footer Section
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    
    with footer_col1:
        st.markdown("""
        <div class='modern-card'>
            <h3 style='font-size: 1.125rem; margin: 0 0 1rem 0;'>🎯 System Status</h3>
            <div style='display: flex; flex-direction: column; gap: 0.5rem;'>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: var(--text-secondary);'>Database</span>
                    <span style='color: var(--accent-green); font-weight: 600;'>🟢 Connected</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: var(--text-secondary);'>API</span>
                    <span style='color: var(--accent-green); font-weight: 600;'>🟢 Operational</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: var(--text-secondary);'>Last Sync</span>
                    <span style='color: var(--text-primary); font-weight: 600;'>Just now</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with footer_col2:
        st.markdown("""
        <div class='modern-card'>
            <h3 style='font-size: 1.125rem; margin: 0 0 1rem 0;'>📊 Today's Summary</h3>
            <div style='display: flex; flex-direction: column; gap: 0.5rem;'>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: var(--text-secondary);'>Bills Processed</span>
                    <span style='color: var(--accent-purple); font-weight: 700;'>124</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: var(--text-secondary);'>Revenue Collected</span>
                    <span style='color: var(--accent-blue); font-weight: 700;'>PKR 385K</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: var(--text-secondary);'>Tickets Resolved</span>
                    <span style='color: var(--accent-green); font-weight: 700;'>8</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with footer_col3:
        st.markdown("""
        <div class='modern-card'>
            <h3 style='font-size: 1.125rem; margin: 0 0 1rem 0;'>🔗 Quick Links</h3>
            <div style='display: flex; flex-direction: column; gap: 0.5rem;'>
                <a href='docs/' style='color: var(--accent-purple); text-decoration: none; transition: all 0.2s;' onmouseover='this.style.color="#9d6fff"' onmouseout='this.style.color="#8b5cf6"'>📚 Documentation →</a>
                <a href='#' style='color: var(--accent-purple); text-decoration: none; transition: all 0.2s;' onmouseover='this.style.color="#9d6fff"' onmouseout='this.style.color="#8b5cf6"'>🔌 API Reference →</a>
                <a href='#' style='color: var(--accent-purple); text-decoration: none; transition: all 0.2s;' onmouseover='this.style.color="#9d6fff"' onmouseout='this.style.color="#8b5cf6"'>💬 Support Center →</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Modern Development Info
    with st.expander("🛠️ Development Info & Settings"):
        st.markdown("""
        <div class='modern-card' style='background: var(--hover-subtle);'>
            <h4 style='margin: 0 0 1rem 0; color: var(--accent-purple);'>Development Mode Active</h4>
            <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;'>
                <div>
                    <div style='color: var(--accent-green); font-weight: 600; margin-bottom: 0.5rem;'>✅ Enabled Features</div>
                    <ul style='margin: 0; padding-left: 1.5rem; color: var(--text-secondary);'>
                        <li>Modern dark theme</li>
                        <li>Real-time data integration</li>
                        <li>Interactive analytics</li>
                        <li>Responsive design</li>
                    </ul>
                </div>
                <div>
                    <div style='color: var(--accent-orange); font-weight: 600; margin-bottom: 0.5rem;'>⚠️ Disabled For Testing</div>
                    <ul style='margin: 0; padding-left: 1.5rem; color: var(--text-secondary);'>
                        <li>Authentication system</li>
                        <li>All page navigation</li>
                        <li>Session management</li>
                    </ul>
                </div>
            </div>
            <hr style='margin: 1.5rem 0; opacity: 0.3;'>
            <div style='font-size: 0.875rem; color: var(--text-secondary);'>
                <strong>Re-enable pages:</strong> Rename <code>.disabled</code> files to <code>.py</code><br>
                <strong>Enable auth:</strong> Uncomment auth code in <code>main()</code> function
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()