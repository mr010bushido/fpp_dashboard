# app.py (Main Application File)
import streamlit as st

# Set page configuration - this should ideally be done only once
st.set_page_config(
    page_title="Football Analysis Hub",
    page_icon="⚽",  # Optional: Add a favicon
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help', # Replace with your help link
        'Report a bug': "https://www.example.com/bug", # Replace with your bug report link
        'About': "# This is a Football Analysis Dashboard!" # Can use markdown
    }
)

# --- Main Landing Page Content (Optional) ---
st.title("⚽ Welcome to the Football Analysis Hub ")
st.markdown("---")

st.header("About This Application")
st.markdown("""
This dashboard is designed to provide pre-match football analysis based on statistical data and predictive model.
Our goal is to offer insights that can help in understanding match dynamics, potential outcomes, and identifying value.

**Key Features:**
*   **Pre-Match Analysis:** Detailed breakdown of upcoming fixtures.
*   **Statistical Comparisons:** View team stats against league averages and head-to-head records.
*   **Data-Driven Predictions:** Access recommended bets and value opportunities.
*   **Interactive Filtering:** Narrow down matches by week, date, league, country, and various statistical thresholds.

*(Results Analysis section coming soon!)*
""")
st.markdown("---")

st.header("🚀 How to Use the Dashboard")

st.subheader("1. Navigate Using the Sidebar")
st.markdown("""
The sidebar on the left is your main navigation tool.
*   **Home:** You are here! This page provides an overview.
*   **📅 Pre-Match Analysis:** Click here to dive into upcoming match predictions and stats.
*   *(Other pages will appear here as they are added, like "📊 Results Analysis")*
""")

st.subheader("2. Using the Pre-Match Analysis Page")
st.markdown("""
Once you're on the **📅 Pre-Match Analysis** page:
1.  **Select Prediction Week:** Use the first dropdown in the sidebar to choose the week you want to analyze (e.g., "Week 42"). The dashboard will load matches for that week.
2.  **Apply Filters:** Use the subsequent filters in the sidebar to refine the list of matches:
    *   **Filter by Date:** Select a specific date within the chosen week, or leave as "All Dates".
    *   **Country & League:** Narrow down to specific competitions.
    *   **Recommended Bet & Value Bet:** Filter by prediction types.
    *   **Confidence Score Range:** Adjust the slider to see matches within a certain confidence level.
3.  **View Match Overview:** The main area will display a list of matches fitting your criteria, grouped by league. You'll see team names, logos, kick-off times, and key predictions.
4.  **Reset Filters:** If you want to clear all active filters (except the selected week), click the "Reset Filters" button at the top-right of the match overview.
5.  **View Match Details:** For any match in the list, click the **"View Details"** button on the right. This will take you to a dedicated screen with:
    *   In-depth statistical comparisons (team vs. league average).
    *   Head-to-Head (H2H) statistics.
    *   Graphical representations of goal expectancies (Actual vs. Expected).
    *   A full match report (expandable) with various in-game stats.
6.  **Return to Overview:** When in the detail view, click the **"⬅️ Back to Overview"** button in the sidebar to return to the match list.
""")
st.markdown("---")

st.header("💡 Tips for Best Experience")
st.markdown("""
*   **Allow Data to Load:** After selecting a new week, give the app a moment to load and process the data.
*   **Use Filters Incrementally:** Start with broader filters (like week and country) and then narrow down further.
*   **Check Back Regularly:** Prediction data is updated periodically (e.g., weekly).
""")
st.markdown("---")

st.caption("We hope you find this tool insightful! For feedback or issues, please use the links in the app menu (☰) -> 'Report a bug'.")

# Optional: Add a link to your GitHub repository if it's public
# st.sidebar.markdown("---")
# st.sidebar.markdown("⭐ [View on GitHub](https://github.com/[YOUR_USERNAME]/[YOUR_REPONAME])")

# st.markdown("""
# Select an analysis section from the sidebar to get started.

# *   **Match Analysis:** View upcoming matches, predictions, and stats based on weekly data.
# *   **Results Analysis:** (Coming Soon) Analyze historical performance and trends.
# """)

# st.sidebar.success("Select an analysis page above.")

# --- Add any other truly global setup here if needed ---
# For example, loading a theme or global configurations.
# Avoid putting page-specific logic here.