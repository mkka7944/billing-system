#!/usr/bin/env python3
"""
Script to combine Latitude and Longitude columns into a single Location column
formatted as "latitude,longitude" for AppSheet support.
"""

import pandas as pd
import os
import glob

# Define input and output folders
INPUT_FOLDER = os.path.join("..", "outputs", "scraped_data")
OUTPUT_FOLDER = os.path.join("..", "outputs", "scraped_data_appsheet")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def combine_location_columns_in_file(file_path):
    """
    Combine Latitude and Longitude columns into a single Location column
    """
    print(f"Processing {file_path}...")
    
    # Read the file
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        print(f"Unsupported file format: {file_path}")
        return
    
    # Check if required columns exist
    if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
        print(f"Warning: Latitude or Longitude column not found in {file_path}")
        # Save file as is
        output_path = file_path.replace(INPUT_FOLDER, OUTPUT_FOLDER)
        if file_path.endswith('.csv'):
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
        elif file_path.endswith('.xlsx'):
            df.to_excel(output_path, index=False)
        return
    
    # Create the Location column by combining Latitude and Longitude
    # Handle potential NaN values
    df['Location'] = df.apply(
        lambda row: f"{row['Latitude']},{row['Longitude']}" 
        if pd.notna(row['Latitude']) and pd.notna(row['Longitude']) 
        else "", 
        axis=1
    )
    
    # Move the Location column to be right after Longitude
    cols = list(df.columns)
    location_index = cols.index('Location')
    cols.pop(location_index)  # Remove Location from current position
    longitude_index = cols.index('Longitude')
    cols.insert(longitude_index + 1, 'Location')  # Insert after Longitude
    df = df[cols]
    
    # Save the updated file
    output_path = file_path.replace(INPUT_FOLDER, OUTPUT_FOLDER)
    
    try:
        if file_path.endswith('.csv'):
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
        elif file_path.endswith('.xlsx'):
            df.to_excel(output_path, index=False)
        
        print(f"Saved updated file to {output_path}")
        print(f"  - Total records: {len(df)}")
        print(f"  - Location column added with lat,long format")
        
    except Exception as e:
        print(f"Error saving {output_path}: {e}")

def main():
    print("==============================================")
    print("  Location Column Combiner for AppSheet")
    print("==============================================\n")
    
    # Find all CSV and Excel files in the input folder
    csv_files = glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))
    excel_files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx"))
    
    print(f"Found {len(csv_files)} CSV files and {len(excel_files)} Excel files\n")
    
    # Process all files
    all_files = csv_files + excel_files
    processed_files = 0
    
    for file_path in all_files:
        try:
            combine_location_columns_in_file(file_path)
            processed_files += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print("\n==============================================")
    print(f"  Processing Complete! {processed_files} files processed.")
    print(f"  Updated files saved to: {OUTPUT_FOLDER}")
    print("==============================================")

if __name__ == "__main__":
    main()