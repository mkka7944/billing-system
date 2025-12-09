import os

def create_structure():
    # Define the root name
    root = "."
    
    # Define the folder tree
    structure = {
        # ZONE 1: LOCAL ENGINE (The Factory) - Stays on your PC
        f"{root}/01_Local_Engine/inputs/raw_pdfs": "Put downloaded A4 PDFs here",
        f"{root}/01_Local_Engine/inputs/excel_dumps": "Put BillersList.xlsx here",
        f"{root}/01_Local_Engine/inputs/config_files": "Put areas_export.csv here",
        
        f"{root}/01_Local_Engine/outputs/processed_pdfs": "Output for A5 PDFs with QR codes",
        f"{root}/01_Local_Engine/outputs/scraped_data": "CSVs from Bill/Survey Extractor go here",
        f"{root}/01_Local_Engine/outputs/logs": "Error logs",
        
        f"{root}/01_Local_Engine/scripts": "Your Python .py files go here",
        
        # ZONE 2: CLOUD APP (The Storefront) - Uploads to GitHub/Streamlit
        f"{root}/02_Cloud_App/.streamlit": "Streamlit config",
        f"{root}/02_Cloud_App/pages": "Multi-page app screens (Admin, Field Staff)",
        f"{root}/02_Cloud_App/assets": "Logos and static icons",
    }

    print(f"🚀 Initializing Project Structure for {root}...\n")

    for folder, description in structure.items():
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"✅ Created: {folder}")
            # Create a tiny Readme in each to explain usage
            with open(os.path.join(folder, ".placeholder"), "w") as f:
                f.write(f"USAGE: {description}")
        except Exception as e:
            print(f"❌ Error creating {folder}: {e}")

    # Create empty essential files
    open(f"{root}/01_Local_Engine/scripts/config.py", "a").close()
    open(f"{root}/02_Cloud_App/app.py", "a").close()
    open(f"{root}/requirements.txt", "a").close()
    
    print("\n🎉 Structure Ready! Move your existing scripts into '01_Local_Engine/scripts'.")

if __name__ == "__main__":
    create_structure()