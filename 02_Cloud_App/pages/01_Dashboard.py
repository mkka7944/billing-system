import streamlit as st

st.title("Dashboard")
st.write("This is the dashboard page.")

# Add some sample content
st.subheader("System Overview")
st.metric(label="Total Bills", value="1,250")
st.metric(label="Paid Bills", value="890")
st.metric(label="Pending Bills", value="360")

st.subheader("Recent Activity")
st.write("- New bill processed")
st.write("- Payment received")
st.write("- Ticket resolved")