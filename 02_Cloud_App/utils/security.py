"""
Security utilities for the billing system.
Provides password hashing and validation functions.
"""
import bcrypt
import streamlit as st

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password (str): Plain text password
        hashed_password (str): Hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Convert to bytes
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # Check if password matches
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as e:
        st.error(f"Password verification error: {e}")
        return False

def is_password_secure(password: str) -> bool:
    """
    Check if a password meets security requirements.
    
    Args:
        password (str): Password to check
        
    Returns:
        bool: True if password is secure, False otherwise
    """
    # Minimum 8 characters
    if len(password) < 8:
        return False
    
    # Must contain at least one uppercase letter
    if not any(c.isupper() for c in password):
        return False
    
    # Must contain at least one lowercase letter
    if not any(c.islower() for c in password):
        return False
    
    # Must contain at least one digit
    if not any(c.isdigit() for c in password):
        return False
    
    # Must contain at least one special character
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False
    
    return True