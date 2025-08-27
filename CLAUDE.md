# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a Streamlit-based football prediction dashboard that analyzes weekly football match data and provides pre-match predictions. The application uses a multi-page structure with navigation through Streamlit's sidebar.

## Development Commands

### Running the Application
```bash
streamlit run 0_Home.py
```

### Package Management
The project uses `uv` as the package manager:
```bash
# Install dependencies
uv pip install -r requirements.txt

# Add new dependencies
uv add package_name
```

### Alternative with pip
```bash
pip install -r requirements.txt
```

## Project Structure

### Core Architecture
- **Entry Point**: `0_Home.py` - Main landing page with application overview
- **Pages**: Multi-page Streamlit app with pages in `/pages/` directory
  - `1_Match_Analysis.py` - Pre-match analysis (main functionality, ~3000 lines)
  - `2_Results_Analysis.py` - Historical results analysis (placeholder)
- **Data**: CSV files stored in `/data/pre_match/` with weekly prediction data (numbered files: 17.csv, 18.csv, etc.)

### Data Architecture
- **Weekly Data Files**: Located in `data/pre_match/` as numbered CSV files (e.g., `34.csv`, `35.csv`)
- **Data Loading**: Uses `@st.cache_data` decorator for performance optimization
- **Multiple Data Sources**: Supports CSV files, PostgreSQL, and text file formats
- **Country/League Mapping**: Extensive country code mapping for flags and team logos via CDN

### Key Configuration (pages/1_Match_Analysis.py)
- `WEEKLY_PREDICTIONS_DIR`: Points to `data/pre_match/` 
- `COMBINED_RESULTS_FILE`: For historical analysis (future feature)
- `DATA_SOURCE`: Configurable between "csv", "postgres", "text"

### Data Loading Functions
- `load_weekly_data()`: Main function for loading weekly CSV files
- `load_data_from_csv()`: Cached CSV loader
- `load_data_from_postgres()`: Database integration (optional)
- `load_data_from_text()`: Text file support

## Key Features

### Multi-Page Navigation
The app uses Streamlit's native page system. Each page has its own `st.set_page_config()` call with consistent icons and layout.

### Data Filtering System
Complex filtering system in Match Analysis page:
- Week selection
- Date filtering
- Country/League filters  
- Bet type filters (recommended, value bets)
- Confidence score ranges

### Caching Strategy
Heavy use of `@st.cache_data` decorators for performance, especially for data loading functions.

### Media Integration
Uses CDN for team logos and country flags: `https://fpp-dashboard-media.b-cdn.net/`

## Development Notes

### File Naming Convention
- Main pages: `0_Home.py`, `pages/1_Match_Analysis.py`, `pages/2_Results_Analysis.py`
- Data files: Numeric naming (e.g., `34.csv` for week 34)

### Code Style
- Heavy use of Streamlit components and layout
- Pandas for data manipulation
- Altair for visualizations
- Path objects for file handling

### Current Status
- Pre-match analysis is fully implemented
- Results analysis is placeholder/stub
- PostgreSQL integration available but not required
- Main application logic concentrated in 1_Match_Analysis.py (~3000 lines)[byterover-mcp]

# important 
always use byterover-retrieve-knowledge tool to get the related context before any tasks 
always use byterover-store-knowledge to store all the critical informations after sucessful tasks