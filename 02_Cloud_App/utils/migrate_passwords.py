import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import supabase
from utils.security import hash_password

def migrate_passwords():
    """
    Migrate all plain-text passwords to hashed passwords.
    """
    try:
        # Get all staff members
        response = supabase.table("staff").select("id, username, password").execute()
        staff_members = response.data
        
        print(f"Found {len(staff_members)} staff members to migrate.")
        
        migrated_count = 0
        for staff in staff_members:
            # Skip if already hashed (check if password looks like a hash)
            if staff['password'] and (staff['password'].startswith('$2b$') or len(staff['password']) > 50):
                print(f"Skipping {staff['username']} - password already hashed")
                continue
                
            # Hash the plain text password
            if staff['password']:
                hashed_password = hash_password(staff['password'])
                
                # Update the database with the hashed password
                update_response = supabase.table("staff").update({
                    "password": hashed_password  # Store hashed password in the password field
                }).eq("id", staff['id']).execute()
                
                print(f"Migrated password for {staff['username']}")
                migrated_count += 1
            else:
                print(f"Skipping {staff['username']} - no password set")
        
        print(f"Successfully migrated {migrated_count} passwords.")
        
    except Exception as e:
        print(f"Error migrating passwords: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting password migration...")
    if migrate_passwords():
        print("Password migration completed successfully!")
    else:
        print("Password migration failed!")
        sys.exit(1)