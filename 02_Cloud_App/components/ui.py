# components/ui.py
import streamlit as st
from streamlit_modal import Modal

# This is the single, standardized function for creating a modal.
def confirmation_modal(title, key):
    """Creates and returns a reusable confirmation modal."""
    return Modal(
        title=title,
        key=key,
        padding=20,
        max_width=400
    )