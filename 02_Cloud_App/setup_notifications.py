"""
Setup script to create the notifications table in Supabase.
"""
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import supabase

def setup_notifications_table():
    """
    Create the notifications table in Supabase.
    """
    try:
        print("Checking if notifications table exists...")
        
        # Try to access the notifications table
        response = supabase.table("notifications").select("count").limit(1).execute()
        
        print("Notifications table already exists!")
        return True
        
    except Exception as e:
        # If the table doesn't exist, we'll get an error
        print(f"Notifications table doesn't exist. You'll need to create it manually in Supabase dashboard.")
        print(f"Error: {e}")
        print("\nTo create the table, please run the following SQL in your Supabase SQL editor:")
        print("\n--- START SQL ---")
        with open("database/notifications_schema.sql", "r") as f:
            print(f.read())
        print("--- END SQL ---")
        return False

if __name__ == "__main__":
    print("Setting up notifications table...")
    if setup_notifications_table():
        print("Notifications table setup completed successfully!")
    else:
        print("Please create the notifications table manually using the SQL provided above.")
        sys.exit(1)