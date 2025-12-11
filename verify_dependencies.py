#!/usr/bin/env python3
"""
Dependency Verification Script
Checks if all required packages are installed and importable
"""

import sys
from typing import List, Tuple

def check_import(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """
    Try to import a package and return status
    
    Args:
        package_name: Display name of the package
        import_name: Actual import name (if different from package_name)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True, f"✅ {package_name}"
    except ImportError as e:
        return False, f"❌ {package_name}: {str(e)}"

def main():
    """Main verification function"""
    print("=" * 70)
    print("BILLING SYSTEM - DEPENDENCY VERIFICATION")
    print("=" * 70)
    print()
    
    # Define packages to check
    cloud_app_packages = [
        ("Streamlit", "streamlit"),
        ("Supabase", "supabase"),
        ("Python-dotenv", "dotenv"),
        ("Pandas", "pandas"),
        ("Plotly", "plotly"),
        ("Streamlit-aggrid", "st_aggrid"),
        ("Streamlit-modal", "streamlit_modal"),
        ("Streamlit-image-select", "streamlit_image_select"),
        ("Watchdog", "watchdog"),
        ("Pydantic-settings", "pydantic_settings"),
    ]
    
    local_engine_packages = [
        ("Requests", "requests"),
        ("Pandas", "pandas"),
        ("NumPy", "numpy"),
        ("Supabase", "supabase"),
        ("Python-dotenv", "dotenv"),
        ("Tqdm", "tqdm"),
        ("OpenPyXL", "openpyxl"),
    ]
    
    all_success = True
    
    # Check Cloud App dependencies
    print("📦 CLOUD APP DEPENDENCIES (02_Cloud_App)")
    print("-" * 70)
    for display_name, import_name in cloud_app_packages:
        success, message = check_import(display_name, import_name)
        print(message)
        if not success:
            all_success = False
    
    print()
    
    # Check Local Engine dependencies
    print("🔧 LOCAL ENGINE DEPENDENCIES (01_Local_Engine)")
    print("-" * 70)
    checked_local = set()
    for display_name, import_name in local_engine_packages:
        # Avoid duplicate checks
        if import_name not in checked_local:
            success, message = check_import(display_name, import_name)
            print(message)
            checked_local.add(import_name)
            if not success:
                all_success = False
    
    print()
    print("=" * 70)
    
    if all_success:
        print("🎉 SUCCESS! All dependencies are installed and importable.")
        print()
        print("Next steps:")
        print("  • Run Cloud App: streamlit run 02_Cloud_App\\Home.py")
        print("  • Run Bill Extractor: py 01_Local_Engine\\scripts\\bill-extractor-v4.py")
        print("  • Run DB Uploader: py 01_Local_Engine\\scripts\\db-uploader.py")
        return 0
    else:
        print("⚠️  ERRORS DETECTED! Some dependencies are missing.")
        print("Please install missing packages using pip.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
