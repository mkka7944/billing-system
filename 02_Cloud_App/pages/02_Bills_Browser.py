import streamlit as st
import pandas as pd

st.title("Bills Browser")
st.write("Browse and search bills.")

# Sample data
data = {
    'Bill ID': ['BILL-001', 'BILL-002', 'BILL-003'],
    'Consumer': ['John Doe', 'Jane Smith', 'Bob Johnson'],
    'Amount': ['PKR 1,200', 'PKR 800', 'PKR 1,500'],
    'Status': ['Paid', 'Pending', 'Overdue']
}

df = pd.DataFrame(data)
st.dataframe(df)

# Add search functionality
search_term = st.text_input("Search bills...")
if search_term:
    st.write(f"Searching for: {search_term}")