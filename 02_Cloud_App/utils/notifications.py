"""
Notification system for the billing system.
Provides in-app notifications and activity tracking.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from services.db import supabase

# Notification types
NOTIFICATION_TYPES = {
    "info": "ℹ️",
    "success": "✅",
    "warning": "⚠️",
    "error": "❌"
}

def create_notification(user_id: int, message: str, notification_type: str = "info", 
                       related_entity: str = None, entity_id: str = None) -> bool:
    """
    Create a new notification for a user.
    
    Args:
        user_id (int): ID of the user to notify
        message (str): Notification message
        notification_type (str): Type of notification (info, success, warning, error)
        related_entity (str): Type of entity related to notification (bill, consumer, etc.)
        entity_id (str): ID of the related entity
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        notification_data = {
            "user_id": user_id,
            "message": message,
            "type": notification_type,
            "related_entity": related_entity,
            "entity_id": entity_id,
            "is_read": False,
            "created_at": datetime.now().isoformat()
        }
        
        response = supabase.table("notifications").insert(notification_data).execute()
        return True if response.data else False
        
    except Exception as e:
        # Silently fail if notifications table doesn't exist to prevent errors
        # st.error(f"Error creating notification: {str(e)}")
        return False

def get_user_notifications(user_id: int, limit: int = 50, unread_only: bool = False) -> List[Dict]:
    """
    Get notifications for a user.
    
    Args:
        user_id (int): ID of the user
        limit (int): Maximum number of notifications to return
        unread_only (bool): Whether to return only unread notifications
        
    Returns:
        List[Dict]: List of notifications
    """
    try:
        query = supabase.table("notifications").select("*").eq("user_id", user_id)
        
        if unread_only:
            query = query.eq("is_read", False)
            
        query = query.order("created_at", desc=True).limit(limit)
        
        response = query.execute()
        return response.data if response.data else []
        
    except Exception as e:
        # Silently fail if notifications table doesn't exist
        # st.error(f"Error fetching notifications: {str(e)}")
        return []

def mark_notification_as_read(notification_id: int) -> bool:
    """
    Mark a notification as read.
    
    Args:
        notification_id (int): ID of the notification
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
        return True if response.data else False
        
    except Exception as e:
        # Silently fail if notifications table doesn't exist
        # st.error(f"Error marking notification as read: {str(e)}")
        return False

def mark_all_notifications_as_read(user_id: int) -> bool:
    """
    Mark all notifications for a user as read.
    
    Args:
        user_id (int): ID of the user
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = supabase.table("notifications").update({"is_read": True}).eq("user_id", user_id).execute()
        return True if response.data else False
        
    except Exception as e:
        # Silently fail if notifications table doesn't exist
        # st.error(f"Error marking all notifications as read: {str(e)}")
        return False

def delete_notification(notification_id: int) -> bool:
    """
    Delete a notification.
    
    Args:
        notification_id (int): ID of the notification
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = supabase.table("notifications").delete().eq("id", notification_id).execute()
        return True if response.data else False
        
    except Exception as e:
        # Silently fail if notifications table doesn't exist
        # st.error(f"Error deleting notification: {str(e)}")
        return False

def get_unread_notification_count(user_id: int) -> int:
    """
    Get count of unread notifications for a user.
    
    Args:
        user_id (int): ID of the user
        
    Returns:
        int: Count of unread notifications
    """
    try:
        response = supabase.table("notifications").select("count", count="exact").eq("user_id", user_id).eq("is_read", False).execute()
        return response.count if hasattr(response, 'count') else len(response.data)
        
    except Exception as e:
        # Silently fail if notifications table doesn't exist to prevent errors
        # st.error(f"Error counting unread notifications: {str(e)}")
        return 0

def show_notification_banner(user_id: int):
    """
    Display a notification banner in the sidebar showing unread count.
    
    Args:
        user_id (int): ID of the current user
    """
    unread_count = get_unread_notification_count(user_id)
    
    if unread_count > 0:
        st.sidebar.markdown(f"""
        <div style="background-color: #ffeb3b; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <strong>🔔 {unread_count} unread notifications</strong>
        </div>
        """, unsafe_allow_html=True)

def display_notifications(user_id: int, limit: int = 10):
    """
    Display recent notifications in a compact format.
    
    Args:
        user_id (int): ID of the current user
        limit (int): Number of notifications to display
    """
    notifications = get_user_notifications(user_id, limit=limit)
    
    if not notifications:
        return
    
    for notification in notifications[:limit]:
        icon = NOTIFICATION_TYPES.get(notification['type'], "ℹ️")
        timestamp = pd.to_datetime(notification['created_at']).strftime("%Y-%m-%d %H:%M")
        
        bg_color = {
            "info": "#e3f2fd" if notification['is_read'] else "#bbdefb",
            "success": "#e8f5e9" if notification['is_read'] else "#c8e6c9",
            "warning": "#fff3e0" if notification['is_read'] else "#ffe0b2",
            "error": "#ffebee" if notification['is_read'] else "#ffcdd2"
        }.get(notification['type'], "#f5f5f5")
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span><strong>{icon}</strong> {notification['message']}</span>
                <span style="font-size: 0.8em; color: #666;">{timestamp}</span>
            </div>
            {f"<div style='font-size: 0.8em; color: #666; margin-top: 5px;'>Related to: {notification['related_entity']} #{notification['entity_id']}</div>" if notification['related_entity'] else ""}
        </div>
        """, unsafe_allow_html=True)
        
        # Mark as read when viewed
        if not notification['is_read']:
            mark_notification_as_read(notification['id'])

def create_system_notification(message: str, notification_type: str = "info", 
                             related_entity: str = None, entity_id: str = None) -> bool:
    """
    Create a system-wide notification for all users.
    
    Args:
        message (str): Notification message
        notification_type (str): Type of notification
        related_entity (str): Type of entity related to notification
        entity_id (str): ID of the related entity
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get all active users
        users_response = supabase.table("staff").select("id").eq("is_active", True).execute()
        user_ids = [user['id'] for user in users_response.data] if users_response.data else []
        
        # Create notification for each user
        success_count = 0
        for user_id in user_ids:
            if create_notification(user_id, message, notification_type, related_entity, entity_id):
                success_count += 1
        
        return success_count == len(user_ids)
        
    except Exception as e:
        # Silently fail if notifications table doesn't exist
        # st.error(f"Error creating system notification: {str(e)}")
        return False

def create_bill_notification(bill_psid: str, action: str, user_id: int = None):
    """
    Create a notification related to a bill action.
    
    Args:
        bill_psid (str): PSID of the bill
        action (str): Action performed (created, updated, paid, etc.)
        user_id (int): ID of user to notify (if None, notifies relevant users)
    """
    message = f"Bill {bill_psid} has been {action}"
    
    if user_id:
        # Notify specific user
        create_notification(user_id, message, "info", "bill", bill_psid)