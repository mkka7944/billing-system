#!/usr/bin/env python3
"""
Script to update consumer type classification in existing CSV/Excel files
based on the simplified logic:
- If House Type field is empty -> Commercial
- If House Type field contains any value -> Domestic
"""

import pandas as pd
import os
import glob
from pathlib import Path
import openpyxl

# Define the input/output folder
INPUT_FOLDER = os.path.join("..", "outputs", "scraped_data")
OUTPUT_FOLDER = os.path.join("..", "outputs", "scraped_data_updated")

def update_consumer_type_logic(row):
    """
    Apply the simplified consumer type logic:
    - If House Type field is empty -> Commercial
    - If House Type field contains any value -> Domestic
    """
    house_type = str(row.get('House Type', '')).strip()
    
    if house_type == '' or house_type.lower() == 'nan' or house_type.lower() == 'none':
        return 'Commercial'
    else:
        return 'Domestic'

def process_file(file_path):
    """Process a single CSV or Excel file and update consumer types"""
    print(f"Processing {file_path}...")
    
    # Read the file
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            print(f"Unsupported file format: {file_path}")
            return
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return
    
    # Check if required columns exist
    if 'House Type' not in df.columns:
        print(f"'House Type' column not found in {file_path}")
        return
    
    # Apply the new consumer type logic
    df['Consumer Type'] = df.apply(update_consumer_type_logic, axis=1)
    
    # Save the updated file
    output_path = file_path.replace(INPUT_FOLDER, OUTPUT_FOLDER)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        if file_path.endswith('.csv'):
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
        elif file_path.endswith('.xlsx'):
            df.to_excel(output_path, index=False, engine='openpyxl')
        
        print(f"Saved updated file to {output_path}")
        print(f"  - Total records: {len(df)}")
        commercial_count = len(df[df['Consumer Type'] == 'Commercial'])
        domestic_count = len(df[df['Consumer Type'] == 'Domestic'])
        print(f"  - Commercial: {commercial_count}")
        print(f"  - Domestic: {domestic_count}")
        print()
    except Exception as e:
        print(f"Error saving {output_path}: {e}")

def main():
    print("==============================================")
    print("  Consumer Type Updater Script")
    print("==============================================\n")
    
    # Create output folder
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Find all CSV and Excel files in the input folder
    csv_files = glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))
    excel_files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx"))
    
    print(f"Found {len(csv_files)} CSV files and {len(excel_files)} Excel files\n")
    
    # Process all files
    all_files = csv_files + excel_files
    processed_files = 0
    
    for file_path in all_files:
        try:
            process_file(file_path)
            processed_files += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print("==============================================")
    print(f"  Processing Complete! {processed_files} files processed.")
    print(f"  Updated files saved to: {OUTPUT_FOLDER}")
    print("==============================================")

if __name__ == "__main__":
    main()