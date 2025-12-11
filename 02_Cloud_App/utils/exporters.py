"""
Export utilities for the billing system.
Provides functions to export data to CSV and Excel formats.
"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime
from typing import Optional

def export_to_csv(df: pd.DataFrame, filename: Optional[str] = None) -> bytes:
    """
    Export a DataFrame to CSV format.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        filename (str, optional): Filename for the export
        
    Returns:
        bytes: CSV data as bytes
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.csv"
    
    # Convert DataFrame to CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_data = csv_buffer.getvalue()
    
    return csv_data.encode('utf-8-sig')

def export_to_excel(df: pd.DataFrame, filename: Optional[str] = None, 
                   sheet_name: str = "Data") -> bytes:
    """
    Export a DataFrame to Excel format.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        filename (str, optional): Filename for the export
        sheet_name (str): Name of the Excel sheet
        
    Returns:
        bytes: Excel data as bytes
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.xlsx"
    
    # Convert DataFrame to Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    excel_data = excel_buffer.getvalue()
    
    return excel_data

def download_button_csv(df: pd.DataFrame, filename: Optional[str] = None, 
                       button_text: str = "Download CSV"):
    """
    Create a Streamlit download button for CSV data.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        filename (str, optional): Filename for the export
        button_text (str): Text for the download button
    """
    if df.empty:
        st.warning("No data to export.")
        return
    
    csv_data = export_to_csv(df, filename)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.csv"
    
    st.download_button(
        label=button_text,
        data=csv_data,
        file_name=filename,
        mime="text/csv"
    )

def download_button_excel(df: pd.DataFrame, filename: Optional[str] = None, 
                         sheet_name: str = "Data", button_text: str = "Download Excel"):
    """
    Create a Streamlit download button for Excel data.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        filename (str, optional): Filename for the export
        sheet_name (str): Name of the Excel sheet
        button_text (str): Text for the download button
    """
    if df.empty:
        st.warning("No data to export.")
        return
    
    excel_data = export_to_excel(df, filename, sheet_name)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.xlsx"
    
    st.download_button(
        label=button_text,
        data=excel_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def export_bill_summary(bills_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary report of bills data.
    
    Args:
        bills_df (pd.DataFrame): Raw bills data
        
    Returns:
        pd.DataFrame: Summarized bill data
    """
    if bills_df.empty:
        return pd.DataFrame()
    
    # Group by payment status and calculate summary statistics
    summary = bills_df.groupby('payment_status').agg({
        'amount_due': ['count', 'sum', 'mean'],
        'paid_amount': 'sum'
    }).round(2)
    
    # Flatten column names
    summary.columns = ['_'.join(col).strip() for col in summary.columns]
    summary = summary.reset_index()
    
    # Add overall totals
    totals = pd.DataFrame([{
        'payment_status': 'TOTAL',
        'amount_due_count': bills_df['amount_due'].count(),
        'amount_due_sum': bills_df['amount_due'].sum(),
        'amount_due_mean': bills_df['amount_due'].mean(),
        'paid_amount_sum': bills_df['paid_amount'].sum() if 'paid_amount' in bills_df.columns else 0
    }])
    
    # Combine summary and totals
    result = pd.concat([summary, totals], ignore_index=True)
    
    return result

def export_consumer_summary(consumers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary report of consumer data.
    
    Args:
        consumers_df (pd.DataFrame): Raw consumer data
        
    Returns:
        pd.DataFrame: Summarized consumer data
    """
    if consumers_df.empty:
        return pd.DataFrame()
    
    # Create summary by city/district
    if 'city_district' in consumers_df.columns:
        summary = consumers_df.groupby('city_district').agg({
            'survey_id': 'count',
            'is_active_portal': lambda x: sum(x == True)
        }).reset_index()
        
        summary.columns = ['City/District', 'Total Consumers', 'Active Consumers']
        summary['Inactive Consumers'] = summary['Total Consumers'] - summary['Active Consumers']
        
        return summary
    
    return pd.DataFrame()