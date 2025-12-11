"""
Bulk operations utilities for the billing system.
Provides functions for bulk data manipulation and updates.
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from services.db import supabase

def bulk_update_records(table_name: str, record_ids: List[str], id_column: str, 
                       updates: Dict[str, Any], batch_size: int = 100) -> Dict[str, int]:
    """
    Bulk update records in a table.
    
    Args:
        table_name (str): Name of the table to update
        record_ids (List[str]): List of record IDs to update
        id_column (str): Name of the ID column
        updates (Dict[str, Any]): Dictionary of column-value pairs to update
        batch_size (int): Number of records to update in each batch
        
    Returns:
        Dict[str, int]: Results with 'success' and 'failed' counts
    """
    success_count = 0
    failed_count = 0
    
    # Process in batches to avoid timeouts
    for i in range(0, len(record_ids), batch_size):
        batch_ids = record_ids[i:i + batch_size]
        
        try:
            # Build the query for batch update
            query = supabase.table(table_name).update(updates)
            
            # Apply filter for this batch
            query = query.in_(id_column, batch_ids)
            
            # Execute the update
            response = query.execute()
            
            # Count successful updates (response.data contains updated records)
            success_count += len(response.data) if response.data else 0
            
        except Exception as e:
            st.error(f"Error updating batch {i//batch_size + 1}: {str(e)}")
            failed_count += len(batch_ids)
    
    return {
        "success": success_count,
        "failed": failed_count
    }

def bulk_delete_records(table_name: str, record_ids: List[str], id_column: str, 
                       batch_size: int = 100) -> Dict[str, int]:
    """
    Bulk delete records from a table.
    
    Args:
        table_name (str): Name of the table to delete from
        record_ids (List[str]): List of record IDs to delete
        id_column (str): Name of the ID column
        batch_size (int): Number of records to delete in each batch
        
    Returns:
        Dict[str, int]: Results with 'success' and 'failed' counts
    """
    success_count = 0
    failed_count = 0
    
    # Process in batches to avoid timeouts
    for i in range(0, len(record_ids), batch_size):
        batch_ids = record_ids[i:i + batch_size]
        
        try:
            # Build the query for batch delete
            query = supabase.table(table_name).delete()
            
            # Apply filter for this batch
            query = query.in_(id_column, batch_ids)
            
            # Execute the delete
            response = query.execute()
            
            # Count successful deletions
            success_count += len(response.data) if response.data else 0
            
        except Exception as e:
            st.error(f"Error deleting batch {i//batch_size + 1}: {str(e)}")
            failed_count += len(batch_ids)
    
    return {
        "success": success_count,
        "failed": failed_count
    }

def bulk_insert_records(table_name: str, records: List[Dict[str, Any]], 
                       batch_size: int = 100) -> Dict[str, int]:
    """
    Bulk insert records into a table.
    
    Args:
        table_name (str): Name of the table to insert into
        records (List[Dict[str, Any]]): List of records to insert
        batch_size (int): Number of records to insert in each batch
        
    Returns:
        Dict[str, int]: Results with 'success' and 'failed' counts
    """
    success_count = 0
    failed_count = 0
    
    # Process in batches to avoid timeouts
    for i in range(0, len(records), batch_size):
        batch_records = records[i:i + batch_size]
        
        try:
            # Insert the batch
            response = supabase.table(table_name).insert(batch_records).execute()
            
            # Count successful insertions
            success_count += len(response.data) if response.data else 0
            
        except Exception as e:
            st.error(f"Error inserting batch {i//batch_size + 1}: {str(e)}")
            failed_count += len(batch_records)
    
    return {
        "success": success_count,
        "failed": failed_count
    }

def bulk_payment_status_update(bill_ids: List[str], new_status: str, 
                             paid_date: str = None, paid_amount: float = None) -> Dict[str, int]:
    """
    Bulk update payment status for bills.
    
    Args:
        bill_ids (List[str]): List of bill PSIDs to update
        new_status (str): New payment status (PAID/UNPAID/ARREARS)
        paid_date (str, optional): Date when payment was made
        paid_amount (float, optional): Amount paid
        
    Returns:
        Dict[str, int]: Results with 'success' and 'failed' counts
    """
    # Prepare updates
    updates = {"payment_status": new_status}
    
    if paid_date:
        updates["paid_date"] = paid_date
    
    if paid_amount is not None:
        updates["paid_amount"] = paid_amount
    
    # Perform bulk update
    return bulk_update_records("bills", bill_ids, "psid", updates)

def bulk_consumer_status_update(consumer_ids: List[str], is_active: bool) -> Dict[str, int]:
    """
    Bulk update consumer active status.
    
    Args:
        consumer_ids (List[str]): List of consumer survey IDs to update
        is_active (bool): New active status
        
    Returns:
        Dict[str, int]: Results with 'success' and 'failed' counts
    """
    updates = {"is_active_portal": is_active}
    return bulk_update_records("survey_units", consumer_ids, "survey_id", updates)

def validate_bulk_operation(table_name: str, operation: str, records: List[Dict[str, Any]]) -> List[str]:
    """
    Validate records before bulk operation.
    
    Args:
        table_name (str): Name of the table
        operation (str): Type of operation (insert/update/delete)
        records (List[Dict[str, Any]]): Records to validate
        
    Returns:
        List[str]: List of validation errors
    """
    errors = []
    
    # Basic validation
    if not records:
        errors.append("No records provided for bulk operation")
        return errors
    
    # Table-specific validation
    if table_name == "bills":
        required_fields = ["psid", "bill_month"] if operation == "insert" else ["psid"]
        for i, record in enumerate(records):
            for field in required_fields:
                if field not in record or not record[field]:
                    errors.append(f"Record {i+1}: Missing required field '{field}'")
    
    elif table_name == "survey_units":
        required_fields = ["survey_id"] if operation == "update" else ["survey_id", "city_district", "uc_name"]
        for i, record in enumerate(records):
            for field in required_fields:
                if field not in record or not record[field]:
                    errors.append(f"Record {i+1}: Missing required field '{field}'")
    
    elif table_name == "staff":
        required_fields = ["username"] if operation == "update" else ["username", "full_name", "role"]
        for i, record in enumerate(records):
            for field in required_fields:
                if field not in record or not record[field]:
                    errors.append(f"Record {i+1}: Missing required field '{field}'")
    
    return errors

def get_bulk_operation_progress(total_records: int, processed_records: int) -> str:
    """
    Get formatted progress string for bulk operations.
    
    Args:
        total_records (int): Total number of records
        processed_records (int): Number of processed records
        
    Returns:
        str: Formatted progress string
    """
    if total_records == 0:
        return "0/0 (0%)"
    
    percentage = (processed_records / total_records) * 100
    return f"{processed_records}/{total_records} ({percentage:.1f}%)"