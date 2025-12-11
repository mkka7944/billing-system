from services.db import supabase
import pandas as pd
import streamlit as st

@st.cache_data(ttl=60)
def fetch_data(table_name: str, columns: str = "*", filters: dict = None, order_by: str = None):
    """
    Generic data fetcher with caching (1 min TTL).
    filters: dict where key is column name and value is value to equal match.
    """
    try:
        query = supabase.table(table_name).select(columns)
        
        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)
        
        if order_by:
            # Simple ordering, defaults to Ascending
            query = query.order(order_by)
            
        response = query.execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def fetch_paginated_data(table_name: str, columns: str = "*", filters: dict = None, 
                       order_by: str = None, page: int = 1, page_size: int = 50):
    """
    Fetch paginated data from a table with optimized limits to prevent over-fetching.
    
    Args:
        table_name (str): Name of the table
        columns (str): Columns to select
        filters (dict): Filter conditions
        order_by (str): Column to order by
        page (int): Page number (1-based)
        page_size (int): Number of records per page (max 50 to prevent over-fetching)
        
    Returns:
        tuple: (data_df, total_count)
    """
    # Limit page_size to prevent over-fetching
    page_size = min(page_size, 50)
    
    try:
        # First, get total count with filters applied
        count_query = supabase.table(table_name).select("count", count="exact")
        
        if filters:
            for col, val in filters.items():
                count_query = count_query.eq(col, val)
                
        count_response = count_query.execute()
        total_count = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
        
        # Then fetch paginated data
        query = supabase.table(table_name).select(columns)
        
        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)
        
        if order_by:
            query = query.order(order_by)
            
        # Apply pagination
        query = query.range((page - 1) * page_size, page * page_size - 1)
        
        response = query.execute()
        
        if response.data:
            return pd.DataFrame(response.data), total_count
        return pd.DataFrame(), total_count
        
    except Exception as e:
        st.error(f"Error fetching paginated data from {table_name}: {str(e)}")
        return pd.DataFrame(), 0

def upsert_record(table_name: str, record: dict, on_conflict: str = None):
    """
    Inserts or updates a record.
    record: Dictionary of data
    """
    try:
        query = supabase.table(table_name).upsert(record)
        if on_conflict:
             query = supabase.table(table_name).upsert(record, on_conflict=on_conflict)
             
        response = query.execute()
        return response.data
    except Exception as e:
        raise e

def delete_record(table_name: str, id_column: str, id_value):
    """
    Deletes a record.
    """
    try:
        response = supabase.table(table_name).delete().eq(id_column, id_value).execute()
        return response.data
    except Exception as e:
        raise e

@st.cache_data(ttl=300)  # Cache for 5 minutes for location data
def fetch_unique_locations():
    """
    Fetch unique locations with caching to prevent repeated queries.
    """
    try:
        response = supabase.table("unique_locations").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching locations: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=120)  # Cache for 2 minutes for staff data
def fetch_active_staff():
    """
    Fetch active staff members with caching.
    """
    try:
        response = supabase.table("staff").select("id, full_name, username, role").eq("is_active", True).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching staff: {str(e)}")
        return pd.DataFrame()