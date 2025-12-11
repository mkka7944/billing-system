"""
Pagination component for the billing system.
Provides reusable pagination functionality for large datasets.
"""
import streamlit as st
import math
from typing import List, Any

def paginate_data(data: List[Any], page_size: int = 100, key_prefix: str = "pagination") -> List[Any]:
    """
    Paginate a list of data.
    
    Args:
        data (List[Any]): The data to paginate
        page_size (int): Number of items per page (default: 100)
        key_prefix (str): Prefix for Streamlit keys to avoid conflicts
        
    Returns:
        List[Any]: The paginated data for the current page
    """
    if not data:
        return []
    
    # Calculate total pages
    total_items = len(data)
    total_pages = math.ceil(total_items / page_size)
    
    # Initialize session state for current page if not exists
    page_key = f"{key_prefix}_current_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    
    # Create pagination controls
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
    
    with col1:
        if st.button("⏮️ First", key=f"{key_prefix}_first", disabled=st.session_state[page_key] <= 1):
            st.session_state[page_key] = 1
            st.rerun()
    
    with col2:
        if st.button("◀️ Prev", key=f"{key_prefix}_prev", disabled=st.session_state[page_key] <= 1):
            st.session_state[page_key] -= 1
            st.rerun()
    
    with col3:
        st.write(f"Page {st.session_state[page_key]} of {total_pages}")
    
    with col4:
        if st.button("Next ▶️", key=f"{key_prefix}_next", disabled=st.session_state[page_key] >= total_pages):
            st.session_state[page_key] += 1
            st.rerun()
    
    with col5:
        if st.button("Last ⏭️", key=f"{key_prefix}_last", disabled=st.session_state[page_key] >= total_pages):
            st.session_state[page_key] = total_pages
            st.rerun()
    
    # Display page size selector
    st_cols = st.columns([1, 3])
    with st_cols[0]:
        selected_page_size = st.selectbox(
            "Items per page:",
            options=[50, 100, 200, 500],
            index=[50, 100, 200, 500].index(min(page_size, 500)),
            key=f"{key_prefix}_page_size"
        )
    
    # Update page size if changed
    if selected_page_size != page_size:
        page_size = selected_page_size
        total_pages = math.ceil(total_items / page_size)
        # Reset to first page if current page exceeds new total
        if st.session_state[page_key] > total_pages:
            st.session_state[page_key] = 1
        st.rerun()
    
    # Calculate start and end indices for current page
    start_idx = (st.session_state[page_key] - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)
    
    # Return the data slice for current page
    return data[start_idx:end_idx]

def paginated_dataframe(df, page_size: int = 100, key_prefix: str = "df_pagination"):
    """
    Display a pandas DataFrame with pagination.
    
    Args:
        df (pd.DataFrame): The DataFrame to display
        page_size (int): Number of rows per page (default: 100)
        key_prefix (str): Prefix for Streamlit keys to avoid conflicts
    """
    if df.empty:
        st.info("No data to display.")
        return
    
    # Paginate the dataframe
    paginated_df = paginate_data(df.to_dict('records'), page_size, key_prefix)
    
    # Convert back to DataFrame for display
    if paginated_df:
        st.dataframe(pd.DataFrame(paginated_df), use_container_width=True)
    else:
        st.info("No data to display for this page.")

# Import pandas here to avoid circular imports
import pandas as pd