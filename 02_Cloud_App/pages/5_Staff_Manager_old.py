# pages/5_Staff_Manager.py
import streamlit as st
import pandas as pd
from pydantic import ValidationError
from components.auth import enforce_auth
from components.db import supabase
from components.forms import StaffModel
from components.ui import confirmation_modal # This import will now work
from utils.security import hash_password  # Import password hashing function

enforce_auth(head_admin_only=True)

st.title("👥 Staff Account Management")

# --- Fetch and Display Staff ---
staff_res = supabase.table('staff').select('*').order('id').execute()
df_staff = pd.DataFrame(staff_res.data)
selection = st.dataframe(df_staff.drop(columns=['password']), on_select='rerun', selection_mode='single-row', use_container_width=True)

# --- Tabs for Create/Edit/Delete ---
tab_create, tab_edit = st.tabs(["➕ Create New Staff", "✍️ Edit / Delete Selected"])

with tab_create:
    with st.form("new_staff_form"):
        st.subheader("New Staff Details")
        new_user = {
            "username": st.text_input("Username"),
            "password": st.text_input("Password", type="password"),
            "full_name": st.text_input("Full Name"),
            "role": st.selectbox("Role", ["AGENT", "SUPERVISOR", "MANAGER", "HEAD"]),
            "assigned_city": st.text_input("Assigned City"),
            "is_active": st.checkbox("Is Active", value=True)
            # assigned_ucs can be added here if needed
        }
        submitted = st.form_submit_button("Create Staff Member")

    if submitted:
        try:
            # Validate data using the Pydantic model
            StaffModel(**new_user)
            # Hash the password before storing
            if new_user["password"]:
                new_user["password"] = hash_password(new_user["password"])
            supabase.table('staff').insert(new_user).execute()
            st.success("Staff member created successfully!"); st.rerun()
        except ValidationError as e:
            st.error(f"Form validation error: {e.errors()}")
        except Exception as e:
            st.error(f"Error creating user: {e}")

with tab_edit:
    if not selection.selection['rows']:
        st.info("Select a staff member from the table above to edit or delete.")
    else:
        selected_index = selection.selection['rows'][0]
        user_data = df_staff.iloc[selected_index].to_dict()
        
        with st.form(f"edit_form_{user_data['id']}"):
            st.subheader(f"Editing: {user_data['full_name']}")
            
            # Pre-populate form with existing data
            edited_user = {
                "full_name": st.text_input("Full Name", value=user_data.get('full_name', '')),
                "role": st.selectbox("Role", ["AGENT", "SUPERVISOR", "MANAGER", "HEAD"], index=["AGENT", "SUPERVISOR", "MANAGER", "HEAD"].index(user_data.get('role', 'AGENT'))),
                "assigned_city": st.text_input("Assigned City", value=user_data.get('assigned_city', '')),
                "password": st.text_input("New Password (leave blank to keep unchanged)", type="password"),
                "is_active": st.checkbox("Is Active", value=user_data.get('is_active', True))
            }
            
            submitted = st.form_submit_button("Update User")

        if submitted:
            # Prepare payload, removing empty password
            update_payload = edited_user.copy()
            if not update_payload['password']:
                del update_payload['password']
            else:
                # Hash the new password before storing
                update_payload['password'] = hash_password(update_payload['password'])
            
            try:
                supabase.table('staff').update(update_payload).eq('id', user_data['id']).execute()
                st.success("User updated!"); st.rerun()
            except Exception as e:
                st.error(f"Error updating user: {e}")

        st.markdown("---")
        st.subheader("Delete User")
        delete_modal = confirmation_modal("Confirm Deletion", f"delete_modal_{user_data['id']}")
        if st.button("Delete This User", type="primary"):
            delete_modal.open()
            
        if delete_modal.is_open():
            with delete_modal.container():
                st.write(f"Are you sure you want to delete **{user_data['full_name']}**? This action cannot be undone.")
                if st.button("Confirm & Delete Permanently"):
                    supabase.table('staff').delete().eq('id', user_data['id']).execute()
                    st.warning("User deleted."); st.rerun()