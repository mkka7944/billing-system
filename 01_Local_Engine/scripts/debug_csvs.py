import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DATA = os.path.join(BASE_DIR, "..", "outputs", "scraped_data")
INPUTS_DATA = os.path.join(BASE_DIR, "..", "inputs", "survey_dumps")

def analyze_folder(folder_path, name):
    print(f"\n--- Analyzing {name} ({folder_path}) ---")
    if not os.path.exists(folder_path):
        print("Folder does not exist")
        return

    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    print(f"Found {len(csv_files)} CSVs")
    
    total_records = 0
    all_ids = set()
    
    for f in csv_files:
        is_survey = 'SURVEY' in f.upper()
        is_master = 'MASTER' in f.upper()
        
        # Simulate the filter
        wb_included = is_survey and not is_master and 'PAID' not in f.upper()
        
        path = os.path.join(folder_path, f)
        try:
            df = pd.read_csv(path, low_memory=False)
            count = len(df)
            print(f"- {f}: {count} rows. (Included by filter? {wb_included})")
            
            if wb_included:
                total_records += count
                if 'Survey ID' in df.columns:
                    ids = df['Survey ID'].dropna().astype(str).tolist()
                    all_ids.update(ids)
        except Exception as e:
            print(f"  Error reading {f}: {e}")

    print(f"Total 'Included' Records: {total_records}")
    print(f"Unique IDs in 'Included': {len(all_ids)}")

if __name__ == "__main__":
    analyze_folder(OUTPUTS_DATA, "OUTPUTS folder (Current Source)")
    # analyze_folder(INPUTS_DATA, "INPUTS folder (Alternative?)") # Check if this exists
