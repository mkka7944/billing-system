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
