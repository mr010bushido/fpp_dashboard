# ⚽ Football Analysis Streamlit Dashboard

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25%2B-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Choose your license -->

A Streamlit web application designed for pre-match football analysis using weekly prediction data, with plans for historical results analysis.

<!-- Optional: Add a nice screenshot or GIF here! -->
<!-- ![App Screenshot](link/to/your/screenshot.png) -->

---

## ✨ Features

*   **Multi-Page Interface:** Separate sections for different types of analysis (currently Pre-Match).
*   **Weekly Pre-Match Analysis:**
    *   Select specific weeks (based on numeric file names, e.g., `43.csv`).
    *   View matches scheduled for the selected week, sorted chronologically.
    *   Filter matches by:
        *   Date (within the selected week)
        *   Country
        *   League
        *   Recommended Bet type
        *   Value Bet type (H/X/A)
        *   Confidence Score range
    *   Overview display grouping matches by league with country flags and team logos.
    *   Detailed match view (when clicking "View Details").
*   **Visualizations:**
    *   Bar charts displaying key metrics (e.g., Avg Goals, Bet Distribution) with value labels.
*   **(Planned) Customizable Theme:** Supports Streamlit's theming via `.streamlit/config.toml`.
*   **(Planned) Results Analysis:** Future section for analyzing historical predictions against actual results using a combined dataset.

---

## 🛠️ Technology Stack

*   **Language:** Python 3.9+
*   **Web Framework:** [Streamlit](https://streamlit.io/)
*   **Data Handling:** [Pandas](https://pandas.pydata.org/)
*   **Visualization:** [Altair](https://altair-viz.github.io/)
*   **File Handling:** `glob`, `os`, `re`

---

## ⚙️ Setup and Installation

Follow these steps to get the application running locally:

1.  **Prerequisites:**
    *   Python 3.9 or higher installed.
    *   `pip` (Python package installer).

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/[YOUR_USERNAME]/[YOUR_REPONAME].git
    cd [YOUR_REPONAME]
    ```

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    *   Make sure you have a `requirements.txt` file in the root directory listing all necessary packages. If not, create one:
        ```
        pip freeze > requirements.txt
        ```
        *(Do this after installing the packages below if you don't have the file yet)*
    *   Install the packages:
        ```bash
        pip install -r requirements.txt
        ```
        *Likely contents of `requirements.txt`:*
        ```txt
        streamlit
        pandas
        altair
        # Add any other specific libraries you use
        ```

---

## 🔧 Configuration

1.  **Data Paths:**
    *   The application expects weekly prediction data files in a specific directory.
    *   Update the `WEEKLY_PREDICTIONS_DIR` variable in `pages/1_📅_Pre_Match_Analysis.py` to point to the correct location relative to the project root where you run the app.
    *   *(Future)* Update `COMBINED_RESULTS_FILE` when implementing the results analysis section.

2.  **Weekly File Naming:**
    *   The Pre-Match analysis currently expects weekly files named numerically (e.g., `42.csv`, `43.csv`, `44.csv`) inside the `WEEKLY_PREDICTIONS_DIR`.

3.  **Theme (Optional):**
    *   To customize the visual theme (colors, fonts), create a `.streamlit` directory in the project root.
    *   Inside `.streamlit`, create a `config.toml` file. See the [Streamlit Theming Documentation](https://docs.streamlit.io/library/advanced-features/theming) for options.
    *   Example `config.toml`:
        ```toml
        [theme]
        primaryColor="#f63366"
        backgroundColor="#ffffff"
        secondaryBackgroundColor="#f0f2f6"
        textColor="#262730"
        font="sans serif"
        ```
    *   Restart the Streamlit app after modifying `config.toml`.

---

## ▶️ Running the App

1.  Make sure you are in the project's root directory in your terminal.
2.  Ensure your virtual environment is activated.
3.  Run the Streamlit application:
    ```bash
    streamlit run pages/0_🏠_Home.py
    ```
    *(Streamlit usually figures out the entry point automatically if `0_🏠_Home.py` is the first file alphabetically in `pages/`, but specifying it is explicit.)*

4.  The application should open in your default web browser.

---

## 🖱️ Usage

1.  **Navigation:** Use the sidebar menu to switch between application sections ("Home", "Pre-Match Analysis", etc.).
2.  **Pre-Match Analysis:**
    *   Select the desired **Prediction Week** from the first dropdown in the sidebar.
    *   The main view will load the matches for that week.
    *   Use the other filters in the sidebar (Date, Country, League, Bets, Confidence) to narrow down the match list.
    *   Click the **"Reset Filters"** button (top-right of the main view) to return all filters to their default state for the selected week.
    *   Click **"View Details"** on a specific match row to see more in-depth analysis for that fixture (if implemented).
    *   Click **"⬅️ Back to Overview"** in the sidebar when in the detail view to return to the match list.

---

## 💾 Data Structure

*   **Weekly Pre-Match Data:** Stored as individual `.csv` files named by week number (e.g., `43.csv`) in the directory specified by `WEEKLY_PREDICTIONS_DIR`. Each file contains match predictions and relevant stats for that specific week. Key columns likely include `match_id`, `date`, `time`, `country`, `league_name`, `home_team`, `away_team`, `rec_prediction`, `value_bets`, `confidence_score`, team logos, country flags, etc.
*   **(Planned) Combined Results Data:** A single `.csv` file intended to store historical predictions alongside actual match results for performance tracking.

---

## 🚀 Future Enhancements (Example)

*   Implement the **Results Analysis** page.
*   Add more detailed visualizations in the match detail view.
*   Implement **database integration** (SQLite or PostgreSQL) to improve performance and scalability, especially for results analysis.
*   Add user accounts or saving preferences.
*   Deploy the application (e.g., using Streamlit Community Cloud, Heroku, Docker).

---

## 🤝 Contributing (Optional)

Contributions are welcome! If you'd like to contribute, please fork the repository and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. *(Make sure you add a LICENSE file to your repo if you choose one!)*

---
