# app.py (Main Application File)
import streamlit as st

# Set page configuration - this should ideally be done only once
st.set_page_config(
    page_title="Football Analysis Hub",
    layout="wide",
    initial_sidebar_state="expanded" # Keep sidebar open initially
)

# --- Main Landing Page Content (Optional) ---
st.title("⚽ Welcome to the Football Analysis Hub")
st.markdown("""
Select an analysis section from the sidebar to get started.

*   **Match Analysis:** View upcoming matches, predictions, and stats based on weekly data.
*   **Results Analysis:** (Coming Soon) Analyze historical performance and trends.
""")

st.sidebar.success("Select an analysis page above.")

# --- Add any other truly global setup here if needed ---
# For example, loading a theme or global configurations.
# Avoid putting page-specific logic here.