import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io
from collections import defaultdict # For grouping by league
# import psycopg2 # Optional
# from psycopg2 import sql # Optional
import altair as alt # Keep altair import
import emoji
import os
import time # Needed for timestamps
import traceback # For detailed error logging
import numpy as np # For NaN handling
import glob # For finding weekly files

# --- Configuration ---
# Change this to 'csv', 'postgres', or 'text' to simulate different sources
WEEKLY_PREDICTIONS_DIR = "data/pre_match/"
COMBINED_RESULTS_FILE = "data/combined_results.csv"

DATA_SOURCE = 'csv'
# Placeholder for DB connection (replace with actuals if using postgres)
DB_PARAMS = {
    "dbname": "football_db",
    "user": "user",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}
TEXT_FILE_PATH = "Confidence-7.txt"
CSV_FILE_PATH = "dashboard/dashboard_data.csv" # Path for saving/loading simulated CSV

# Map country names (as they appear in your data) to their flag codes
COUNTRY_CODE_MAP = {
    
'UEFA Champions League':"https://media.api-sports.io/football/leagues/2.png",
'UEFA Europa Conference League': "https://media.api-sports.io/football/leagues/848.png" ,
'UEFA Europa League': "https://media.api-sports.io/football/leagues/3.png",
'World': "https://media.api-sports.io/football/leagues/17.png",
'Albania': 'https://media.api-sports.io/flags/al.svg',
'Algeria': 'https://media.api-sports.io/flags/dz.svg',
'Andorra': 'https://media.api-sports.io/flags/ad.svg',
'Angola': 'https://media.api-sports.io/flags/ao.svg',
'Antigua-And-Barbuda': 'https://media.api-sports.io/flags/ag.svg',
'Argentina': 'https://media.api-sports.io/flags/ar.svg',
'Armenia': 'https://media.api-sports.io/flags/am.svg',
'Aruba': 'https://media.api-sports.io/flags/aw.svg',
'Australia': 'https://media.api-sports.io/flags/au.svg',
'Austria': 'https://media.api-sports.io/flags/at.svg',
'Azerbaijan': 'https://media.api-sports.io/flags/az.svg',
'Bahrain': 'https://media.api-sports.io/flags/bh.svg',
'Bangladesh': 'https://media.api-sports.io/flags/bd.svg',
'Barbados': 'https://media.api-sports.io/flags/bb.svg',
'Belarus': 'https://media.api-sports.io/flags/by.svg',
'Belgium': 'https://media.api-sports.io/flags/be.svg',
'Belize': 'https://media.api-sports.io/flags/bz.svg',
'Benin': 'https://media.api-sports.io/flags/bj.svg',
'Bermuda': 'https://media.api-sports.io/flags/bm.svg',
'Bhutan': 'https://media.api-sports.io/flags/bt.svg',
'Bolivia': 'https://media.api-sports.io/flags/bo.svg',
'Bosnia': 'https://media.api-sports.io/flags/ba.svg',
'Botswana': 'https://media.api-sports.io/flags/bw.svg',
'Brazil': 'https://media.api-sports.io/flags/br.svg',
'Bulgaria': 'https://media.api-sports.io/flags/bg.svg',
'Burkina-Faso': 'https://media.api-sports.io/flags/bf.svg',
'Burundi': 'https://media.api-sports.io/flags/bi.svg',
'Cambodia': 'https://media.api-sports.io/flags/kh.svg',
'Cameroon': 'https://media.api-sports.io/flags/cm.svg',
'Canada': 'https://media.api-sports.io/flags/ca.svg',
'Chile': 'https://media.api-sports.io/flags/cl.svg',
'China': 'https://media.api-sports.io/flags/cn.svg',
'Chinese-Taipei': 'https://media.api-sports.io/flags/tw.svg',
'Colombia': 'https://media.api-sports.io/flags/co.svg',
'Congo': 'https://media.api-sports.io/flags/cd.svg',
'Congo-DR': 'https://media.api-sports.io/flags/cg.svg',
'Costa-Rica': 'https://media.api-sports.io/flags/cr.svg',
'Crimea': 'https://media.api-sports.io/flags/ua.svg',
'Croatia': 'https://media.api-sports.io/flags/hr.svg',
'Cuba': 'https://media.api-sports.io/flags/cu.svg',
'Curacao': 'https://media.api-sports.io/flags/cw.svg',
'Cyprus': 'https://media.api-sports.io/flags/cy.svg',
'Czech-Republic': 'https://media.api-sports.io/flags/cz.svg',
'Denmark': 'https://media.api-sports.io/flags/dk.svg',
'Dominican-Republic': 'https://media.api-sports.io/flags/do.svg',
'Ecuador': 'https://media.api-sports.io/flags/ec.svg',
'Egypt': 'https://media.api-sports.io/flags/eg.svg',
'El-Salvador': 'https://media.api-sports.io/flags/sv.svg',
'England': 'https://media.api-sports.io/flags/gb-eng.svg',
'Estonia': 'https://media.api-sports.io/flags/ee.svg',
'Eswatini': 'https://media.api-sports.io/flags/sz.svg',
'Ethiopia': 'https://media.api-sports.io/flags/et.svg',
'Faroe-Islands': 'https://media.api-sports.io/flags/fo.svg',
'Fiji': 'https://media.api-sports.io/flags/fj.svg',
'Finland': 'https://media.api-sports.io/flags/fi.svg',
'France': 'https://media.api-sports.io/flags/fr.svg',
'Gabon': 'https://media.api-sports.io/flags/ga.svg',
'Gambia': 'https://media.api-sports.io/flags/gm.svg',
'Georgia': 'https://media.api-sports.io/flags/ge.svg',
'Germany': 'https://media.api-sports.io/flags/de.svg',
'Ghana': 'https://media.api-sports.io/flags/gh.svg',
'Gibraltar': 'https://media.api-sports.io/flags/gi.svg',
'Greece': 'https://media.api-sports.io/flags/gr.svg',
'Grenada': 'https://media.api-sports.io/flags/gd.svg',
'Guadeloupe': 'https://media.api-sports.io/flags/gp.svg',
'Guatemala': 'https://media.api-sports.io/flags/gt.svg',
'Guinea': 'https://media.api-sports.io/flags/gn.svg',
'Haiti': 'https://media.api-sports.io/flags/ht.svg',
'Honduras': 'https://media.api-sports.io/flags/hn.svg',
'Hong-Kong': 'https://media.api-sports.io/flags/hk.svg',
'Hungary': 'https://media.api-sports.io/flags/hu.svg',
'Iceland': 'https://media.api-sports.io/flags/is.svg',
'India': 'https://media.api-sports.io/flags/in.svg',
'Indonesia': 'https://media.api-sports.io/flags/id.svg',
'Iran': 'https://media.api-sports.io/flags/ir.svg',
'Iraq': 'https://media.api-sports.io/flags/iq.svg',
'Ireland': 'https://media.api-sports.io/flags/ie.svg',
'Israel': 'https://media.api-sports.io/flags/il.svg',
'Italy': 'https://media.api-sports.io/flags/it.svg',
'Ivory-Coast': 'https://media.api-sports.io/flags/ci.svg',
'Jamaica': 'https://media.api-sports.io/flags/jm.svg',
'Japan': 'https://media.api-sports.io/flags/jp.svg',
'Jordan': 'https://media.api-sports.io/flags/jo.svg',
'Kazakhstan': 'https://media.api-sports.io/flags/kz.svg',
'Kenya': 'https://media.api-sports.io/flags/ke.svg',
'Kosovo': 'https://media.api-sports.io/flags/xk.svg',
'Kuwait': 'https://media.api-sports.io/flags/kw.svg',
'Kyrgyzstan': 'https://media.api-sports.io/flags/kg.svg',
'Laos': 'https://media.api-sports.io/flags/la.svg',
'Latvia': 'https://media.api-sports.io/flags/lv.svg',
'Lebanon': 'https://media.api-sports.io/flags/lb.svg',
'Lesotho': 'https://media.api-sports.io/flags/ls.svg',
'Liberia': 'https://media.api-sports.io/flags/lr.svg',
'Libya': 'https://media.api-sports.io/flags/ly.svg',
'Liechtenstein': 'https://media.api-sports.io/flags/li.svg',
'Lithuania': 'https://media.api-sports.io/flags/lt.svg',
'Luxembourg': 'https://media.api-sports.io/flags/lu.svg',
'Macao': 'https://media.api-sports.io/flags/mo.svg',
'Macedonia': 'https://media.api-sports.io/flags/mk.svg',
'Malawi': 'https://media.api-sports.io/flags/mw.svg',
'Malaysia': 'https://media.api-sports.io/flags/my.svg',
'Maldives': 'https://media.api-sports.io/flags/mv.svg',
'Mali': 'https://media.api-sports.io/flags/ml.svg',
'Malta': 'https://media.api-sports.io/flags/mt.svg',
'Mauritania': 'https://media.api-sports.io/flags/mr.svg',
'Mauritius': 'https://media.api-sports.io/flags/mu.svg',
'Mexico': 'https://media.api-sports.io/flags/mx.svg',
'Moldova': 'https://media.api-sports.io/flags/md.svg',
'Mongolia': 'https://media.api-sports.io/flags/mn.svg',
'Montenegro': 'https://media.api-sports.io/flags/me.svg',
'Morocco': 'https://media.api-sports.io/flags/ma.svg',
'Myanmar': 'https://media.api-sports.io/flags/mm.svg',
'Namibia': 'https://media.api-sports.io/flags/na.svg',
'Nepal': 'https://media.api-sports.io/flags/np.svg',
'Netherlands': 'https://media.api-sports.io/flags/nl.svg',
'New-Zealand': 'https://media.api-sports.io/flags/nz.svg',
'Nicaragua': 'https://media.api-sports.io/flags/ni.svg',
'Nigeria': 'https://media.api-sports.io/flags/ng.svg',
'Northern-Ireland': 'https://media.api-sports.io/flags/gb-nir.svg',
'Norway': 'https://media.api-sports.io/flags/no.svg',
'Oman': 'https://media.api-sports.io/flags/om.svg',
'Pakistan': 'https://media.api-sports.io/flags/pk.svg',
'Palestine': 'https://media.api-sports.io/flags/ps.svg',
'Panama': 'https://media.api-sports.io/flags/pa.svg',
'Paraguay': 'https://media.api-sports.io/flags/py.svg',
'Peru': 'https://media.api-sports.io/flags/pe.svg',
'Philippines': 'https://media.api-sports.io/flags/ph.svg',
'Poland': 'https://media.api-sports.io/flags/pl.svg',
'Portugal': 'https://media.api-sports.io/flags/pt.svg',
'Qatar': 'https://media.api-sports.io/flags/qa.svg',
'Romania': 'https://media.api-sports.io/flags/ro.svg',
'Russia': 'https://media.api-sports.io/flags/ru.svg',
'Rwanda': 'https://media.api-sports.io/flags/rw.svg',
'San-Marino': 'https://media.api-sports.io/flags/sm.svg',
'Saudi-Arabia': 'https://media.api-sports.io/flags/sa.svg',
'Scotland': 'https://media.api-sports.io/flags/gb-sct.svg',
'Senegal': 'https://media.api-sports.io/flags/sn.svg',
'Serbia': 'https://media.api-sports.io/flags/rs.svg',
'Singapore': 'https://media.api-sports.io/flags/sg.svg',
'Slovakia': 'https://media.api-sports.io/flags/sk.svg',
'Slovenia': 'https://media.api-sports.io/flags/si.svg',
'Somalia': 'https://media.api-sports.io/flags/so.svg',
'South-Africa': 'https://media.api-sports.io/flags/za.svg',
'South-Korea': 'https://media.api-sports.io/flags/kr.svg',
'Spain': 'https://media.api-sports.io/flags/es.svg',
'Sudan': 'https://media.api-sports.io/flags/sd.svg',
'Suriname': 'https://media.api-sports.io/flags/sr.svg',
'Sweden': 'https://media.api-sports.io/flags/se.svg',
'Switzerland': 'https://media.api-sports.io/flags/ch.svg',
'Syria': 'https://media.api-sports.io/flags/sy.svg',
'Tajikistan': 'https://media.api-sports.io/flags/tj.svg',
'Tanzania': 'https://media.api-sports.io/flags/tz.svg',
'Thailand': 'https://media.api-sports.io/flags/th.svg',
'Togo': 'https://media.api-sports.io/flags/tg.svg',
'Trinidad-And-Tobago': 'https://media.api-sports.io/flags/tt.svg',
'Tunisia': 'https://media.api-sports.io/flags/tn.svg',
'Turkey': 'https://media.api-sports.io/flags/tr.svg',
'Turkmenistan': 'https://media.api-sports.io/flags/tm.svg',
'Uganda': 'https://media.api-sports.io/flags/ug.svg',
'Ukraine': 'https://media.api-sports.io/flags/ua.svg',
'United-Arab-Emirates': 'https://media.api-sports.io/flags/ae.svg',
'Uruguay': 'https://media.api-sports.io/flags/uy.svg',
'USA': 'https://media.api-sports.io/flags/us.svg',
'Uzbekistan': 'https://media.api-sports.io/flags/uz.svg',
'Venezuela': 'https://media.api-sports.io/flags/ve.svg',
'Vietnam': 'https://media.api-sports.io/flags/vn.svg',
'Wales': 'https://media.api-sports.io/flags/gb-wls.svg',
'Yemen': 'https://media.api-sports.io/flags/ye.svg',
'Zambia': 'https://media.api-sports.io/flags/zm.svg',
'Zimbabwe': 'https://media.api-sports.io/flags/zw.svg'
}

LEAGUE_CODE_MAP = { 
'World, AFC Champions League': 'https://media.api-sports.io/football/leagues/17.png',
'World, UEFA Champions League': 'https://media.api-sports.io/football/leagues/2.png',
'World, UEFA Europa Conference League': 'https://media.api-sports.io/football/leagues/848.png',
'World, UEFA Europa League': 'https://media.api-sports.io/football/leagues/3.png',
'Algeria, Ligue 1': 'https://media.api-sports.io/football/leagues/186.png',
'Egypt, Premier League': 'https://media.api-sports.io/football/leagues/233.png',
'South-Africa, Premier Soccer League': 'https://media.api-sports.io/football/leagues/288.png',
'Tanzania, Ligi kuu Bara': 'https://media.api-sports.io/football/leagues/567.png',
'Australia, A-League': 'https://media.api-sports.io/football/leagues/188.png',
'China, Super League': 'https://media.api-sports.io/football/leagues/169.png',
'China, League One': 'https://media.api-sports.io/football/leagues/170.png',
'India, Indian Super League': 'https://media.api-sports.io/football/leagues/323.png',
'Indonesia, Liga 1': 'https://media.api-sports.io/football/leagues/274.png',
'Iran, Persian Gulf Pro League': 'https://media.api-sports.io/football/leagues/290.png',
'Japan, J1 League': 'https://media.api-sports.io/football/leagues/98.png',
'Japan, J2 League': 'https://media.api-sports.io/football/leagues/99.png',
'Malaysia, Super League': 'https://media.api-sports.io/football/leagues/278.png',
'Saudi-Arabia, Pro League': 'https://media.api-sports.io/football/leagues/307.png',
'Singapore, Premier League': 'https://media.api-sports.io/football/leagues/368.png',
'South-Korea, K League 1': 'https://media.api-sports.io/football/leagues/292.png',
'South-Korea, K League 2': 'https://media.api-sports.io/football/leagues/293.png',
'Vietnam, V.League 1': 'https://media.api-sports.io/football/leagues/340.png',
'Austria, Bundesliga': 'https://media.api-sports.io/football/leagues/218.png',
'Austria, 2. Liga': 'https://media.api-sports.io/football/leagues/219.png',
'Azerbaijan, Premyer Liqa': 'https://media.api-sports.io/football/leagues/419.png',
'Belarus, Premier League': 'https://media.api-sports.io/football/leagues/116.png',
'Belgium, Jupiler Pro League': 'https://media.api-sports.io/football/leagues/144.png',
'Croatia, HNL': 'https://media.api-sports.io/football/leagues/210.png',
'Czech-Republic, Czech Liga': 'https://media.api-sports.io/football/leagues/345.png',
'Denmark, Superliga': 'https://media.api-sports.io/football/leagues/119.png',
'England, Premier League': 'https://media.api-sports.io/football/leagues/39.png',
'England, Championship': 'https://media.api-sports.io/football/leagues/40.png',
'England, League One': 'https://media.api-sports.io/football/leagues/41.png',
'England, League Two': 'https://media.api-sports.io/football/leagues/42.png',
'Faroe-Islands, Meistaradeildin': 'https://media.api-sports.io/football/leagues/367.png',
'France, Ligue 1': 'https://media.api-sports.io/football/leagues/61.png',
'France, Ligue 2': 'https://media.api-sports.io/football/leagues/62.png',
'Germany, Bundesliga': 'https://media.api-sports.io/football/leagues/78.png',
'Germany, 2. Bundesliga': 'https://media.api-sports.io/football/leagues/79.png',
'Italy, Serie A': 'https://media.api-sports.io/football/leagues/135.png',
'Italy, Serie B': 'https://media.api-sports.io/football/leagues/136.png',
'Ireland, Premier Division': 'https://media.api-sports.io/football/leagues/357.png',
'Ireland, First Division': 'https://media.api-sports.io/football/leagues/358.png',
'Latvia, Virsliga': 'https://media.api-sports.io/football/leagues/365.png',
'Lithuania, A Lyga': 'https://media.api-sports.io/football/leagues/362.png',
'Netherlands, Eredivisie': 'https://media.api-sports.io/football/leagues/88.png',
'Netherlands, Eerste Divisie': 'https://media.api-sports.io/football/leagues/89.png',
'Portugal, Primeira Liga': 'https://media.api-sports.io/football/leagues/94.png',
'Poland, Ekstraklasa': 'https://media.api-sports.io/football/leagues/106.png',
'Russia, Premier League': 'https://media.api-sports.io/football/leagues/235.png',
'Scotland, Premiership': 'https://media.api-sports.io/football/leagues/179.png',
'Spain, La Liga': 'https://media.api-sports.io/football/leagues/140.png',
'Spain, Segunda División': 'https://media.api-sports.io/football/leagues/141.png',
'Switzerland, Super League': 'https://media.api-sports.io/football/leagues/207.png',
'Turkey, Süper Lig': 'https://media.api-sports.io/football/leagues/203.png',
'Turkey, 1. Lig': 'https://media.api-sports.io/football/leagues/204.png',
'Ukraine, Premier League': 'https://media.api-sports.io/football/leagues/333.png',
'Wales, Premier League': 'https://media.api-sports.io/football/leagues/110.png',
'Argentina, Liga Profesional Argentina': 'https://media.api-sports.io/football/leagues/128.png',
'Argentina, Primera B Metropolitana': 'https://media.api-sports.io/football/leagues/131.png',
'Chile, Primera División': 'https://media.api-sports.io/football/leagues/265.png',
'Colombia, Primera A': 'https://media.api-sports.io/football/leagues/239.png',
'Colombia, Primera B': 'https://media.api-sports.io/football/leagues/240.png',
'Costa-Rica, Primera División': 'https://media.api-sports.io/football/leagues/162.png',
'Ecuador, Liga Pro': 'https://media.api-sports.io/football/leagues/242.png',
'Mexico, Liga MX': 'https://media.api-sports.io/football/leagues/262.png',
'Uruguay, Primera División - Apertura': 'https://media.api-sports.io/football/leagues/268.png',
'USA, Major League Soccer': 'https://media.api-sports.io/football/leagues/253.png',
}
# Base URL for the flags
FLAG_BASE_URL = "https://media.api-sports.io/flags/"

MESSAGE_TIMEOUT_SECONDS = 7 # How long messages should persist (in seconds)

# --- Session State Initialization ---
# Ensure the message list exists in session state
if 'transient_messages' not in st.session_state:
    st.session_state.transient_messages = []

# --- Helper Functions (Keep from previous version) ---
def load_weekly_data(file_path):
    try:
        if os.path.exists(file_path):
            return load_data_from_csv(file_path)
            # return pd.read_csv(file_path)
        else:
            st.error(f"File not found: {file_path}")
            return pd.DataFrame() # Return empty dataframe
    except Exception as e:
        st.error(f"Error loading weekly file {file_path}: {e}")
        return pd.DataFrame()
    
def remove_duplicate_records(df) -> pd.DataFrame:
    # duplicates_count = df.duplicated(subset=['match_id']).sum()
    # if duplicates_count > 0:
    #     # st.warning(f"Found {duplicates_count} duplicate match_id entries in the CSV. Keeping the first occurrence of each.")
    #     add_transient_message("warning", f"Found {duplicates_count} duplicate match_id entries in the CSV. Keeping the first occurrence of each.")

    # Drop duplicates based on 'match_id', keeping the first instance
    df_deduplicated = df.drop_duplicates(subset=['match_id'], keep='first')

    # --- Convert back to list of dictionaries ---
    # This format seems expected by the rest of your app
    # Handle potential NaN values properly during conversion
    cleaned_data = df_deduplicated.astype(object).where(pd.notnull(df_deduplicated), None)#.to_dict('records')
    return cleaned_data

# parse_percent, parse_specific_percent, parse_insights_string, parse_h2h_value
def parse_percent(text_value, default=0):
    if not isinstance(text_value, str): return default
    try:
        match = re.search(r'(\d+(\.\d+)?)\s*%', text_value)
        return int(float(match.group(1))) if match else default
    except: return default

def parse_specific_percent(text_value, label_prefix, default=0):
    if not isinstance(text_value, str): return default
    try:
        # Prioritize exact label match with colon/hyphen
        pattern_exact = rf"^{re.escape(label_prefix)}\s*[:\-]?\s*(\d+(\.\d+)?)\s*%"
        match = re.search(pattern_exact, text_value.strip(), re.IGNORECASE)
        if match: return int(float(match.group(1)))

        # Fallback: Look for label within parts separated by '|'
        parts = text_value.split('|')
        if len(parts) > 1:
            for part in parts:
                cleaned_part = part.strip().lower()
                cleaned_label = label_prefix.strip().lower()
                # Check if label like "HT" or "FT" or "O1.5" is at the start or followed by ':'
                pattern_part = rf"^{re.escape(cleaned_label)}\s*[:\-]?\s*(\d+(\.\d+)?)\s*%"
                match = re.search(pattern_part, cleaned_part, re.IGNORECASE)
                if match:
                    return int(float(match.group(1)))
        # Fallback: if no parts and no exact match, try simple search anywhere
        pattern_simple = rf"{re.escape(label_prefix)}\s*[:\-]?\s*(\d+(\.\d+)?)\s*%"
        match = re.search(pattern_simple, text_value, re.IGNORECASE)
        if match: return int(float(match.group(1)))

        return default # Return default if nothing found
    except: return default


def parse_insights_string(text_block):
    parsed_insights = []
    if not isinstance(text_block, str): return parsed_insights
    lines = text_block.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        # Skip lines that are just hyphens or similar separators if any
        if line.startswith('---') or line.startswith('==='): continue
        insight = {'label': line, 'value': None, 'delta_str': None, 'delta_val': None, 'direction': None}
        try:
            # Regex: Label (often ending with '/game' or 'goals' etc): Value (Delta% Direction avg)
            # Allow label to contain spaces. Value is numeric. Delta is optional.
            pattern = r"^(.*?):\s*([\d.]+)\%?\s*(?:\(\s*([+\-]?[\d.]+)\s*%?\s*([🔼🔻])\s*avg\s*\))?"
            match = re.match(pattern, line, re.IGNORECASE)

            if match:
                insight['label'] = match.group(1).strip()
                insight['value'] = match.group(2).strip()
                if match.group(3): # Delta part exists
                    insight['delta_str'] = f"{match.group(3).strip()}% {match.group(4)} league average"
                    try: insight['delta_val'] = float(match.group(3).strip())
                    except ValueError: pass
                    insight['direction'] = match.group(4)
            elif ':' in line: # Simpler fallback: Label: Value (string value)
                parts = line.split(':', 1)
                insight['label'] = parts[0].strip()
                insight['value'] = parts[1].strip() # Value could be text here

            # Only add if label is meaningful
            if insight['label']:
                parsed_insights.append(insight)
        except Exception as e:
            # Optionally log the error: print(f"Error parsing insight line: {line} -> {e}")
            if insight['label']: # Add even if parsing failed partially
                parsed_insights.append(insight)
    return parsed_insights


def parse_h2h_value(text_value, key_label, is_numeric=True, default=None):
    """ Extracts H or A value from strings like 'H:1.125 | A:1.5' """
    if not isinstance(text_value, str): return default
    try:
        # More robust pattern: handles optional spaces, case-insensitive
        pattern = rf"{key_label}\s*:\s*([\d.]+)"
        match = re.search(pattern, text_value, re.IGNORECASE)
        if match:
            val_str = match.group(1)
            # Try converting to float if numeric, else return string if not required
            if is_numeric:
                try:
                    return float(val_str)
                except ValueError:
                    return default # Failed numeric conversion
            else:
                return val_str # Return as string
        return default # Label not found
    except Exception:
        return default

def get_progress_color(value):
    """Determines a color based on the percentage value (0-100)."""
    if value < 33:
        return "#f44336" # Red
    elif value < 66:
        return "#ff9800" # Orange
    else:
        return "#8bc34a" # Light Green

def create_colored_progress_bar(value, text_label=None):
    """Generates HTML for a progress bar with color based on value."""
    # st.write(value)
    if value is None or not isinstance(value, (int, float)):
        value = 0 # Default to 0 if invalid input
    value = max(0, min(100, value)) # Clamp value between 0 and 100

    color = get_progress_color(value)
    # Text color based on background for better readability
    text_color = "#ffffff" if value >= 33 else "#000000" # White text for orange/green, black for red

    # Optional: Display text label inside the bar
    display_text = f"{int(value)}%"
    # if text_label:
    #     display_text = f"{text_label}: {int(value)}%"

    # Simple HTML structure using divs 
    bar_html = f"""
    <div style="background-color: #e0e0e0; border-radius: 5px; height: 20px; width: 100%; overflow: hidden; position: relative;">
        <div style="width: {value}%; background-color: {color}; height: 100%; border-radius: 5px 0 0 5px; text-align: center; color: {text_color}; font-weight: bold; line-height: 20px; font-size: 12px; position: absolute; left: 0; top: 0;">
            <!-- {display_text} -->
        </div>
        <div style="width: 100%; text-align: center; color: #424242; font-weight: bold; line-height: 20px; font-size: 12px; position: absolute; left: 0; top: 0; z-index: 0;">
            {display_text} <!-- Background text for contrast if bar is short -->
        </div>
    </div>
    """
    return bar_html

# --- Data Loading Functions ---
# @st.cache_data # Cache results if data doesn't change often
def load_data_from_text(filepath):
    """Loads and parses match data from the text file."""
    st.info(f"Loading data from Text file: {filepath}")
    # --- Paste the complex text parsing logic from the previous response here ---
    # This function should return a list of match dictionaries
    all_matches = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        st.error(f"Error: Data file '{filepath}' not found.")
        return []
    except Exception as e:
        st.error(f"Error reading file '{filepath}': {e}")
        return []

    # Split into match blocks - assumes '📅' starts a new match
    # Use positive lookahead (?=...) to keep the delimiter
    match_blocks = re.split(r'(?=📅)', content)

    for i, block in enumerate(match_blocks):
        block = block.strip()
        if not block or not block.startswith('📅'):
            continue # Skip empty blocks or fragments

        match = {'raw_block': block} # Store raw block for debugging if needed
        lines = block.strip().split('\n')
        current_insight_type = None
        insight_buffer = ""

        # Initialize with defaults (important!)
        match.update({
            'date': None, 'time': None, 'country': None, 'league': None, 'league_name': None,
            'home_team': None, 'home_rank': '', 'away_team': None, 'away_rank': '',
            'exp_val_h': None, 'exp_val_d': None, 'exp_val_a': None,
            'advice': None, 'value_bets': None,
            'form_home': None, 'form_away': None,
            'ppg_h': None, 'ppg_h_all': None, 'ppg_a': None, 'ppg_a_all': None,
            'goals_h': None, 'xg_h': None, 'goals_a': None, 'xg_a': None,
            'conceded_h': None, 'xga_h': None, 'conceded_a': None, 'xga_a': None,
            'halves_o05_h': None, 'halves_o05_a': None,
            'team_goals_h': None, 'team_goals_a': None,
            'match_goals_h': None, 'match_goals_a': None,
            'clean_sheet_h': None, 'clean_sheet_a': None,
            'win_rates_h': None, 'win_rates_a': None,
            'h2h_hva_record': None, 'h2h_hva_games': None,
            'h2h_all_record': None, 'h2h_all_games': None,
            'h2h_hva_ppg_str': None, 'h2h_hva_goals_str': None, 'h2h_hva_ou': None,
            'insights_home': '', 'insights_away': '', 'insights_total_h': '', 'insights_total_a': '',
            'confidence_score': None,
            'pred_outcome': None, 'pred_outcome_conf': None,
            'pred_goals': None, 'pred_goals_conf': None,
            'pred_corners': None, 'pred_corners_conf': None,
            'rec_prediction': None,
            'match_id': None # Will be generated at the end
        })

        home_team_buffer = None # Buffer to identify total insights block

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line: continue

            try: # Wrap line parsing in try-except
                # --- Parse Core Info ---
                if line.startswith('📅'):
                    m = re.search(r'📅\s*([\d/]+),\s*🕛\s*([\d:]+)', line)
                    if m: match['date'], match['time'] = m.groups()
                elif re.match(r'^[🌍🌎🌏🗺️⚽🏀🏈⚾🥎🎾🏐🏉🎱🔮🎮👾🏆🥇🥈🥉🏅🎖️🏵️🎗️🎀🎁🎂🎃🎄🎅🎆🎇✨🎈🎉🎊🎋🎍🎎🎏🎐🎑🧧🎀🎁🎗️🎟️🎫', line): # Match most common flags/emojis used for league
                     parts = line.split(' ', 1)
                     if len(parts) == 2:
                        match['league'] = parts[1]
                        country_parts = parts[1].split(',', 1)
                        match['country'] = country_parts[0].strip()
                        if len(country_parts) > 1:
                           # Remove parentheses and content inside like ( 24 )
                           league_part = re.sub(r'\s*\(\s*\d+\s*\)\s*$', '', country_parts[1]).strip()
                           match['league_name'] = league_part
                        else:
                            match['league_name'] = match['country'] # Fallback if no comma
                elif line.startswith('⚡'):
                    # Make rank optional with (?:...)?
                    m = re.search(r'\*(.*?)(?:\s*\((.*?)\))?\s*v\s*(.*?)(?:\s*\((.*?)\))?\*', line)
                    if m:
                        match['home_team'], match['home_rank'], match['away_team'], match['away_rank'] = [g.strip() if g else '' for g in m.groups()]
                        home_team_buffer = match['home_team'] # Store home team name

                # --- Parse Predictions & Values ---
                elif line.startswith('✨ *Expected Value*:'):
                     match['exp_val_h'] = re.search(r'H\*:\s*([\d.]+%)', line).group(1) if re.search(r'H\*:\s*([\d.]+%)', line) else None
                     match['exp_val_d'] = re.search(r'D\*:\s*([\d.]+%)', line).group(1) if re.search(r'D\*:\s*([\d.]+%)', line) else None
                     match['exp_val_a'] = re.search(r'A\*:\s*([\d.]+%)', line).group(1) if re.search(r'A\*:\s*([\d.]+%)', line) else None
                elif line.startswith('✨ *Advice*:'):
                    match['advice'] = line.split(':', 1)[1].strip()
                elif line.startswith('🎯'):
                    match['value_bets'] = line.split(':', 1)[1].strip()

                # --- Parse Stats ---
                elif line.startswith('📊 *H/All Form*:'):
                     form_line = line.split(': ', 1)[1]
                     parts = form_line.split('//') # Split current form and all form
                     home_parts = parts[0].split('║') if '║' in parts[0] else [parts[0], '']
                     away_parts = parts[1].split('║') if len(parts)>1 and '║' in parts[1] else [parts[1] if len(parts)>1 else '', '']
                     match['form_home'] = home_parts[0].strip()
                     match['form_away'] = away_parts[0].strip() # Adjusted splitting needed if format changes
                elif line.startswith('📈 *PPG:'):
                     m_ppg = re.search(r'H\*:\s*([\d.]+)\s*\|\s*All:\s*([\d.]+)\s*║\s*\*A\*:\s*([\d.]+)\s*\|\s*All:\s*([\d.]+)', line)
                     if m_ppg:
                         try: match['ppg_h'] = float(m_ppg.group(1))
                         except: pass
                         try: match['ppg_h_all'] = float(m_ppg.group(2))
                         except: pass
                         try: match['ppg_a'] = float(m_ppg.group(3))
                         except: pass
                         try: match['ppg_a_all'] = float(m_ppg.group(4))
                         except: pass
                elif line.startswith('⚽ *Goals/g:'):
                     m_goals = re.search(r'H\*:\s*([\d.]+)\s*\(xG:\s*(.*?)\)\s*\|\s*\*A\*:\s*([\d.]+)\s*\(xG:\s*(.*?)\)', line)
                     if m_goals:
                        try: match['goals_h'] = float(m_goals.group(1))
                        except: pass
                        xg_h_val = m_goals.group(2).strip()
                        match['xg_h'] = float(xg_h_val) if xg_h_val and xg_h_val != '' else None
                        try: match['goals_a'] = float(m_goals.group(3))
                        except: pass
                        xg_a_val = m_goals.group(4).strip().rstrip(')') # Strip trailing ')'
                        match['xg_a'] = float(xg_a_val) if xg_a_val and xg_a_val != '' else None
                elif line.startswith('⚽ *Conceded/g:'):
                     m_conc = re.search(r'H\*:\s*([\d.]+)\s*\(xGA:\s*(.*?)\)\s*\|\s*\*A\*:\s*([\d.]+)\s*\(xGA:\s*(.*?)\)', line)
                     if m_conc:
                        try: match['conceded_h'] = float(m_conc.group(1))
                        except: pass
                        xga_h_val = m_conc.group(2).strip()
                        match['xga_h'] = float(xga_h_val) if xga_h_val and xga_h_val != '' else None
                        try: match['conceded_a'] = float(m_conc.group(3))
                        except: pass
                        xga_a_val = m_conc.group(4).strip().rstrip(')') # Strip trailing ')'
                        match['xga_a'] = float(xga_a_val) if xga_a_val and xga_a_val != '' else None
                elif line.startswith('🥅 *Halves Over 0.5:'):
                     parts = line.split(': ', 1)[1].split(' ║ ')
                     match['halves_o05_h'] = parts[0].strip()
                     match['halves_o05_a'] = parts[1].strip()
                elif line.startswith('⚽ *Team Goals:'):
                     parts = line.split(': ', 1)[1].split(' ║ ')
                     match['team_goals_h'] = parts[0].strip()
                     match['team_goals_a'] = parts[1].strip()
                elif line.startswith('🥅 *Match Goals:'):
                     parts = line.split(': ', 1)[1].split(' ║ ')
                     match['match_goals_h'] = parts[0].strip()
                     match['match_goals_a'] = parts[1].strip()
                elif line.startswith('🧼'):
                     parts = line.split(': ', 1)[1].split(' | ')
                     cs_h = parts[0].replace('*A*', '').strip()
                     cs_a = parts[1].replace('*A*', '').strip() if len(parts)>1 else None
                     match['clean_sheet_h'] = cs_h if cs_h != 'nan' else None
                     match['clean_sheet_a'] = cs_a if cs_a and cs_a != 'nan' else None
                elif line.startswith('🏆'):
                     parts = line.split(': ', 1)[1].split(' | *A*: ')
                     match['win_rates_h'] = parts[0].strip()
                     match['win_rates_a'] = parts[1].strip() if len(parts) > 1 else None

                # --- Parse H2H ---
                elif line.startswith('📉 *HvA H2H Record*:'):
                     m_h2h_hva = re.search(r':\s*([\d\-]+)\/(\d+)', line)
                     if m_h2h_hva:
                        match['h2h_hva_record'] = m_h2h_hva.group(1)
                        try: match['h2h_hva_games'] = int(m_h2h_hva.group(2))
                        except: pass
                elif line.startswith('📉 *All H2H Record*:'):
                     m_h2h_all = re.search(r':\s*([\d\-]+)\/(\d+)', line)
                     if m_h2h_all:
                         match['h2h_all_record'] = m_h2h_all.group(1)
                         try: match['h2h_all_games'] = int(m_h2h_all.group(2))
                         except: pass
                elif line.startswith('📈 *H2H PPG:'):
                     match['h2h_hva_ppg_str'] = line.split(': ', 1)[1]
                elif line.startswith('⚽ *H2H Goals Scored:'):
                      match['h2h_hva_goals_str'] = line.split(': ', 1)[1]
                elif line.startswith('🥅 *H2H HvA Over/Under*:'):
                     match['h2h_hva_ou'] = line.split(': ', 1)[1]


                # --- Parse Insights (Improved Buffering) ---
                elif line.startswith('✨ *Home Insights*:'):
                    if current_insight_type: match[f'insights_{current_insight_type}'] = insight_buffer.strip()
                    current_insight_type = 'home'
                    insight_buffer = line.split(':', 1)[1].strip() + "\n" if ':' in line else "\n"
                elif line.startswith('✨ *Away Insights*:'):
                    if current_insight_type: match[f'insights_{current_insight_type}'] = insight_buffer.strip()
                    current_insight_type = 'away'
                    insight_buffer = line.split(':', 1)[1].strip() + "\n" if ':' in line else "\n"
                elif line.startswith('✨ *Total Match Insights*:'):
                     if current_insight_type: match[f'insights_{current_insight_type}'] = insight_buffer.strip()
                     current_insight_type = None # Stop basic insight capture
                     insight_buffer = ""
                elif line.startswith('⚡*'): # Start of Total Match Insights block
                     if insight_buffer and current_insight_type in ['home', 'away']: # Save previous basic block
                         match[f'insights_{current_insight_type}'] = insight_buffer.strip()
                     insight_buffer = "" # Reset buffer for total insights
                     team_name_match = re.match(r'⚡\*(.*?)\s*\(.*?\):', line)
                     if team_name_match:
                         team_name_in_line = team_name_match.group(1).strip()
                         # Assign to total_h or total_a based on home_team_buffer
                         if home_team_buffer and team_name_in_line == home_team_buffer:
                             current_insight_type = 'total_h'
                         else:
                              current_insight_type = 'total_a'
                         # Start buffer with content after the team name part
                         insight_buffer = line.split('):', 1)[1].strip() + "\n" if '):' in line else ""
                     else: # If pattern fails, assume it's a continuation
                         if current_insight_type: insight_buffer += line + "\n"

                elif current_insight_type and line.startswith('   -'): # Indented lines belong to current block
                     insight_buffer += line.strip() + "\n"
                elif current_insight_type and not re.match(r'^(?:🎲|Match Outcome:|Over/Under Goals:|Over/Under Corners:|Recommended Prediction:)', line):
                     # Capture non-indented lines if we are inside an insight block, before confidence section starts
                      insight_buffer += line.strip() + "\n"


                # --- Parse Confidence & Final Predictions ---
                elif line.startswith('🎲'):
                     if insight_buffer and current_insight_type: # Store last insight block
                          match[f'insights_{current_insight_type}'] = insight_buffer.strip()
                          insight_buffer = ""
                          current_insight_type = None # Reset type after storing
                     m_conf = re.search(r'Score:\s*(\d+)', line)
                     if m_conf:
                         try: match['confidence_score'] = int(m_conf.group(1))
                         except: pass
                elif line.startswith('Match Outcome:'):
                     m_pred = re.search(r':\s*(.*?)(?:\s*\((\d+)/10\))?$', line) # Make confidence optional
                     if m_pred:
                        match['pred_outcome'] = m_pred.group(1).strip()
                        if m_pred.group(2):
                            try: match['pred_outcome_conf'] = int(m_pred.group(2))
                            except: pass
                elif line.startswith('Over/Under Goals:'):
                     m_pred = re.search(r':\s*(.*?)(?:\s*\((\d+)/10\))?$', line)
                     if m_pred:
                        match['pred_goals'] = m_pred.group(1).strip()
                        if m_pred.group(2):
                           try: match['pred_goals_conf'] = int(m_pred.group(2))
                           except: pass
                elif line.startswith('Over/Under Corners:'):
                     m_pred = re.search(r':\s*(.*?)(?:\s*\((\d+)/10\))?$', line)
                     if m_pred:
                        match['pred_corners'] = m_pred.group(1).strip()
                        if m_pred.group(2):
                           try: match['pred_corners_conf'] = int(m_pred.group(2))
                           except: pass
                elif line.startswith('Recommended Prediction:'):
                     match['rec_prediction'] = line.split(':', 1)[1].strip()

                # --- Fallback/End of block ---
                elif line_num == len(lines) - 1: # Last line check
                    if insight_buffer and current_insight_type:
                        match[f'insights_{current_insight_type}'] = insight_buffer.strip()

            except Exception as e_line:
                 st.warning(f"Error parsing line {line_num+1} in block {i+1}: '{line}' - {e_line}")
                 continue # Skip to next line on error

        # --- Post-processing & ID ---
        if match.get('home_team') and match.get('date'): # Only add if core info was parsed
            # Ensure all insight keys exist even if empty
            for k in ['insights_home', 'insights_away', 'insights_total_h', 'insights_total_a']:
                if k not in match: match[k] = ''
            match['match_id'] = f"{match['home_team']}_{match['away_team']}_{match['date']}_{i}"
            all_matches.append(match)
        else:
             st.warning(f"Skipped block {i+1} due to missing core info (team/date).")

    st.success(f"Successfully parsed {len(all_matches)} matches from '{filepath}'.")
    return all_matches

@st.cache_data
def load_data_from_csv(filepath) -> pd.DataFrame:
    """Loads match data from a CSV file."""
    # st.info(f"Loading data from CSV file: {filepath}")
    add_transient_message("info", f"Loading data from CSV file: {filepath}")

    try:
        df = pd.read_csv(filepath)
        
        # Basic Cleaning & Type Conversion (adjust as needed based on actual CSV)
        # Convert potential numeric columns, coercing errors to NaN then filling
        float_cols = ['exp_val_h','exp_val_d','exp_val_a','ppg_h','ppg_h_all','ppg_a','ppg_a_all','goals_h','xg_h','goals_a','xg_a','conceded_h','xga_h','conceded_a','xga_a','1h_o05_h','1h_o05_a','2h_o05_h','2h_o05_a','team_goals_0_5_h','team_goals_1_5_h','team_goals_0_5_a','team_goals_1_5_a','match_goals_1_5_a','match_goals_2_5_h','match_goals_1_5_h','match_goals_2_5_a','clean_sheet_h','clean_sheet_a','ht_win_rates_h','ft_win_rates_h','ht_win_rates_a','ft_win_rates_a','h2h_hva_ppg_str','h2h_hva_ppg_str','h2h_h_goals_str','HeadToHeadHomeXG','h2h_a_goals_str','HeadToHeadAwayXG','h2h_hva_o1_5','h2h_hva_o2_5','confidence_score','pred_outcome_conf','pred_goals_conf','pred_corners_conf',

        'Last5_HomeBothTeamsToScore','Last5HomeAvergeTotalShots','Last5HomeAvergeTotalShotsOnGoal','Last5HomeAvergeTotalFouls','Last5HomeAvergeTotalcorners','Last5HomeAvergeTotalYellowCards','Last5HomeAvergeTotalRedCards','Last5_AwayBothTeamsToScore','Last5AwayAvergeTotalShots','Last5AwayAvergeTotalShotsOnGoal','Last5AwayAvergeTotalFouls','Last5AwayAvergeTotalcorners','Last5AwayAvergeTotalYellowCards','Last5AwayAvergeTotalRedCards','l5_home_for_league_avg_shots','l5_home_for_league_avg_sot','l5_home_for_league_avg_corners','l5_home_for_league_avg_fouls','l5_home_for_league_avg_yellow_cards','l5_home_for_league_avg_red_cards','l5_away_for_league_avg_shots','l5_away_for_league_avg_sot','l5_away_for_league_avg_corners','l5_away_for_league_avg_fouls','l5_away_for_league_avg_yellow_cards','l5_away_for_league_avg_red_cards','l5_away_against_league_avg_shots','l5_away_against_league_avg_sot','l5_away_against_league_avg_corners','l5_away_against_league_avg_fouls','l5_away_against_league_avg_yellow_cards','l5_away_against_league_avg_red_cards','l5_home_against_league_avg_shots','l5_home_against_league_avg_sot','l5_home_against_league_avg_corners','l5_home_against_league_avg_fouls','l5_home_against_league_avg_yellow_cards','l5_home_against_league_avg_red_cards','HeadToHeadBTTS','HeadToHeadHomeTotalShots','HeadToHeadAwayTotalShots','HeadToHeadHomeShotsOnTarget','HeadToHeadAwayShotsOnTarget','HeadToHeadHomeFouls','HeadToHeadAwayFouls','HeadToHeadHomeCorners','HeadToHeadAwayCorners','HeadToHeadHomeYellowCards','HeadToHeadAwayYellowCards','HeadToHeadHomeRedCards','HeadToHeadAwayRedCards','HeadToHeadOver7Corners','HeadToHeadOver8Corners','HeadToHeadOver9Corners','HeadToHeadOver10Corners','HeadToHeadOver1YellowCards','HeadToHeadOver2YellowCards','HeadToHeadOver3YellowCards','HeadToHeadOver4YellowCards','HomeGoals','AwayGoals','Corners','YellowCards','RedCards',
        'HTRHome','HTRDraw','HTRAway','FTTotalGoalsOver0.5','FTTotalGoalsOver1.5','FTTotalGoalsOver2.5','FTTotalGoalsOver3.5','FTBTTS','FHTTotalGoalsOver0.5','FHTTotalGoalsOver1.5','FHTTotalGoalsOver2.5','FHTTotalGoalsOver3.5','SHTTotalGoalsOver0.5','SHTTotalGoalsOver1.5','SHTTotalGoalsOver2.5','SHTTotalGoalsOver3.5','HomeWinToNil','AwayWinToNil','ScoredFirstTime','HomeSOTResults',
        'HomeShotsResults','HomeFoulsResults','HomeCornersResults','HomeOffsidesResults','HomeYellowsResults','HomeRedsResults','HomeGoalKeeperSavesResults','HomeXGResults','AwaySOTResults','AwayShotsResults','AwayFoulsResults','AwayCornersResults','AwayOffsidesResults','AwayYellowsResults','AwayRedsResults','AwayGoalKeeperSavesResults','AwayXGResults',
        
        'HomeGoals','AwayGoals','Corners','YellowCards','RedCards','HTRHome','HTRDraw','HTRAway','FTTotalGoalsOver0.5 ','FTTotalGoalsOver1.5 ','FTTotalGoalsOver2.5 ','FTTotalGoalsOver3.5 ','FTBTTS','FHTTotalGoalsOver0.5','FHTTotalGoalsOver1.5','FHTTotalGoalsOver2.5','FHTTotalGoalsOver3.5','SHTTotalGoalsOver0.5','SHTTotalGoalsOver1.5','SHTTotalGoalsOver2.5','SHTTotalGoalsOver3.5','HomeWinToNil','AwayWinToNil','ScoredFirstTime',
        
        'Last5HomeOver7Corners','Last5HomeOver8Corners','Last5HomeOver9Corners','Last5HomeOver10Corners','Last5HomeAvergeTotalYellowCards','Last5HomeOver1YellowCards','Last5HomeOver2YellowCards','Last5HomeOver3YellowCards','Last5HomeOver4YellowCards','Last5HomeAvergeTotalRedCards',
        'Last5AwayOver7Corners','Last5AwayOver8Corners','Last5AwayOver9Corners','Last5AwayOver10Corners','Last5AwayAvergeTotalYellowCards','Last5AwayOver1YellowCards','Last5AwayOver2YellowCards','Last5AwayOver3YellowCards','Last5AwayOver4YellowCards','Last5AwayAvergeTotalRedCards',
        
        'l5_league_avg_btts', 'l5HomeLeagueCleanSheet', 'l5AwayLeagueCleanSheet',
        ]

        int_cols = ['h2h_hva_games','h2h_all_games','match_id']

        for col in float_cols:
            if col in df.columns:
                # Coerce errors during conversion, then fill NaN with None (or 0 if appropriate)
                # df[col] = df[col].fillna(pd.NA) # Replace NaN with pandas NA for better handling
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        for col in int_cols:
            if col in df.columns:
                # Coerce errors during conversion, then fill NaN with None (or 0 if appropriate)
                # df[col] = df[col].fillna(pd.NA) # Replace NaN with pandas NA for better handling
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64') # Use nullable Int

        # Fill NaN in string columns with None or empty string
        string_cols = df.select_dtypes(include='object').columns
        df[string_cols] = df[string_cols].fillna('') # Fill NaNs in object columns with empty strings
        
        # Typecast HomeGoals and AwayGoals to int if they exist and are not NaN
        
        # if 'HomeGoals' in df.columns:
        #     df['HomeGoals'] = pd.to_numeric(df['HomeGoals'], errors='coerce')
        #     df.loc[df['HomeGoals'].notna(), 'HomeGoals'] = df['HomeGoals'].astype(int)
        # if 'AwayGoals' in df.columns:
        #     df['AwayGoals'] = pd.to_numeric(df['AwayGoals'], errors='coerce')
        #     df.loc[df['AwayGoals'].notna(), 'AwayGoals'] = df['AwayGoals'].astype(int)

        # --- !!! Deduplication Step !!! ---
        # Check if 'match_id' column exists
        if 'match_id' not in df.columns:
            st.error("CSV file is missing the required 'match_id' column.")
            add_transient_message("error", "CSV file is missing the required 'match_id' column.")
            return [] # Return empty list

        # Count duplicates before dropping (optional info)
        # initial_rows = len(df)
        duplicates_count = df.duplicated(subset=['match_id']).sum()
        if duplicates_count > 0:
            # st.warning(f"Found {duplicates_count} duplicate match_id entries in the CSV. Keeping the first occurrence of each.")
            add_transient_message("warning", f"Found {duplicates_count} duplicate match_id entries in the CSV. Keeping the first occurrence of each.")

        # Drop duplicates based on 'match_id', keeping the first instance
        df_deduplicated = df.drop_duplicates(subset=['match_id'], keep='first')

        # --- Convert back to list of dictionaries ---
        # This format seems expected by the rest of your app
        # Handle potential NaN values properly during conversion
        cleaned_data = df_deduplicated.astype(object).where(pd.notnull(df_deduplicated), None).to_dict('records')
        cleaned_data_df = pd.DataFrame(cleaned_data)
        # Optional: Log how many rows remain
        # st.info(f"Loaded {len(cleaned_data)} unique matches from {initial_rows} rows in CSV.")

        # st.success(f"Successfully loaded {len(cleaned_data)} matches from '{filepath}'.")
        add_transient_message('success', f"Successfully loaded {len(cleaned_data)} matches from '{filepath}'.")
        return cleaned_data_df
        
    except FileNotFoundError:
        st.error(f"Error: CSV file '{filepath}' not found. Please create it or change DATA_SOURCE.")
        add_transient_message("error", f"CSV file '{filepath}' not found. Please create it or change DATA_SOURCE.")
        # --- Create a sample CSV if it doesn't exist for simulation ---
        # st.warning("Creating a sample CSV file for simulation.")
        # sample_df = create_sample_dataframe() # Generate sample data
        # try:
        #     sample_df.to_csv(filepath, index=False)
        #     st.info(f"Sample CSV created at '{filepath}'. Please reload the page.")
        #     return []
        # except Exception as e_write:
        #     st.error(f"Could not write sample CSV: {e_write}")
        return []
    except Exception as e:
        # st.error(f"Error loading data from CSV '{filepath}': {e}")
        add_transient_message("error", f"Error loading data from CSV '{filepath}': {e}")
        return []

@st.cache_data
def load_data_from_postgres(db_params):
    """Simulates loading data from PostgreSQL."""
    st.info("Simulating data loading from PostgreSQL...")
    # --- This part is SIMULATED ---
    # In a real scenario, you would uncomment psycopg2 imports and use them here
    # conn = None
    # try:
    #     conn = psycopg2.connect(**db_params)
    #     cur = conn.cursor()
    #     # IMPORTANT: Use sql module for safe query building if filters were involved
    #     query = "SELECT * FROM football_predictions;" # Adjust table name
    #     cur.execute(query)
    #     colnames = [desc[0] for desc in cur.description]
    #     rows = cur.fetchall()
    #     cur.close()
    #     # Convert rows (tuples) to list of dictionaries
    #     data = [dict(zip(colnames, row)) for row in rows]
    #     # Optional: Data type conversion if needed (e.g., Decimal to float)
    #     st.success(f"Successfully loaded {len(data)} matches from PostgreSQL.")
    #     return data
    # except (Exception, psycopg2.DatabaseError) as error:
    #     st.error(f"Error connecting to or fetching from PostgreSQL: {error}")
    #     return []
    # finally:
    #     if conn is not None:
    #         conn.close()

    # --- Return Sample Data for Simulation ---
    st.warning("Returning sample data instead of connecting to DB.")
    sample_df = create_sample_dataframe()
    return sample_df.to_dict('records')

# def create_sample_dataframe():
#     """Creates a sample Pandas DataFrame for simulation with more variety."""
#     sample_data = [
#         # --- Existing Samples ---
#         {
#             'date': "26/04/2025",
#             'time': "07:00",
#             'country': "Japan",
#             'league': "Japan, J1 League ( 20 )",
#             'league_name': "J1 League",
#             'home_team': "Kashiwa Reysol",
#             'home_rank': "2nd/Top",
#             'away_team': "Albirex Niigata",
#             'away_rank': "19th/Bottom",
#             'exp_val_h': '17.71%',
#             'exp_val_d': None,
#             'exp_val_a': None,
#             'advice': "Combo Double chance : Kashiwa Reysol or draw and -3.5 goals",
#             'value_bets': "H(2.23)",
#             'form_home': "⬜🟩🟥⬜🟩//🟩⬜🟩⬜⬜",
#             'form_away': "⬜🟥🟥🟥🟩//🟥⬜🟩🟥⬜",
#             'ppg_h': 1.6,
#             'ppg_h_all': 1.8,
#             'ppg_a': 0.8,
#             'ppg_a_all': 1.0,
#             'goals_h': 1.0,
#             'xg_h': 1.07,
#             'goals_a': 0.6,
#             'xg_a': 1.47,
#             'conceded_h': 1.0,
#             'xga_h': 0.64,
#             'conceded_a': 1.2,
#             'xga_a': 1.25,
#             'halves_o05_h': "1H: 40% | 2H: 80%",
#             'halves_o05_a': "1H: 100% | 2H: 60%",
#             'team_goals_h': "Over 0.5: 60% | O1.5: 40%",
#             'team_goals_a': "Over 0.5: 60% | O1.5: 40%",
#             'match_goals_h': "O1.5: 80% | O2.5: 20%",
#             'match_goals_a': "O1.5: 60% | O2.5: 0%",
#             'clean_sheet_h': "100%",
#             'clean_sheet_a': "60%",
#             'win_rates_h': "HT: 0% | FT: 40%",
#             'win_rates_a': "HT: 40% | FT: 20%",
#             'h2h_hva_record': "3-6-0",
#             'h2h_hva_games': 9,
#             'h2h_all_record': "6-10-2",
#             'h2h_all_games': 18,
#             'h2h_hva_ppg_str': "H:1.66 | A:0.66",
#             'h2h_hva_goals_str': "H:1.0 | A:0.56",
#             'h2h_hva_ou': "O1.5: 60% | O2.5: 20% ║ U2.5: 20% | U3.5: 66%",
#             'insights_home': "Home goals/game: 1.00 (-29.58% 🔻 avg )\nHome corners/game: 6.60 (+24.06% 🔼 avg)",
#             'insights_away': "Away goals/game: 0.60 (-52.00% 🔻 avg)\nAway corners/game: 3.60 (-23.89% 🔻 avg)",
#             'insights_total_h': "Total match goals/game: 1.83 (-31.34% 🔻 avg)\nTotal match corners/game: 11.35 (+13.61% 🔼 avg)\nU2.5 goals: 80.00% (+30.00% 🔼 avg)\nU3.5 goals: 90.00% (+16.00% 🔼 avg)\nO8.5 corners: 91.67% (+23.67% 🔼 avg)\nU12.5 corners: 71.67% (-5.33% 🔼 avg)",
#             'insights_total_a': "U12.5 corners: 73.33% (-3.67% 🔼 avg)",
#             'confidence_score': 7,
#             'pred_outcome': "Home Win",
#             'pred_outcome_conf': 7,
#             'pred_goals': "Under 2.5",
#             'pred_goals_conf': 7,
#             'pred_corners': "Over 8.5",
#             'pred_corners_conf': 7,
#             'rec_prediction': "Under 2.5",
#             'match_id': 'Kashiwa Reysol_Albirex Niigata_26/04/2025_0'
#         },
#         {
#             'date': "26/04/2025", 'time': "13:00", 'country': "Germany", 'league': "Germany, 2. Bundesliga", 'league_name': "2. Bundesliga",
#             'home_team': "SSV Jahn Regensburg", 'home_rank': "18th/Bottom", 'away_team': "Eintracht Braunschweig", 'away_rank': "15th/Mid",
#              'exp_val_h': None, 'exp_val_d': '1.00%', 'exp_val_a': None,
#             'advice': "Double chance : draw or Eintracht Braunschweig", 'value_bets': "A(2.31), X(3.46)",
#             'form_home': "🟩⬜⬜🟩🟩//🟥🟩🟥🟩🟥", 'form_away': "🟩🟥⬜⬜🟩//🟩🟩🟩⬜🟥",
#             'ppg_h': 2.2, 'ppg_h_all': 1.2, 'ppg_a': 1.6, 'ppg_a_all': 2.0,
#              'goals_h': 1.4, 'xg_h': None, 'goals_a': 1.6, 'xg_a': None, # xG/xGA often missing
#              'conceded_h': 0.4, 'xga_h': None, 'conceded_a': 1.4, 'xga_a': None,
#             'halves_o05_h': "1H: 80% | 2H: 80%", 'halves_o05_a': "1H: 80% | 2H: 80%",
#             'team_goals_h': "Over 0.5: 40% | O1.5: 60%", 'team_goals_a': "Over 0.5: 80% | O1.5: 20%",
#             'match_goals_h': "O1.5: 80% | O2.5: 60%", 'match_goals_a': "O1.5: 80% | O2.5: 40%",
#             'clean_sheet_h': "100%", 'clean_sheet_a': "80%",
#             'win_rates_h': "HT: 60% | FT: 60%", 'win_rates_a': "HT: 40% | FT: 40%",
#             'h2h_hva_record': "4-2-0", 'h2h_hva_games': 6,
#             'h2h_all_record': "6-4-4", 'h2h_all_games': 14,
#             'h2h_hva_ppg_str': "H:1.0 | A:0.33", 'h2h_hva_goals_str': "H: | A:0.67", 'h2h_hva_ou': "O1.5: 100% | O2.5: 40% ║ U2.5: 40% | U3.5: 100%",
#             'insights_home': "Home goals/game: 0.73 (-55.01% 🔻 avg )\nHome corners/game: 5.13 (-8.50% 🔻 avg)",
#             'insights_away': "Away goals/game: 1.00 (-27.01% 🔻 avg)\nAway corners/game: 5.13 (+6.28% 🔼 avg)",
#             'insights_total_h': "NG: 76.67% (+35.67% 🔼 avg)\nO8.5 corners: 76.67% (+5.67% 🔼 avg)\nU12.5 corners: 80.00% (+5.00% 🔼 avg)",
#             'insights_total_a': "O1.5 goals: 83.33% (+5.33% 🔼 avg)\nU12.5 corners: 76.67% (+1.67% 🔼 avg)",
#             'confidence_score': 7,
#             'pred_outcome': "Home Win", 'pred_outcome_conf': 7,
#             'pred_goals': "Under 2.5", 'pred_goals_conf': 7,
#             'pred_corners': "Over 8.5", 'pred_corners_conf': 7,
#             'rec_prediction': "Home Win",
#             'match_id': 'SSV Jahn Regensburg_Eintracht Braunschweig_26/04/2025_1'
#         },
#         # --- New Sample Matches ---
#         { # Same day as above, different league
#             'date': "26/04/2025", 'time': "14:00", 'country': "England", 'league': "England, League Two ( 24 )", 'league_name': "League Two",
#             'home_team': "Harrogate Town", 'home_rank': "19th/Mid", 'away_team': "Notts County", 'away_rank': "6th/Top",
#             'exp_val_h': None, 'exp_val_d': '1.58%', 'exp_val_a': None,
#             'advice': "Double chance : Harrogate Town or draw", 'value_bets': "A(1.75), X(3.87)",
#             'form_home': "🟩⬜🟩⬜🟩//🟩⬜⬜🟥🟩", 'form_away': "⬜🟥🟩🟥⬜//🟥⬜🟥🟥🟩",
#             'ppg_h': 2.2, 'ppg_h_all': 1.6, 'ppg_a': 1.0, 'ppg_a_all': 0.8,
#             'goals_h': 2.0, 'xg_h': 1.8, 'goals_a': 1.0, 'xg_a': 1.1, # Added some xG
#             'conceded_h': 1.2, 'xga_h': 1.4, 'conceded_a': 1.2, 'xga_a': 1.3, # Added some xGA
#             'halves_o05_h': "1H: 60% | 2H: 100%", 'halves_o05_a': "1H: 80% | 2H: 60%",
#             'team_goals_h': "Over 0.5: 80% | O1.5: 40%", 'team_goals_a': "Over 0.5: 80% | O1.5: 60%",
#             'match_goals_h': "O1.5: 100% | O2.5: 60%", 'match_goals_a': "O1.5: 60% | O2.5: 40%",
#             'clean_sheet_h': "0%", 'clean_sheet_a': "40%",
#             'win_rates_h': "HT: 40% | FT: 60%", 'win_rates_a': "HT: 40% | FT: 20%",
#             'h2h_hva_record': "2-0-0", 'h2h_hva_games': 2,
#             'h2h_all_record': "2-0-4", 'h2h_all_games': 6,
#             'h2h_hva_ppg_str': "H:3.0 | A:0.0", 'h2h_hva_goals_str': "H:3.0 | A:1.0", 'h2h_hva_ou': "O1.5: 80% | O2.5: 20% ║ U2.5: 20% | U3.5: 100%",
#             'insights_home': "Home goals/game: 1.14 (-17.65% 🔻 avg )\nHome corners/game: 4.48 (-14.58% 🔻 avg)",
#             'insights_away': "Away goals/game: 1.55 (+37.99% 🔼 avg)\nAway corners/game: 4.48 (+2.90% 🔼 avg)",
#             'insights_total_h': "Total match corners/game: 10.84 (+17.28% 🔼 avg)",
#             'insights_total_a': "O1.5 goals: 77.27% (+6.27% 🔼 avg)\nU12.5 corners: 77.27% (-0.73% 🔼 avg)",
#             'confidence_score': 7,
#             'pred_outcome': "Home or Draw", 'pred_outcome_conf': 7,
#             'pred_goals': "Over 1.5", 'pred_goals_conf': 7,
#             'pred_corners': "Under 12.5", 'pred_corners_conf': 7,
#             'rec_prediction': "Over 1.5",
#             'match_id': 'Harrogate Town_Notts County_26/04/2025_2'
#         },
#         { # Same day, another German league game
#             'date': "26/04/2025", 'time': "15:30", 'country': "Germany", 'league': "Germany, 2. Bundesliga", 'league_name': "2. Bundesliga",
#             'home_team': "Bayern Munich", 'home_rank': "1st/Top", 'away_team': "Borussia Dortmund", 'away_rank': "3rd/Top",
#             'exp_val_h': '25.0%', 'exp_val_d': None, 'exp_val_a': None,
#             'advice': "Winner: Bayern Munich", 'value_bets': "H(1.40)",
#             'form_home': "🟩🟩🟩🟩⬜", 'form_away': "🟩⬜🟩🟩🟥",
#             'ppg_h': 2.8, 'ppg_h_all': 2.6, 'ppg_a': 2.1, 'ppg_a_all': 2.0,
#             'goals_h': 3.1, 'xg_h': 2.9, 'goals_a': 2.2, 'xg_a': 2.0,
#             'conceded_h': 0.7, 'xga_h': 0.9, 'conceded_a': 1.1, 'xga_a': 1.2,
#             'halves_o05_h': "1H: 90% | 2H: 95%", 'halves_o05_a': "1H: 85% | 2H: 90%",
#             'team_goals_h': "Over 0.5: 100% | O1.5: 90%", 'team_goals_a': "Over 0.5: 95% | O1.5: 70%",
#             'match_goals_h': "O1.5: 100% | O2.5: 85%", 'match_goals_a': "O1.5: 95% | O2.5: 75%",
#             'clean_sheet_h': "60%", 'clean_sheet_a': "45%",
#             'win_rates_h': "HT: 65% | FT: 80%", 'win_rates_a': "HT: 50% | FT: 65%",
#             'h2h_hva_record': "7-2-1", 'h2h_hva_games': 10,
#             'h2h_all_record': "15-5-5", 'h2h_all_games': 25,
#             'h2h_hva_ppg_str': "H:2.3 | A:0.8", 'h2h_hva_goals_str': "H:2.8 | A:1.1", 'h2h_hva_ou': "O1.5: 90% | O2.5: 70% ║ U2.5: 30% | U3.5: 50%",
#             'insights_home': "Home goals/game: 3.1 (+15% 🔼 avg)",
#             'insights_away': "Away goals/game: 2.2 (+8% 🔼 avg)",
#             'insights_total_h': "O2.5 goals: 85% (+20% 🔼 avg)\nO10.5 corners: 60% (+5% 🔼 avg)",
#             'insights_total_a': "O2.5 goals: 75% (+10% 🔼 avg)",
#             'confidence_score': 8,
#             'pred_outcome': "Home Win", 'pred_outcome_conf': 8,
#             'pred_goals': "Over 2.5", 'pred_goals_conf': 8,
#             'pred_corners': "Over 10.5", 'pred_corners_conf': 6,
#             'rec_prediction': "Over 2.5",
#             'match_id': 'Bayern Munich_Borussia Dortmund_26/04/2025_3'
#         },
#         { # Different date, different league
#             'date': "27/04/2025", 'time': "17:15", 'country': "France", 'league': "France, Ligue 1 ( 18 )", 'league_name': "Ligue 1",
#             'home_team': "Lens", 'home_rank': "8th/Mid", 'away_team': "Auxerre", 'away_rank': "11th/Mid",
#             'exp_val_h': '4.62%', 'exp_val_d': '1.60%', 'exp_val_a': None,
#             'advice': "Double chance : Lens or draw", 'value_bets': "H(1.62), X(4.31)",
#             'form_home': "🟩//🟩🟥🟩🟥🟩", 'form_away': "⬜🟩⬜🟩🟥//🟥🟥🟩🟩⬜", # Short form example
#             'ppg_h': 3.0, 'ppg_h_all': 1.8, 'ppg_a': 1.6, 'ppg_a_all': 1.4,
#             'goals_h': 1.0, 'xg_h': 1.76, 'goals_a': 1.4, 'xg_a': 1.02,
#             'conceded_h': 1.6, 'xga_h': 1.46, 'conceded_a': 1.2, 'xga_a': 1.8,
#             'halves_o05_h': "1H: 40% | 2H: 100%", 'halves_o05_a': "1H: 80% | 2H: 80%",
#             'team_goals_h': "Over 0.5: 20% | O1.5: 60%", 'team_goals_a': "Over 0.5: 60% | O1.5: 20%",
#             'match_goals_h': "O1.5: 60% | O2.5: 20%", 'match_goals_a': "O1.5: 100% | O2.5: 40%",
#             'clean_sheet_h': "100%", 'clean_sheet_a': "80%",
#             'win_rates_h': "HT: 0% | FT: 40%", 'win_rates_a': "HT: 40% | FT: 40%",
#             'h2h_hva_record': "6-2-0", 'h2h_hva_games': 8,
#             'h2h_all_record': "10-4-2", 'h2h_all_games': 16,
#             'h2h_hva_ppg_str': "H:2.5 | A:0.25", 'h2h_hva_goals_str': "H:1.25 | A:0.25", 'h2h_hva_ou': "O1.5: 80% | O2.5: 40% ║ U2.5: 40% | U3.5: 50%",
#             'insights_home': "Home goals/game: 2.00 (+23.46% 🔼 avg )\nHome corners/game: 2.00 (-61.01% 🔻 avg)",
#             'insights_away': "Away goals/game: 1.27 (-8.21% 🔻 avg )\nAway corners/game: 4.67 (+4.63% 🔼 avg)",
#             'insights_total_h': "Total match corners/game: 6.50 (+46.40% 🔼 avg)\nO1.5 goals: 100.00% (+27.00% 🔼 avg)\nU8.5 corners: 100.00% (+79.00% 🔼 avg)\nU10.5 corners: 100.00% (+69.00% 🔼 avg)\nU12.5 corners: 100.00% (+61.00% 🔼 avg)",
#             'insights_total_a': "O1.5 goals: 80.00% (-2.00% 🔼 avg)\nU12.5 corners: 73.33% (-9.67% 🔼 avg)",
#             'confidence_score': 7,
#             'pred_outcome': "Home Win", 'pred_outcome_conf': 7,
#             'pred_goals': "Over 1.5", 'pred_goals_conf': 7,
#             'pred_corners': "Under 10.5", 'pred_corners_conf': 7,
#             'rec_prediction': "Home Win",
#             'match_id': 'Lens_Auxerre_27/04/2025_4'
#         },
#          { # Same date as above, different league
#             'date': "27/04/2025", 'time': "14:30", 'country': "Austria", 'league': "Austria, Bundesliga ( 24 )", 'league_name': "Bundesliga",
#             'home_team': "Rapid Vienna", 'home_rank': "5th/Top", 'away_team': "FC BW Linz", 'away_rank': "6th/Mid",
#             'exp_val_h': '9.05%', 'exp_val_d': None, 'exp_val_a': None,
#             'advice': "Double chance : Rapid Vienna or draw", 'value_bets': "H(1.62)",
#             'form_home': "🟩⬜🟩⬜🟥//🟥🟩🟥🟥", 'form_away': "⬜🟥🟩🟥🟥//🟥🟥🟥🟥",
#             'ppg_h': 1.6, 'ppg_h_all': 1.2, 'ppg_a': 0.8, 'ppg_a_all': 0.6,
#             'goals_h': 2.2, 'xg_h': 1.9, 'goals_a': 1.0, 'xg_a': 1.1,
#             'conceded_h': 1.0, 'xga_h': 1.2, 'conceded_a': 1.8, 'xga_a': 1.5,
#             'halves_o05_h': "1H: 100% | 2H: 80%", 'halves_o05_a': "1H: 80% | 2H: 100%",
#             'team_goals_h': "Over 0.5: 20% | O1.5: 80%", 'team_goals_a': "Over 0.5: 100% | O1.5: 60%",
#             'match_goals_h': "O1.5: 80% | O2.5: 60%", 'match_goals_a': "O1.5: 80% | O2.5: 20%",
#             'clean_sheet_h': "100%", 'clean_sheet_a': "40%",
#             'win_rates_h': "HT: 80% | FT: 60%", 'win_rates_a': "HT: 20% | FT: 20%",
#             'h2h_hva_record': "2-0-2", 'h2h_hva_games': 4,
#             'h2h_all_record': "4-0-4", 'h2h_all_games': 8,
#             'h2h_hva_ppg_str': "H:1.5 | A:1.5", 'h2h_hva_goals_str': "H:0.5 | A:0.5", 'h2h_hva_ou': "O1.5: 100% | O2.5: 80% ║ U2.5: 80% | U3.5: 0%",
#             'insights_home': "Home goals/game: 1.40 (+-13.58% 🔼 avg )\nHome corners/game: 10.20 (+98.83% 🔼 avg)",
#             'insights_away': "Away goals/game: 1.00 (-16.67% 🔻 avg )\nAway corners/game: 4.08 (-5.63% 🔻 avg)",
#             'insights_total_h': "Total match corners/game: 11.60 (+161.26% 🔼 avg)\nO1.5 goals: 80.00% (+7.00% 🔼 avg)",
#             'insights_total_a': "O1.5 goals: 76.92% (-2.08% 🔼 avg)\nU12.5 corners: 76.92% (-5.08% 🔼 avg)",
#             'confidence_score': 7,
#             'pred_outcome': "Home Win", 'pred_outcome_conf': 7,
#             'pred_goals': "Over 1.5", 'pred_goals_conf': 7,
#             'pred_corners': "Over 10.5", 'pred_corners_conf': 7,
#             'rec_prediction': "Home Win",
#             'match_id': 'Rapid Vienna_FC BW Linz_27/04/2025_5'
#         },
#          { # USA game
#             'date': "27/04/2025", 'time': "01:15", 'country': "USA", 'league': "USA, Major League Soccer ( 30 )", 'league_name': "Major League Soccer",
#             'home_team': "Orlando City SC", 'home_rank': "7th/Top", 'away_team': "Atlanta United FC", 'away_rank': "11th/Mid",
#             'exp_val_h': None, 'exp_val_d': '2.17%', 'exp_val_a': None,
#             'advice': "Double chance : Orlando City SC or draw", 'value_bets': "H(1.70), X(3.79)",
#             'form_home': "🟥🟥🟩🟩⬜//⬜⬜🟩🟩⬜", 'form_away': "🟩🟥🟥⬜🟥//🟥⬜🟩⬜🟥",
#             'ppg_h': 1.4, 'ppg_h_all': 1.8, 'ppg_a': 0.8, 'ppg_a_all': 1.4,
#             'goals_h': 3.2, 'xg_h': 2.09, 'goals_a': 0.8, 'xg_a': 1.36,
#             'conceded_h': 1.2, 'xga_h': 0.78, 'conceded_a': 2.2, 'xga_a': 1.15,
#             'halves_o05_h': "1H: 80% | 2H: 80%", 'halves_o05_a': "1H: 20% | 2H: 100%",
#             'team_goals_h': "Over 0.5: 80% | O1.5: 40%", 'team_goals_a': "Over 0.5: 80% | O1.5: 80%",
#             'match_goals_h': "O1.5: 80% | O2.5: 80%", 'match_goals_a': "O1.5: 40% | O2.5: 40%",
#             'clean_sheet_h': "77%", 'clean_sheet_a': "20%",
#             'win_rates_h': "HT: 80% | FT: 80%", 'win_rates_a': "HT: 0% | FT: 0%",
#             'h2h_hva_record': "5-5-8", 'h2h_hva_games': 18,
#             'h2h_all_record': "8-10-12", 'h2h_all_games': 30,
#             'h2h_hva_ppg_str': "H:1.11 | A:1.61", 'h2h_hva_goals_str': "H:1.28 | A:1.22", 'h2h_hva_ou': "O1.5: 100% | O2.5: 60% ║ U2.5: 60% | U3.5: 66%",
#             'insights_home': "Home goals/game: 1.68 (+0.00% 🔼 avg )\nHome corners/game: 5.84 (+6.18% 🔼 avg)",
#             'insights_away': "Away goals/game: 1.00 (-24.81% 🔻 avg)\nAway corners/game: 4.35 (+0.41% 🔼 avg)",
#             'insights_total_h': "O1.5 goals: 77.13% (-1.87% 🔼 avg)\nU12.5 corners: 82.96% (+3.96% 🔼 avg)",
#             'insights_total_a': "O1.5 goals: 79.17% (+0.17% 🔼 avg)",
#             'confidence_score': 7,
#             'pred_outcome': "Home Win", 'pred_outcome_conf': 7,
#             'pred_goals': "Over 1.5", 'pred_goals_conf': 7,
#             'pred_corners': "Under 12.5", 'pred_corners_conf': 7,
#             'rec_prediction': "Home Win",
#             'match_id': 'Orlando City SC_Atlanta United FC_27/04/2025_6'
#         },
#         { # Future date
#             'date': "28/04/2025", 'time': "20:00", 'country': "Argentina", 'league': "Argentina, Liga Profesional Argentina ( 90 )", 'league_name': "Liga Profesional Argentina",
#             'home_team': "Barracas Central", 'home_rank': "14th/Mid", 'away_team': "Union Santa Fe", 'away_rank': "22nd/Mid",
#             'exp_val_h': '25.75%', 'exp_val_d': None, 'exp_val_a': None,
#             'advice': "Combo Double chance : draw or Union Santa Fe and -3.5 goals", 'value_bets': "H(2.97)",
#             'form_home': "🟥🟩⬜🟩🟩//🟥🟩🟥🟩⬜", 'form_away': "🟥🟥🟥🟥⬜//⬜⬜🟩🟥🟥",
#             'ppg_h': 2.0, 'ppg_h_all': 1.8, 'ppg_a': 0.2, 'ppg_a_all': 1.4,
#             'goals_h': 1.6, 'xg_h': 1.98, 'goals_a': 0.4, 'xg_a': 0.96,
#             'conceded_h': 0.8, 'xga_h': None, 'conceded_a': 1.2, 'xga_a': None, # Missing xGA
#             'halves_o05_h': "1H: 100% | 2H: 80%", 'halves_o05_a': "1H: 60% | 2H: 60%",
#             'team_goals_h': "Over 0.5: 60% | O1.5: 40%", 'team_goals_a': "Over 0.5: 80% | O1.5: 60%",
#             'match_goals_h': "O1.5: 100% | O2.5: 60%", 'match_goals_a': "O1.5: 40% | O2.5: 0%",
#             'clean_sheet_h': "100%", 'clean_sheet_a': "40%",
#             'win_rates_h': "HT: 80% | FT: 80%", 'win_rates_a': "HT: 0% | FT: 0%",
#             'h2h_hva_record': "0-1-1", 'h2h_hva_games': 2,
#             'h2h_all_record': "0-1-2", 'h2h_all_games': 3,
#             'h2h_hva_ppg_str': "H:0.5 | A:2.0", 'h2h_hva_goals_str': "H:1.0 | A:1.5", 'h2h_hva_ou': "O1.5: 60% | O2.5: 40% ║ U2.5: 40% | U3.5: 100%",
#             'insights_home': "Home goals/game: 1.80 (+51.26% 🔼 avg )\nHome corners/game: 2.00 (-60.71% 🔻 avg)",
#             'insights_away': "Away goals/game: 0.33 (-59.84% 🔻 avg)\nAway corners/game: 5.67 (46.80% 🔼 avg)",
#             'insights_total_h': "Total match goals/game: 2.68 (+32.84% 🔼 avg)\nO1.5 goals: 81.67% (+20.67% 🔼 avg)\nU8.5 corners: 83.33% (+35.33% 🔼 avg)\nU10.5 corners: 91.67% (+19.67% 🔼 avg)\nU12.5 corners: 91.67% (+6.67% 🔼 avg)",
#             'insights_total_a': "Total match corners/game: 10.19 (+13.70% 🔼 avg)\nU2.5 goals: 77.08% (+7.08% 🔼 avg)\nU3.5 goals: 85.42% (-0.58% 🔼 avg)\nU12.5 corners: 70.83% (-14.17% 🔼 avg)",
#             'confidence_score': 7,
#             'pred_outcome': "Home Win", 'pred_outcome_conf': 7,
#             'pred_goals': "Under 2.5", 'pred_goals_conf': 7,
#             'pred_corners': "Under 10.5", 'pred_corners_conf': 7,
#             'rec_prediction': "Under 2.5",
#             'match_id': 'Barracas Central_Union Santa Fe_28/04/2025_7'
#         },
#         { # Same future date, different league
#             'date': "28/04/2025", 'time': "21:15", 'country': "Portugal", 'league': "Portugal, Primeira Liga ( 18 )", 'league_name': "Primeira Liga",
#             'home_team': "Casa Pia", 'home_rank': "8th/Mid", 'away_team': "Estoril", 'away_rank': "9th/Mid",
#             'exp_val_h': '11.06%', 'exp_val_d': None, 'exp_val_a': None,
#             'advice': "Double chance : draw or Estoril", 'value_bets': "H(2.23)",
#             'form_home': "🟩🟩🟩🟥🟩//⬜🟥⬜🟩🟥", 'form_away': "⬜🟥⬜🟩🟥//🟥🟥🟩🟥⬜",
#             'ppg_h': 2.4, 'ppg_h_all': 1.0, 'ppg_a': 1.0, 'ppg_a_all': 0.8,
#             'goals_h': 1.6, 'xg_h': 0.96, 'goals_a': 1.4, 'xg_a': 1.41,
#             'conceded_h': 1.0, 'xga_h': 1.35, 'conceded_a': 1.8, 'xga_a': 1.63,
#             'halves_o05_h': "1H: 80% | 2H: 80%", 'halves_o05_a': "1H: 80% | 2H: 100%",
#             'team_goals_h': "Over 0.5: 60% | O1.5: 60%", 'team_goals_a': "Over 0.5: 60% | O1.5: 60%",
#             'match_goals_h': "O1.5: 100% | O2.5: 40%", 'match_goals_a': "O1.5: 80% | O2.5: 40%",
#             'clean_sheet_h': "50%", 'clean_sheet_a': "40%",
#             'win_rates_h': "HT: 20% | FT: 80%", 'win_rates_a': "HT: 20% | FT: 20%",
#             'h2h_hva_record': "0-4-0", 'h2h_hva_games': 4,
#             'h2h_all_record': "2-4-4", 'h2h_all_games': 10,
#             'h2h_hva_ppg_str': "H:1.0 | A:1.0", 'h2h_hva_goals_str': "H:1.0 | A:1.0", 'h2h_hva_ou': "O1.5: 100% | O2.5: 80% ║ U2.5: 80% | U3.5: 50%",
#             'insights_home': "Home goals/game: 1.36 (-0.94% 🔻 avg )\nHome corners/game: 4.71 (-10.20% 🔻 avg)",
#             'insights_away': "Away goals/game: 1.33 (+14.94% 🔼 avg)\nAway corners/game: 3.40 (-20.19% 🔻 avg)",
#             'insights_total_h': "O1.5 goals: 75.71% (+3.71% 🔼 avg)\nU12.5 corners: 82.86% (+1.86% 🔼 avg)",
#             'insights_total_a': "Total match goals/game: 2.87 (+12.86% 🔼 avg)\nO1.5 goals: 76.67% (+4.67% 🔼 avg)\nU12.5 corners: 86.67% (+5.67% 🔼 avg)",
#             'confidence_score': 7,
#             'pred_outcome': "Home Win", 'pred_outcome_conf': 7,
#             'pred_goals': "Under 2.5", 'pred_goals_conf': 7,
#             'pred_corners': "Under 12.5", 'pred_corners_conf': 7,
#             'rec_prediction': "Under 2.5",
#             'match_id': 'Casa Pia_Estoril_28/04/2025_8'
#         }

#     ]
#     return pd.DataFrame(sample_data)

# --- Navigation Functions  ---
def set_selected_match(match_id):
    st.session_state.selected_match_id = match_id

def clear_selected_match():
    #  if 'selected_match_id' in st.session_state:
    #      del st.session_state['selected_match_id']

     # Optional: Clear other states if needed when going back
     # st.experimental_rerun() # Force rerun if state changes aren't picking up

    st.session_state.selected_match_id = None

def get_country_emoji(country_name):
		country_code_mapping = {
                # "Asia" : '🇦🇸',
                "Europe": '🇪🇺',
				
				# Add more country mappings as needed
		}

		country_code = country_name.title()
		return country_code_mapping.get(country_code, emoji.emojize(f":{country_code}:"))

def get_flag_url(country_name,league_name):
    """Looks up the country code and returns the full flag URL."""
    if not isinstance(country_name, str):
        return None # Return None if input is not a string

    # Attempt lookup (consider case-insensitivity if needed)
    # code = COUNTRY_CODE_MAP.get(country_name)
    # Case-insensitive example:
    # if country_name not in ['UEFA Champions League','UEFA Europa Conference League','UEFA Europa League','AFC Champions League']: 
    league_string = f"{country_name}, {league_name}"
    # url = COUNTRY_CODE_MAP.get(country_name.title()) # Match title case keys
    url = LEAGUE_CODE_MAP.get(league_string.title()) # Match title case keys
    # else:
    #     url = COUNTRY_CODE_MAP.get(country_name)

    return url
    if url:
        return url
    else:
        url = get_country_emoji(country_name)
        # Optional: Log or warn about missing countries
        # print(f"Warning: No flag code found for country: {country_name}")
        return None # Return None if country not found in map

def handle_week_change():
    """Resets dependent filters when the selected week changes."""
    st.info("Week changed, resetting dependent filters...") # Optional debug message
    st.session_state.day_filter = "All Dates"
    st.session_state.country_filter = "All"
    st.session_state.league_filter = "All"
    st.session_state.rec_bet_filter = ["All"]
    # Value Bet options are static, no need to reset typically
    st.session_state.value_bet_filter = ["All"]
    # Reset confidence based on a fixed default or stored overall default
    # Avoid calculating min/max within callback as data isn't loaded yet in this exact step
    st.session_state.include_no_score = True # Reset checkbox to default state
    st.session_state.confidence_filter = st.session_state.get('global_default_confidence_range', (0, 10)) # Use a fixed default here
    # st.session_state.confidence_filter = st.session_state.get('default_confidence_range', (0, 10))
    # Crucially, also clear the selected match ID when the week changes
    if 'selected_match_id' in st.session_state:
        st.session_state.selected_match_id = None

# --- Reset Filters Function (for the reset button) ---
def reset_all_filters():
    # This can now potentially call the week change handler if you want
    # Or keep it separate if it needs slightly different logic (like resetting the week selector itself)
    handle_week_change() # Call the common reset logic
    # If you want the Reset button to also reset the week selector to latest:
    # This requires storing the key/value of the latest week option
    # if 'latest_week_key' in st.session_state:
    #     st.session_state.week_selector_key = st.session_state.latest_week_key
# def reset_all_filters():
#     """
#     Reset all filters to default values (e.g., "All") and clear selected match.
#     - Determine the default date (latest available)
#     - Recalculate valid dates here or pass the default date value if needed
#     - This logic assumes raw_dates_sorted is available or recalculated easily
#     - Let's assume we stored the default date value in session state earlier or can calculate it
#     """
#     # if 'default_date_value' in st.session_state:
#     #     st.session_state.date_filter = st.session_state.default_date_value
#     # Reset other filters to "All"
#     st.session_state.day_filter = "All Dates"
#     st.session_state.country_filter = "All"
#     st.session_state.league_filter = "All"
#     st.session_state.rec_bet_filter = ["All"] # Note: Multiselect needs a list
#     st.session_state.value_bet_filter = ["All"] # Note: Multiselect needs a list
#     st.session_state.include_no_score = True # Reset checkbox to default state
#     st.session_state.confidence_filter = st.session_state.get('default_confidence_range', (0, 10))
#     # Clear selected match if any
#     clear_selected_match()

def add_transient_message(msg_type, text):
    """Adds a message with type and timestamp to the session state list."""
    # Assign a unique ID just in case (optional but can be useful)
    msg_id = f"{msg_type}_{time.time()}_{len(st.session_state.transient_messages)}"
    st.session_state.transient_messages.append({
        'id': msg_id,
        'type': msg_type, # 'info', 'warning', 'success', 'error'
        'text': text,
        'timestamp': time.time()
    })

# This is a simplified version, adjust based on your exact prediction strings
# --- NEW Helper function to check ALL prediction types ---
def check_prediction_success(prediction, home_goals, away_goals, corners, home_team, away_team):
    """Checks if a prediction was successful based on match stats."""
    if not prediction:
        return False

    pred_input_str = prediction.strip() # Original prediction string, stripped
    pred_lower = pred_input_str.lower() # Lowercase for general checks

    # --- Determine Actual Result (if scores available) ---
    actual_result_status = None
    scores_valid = isinstance(home_goals, (int, float)) and isinstance(away_goals, (int, float))
    if scores_valid:
        if home_goals > away_goals: actual_result_status = "Home Win"
        elif away_goals > home_goals: actual_result_status = "Away Win"
        else: actual_result_status = "Draw"
    else:
        # If scores aren't valid, cannot check goal-based predictions
        pass # Continue to check potential corner predictions maybe

    # --- Split potential multiple predictions (like "A(1.42), X(4.45)") ---
    # Split by comma, then strip whitespace from each part
    potential_preds = [p.strip() for p in pred_input_str.split(',')]

    # --- Iterate through each part of the prediction string ---
    for part_pred in potential_preds:
        part_pred_lower = part_pred.lower()

        # --- Check Goal-based predictions (W/D/L, H/A/X, Over/Under) ---
        if scores_valid:
            total_goals = home_goals + away_goals
            home_team_lower = home_team.lower()
            away_team_lower = away_team.lower()

            # 1. Check H/A/X(odds) format
            hax_match = re.match(r'^([hax])\s*\(.*\)$', part_pred_lower) # Match H/A/X at the start, followed by (odds)
            if hax_match:
                bet_type = hax_match.group(1)
                if bet_type == 'h' and actual_result_status == "Home Win": return True
                if bet_type == 'a' and actual_result_status == "Away Win": return True
                if bet_type == 'x' and actual_result_status == "Draw": return True
                continue # If HAX format matched but outcome didn't, check next part_pred if any

            # 2. Check standard W/D/L keywords / team names (if not HAX format)
            if actual_result_status == "Home Win" and (re.search(r'\bhome\b', part_pred_lower) or part_pred_lower == '1' or part_pred_lower == home_team_lower):
                return True
            if actual_result_status == "Away Win" and (re.search(r'\baway\b', part_pred_lower) or part_pred_lower == '2' or part_pred_lower == away_team_lower):
                return True
            if actual_result_status == "Draw" and (re.search(r'\bdraw\b', part_pred_lower) or part_pred_lower == 'x'):
                return True

            # 3. Check Over/Under Goals (only check if WDL/HAX didn't match for this part_pred)
            # Use the original combined lower string 'pred_lower' here, as O/U shouldn't be split
            # Check only once, outside the loop, or ensure it only runs if WDL/HAX checks fail *for all parts*
            # Let's adjust: Check O/U *after* the loop if no WDL/HAX match was found across all parts.

        # --- Check Corner-based predictions ---
        # Use the original combined lower string 'pred_lower' here as well.
        # Check only once, outside the loop.

    # --- If loop finished without finding a WDL/HAX match, check O/U Goals and Corners ---

    # 4. Check Over/Under Goals (using original combined prediction string)
    if scores_valid:
        total_goals = home_goals + away_goals
        goal_match = re.search(r'(over|under)\s*(\d+(\.\d+)?)', pred_lower)
        if goal_match:
            type = goal_match.group(1)
            value = float(goal_match.group(2))
            # Optional refinement: check if 'goal' is mentioned
            # if 'goal' in pred_lower or 'corner' not in pred_lower:
            if type == "over" and total_goals > value: return True
            if type == "under" and total_goals < value: return True

    # 5. Check Corner-based predictions (using original combined prediction string)
    if isinstance(corners, (int, float)):
        corner_match = re.search(r'(over|under)\s*(\d+(\.\d+)?)\s*corner', pred_lower) # Require 'corner'
        if corner_match:
            type = corner_match.group(1)
            value = float(corner_match.group(2))
            if type == "over" and corners > value: return True
            if type == "under" and corners < value: return True

    # --- Add checks for other prediction types here (e.g., BTTS) using pred_lower ---
    # Example BTTS
    # if scores_valid:
    #    btts_occurred = home_goals > 0 and away_goals > 0
    #    if (re.search(r'\bbtts\b.*\byes\b', pred_lower) or pred_lower == 'gg') and btts_occurred: return True
    #    if (re.search(r'\bbtts\b.*\bno\b', pred_lower) or pred_lower == 'ng') and not btts_occurred: return True


    # Return False if none of the checks above were successful
    return False

def colorize_performance(performance):
		colored_performance = ""
		for char in performance:
				if char == "W":
						colored_performance += f"{emoji.emojize('🟩')}"#W{RESET}"
				elif char == "D":
						colored_performance += f"{emoji.emojize('⬜')}"#D{RESET}"🟨
				elif char == "L":
						colored_performance += f"{emoji.emojize('🟥')}"#L{RESET}"
		return colored_performance

def sort_data(df):
    # Ensure 'date' and 'time' columns exist
    if 'date' not in df.columns or 'time' not in df.columns:
        st.warning("Missing 'date' or 'time' column for sorting.")
        return df # Return unsorted if columns missing

    # Combine date and time, convert to datetime object
    date_format = "%d/%m/%Y"
    time_format = "%H:%M"
    datetime_format = f"{date_format} {time_format}"

    # Combine, coercing errors (invalid formats become NaT - Not a Time)
    df['datetime_obj'] = pd.to_datetime(
        df['date'].astype(str) + ' ' + df['time'].astype(str),
        format=datetime_format,
        errors='coerce'
    )

    # Optional: Drop rows where datetime conversion failed
    original_rows = len(df)
    df = df.dropna(subset=['datetime_obj'])
    if len(df) < original_rows:
            st.caption(f"Dropped {original_rows - len(df)} rows with invalid date/time format.")

    # --- Sorting Step ---
    df = df.sort_values(by='datetime_obj', ascending=True)

    # Optional: Drop the helper column if no longer needed
    # df = df.drop(columns=['datetime_obj'])

    return df

def display_stat_row(label, home_value, away_value, home_align='right', label_align='center', away_align='left', label_weight='bold'):
    """Displays a single row, handling None values by showing '--'."""
    col1, col2, col3 = st.columns([2, 3, 2]) # Adjust ratios as needed

    # Explicitly handle None before creating the final string
    home_display = str(home_value) if home_value is not None else '--'
    away_display = str(away_value) if away_value is not None else '--'

    # Use the display strings in markdown
    with col1:
        st.markdown(f"<div style='text-align: {home_align};'>{home_display}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='text-align: {label_align}; font-weight: {label_weight};'>{label}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='text-align: {away_align};'>{away_display}</div>", unsafe_allow_html=True)

# --- Streamlit App ---
# st.set_page_config(layout="wide")

# Initialize session state
# if 'transient_messages' not in st.session_state:
#     st.session_state.transient_messages = []
if 'day_filter' not in st.session_state:
    st.session_state.day_filter = "All Dates" # Default value
if 'country_filter' not in st.session_state:
    st.session_state.country_filter = "All"
if 'league_filter' not in st.session_state:
    st.session_state.league_filter = "All"
if 'rec_bet_filter' not in st.session_state:
    st.session_state.rec_bet_filter = "All"
if 'value_bet_filter' not in st.session_state:
    st.session_state.value_bet_filter = "All"
if 'confidence_filter' not in st.session_state:
    # st.session_state.confidence_filter = (0, 10) # Initial default range
    st.session_state.global_default_confidence_range = (0, 10) # Initial default range
if 'include_no_score' not in st.session_state:
    st.session_state.include_no_score = True # Default to including matches without scores

# --- Load Data Based on Configuration ---
# all_matches_raw = []
# if DATA_SOURCE == 'csv':
#     all_matches_raw = load_data_from_csv(CSV_FILE_PATH)
# elif DATA_SOURCE == 'postgres':
#     all_matches_raw = load_data_from_postgres(DB_PARAMS)
# elif DATA_SOURCE == 'text':
#     all_matches_raw = load_data_from_text(TEXT_FILE_PATH)
# else:
#     st.error(f"Invalid DATA_SOURCE configured: {DATA_SOURCE}. Choose 'csv', 'postgres', or 'text'.")

# Basic check if data loading failed
# if not all_matches_raw:
#     st.error("Data loading failed. Please check the configuration and data source.")
#     st.stop() # Stop execution if no data

# --- !!! Display Transient Messages Area !!! ---
message_placeholder = st.empty() # Create an empty placeholder
display_messages: list[dict] = []
current_time = time.time()

# Filter out expired messages and prepare list of messages to show
st.session_state.transient_messages = [
    msg for msg in st.session_state.transient_messages
    if (current_time - msg['timestamp']) < MESSAGE_TIMEOUT_SECONDS
]

# Create a container within the placeholder to hold multiple messages if needed
with message_placeholder.container():
    for msg in st.session_state.transient_messages:
        if msg['type'] == 'info':
            st.info(msg['text'], icon="ℹ️")
        elif msg['type'] == 'warning':
            st.warning(msg['text'], icon="⚠️")
        elif msg['type'] == 'error':
            st.error(msg['text'], icon="🚨")
        elif msg['type'] == 'success':
            st.success(msg['text'], icon="✅")
        # Add more types if needed

# --- Sidebar Filters ---
st.sidebar.title("Filters")
# --- !!! MODIFIED Weekly File Selection !!! ---

# 1. Find files matching the numeric pattern (e.g., "43.csv")
#    Using "[0-9]*.csv" ensures we only grab files starting with digits.
raw_files = glob.glob(os.path.join(WEEKLY_PREDICTIONS_DIR, "[0-9]*.csv"))

# 2. Extract week number and path, handling potential errors
week_path_pairs = []
for f_path in raw_files:
    basename = os.path.basename(f_path)
    # Use regex to extract digits before ".csv"
    match = re.match(r"(\d+)\.csv$", basename)
    if match:
        try:
            week_num = int(match.group(1))
            week_path_pairs.append((week_num, f_path))
        except ValueError:
            # Skip if the extracted part isn't a valid integer
            st.sidebar.caption(f"Skipping non-integer file: {basename}")
    # else: File didn't match the pattern "number.csv", silently ignore

# 3. Sort based on week number (descending for latest first)
week_path_pairs.sort(key=lambda pair: pair[0], reverse=True)

# 4. Create options dictionary {display_name: full_path}
weekly_file_options = {f"Week {week_num}": path for week_num, path in week_path_pairs}

# 5. Create the selectbox
selected_week_display_name = None # Initialize
if not weekly_file_options:
    st.sidebar.warning("No weekly match files (e.g., 43.csv) found.")
    # Handle case where no files are found - perhaps disable subsequent actions
else:
    selected_week_display_name = st.sidebar.selectbox(
        "Select Match Week:",
        options=list(weekly_file_options.keys()), # Display "Week 43", "Week 42", etc.
        key='week_selector_key', # Assign a key to the selector itself
        on_change=handle_week_change # *** Attach the callback ***
    )

# --- End Modified Weekly File Selection ---

# --- Load Data for Selected Week ---
# Load data only if a valid week was selected
weekly_df = pd.DataFrame() # Default to empty DataFrame
selected_file_path = None

# Use the session state key which reflects the *current* selection after any change
current_selected_week_key = st.session_state.get('week_selector_key') # Get value using key

if current_selected_week_key and current_selected_week_key in weekly_file_options:
    selected_file_path = weekly_file_options[current_selected_week_key]
    weekly_df_raw = load_weekly_data(selected_file_path)
    weekly_df = sort_data(weekly_df_raw) # Sort the DataFrame by date/time

# if selected_week_display_name:
#     selected_file_path = weekly_file_options[selected_week_display_name]
#     weekly_df = load_weekly_data(selected_file_path) # Function is cached
        
# --- !!! NEW Day Filter based on Loaded Data !!! ---
date_filter_options = ["All Dates"] # Start with 'All Dates'
valid_dates_in_week = []
date_format = "%d/%m/%Y" # Define your expected date format

if not weekly_df.empty and 'date' in weekly_df.columns:
    # Attempt to parse and validate dates
    unique_dates_str = weekly_df['date'].dropna().unique()
    for d_str in unique_dates_str:
        try:
            # Validate format and convert to datetime object for sorting
            date_obj = datetime.strptime(str(d_str), date_format)
            valid_dates_in_week.append(date_obj)
        except (ValueError, TypeError):
            # st.sidebar.caption(f"Ignoring invalid date format: {d_str}")
            continue # Skip invalid formats

    # Sort dates chronologically and format back to string for display
    if valid_dates_in_week:
        valid_dates_in_week.sort()
        date_filter_options.extend([d.strftime(date_format) for d in valid_dates_in_week])

# Create the Day filter selectbox
# Ensure the current session state value exists in the options
current_day_selection = st.session_state.day_filter
if current_day_selection not in date_filter_options:
    st.session_state.day_filter = "All Dates" # Reset if invalid

st.sidebar.selectbox("Date:", options=date_filter_options, key='day_filter') # Use session state key 

# Country and League filters (Keep "All" option)
filter_countries = ["All"]
if not weekly_df.empty and 'country' in weekly_df.columns:
    filter_countries = ["All"] + sorted(weekly_df['country'].dropna().unique())
st.sidebar.selectbox("Country:", options=filter_countries, key='country_filter')

# Example: League Filter
filter_leagues = ["All"]
if not weekly_df.empty and 'league_name' in weekly_df.columns:
    filter_leagues = ["All"] + sorted(weekly_df['league_name'].dropna().unique())
st.sidebar.selectbox("League:", options=filter_leagues, key='league_filter')

# Extract Recommended Bet options
rec_bet_options = ["All"]
if not weekly_df.empty and 'rec_prediction' in weekly_df.columns:
    rec_bet_options = ["All"] + sorted(weekly_df['rec_prediction'].dropna().unique())
# Validate current selection (for multiselect)
current_rec_bet_selection = st.session_state.rec_bet_filter
# Check if all selected items are still valid options OR if the selection is empty (which we also want to reset)
# Validate current selection (for multiselect)
current_rec_bet_selection = st.session_state.rec_bet_filter
is_rec_bet_valid = all(item in rec_bet_options for item in current_rec_bet_selection)
if not is_rec_bet_valid:
    # !!! This is the crucial fix !!!
    st.session_state.rec_bet_filter = ["All"] # Reset to default if invalid

# Now create the widget
st.sidebar.multiselect("Recommended Bet:", options=rec_bet_options, key='rec_bet_filter')

# Value Bet Filter (Hardcoded options H/X/A)
value_bet_filter_options = ["All", "H", "X", "A"]
st.sidebar.multiselect("Value Bet (H/X/A):", options=value_bet_filter_options, key='value_bet_filter')
# --- Now define other filters based *on the loaded weekly_df* ---
# Example: Calculate confidence range based on the selected week's data

min_conf = 0
max_conf = 10 # Default scale
if not weekly_df.empty and 'confidence_score' in weekly_df.columns:
    valid_scores = pd.to_numeric(weekly_df['confidence_score'], errors='coerce').dropna()
    if not valid_scores.empty:
        min_conf = int(valid_scores.min())
        max_conf = int(valid_scores.max())
    min_conf = max(0, min_conf)
    max_conf = max(min_conf, max_conf) # Ensure max >= min

# Initialize/Adjust session state for confidence slider based on loaded data range
if 'confidence_filter' not in st.session_state:
    st.session_state.confidence_filter = (min_conf, max_conf)
else: # Ensure current state value is within the actual data range for this week
    current_conf_range = st.session_state.confidence_filter
    st.session_state.confidence_filter = (
        max(min_conf, current_conf_range[0]),
        min(max_conf, current_conf_range[1])
    )
    if st.session_state.confidence_filter[0] > st.session_state.confidence_filter[1]:
        st.session_state.confidence_filter = (min_conf, max_conf)

st.sidebar.slider(
    "Confidence Score Range:",
    min_value=min_conf,
    max_value=max_conf,
    value=st.session_state.confidence_filter,
    key='confidence_filter'
)

# --- !!! NEW Checkbox !!! ---
st.sidebar.checkbox(
    "Include matches with no score",
    key='include_no_score' # Link to session state
)
# --- End New Checkbox ---

# --- Apply filters ---
selected_day = st.session_state.day_filter
selected_country = st.session_state.country_filter
selected_league = st.session_state.league_filter
selected_rec_bets = st.session_state.rec_bet_filter
selected_value_bets = st.session_state.value_bet_filter
selected_confidence_range = st.session_state.confidence_filter
include_no_score_flag = st.session_state.include_no_score # Get checkbox state

# Start with the loaded weekly dataframe
filtered_df = weekly_df.copy()

# Apply filters sequentially (if data exists)
if not filtered_df.empty:
    if selected_day != "All Dates":
        # Ensure consistent format comparison if dates were loaded as strings
        filtered_df = filtered_df[filtered_df['date'] == str(selected_day)] # Filter based on the selected date string
    
    if selected_country != "All":
        filtered_df = filtered_df[filtered_df['country'] == selected_country]
    if selected_league != "All":
        filtered_df = filtered_df[filtered_df['league_name'] == selected_league]
    if "All" not in selected_rec_bets:
        filtered_df = filtered_df[filtered_df['rec_prediction'].isin(selected_rec_bets)]

    # --- !!! MODIFIED Value Bet Filter Logic !!! ---
    if "All" not in selected_value_bets:
        # Create a boolean mask based on the first character check
        # 1. Convert 'value_bets' column to string type
        # 2. Access the first character using .str[0]
        # 3. Convert to uppercase using .str.upper()
        # 4. Check if this character is in the user's selection ('H', 'X', or 'A') using .isin()
        # 5. Handle potential errors or missing values (e.g., empty strings) by filling NaN with False
        value_mask = filtered_df['value_bets'].astype(str).str[0].str.upper().isin(selected_value_bets).fillna(False)
        filtered_df = filtered_df[value_mask]
    # else: value is None, empty string, not a string, or 'All' wasn't selected -> keep value_bet_match = False

    # Confidence Score Filter
    # Convert score to numeric, handle errors, then apply range
    # Apply Confidence Score Filter (Include rows with NaN scores)
    # --- !!! MODIFIED Confidence Score Filter Logic !!! ---
    # Convert score column to numeric, coercing errors to NaN
    scores_numeric = pd.to_numeric(filtered_df['confidence_score'], errors='coerce')

    # Create mask for rows that are WITHIN the selected score range
    range_mask = (scores_numeric >= selected_confidence_range[0]) & \
                (scores_numeric <= selected_confidence_range[1])

    # Create mask for rows that HAVE NO score (are NaN after coercion)
    no_score_mask = scores_numeric.isna()

    # Combine the masks based on the checkbox state
    if include_no_score_flag:
        # Keep rows that are IN range OR have NO score
        final_conf_mask = range_mask | no_score_mask
    else:
        # Keep only rows that are IN range (implicitly excludes no score rows)
        final_conf_mask = range_mask

    # Apply the final combined mask
    filtered_df = filtered_df[final_conf_mask]
    # --- End Modified Confidence Filter Logic ---
        
    # st.sidebar.metric("Rows After Filtering (filtered_df)", filtered_df.shape[0] if not filtered_df.empty else 0)        
# --- Main Page Content ---
st.title("Match Analysis")#⚽ Match 

# Use 'selected_week_display_name' for subheader
if selected_week_display_name:
    st.subheader(f"{selected_week_display_name} - {selected_day}")
else:
    st.subheader("Please select a week")

# Convert filtered DataFrame back to list of dicts for existing display logic
# Or adapt display logic to use the filtered_df directly
filtered_matches_list = []
if not filtered_df.empty:
    # Replace NaN with None for compatibility if needed by display code
    filtered_matches_list = filtered_df.astype(object).where(pd.notnull(filtered_df), None).to_dict('records')


# Now use filtered_matches_list in your existing overview/detail display logic
selected_match_id = st.session_state.get('selected_match_id')
selected_match_data = None

# --- Debugging Start ---
# st.write("--- Debug Match Finding ---")
# st.write(f"Weekly Df count: {len(weekly_df)}")
# st.write(f"Session State selected_match_id: {selected_match_id} (Type: {type(selected_match_id)})")
# st.write(f"Number of items in filtered_matches_list: {len(filtered_matches_list)}")
# if filtered_matches_list:
#     ids_in_list = [m.get('match_id') for m in filtered_matches_list[:10]] # Show first 10 IDs
#     st.write(f"First IDs in current filtered list: {ids_in_list}")
# # --- Debugging End ---
match_found_flag = False # Flag to check if loop found it
# --- Handle Cases After Loop ---
if selected_match_id is not None and not match_found_flag:
    # An ID was selected, but it wasn't found in the *current* filtered list
    # st.warning(f"Match details for ID {selected_match_id} are not visible with the current filters. Displaying overview.", icon="⚠️")
    # Decide if you want to automatically clear the selection when filters hide the match
    # Option 1: Keep selection, user might change filters back
    # Option 2: Clear selection automatically
    # clear_selected_match()
    selected_match_data = None # Ensure it's None if not found
# Find selected match data (search in the filtered list)
if selected_match_id:
    for match in filtered_matches_list:
        if isinstance(match, dict) and match.get('match_id') == selected_match_id:
            selected_match_data = match
            break
    # ... (logic if selected match not found in filtered list) ...

# --- Display Overview or Details using filtered_matches_list ---
if not selected_match_data:
    # Overview Display
    overview_header_cols = st.columns([3, 1])
    with overview_header_cols[0]:
        st.write("") # Placeholder instead of header, already have subheader
    with overview_header_cols[1]:
        st.button("Reset Filters", on_click=reset_all_filters, use_container_width=True) # Keep reset button

    if not filtered_matches_list:
        st.info("No matches found matching your filter criteria for this week.")
    else:
        # --- Display matches grouped by league using filtered_matches_list ---
        matches_by_league = defaultdict(list)
        for match in filtered_matches_list:
            if isinstance(match, dict):
                league_key = (match.get('country', 'Unknown Country'), match.get('league_name', 'Unknown League'))
                matches_by_league[league_key].append(match)

        if not matches_by_league:
            st.info("No matches found matching filter criteria.") # Should be caught earlier
        else:
            sorted_leagues = sorted(matches_by_league.keys())
            for league_key in sorted_leagues:
                country, league_name = league_key
                league_matches = matches_by_league[league_key]
                # Display League Header with country emoji and league name in one row
                col1, col2 = st.columns([0.1, 4])  # Adjust column widths as needed
                with col1:
                    flag_url_from_data = None
                    if league_matches: # Check if there are matches in this league group
                        first_match_in_league = league_matches[0]
                        if isinstance(first_match_in_league, dict):
                            # --- Adjust this key name if needed ---
                            flag_url_from_data = first_match_in_league.get('country_logo')
                            # --------------------------------------

                    # if flag_url_from_data:
                    #     st.image(flag_url_from_data, width=25) # Display image if URL found
                    # else:
                        # Optional: Placeholder if no flag URL found in data or no matches
                        # This might happen if the key is missing or the league_matches list is empty
                        # if league_name in ['UEFA Champions League', 'UEFA Europa Conference League', 'UEFA Europa League', 'AFC Champions League']:
                        #     flag_url = get_flag_url(league_name)
                        #     if flag_url:
                        #         st.image(flag_url, width=25)

                    flag_url = get_flag_url(country,league_name) # Get emoji for country
                    if flag_url:
                        st.image(flag_url, width=25)
                with col2:
                    st.markdown(f"##### {country} - {league_name}")  # League name

                # Display matches within the league
                for match in league_matches:
                    # --- Get match data ---
                    home_goals = match.get('HomeGoals', '?')
                    away_goals = match.get('AwayGoals', '?')
                    corners = match.get('Corners') # Get corners count
                    home_team = match.get('home_team', '?')
                    away_team = match.get('away_team', '?')
                    rec_pred = match.get('rec_prediction')
                    value_bet = match.get('value_bets')
                    match_time = match.get('time', '--')
                    confidence_score = match.get('confidence_score')
                    
                    # --- Determine Result Status ---
                    result_status = None
                    scores_available = isinstance(home_goals, (int, float)) and isinstance(away_goals, (int, float)) # More specific check

                    if scores_available:
                        if home_goals > away_goals:
                            result_status = "Home Win"
                        elif away_goals > home_goals:
                            result_status = "Away Win"
                        else:
                            result_status = "Draw"
                    
                    with st.container():
                        col0,col1, col2,col3,col4,col5,col6,col7 = st.columns(
                            [0.25,0.2,0.7,0.3,0.3,0.3,1,1])
                        
                        with col0:
                            st.markdown(f"**{match_time}**", unsafe_allow_html=True)

                            if confidence_score and confidence_score >= 7:
                                st.markdown("⭐", unsafe_allow_html=True)

                        with col1:
                            home_logo = match.get('home_team_logo', None) or "https://placehold.co/25x25/000000/FFF"
                            away_logo = match.get('away_team_logo', None) or "https://placehold.co/25x25/000000/FFF"
                            st.image(home_logo, width=25)
                            st.image(away_logo, width=25)

                        with col2:
                            home_rank = match.get('home_rank', None) or "--"
                            away_rank = match.get('away_rank', None) or "--"
                            st.markdown(f"**{home_team} ({home_rank})**", unsafe_allow_html=True)
                            st.markdown(f"**{away_team} ({away_rank})**", unsafe_allow_html=True)

                        with col3:
                            # Apply bold styling to the winning score
                            # Display Score with Highlighting
                            if scores_available:
                                home_score_display = f"{int(home_goals)}"
                                away_score_display = f"{int(away_goals)}"

                                # Apply bold styling to the winning score
                                if result_status == "Home Win":
                                    home_score_display = f"**{int(home_goals)}**"
                                    st.markdown(f"{home_score_display}", unsafe_allow_html=True)
                                    st.caption(f"{away_score_display}", unsafe_allow_html=True)
                                elif result_status == "Away Win":
                                    away_score_display = f"**{int(away_goals)}**"
                                    st.caption(f"{home_score_display}", unsafe_allow_html=True)
                                    st.markdown(f"{away_score_display}", unsafe_allow_html=True)
                                
                        with col4:
                            # --- NEW: Display Stats if available ---
                            corners = (match.get('Corners'))

                            if corners is not None:
                                st.markdown(f"🚩 {int(corners)}", unsafe_allow_html=True)

                        with col5:
                            yellow_cards = (match.get('YellowCards'))
                            red_cards = (match.get('RedCards'))
                            if yellow_cards is not None:
                                # Using a unicode character for yellow card
                                st.markdown(f"🟨 {int(yellow_cards)}", unsafe_allow_html=True)
                            if red_cards is not None:
                                # Using a unicode character for red card
                                st.markdown(f"🟥 {int(red_cards)}", unsafe_allow_html=True)

                            # if stats_display:
                            #     # Join the stats with a separator and display
                            #     st.markdown(f"{' '.join(stats_display)}")
                        
                        with col6:
                            confidence_text = f" ({confidence_score}/10)" if confidence_score is not None else ""

                            # --- Check and Display Best Bet ---
                            # Pass necessary stats to the check function
                            rec_pred_won = check_prediction_success(rec_pred, home_goals, away_goals, corners, home_team, away_team)
                            if rec_pred:
                                pred_display = f"{rec_pred}{confidence_text}"
                                if rec_pred_won:
                                    pred_display = f"<span style='color:green; font-weight:bold;'>{rec_pred}{confidence_text} ✅</span>" # Added checkmark
                                st.caption(f"**Best Bet:** {pred_display}", unsafe_allow_html=True)
                            else:
                                st.caption("")

                            # --- Check and Display Value Tip ---
                            # Pass necessary stats to the check function
                            value_bet_won = check_prediction_success(value_bet, home_goals, away_goals, corners, home_team, away_team)
                            if value_bet:
                                value_display = f"{value_bet}"
                                if value_bet_won:
                                    value_display = f"<span style='color:green; font-weight:bold;'>{value_bet} ✅</span>" # Added checkmark
                                st.caption(f"**Value Tip:** {value_display}", unsafe_allow_html=True)
                            else:
                                st.caption("")

                            # st.markdown(f"**Best Bet:** {rec_pred}{confidence_text}", unsafe_allow_html=True)
                            # st.markdown(f"**Value Tip:** {value_bet}", unsafe_allow_html=True)

                        with col7:
                            st.button("View Details", key=match['match_id'], on_click=set_selected_match, args=(match['match_id'],), use_container_width=True)
                            # st.text("View Details")
                
                st.markdown("---", unsafe_allow_html=True) # Divider between leagues

    # else:
    #     # Handles case where selected_date is None (no valid dates found)
    #     st.info("Please select filters to view matches.")

else:
    # Display Dashboard
    st.sidebar.divider()
    st.sidebar.button("⬅️ Back to Overview", on_click=clear_selected_match)

    # st.text(f"📅 {selected_match_data.get('date','--')} 🕛 {selected_match_data.get('time','--')}")
    # st.text(f"🌍 {selected_match_data.get('country','--')} - {selected_match_data.get('league_name','--')}")
    # st.header(f"{selected_match_data.get('home_team','?')} vs {selected_match_data.get('away_team','?')}")
    # match_cols1,match_cols2,match_cols3, match_cols4, match_cols5 = st.columns([1,2, 1, 2, 1])
    # col1, match_cols2 = st.columns([1, 4])
    # Arrange the columns as per the requirement
    # Define columns - adjust ratios if needed
    country = selected_match_data.get('country','--')
    league_name = selected_match_data.get('league_name','--')
    home_goals = selected_match_data.get('HomeGoals', '?')
    away_goals = selected_match_data.get('AwayGoals', '?')
    corners = selected_match_data.get('Corners')
    yellow_cards = selected_match_data.get('YellowCards')
    red_cards = selected_match_data.get('RedCards')

    scores_available = isinstance(home_goals, (int, float)) and isinstance(away_goals, (int, float)) # More 

    home_score_display = ""
    away_score_display = ""
    stats = ""
    
    if scores_available:
        home_score_display = f"{int(home_goals)}"
        away_score_display = f"{int(away_goals)}"

    stats_display = []
    if corners is not None:
        stats_display.append(f"🚩 {int(corners)}")
    if yellow_cards is not None:
        # Using a unicode character for yellow card
        stats_display.append(f"🟨 {int(yellow_cards)}")
    if red_cards is not None:
        # Using a unicode character for red card
        stats_display.append(f"🟥 {int(red_cards)}")

    if stats_display:
        # Join the stats with a separator and display
        stats = f"{' '.join(stats_display)}"
        
    home_logo = selected_match_data.get('home_team_logo', None) or "https://placehold.co/100x100/000000/FFF"
    away_logo = selected_match_data.get('away_team_logo', None) or "https://placehold.co/100x100/000000/FFF"

    
    match_cols0,match_cols1, match_cols2, match_cols3, match_cols4, match_cols5 , match_cols6 = st.columns(
        [0.5,1,0.5,2,0.5,1,0.5] # Example ratios: Adjust based on content width
    )

    with match_cols0:
        # --- Column 1: Image, effectively Right-aligned by pushing content ---
        # Wrap image in a div with right alignment. Set a fixed width for the image.

        st.markdown(
            f"""
            <div style="text-align: right;">
                <img src="{home_logo}" width="100">
            </div>

            """,
            unsafe_allow_html=True
        )
        

        #
        # Note: True right alignment might need more complex CSS depending on column behavior,
        # but placing the image in the right-most column often suffices visually.
        # If using a fixed width smaller than the column, text-align: right works.
    
    with match_cols1:
        # --- Column 2: Text, Left-aligned (Default for markdown) ---
        # st.markdown(f"{selected_match_data.get('home_team', '--')}")
        # st.markdown(f"Rank: {selected_match_data.get('home_rank', '--')}")
        # st.markdown(f"PPG: {selected_match_data.get('ppg_h', '--')}")
        # No special alignment needed here, default is left.'
        
        st.markdown(
            f"""
            <div style="text-align: left;">
                <span style="font-weight: bold; font-size: 1.5em; display: block; margin-bottom: 0.2em;">{selected_match_data.get('home_team', '--')}</span>
                <span style="font-weight: bold; font-size: 1.2em; display: block; margin-bottom: 0.2em;">{selected_match_data.get('home_rank', '--')}</span>
                PPG: {selected_match_data.get('ppg_h', '--')}
            </div>
            """,
            unsafe_allow_html=True
        )

    with match_cols2:
        # st.markdown(f"# {home_score_display}", unsafe_allow_html=True)
        st.markdown(
            f"""
            
            <div style="text-align: center;">
                <span style="font-weight: bold; font-size: 3em; display: block; margin-top: 0.2em;margin-bottom: 0.2em;">{home_score_display}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with match_cols3:
        # --- Column 3: Text, Center-aligned ---
        flag_url = get_flag_url(country, league_name) # Get emoji for country

        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="{flag_url}" width="50">
            </div>
            <div style="text-align: center;">
                {country} - {selected_match_data.get('league_name','--')}
                </div>
            <div style="text-align: center;">
                {selected_match_data.get('date', '--')} | {selected_match_data.get('time', '--')}
            </div>
            <br>
            <div style="text-align: center;">
                {stats}
            </div>
            """,
            unsafe_allow_html=True
        )
        # --- Inject CSS for Centering Expander Label ---
        # st.markdown("""
        # <style>
        #     [data-testid="stExpander"] summary p { /* Common selector for the text */
        #         font-weight: bold; 
        #         width: 100%; 
        #         text-align: right;
        #     }
        #     /* Fallback selector if the above doesn't work */
        #     [data-testid="stExpander"] summary div[data-testid="stExpanderHeader"] {
        #         width: 100%;
        #         text-align: right;
        #     }

        # </style>
        # """, unsafe_allow_html=True)
        
        with st.expander("📊 Match Report", expanded=False):
            # Expected Goals (xG) - Needs specific formatting
            home_xg = selected_match_data.get('HomeXGResults')
            away_xg = selected_match_data.get('AwayXGResults')
            # Format only if it's a number (float or int), otherwise pass None to the helper
            home_xg_display = f"{home_xg:.2f}" if isinstance(home_xg, (int, float)) else home_xg
            away_xg_display = f"{away_xg:.2f}" if isinstance(away_xg, (int, float)) else away_xg
            display_stat_row("Expected Goals (xG)", home_xg_display, away_xg_display)

            # Shots - No special format, just handle None
            home_shots = selected_match_data.get('HomeShotsResults')
            away_shots = selected_match_data.get('AwayShotsResults')
            display_stat_row("Shots", home_shots, away_shots) # Helper handles None -> '--'

            # Shots on Target - No special format
            home_sot = selected_match_data.get('HomeSOTResults')
            away_sot = selected_match_data.get('AwaySOTResults')
            display_stat_row("Shots on Target", home_sot, away_sot)

            # Possession (%) - Needs '%' sign added
            home_poss = selected_match_data.get('HomeBallPossessionResults')
            away_poss = selected_match_data.get('AwayBallPossessionResults')
            # Add '%' only if value is not None
            home_poss_display = f"{home_poss}%" if home_poss is not None else home_poss
            away_poss_display = f"{away_poss}%" if away_poss is not None else away_poss
            display_stat_row("Possession (%)", home_poss_display, away_poss_display)

            # Corners - No special format
            home_cor = selected_match_data.get('HomeCornersResults')
            away_cor = selected_match_data.get('AwayCornersResults')
            display_stat_row("Corners", home_cor, away_cor)

            # Fouls Committed - No special format
            home_fouls = selected_match_data.get('HomeFoulsResults')
            away_fouls = selected_match_data.get('AwayFoulsResults')
            display_stat_row("Fouls Committed", home_fouls, away_fouls)

            # Goalkeeper Saves - No special format
            home_saves = selected_match_data.get('HomeGoalKeeperSavesResults')
            away_saves = selected_match_data.get('AwayGoalKeeperSavesResults')
            display_stat_row("Goalkeeper Saves", home_saves, away_saves)

            # Offsides - No special format
            home_offs = selected_match_data.get('HomeOffsidesResults')
            away_offs = selected_match_data.get('AwayOffsidesResults')
            display_stat_row("Offsides", home_offs, away_offs)

            # Yellow Cards - No special format
            home_yellows = selected_match_data.get('HomeYellowsResults')
            away_yellows = selected_match_data.get('AwayYellowsResults')
            display_stat_row("Yellow Cards", home_yellows, away_yellows)

            # Red Cards - No special format
            home_reds = selected_match_data.get('HomeRedsResults')
            away_reds = selected_match_data.get('AwayRedsResults')
            display_stat_row("Red Cards", home_reds, away_reds)

    with match_cols4:
        # --- Column 6: Score Display ---
        # st.markdown(f"# {away_score_display}", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="text-align: center;">
                <span style="font-weight: bold; font-size: 3em; display: block; margin-bottom: 0.2em;">{away_score_display}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with match_cols5:
        # --- Column 4: Text, Right-aligned ---
        st.markdown(
            f"""
            <div style="text-align: right;">
                <span style="font-weight: bold; font-size: 1.5em; display: block; margin-bottom: 0.2em;">{selected_match_data.get('away_team', '--')}</span>
                <span style="font-weight: bold; font-size: 1.2em; display: block; margin-bottom: 0.2em;">{selected_match_data.get('away_rank', '--')}</span>
                PPG: {selected_match_data.get('ppg_a', '--')}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with match_cols6:
        # --- Column 5: Image, Left-aligned ---
        # Default alignment for image is left. Ensure fixed width.
        st.markdown(
            f"""
            <div style="text-align: left;">
                <img src="{away_logo}" width="100">
            </div>
            """,
            unsafe_allow_html=True
        )
    
        
        # st.image(selected_match_data.get('away_logo_url', ''), width=60)
        # Using st.image directly also works here as left is default. HTML wrapper is for consistency. actual path or URL
    
    st.markdown("---")
    confidence_score = selected_match_data.get('confidence_score', '--')
    confidence_text = f" ({confidence_score}/10)" if confidence_score is not None else ""
    home_goals = selected_match_data.get('HomeGoals', '?')
    away_goals = selected_match_data.get('AwayGoals', '?')
    corners = selected_match_data.get('Corners') # Get corners count
    home_team = selected_match_data.get('home_team', '?')
    away_team = selected_match_data.get('away_team', '?')
    rec_pred = selected_match_data.get('rec_prediction')
    value_bet = selected_match_data.get('value_bets')
    match_time = selected_match_data.get('time', '--')
    
    Last5_HomeBothTeamsToScore = selected_match_data.get('Last5_HomeBothTeamsToScore', '--')*100
    Last5HomeAvergeTotalShots = selected_match_data.get('Last5HomeAvergeTotalShots') or 0                   
    Last5HomeAvergeTotalShotsOnGoal = selected_match_data.get('Last5HomeAvergeTotalShotsOnGoal') or 0            
    Last5HomeAvergeTotalFouls = selected_match_data.get('Last5HomeAvergeTotalFouls') or 0
    Last5HomeAvergeTotalcorners  = selected_match_data.get('Last5HomeAvergeTotalcorners') or 0                
    Last5HomeAvergeTotalYellowCards  = selected_match_data.get('Last5HomeAvergeTotalYellowCards') or 0
    # Last5HomeAvergeTotalRedCards  = selected_match_data.get('Last5HomeAvergeTotalRedCards') or 0  

    Last5_AwayBothTeamsToScore = selected_match_data.get('Last5_AwayBothTeamsToScore', '--') *100               
    Last5AwayAvergeTotalShots = selected_match_data.get('Last5AwayAvergeTotalShots') or 0                  
    Last5AwayAvergeTotalShotsOnGoal = selected_match_data.get('Last5AwayAvergeTotalShotsOnGoal') or 0            
    Last5AwayAvergeTotalFouls = selected_match_data.get('Last5AwayAvergeTotalFouls') or 0 
    Last5AwayAvergeTotalcorners  = selected_match_data.get('Last5AwayAvergeTotalcorners') or 0                
    Last5AwayAvergeTotalYellowCards  = selected_match_data.get('Last5AwayAvergeTotalYellowCards') or 0            
    # Last5AwayAvergeTotalRedCards  = selected_match_data.get('Last5AwayAvergeTotalRedCards') or 0            

    l5_home_for_league_avg_shots = selected_match_data.get('l5_home_for_league_avg_shots') or 0               
    l5_home_for_league_avg_sot = selected_match_data.get('l5_home_for_league_avg_sot') or 0                 
    l5_home_for_league_avg_fouls = selected_match_data.get('l5_home_for_league_avg_fouls') or 0               
    l5_home_for_league_avg_corners = selected_match_data.get('l5_home_for_league_avg_corners') or 0             
    l5_home_for_league_avg_yellow_cards = selected_match_data.get('l5_home_for_league_avg_yellow_cards') or 0        
    l5_home_for_league_avg_red_cards = selected_match_data.get('l5_home_for_league_avg_red_cards') or 0

    l5_home_against_league_avg_shots = selected_match_data.get('l5_home_against_league_avg_shots') or 0           
    l5_home_against_league_avg_sot = selected_match_data.get('l5_home_against_league_avg_sot') or 0             
    l5_home_against_league_avg_corners = selected_match_data.get('l5_home_against_league_avg_corners') or 0         
    l5_home_against_league_avg_fouls = selected_match_data.get('l5_home_against_league_avg_fouls') or 0           
    l5_home_against_league_avg_yellow_cards = selected_match_data.get('l5_home_against_league_avg_yellow_cards') or 0    
    l5_home_against_league_avg_red_cards = selected_match_data.get('l5_home_against_league_avg_red_cards') or 0
    
    l5_away_for_league_avg_shots = selected_match_data.get('l5_away_for_league_avg_shots') or 0               
    l5_away_for_league_avg_sot = selected_match_data.get('l5_away_for_league_avg_sot') or 0                 
    l5_away_for_league_avg_fouls = selected_match_data.get('l5_away_for_league_avg_fouls') or 0               
    l5_away_for_league_avg_corners = selected_match_data.get('l5_away_for_league_avg_corners') or 0             
    l5_away_for_league_avg_yellow_cards = selected_match_data.get('l5_away_for_league_avg_yellow_cards') or 0        
    l5_away_for_league_avg_red_cards = selected_match_data.get('l5_away_for_league_avg_red_cards') or 0

    l5_away_against_league_avg_shots = selected_match_data.get('l5_away_against_league_avg_shots') or 0           
    l5_away_against_league_avg_sot = selected_match_data.get('l5_away_against_league_avg_sot') or 0             
    l5_away_against_league_avg_corners = selected_match_data.get('l5_away_against_league_avg_corners') or 0         
    l5_away_against_league_avg_fouls = selected_match_data.get('l5_away_against_league_avg_fouls') or 0           
    l5_away_against_league_avg_yellow_cards = selected_match_data.get('l5_away_against_league_avg_yellow_cards') or 0    
    l5_away_against_league_avg_red_cards = selected_match_data.get('l5_away_against_league_avg_red_cards') or 0

    HeadToHeadHomeXG = selected_match_data.get('HeadToHeadHomeXG') or 0
    HeadToHeadAwayXG = selected_match_data.get('HeadToHeadAwayXG') or 0 
    HeadToHeadHomeTotalShots = selected_match_data.get('HeadToHeadHomeTotalShots') or 0
    HeadToHeadHomeShotsOnTarget = selected_match_data.get('HeadToHeadHomeShotsOnTarget') or 0
    HeadToHeadHomeFouls = selected_match_data.get('HeadToHeadHomeFouls') or 0
    HeadToHeadHomeCorners = selected_match_data.get('HeadToHeadHomeCorners') or 0
    HeadToHeadHomeYellowCards = selected_match_data.get('HeadToHeadHomeYellowCards') or 0
    HeadToHeadHomeRedCards = selected_match_data.get('HeadToHeadHomeRedCards') or 0
    
    HeadToHeadAwayTotalShots = selected_match_data.get('HeadToHeadAwayTotalShots') or 0
    HeadToHeadAwayShotsOnTarget = selected_match_data.get('HeadToHeadAwayShotsOnTarget') or 0
    HeadToHeadAwayFouls = selected_match_data.get('HeadToHeadAwayFouls') or 0
    HeadToHeadAwayCorners = selected_match_data.get('HeadToHeadAwayCorners') or 0
    HeadToHeadAwayYellowCards = selected_match_data.get('HeadToHeadAwayYellowCards') or 0
    HeadToHeadAwayRedCards = selected_match_data.get('HeadToHeadAwayRedCards') or 0

    Last5HomeOver7Corners = (selected_match_data.get('Last5HomeOver7Corners') or 0)*100
    Last5HomeOver8Corners = (selected_match_data.get('Last5HomeOver8Corners') or 0)*100
    Last5HomeOver9Corners = (selected_match_data.get('Last5HomeOver9Corners') or 0)*100
    Last5HomeOver10Corners = (selected_match_data.get('Last5HomeOver10Corners') or 0)*100
    Last5HomeAvergeTotalYellowCards = selected_match_data.get('Last5HomeAvergeTotalYellowCards') or 0
    Last5HomeOver1YellowCards = (selected_match_data.get('Last5HomeOver1YellowCards') or 0)*100
    Last5HomeOver2YellowCards = (selected_match_data.get('Last5HomeOver2YellowCards') or 0)*100
    Last5HomeOver3YellowCards = (selected_match_data.get('Last5HomeOver3YellowCards') or 0)*100
    Last5HomeOver4YellowCards = (selected_match_data.get('Last5HomeOver4YellowCards') or 0)*100
    Last5HomeAvergeTotalRedCards = selected_match_data.get('Last5HomeAvergeTotalRedCards') or 0

    Last5AwayOver7Corners = (selected_match_data.get('Last5AwayOver7Corners') or 0)*100
    Last5AwayOver8Corners = (selected_match_data.get('Last5AwayOver8Corners') or 0)*100
    Last5AwayOver9Corners = (selected_match_data.get('Last5AwayOver9Corners') or 0)*100
    Last5AwayOver10Corners = (selected_match_data.get('Last5AwayOver10Corners') or 0)*100
    Last5AwayAvergeTotalYellowCards = selected_match_data.get('Last5AwayAvergeTotalYellowCards') or 0
    Last5AwayOver1YellowCards = (selected_match_data.get('Last5AwayOver1YellowCards') or 0)*100
    Last5AwayOver2YellowCards = (selected_match_data.get('Last5AwayOver2YellowCards') or 0)*100
    Last5AwayOver3YellowCards = (selected_match_data.get('Last5AwayOver3YellowCards') or 0)*100
    Last5AwayOver4YellowCards = (selected_match_data.get('Last5AwayOver4YellowCards') or 0)*100
    Last5AwayAvergeTotalRedCards = selected_match_data.get('Last5AwayAvergeTotalRedCards') or 0

    l5_league_avg_btts = (selected_match_data.get('l5_league_avg_btts') or 0)*100
    l5HomeLeagueCleanSheet = selected_match_data.get('l5HomeLeagueCleanSheet') or 0
    l5AwayLeagueCleanSheet = selected_match_data.get('l5AwayLeagueCleanSheet') or 0
    
    pred_display = ""
    rec_pred_won = check_prediction_success(rec_pred, home_goals, away_goals, corners, home_team, away_team)
    if rec_pred:
        pred_display = f"{rec_pred}{confidence_text}"
        if rec_pred_won:
            pred_display = f"{rec_pred}{confidence_text} ✅" #<span style='color:green; font-size=1.5em font-weight:bold;'></span>" # Added checkmark
        # st.caption(f"**Best Bet:** {pred_display}", unsafe_allow_html=True)
        # st.success(f"**Best Bet:** {pred_display}")

    # else:
    #     st.caption("")
        
    # --- Check and Display Value Tip ---
    # Pass necessary stats to the check function
    value_display = ""
    value_bet_won = check_prediction_success(value_bet, home_goals, away_goals, corners, home_team, away_team)
    if value_bet:
        value_display = f"{value_bet}"
        if value_bet_won:
            value_display = f"{value_bet} ✅" #<span style='color:green; font-weight:bold;'></span>" # Added checkmark
        # st.caption(f"**Value Tip:** {value_display}", unsafe_allow_html=True)
    # else:
    #     st.caption("")

    if confidence_score != '--' and not pd.isna(confidence_score):
        confidence_score = int(confidence_score)

    pred_cols1,pred_cols2,pred_cols3,pred_cols4 = st.columns([1,2,2,3])
    pred_cols1.metric("Overall Confidence", f"{confidence_score}")#/10
    pred_cols2.success(f"**Best Bet:** {pred_display}")
    pred_cols3.warning(f"**Value Bets:** {value_display}")
    pred_cols4.info(f"**Advice:** {selected_match_data.get('advice', '--')}")

    # --- Tabs for Detailed Stats (Added Recommendations Tab) ---
    tab_titles = ["🎯 Recommendations", "📈 Performance & Goals", "🤝 H2H", "✨ Insights"]
    tabs = st.tabs(tab_titles)

    # Match report 
    # with tabs[0]:
        # st.markdown("#### ⭐ Prediction Overview")
        # Retrieve and display each stat using the helper function
        

        # st.markdown("---") # Divider after the report
    # Recommendations Tab (New)
    with tabs[0]:
        st.markdown("#### ⭐ Prediction Overview")
        rec_col1, rec_col2 = st.columns([0.5,4])
        with rec_col1:
            
            st.metric("Overall Confidence", f"{confidence_score}") #/10
        with rec_col2:
            st.success(f"**Best Bet:** {pred_display}")
        #      st.info(f"**Advice:** {selected_match_data.get('advice', '--')}")
        #      st.warning(f"**Value Bets:** `{selected_match_data.get('value_bets', '--')}`")
        # --- Check and Display Best Bet ---
        # Pass necessary stats to the check function      
        st.markdown("---")
        st.markdown("##### Detailed Predictions")
        pred_col1, pred_col2, pred_col3 = st.columns(3)
        with pred_col1:
            outcome_display = ""
            outcome_conf = selected_match_data.get('pred_outcome_conf')
            outcome_val = selected_match_data.get('pred_outcome', '--')
            outcome_bet_won = check_prediction_success(outcome_val, home_goals, away_goals, corners, home_team, away_team)
            if outcome_val:
                outcome_display = f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{outcome_val}</span>"
                if outcome_bet_won:
                    outcome_display = f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{outcome_val} ✅</span>" #color:green; 
                
            st.markdown("Match Outcome:") # f"{outcome_conf}/10" if outcome_conf is not None else None)
            st.markdown(f"{outcome_display}", unsafe_allow_html=True) # f"{outcome_conf}/10" if outcome_conf is not None else None)
        with pred_col2:
            goals_display = ""
            goals_conf = selected_match_data.get('pred_goals_conf')
            goals_val = selected_match_data.get('pred_goals', '--')
            goals_bet_won = check_prediction_success(goals_val, home_goals, away_goals, corners, home_team, away_team)
            if goals_val:
                goals_display = f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{goals_val}</span>"
                if goals_bet_won:
                    goals_display = f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{goals_val} ✅</span>" #color:green; 
                
            st.markdown("Goals (O/U):") # f"{outcome_conf}/10" if outcome_conf is not None else None)
            st.markdown(f"{goals_display}", unsafe_allow_html=True) #, f"{goals_conf}/10" if goals_conf is not None else None)
        with pred_col3:
            corners_display = ""
            corners_conf = selected_match_data.get('pred_corners_conf')
            corners_val = selected_match_data.get('pred_corners', '--')
            corners_bet_won = check_prediction_success(corners_val, home_goals, away_goals, corners, home_team, away_team)
            # Check if corner prediction is meaningful before showing
            if corners_val:
                corners_display = f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{corners_val}</span>"
                if corners_bet_won:
                    corners_display = f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{corners_val} ✅</span>" #color:green; 
                
            st.markdown("Corners (O/U):") # f"{outcome_conf}/10" if outcome_conf is not None else None)
            st.markdown(f"{corners_display}", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("##### Expected Value")
        ev_h = f"{selected_match_data.get('exp_val_h') * 100:.2f}%" if selected_match_data.get('exp_val_h') is not None else None
        ev_d = f"{selected_match_data.get('exp_val_d') * 100:.2f}%" if selected_match_data.get('exp_val_d') is not None else None
        ev_a = f"{selected_match_data.get('exp_val_a') * 100:.2f}%" if selected_match_data.get('exp_val_a') is not None else None
        
        pred_col4, pred_col5, pred_col6 = st.columns(3)
        if any([ev_h, ev_d, ev_a]):
            with pred_col4:
                # st.caption(f"**EV (Home):** {ev_h or '--'}")
                st.metric("EV (Home)", ev_h or '--')
            with pred_col5:
                # st.caption(f"**EV (Draw):** {ev_d or '--'}")
                st.metric("EV (Draw)", ev_d or '--')
            with pred_col6:
                # st.caption(f"**EV (Away):** {ev_a or '--'}")
                st.metric("EV (Away)", ev_a or '--')
            #  st.caption(f"**EV:** H: {ev_h or '--'} | D: {ev_d or '--'} | A: {ev_a or '--'}")
        else:
            st.caption("No Expected Value data.")

    # Performance Tab
    with tabs[1]:
        st.markdown("#### Performance & Form - Last 5 Games")
        # ... (Keep existing Performance tab code, ensuring .get() is used) ...
        home_col1, away_col2 = st.columns(2)

        home_btts_delta = Last5_HomeBothTeamsToScore - l5_league_avg_btts
        away_btts_delta = Last5_AwayBothTeamsToScore - l5_league_avg_btts

        ppg_h = selected_match_data.get('ppg_h')
        ppg_h_all = selected_match_data.get('ppg_h_all')
        ppg_a = selected_match_data.get('ppg_a')
        ppg_a_all = selected_match_data.get('ppg_a_all')

        with home_col1:
            st.markdown(f"**{selected_match_data.get('home_team','?')} (Home)**")
            form_home = colorize_performance(selected_match_data.get('form_home', '--'))#.split('//')r
            all_form_home = colorize_performance(selected_match_data.get('all_form_home', '--'))#.split('//')
            # if len(all_form_home) > 1:
            form_cols_h = st.columns(2)
            form_cols_h[0].metric("Form (H)", form_home)#[0]
            form_cols_h[1].metric("Form (Overall)",all_form_home)#[1]
            # else:
                # st.metric(label="Form (H)", value=all_form_home[0])

            # st.caption(f"**Home Form:** `{selected_match_data.get('form_home', '--')}`")
            # st.caption(f"**Overall Form:** `{selected_match_data.get('all_form_home', '--')}`")
            
            delta_h_str = f"{ppg_h_all} (All)" if ppg_h_all is not None else None

            clean_sheet_h = int(selected_match_data.get('clean_sheet_h', '--')*100)

            l5hometotalshots_delta = Last5HomeAvergeTotalShots - l5_home_for_league_avg_shots
            l5homesot_delta = Last5HomeAvergeTotalShotsOnGoal - l5_home_for_league_avg_sot
            lshomefouls_delta = Last5HomeAvergeTotalFouls - l5_home_for_league_avg_fouls
            l5hometotalcorner_delta = Last5HomeAvergeTotalcorners - l5_home_for_league_avg_corners
            l5hometotalyellows_delta = Last5HomeAvergeTotalYellowCards - l5_home_for_league_avg_yellow_cards
            # l5hometotalreds_delta = Last5HomeAvergeTotalRedCards - l5_home_for_league_avg_red_cards
            l5homeCS_delta = clean_sheet_h - l5HomeLeagueCleanSheet

            win_cols_h = st.columns(2)
            
            wr_h_text = selected_match_data.get('win_rates_h', 'HT: 0% | FT: 0%')
            ht_wr_h = int(selected_match_data.get('ht_win_rates_h', '--') * 100) if selected_match_data.get('ht_win_rates_h', '--') is not None else 0 # parse_specific_percent(wr_h_text, 'HT', 0)
            ft_wr_h = int(selected_match_data.get('ft_win_rates_h', '--') * 100) if selected_match_data.get('ft_win_rates_h', '--') is not None else 0 # parse_specific_percent(wr_h_text, 'FT', 0)

            try: 
                ppg_home_delta = ppg_h - ppg_a
                ppg_home_overall_delta = ppg_h_all - ppg_a_all
            except ValueError:
                ppg_home_delta = 0
                ppg_home_overall_delta = 0
            
            win_cols_h[0].metric(label="PPG (Home)", value=f"{ppg_h}/game" if ppg_h is not None else "--",delta=f"{round(ppg_home_delta,2)} vs Opponent PPG ({ppg_a})")
            win_cols_h[1].metric(label="PPG (Overall)", value=f"{ppg_h_all}/game" if ppg_h_all is not None else "--",delta=f"{round(ppg_home_overall_delta,2)} vs Opponent Overall PPG ({ppg_a_all})")
            
            win_cols_h[0].metric("Win Rate HT %", f"{ht_wr_h}%")
            win_cols_h[1].metric("Win Rate FT %", f"{ft_wr_h}%")
            
            win_cols_h[0].metric("GG",f"{round(Last5_HomeBothTeamsToScore)}%",f"{round(home_btts_delta)}% league avg ({round(l5_league_avg_btts)}%)") #leagues average delata
            win_cols_h[1].metric(label="Clean Sheet %", value=f"{round(clean_sheet_h*100)}%",delta=f"{round(l5homeCS_delta*100)}% league avg ({round(l5HomeLeagueCleanSheet*100)}%)") #nleague average clean sheet

            win_cols_h[0].metric("Total Shots",Last5HomeAvergeTotalShots,f"{round(l5hometotalshots_delta,2)} league avg({round(l5_home_for_league_avg_shots,2)}).")
            win_cols_h[1].metric("Shots on Goal",Last5HomeAvergeTotalShotsOnGoal,f"{round(l5homesot_delta,2)} league avg({round(l5_home_for_league_avg_sot,2)}).")

            win_cols_h[0].metric("Fouls",Last5HomeAvergeTotalFouls,f"{round(lshomefouls_delta,2)} league avg({round(l5_home_for_league_avg_fouls,2)}).","inverse")
            
            win_cols_h[1].metric("Total Corners",Last5HomeAvergeTotalcorners,f"{round(l5hometotalcorner_delta,2)} league avg({round(l5_home_for_league_avg_corners,2)}).")
            win_cols_h[0].metric("Total Yellows",Last5HomeAvergeTotalYellowCards,f"{round(l5hometotalyellows_delta,2)} league avg({round(l5_home_for_league_avg_yellow_cards,2)}).","inverse")
        
            # win_cols_h[1].metric("Total Reds",Last5HomeAvergeTotalRedCards,f"{round(l5hometotalreds_delta,2)} league avg.")

        with away_col2:
            st.markdown(f"**{selected_match_data.get('away_team','?')} (Away)**")
            form_away = colorize_performance(selected_match_data.get('form_away', '--'))#.split('//')r
            all_form_away = colorize_performance(selected_match_data.get('all_form_away', '--'))#.split('//')
            # if len(all_form_away) > 1:
            clean_sheet_a = int(selected_match_data.get('clean_sheet_a', '--')*100)
            l5AwayCS_delta = clean_sheet_a - l5AwayLeagueCleanSheet
            
            form_cols_a = st.columns(2)
            
            form_cols_a[0].metric("Form (A)", form_away)#[0]
            form_cols_a[1].metric("Form (Overall)",all_form_away)#[1]
            # st.caption(f"**Form (A/All):** `{selected_match_data.get('form_away', '--')}`")
            
            delta_a_str = f"{ppg_a_all} (All)" if ppg_a_all is not None else None
        
            l5awaytotalshots_delta = Last5AwayAvergeTotalShots - l5_away_for_league_avg_shots
            l5awaysot_delta = Last5AwayAvergeTotalShotsOnGoal - l5_away_for_league_avg_sot
            l5awayfouls_delta = Last5AwayAvergeTotalFouls - l5_away_for_league_avg_fouls 
            l5awaytotalcorner_delta = Last5AwayAvergeTotalcorners - l5_away_for_league_avg_corners 
            l5awaytotalyellows_delta = Last5AwayAvergeTotalYellowCards - l5_away_for_league_avg_yellow_cards 
            # l5awaytotalreds_delta = Last5AwayAvergeTotalRedCards - l5_away_for_league_avg_red_cards 
            
            ppg_away_delta = ppg_a - ppg_h
            ppg_away_overall_delta = ppg_a_all - ppg_h_all

            wr_a_text = selected_match_data.get('win_rates_a', 'HT: 0% | FT: 0%')
            ht_wr_a = int(selected_match_data.get('ht_win_rates_a', '--') * 100) if selected_match_data.get('ht_win_rates_a', '--') is not None else 0 # parse_specific_percent(wr_a_text, 'HT', 0)
            ft_wr_a = int(selected_match_data.get('ft_win_rates_a', '--') * 100) if selected_match_data.get('ft_win_rates_a', '--') is not None else 0 # parse_specific_percent(wr_a_text, 'FT', 0)
            
            win_cols_a = st.columns(2)
            win_cols_a[0].metric(label="PPG (Away)", value=f"{ppg_a}/game" if ppg_a is not None else "--",delta=f"{round(ppg_away_delta,2)} vs Opponent PPG ({ppg_h})")
            win_cols_a[1].metric(label="PPG (Overall)", value=f"{ppg_a_all}/game" if ppg_a_all is not None else "--",delta=f"{round(ppg_away_overall_delta,2)} vs Opponent Overall PPG ({ppg_h_all})")
            
            win_cols_a[0].metric("Win Rate HT %", f"{ht_wr_a}%")
            win_cols_a[1].metric("Win Rate FT %", f"{ft_wr_a}%")

            win_cols_a[0].metric("GG",f"{int(Last5_AwayBothTeamsToScore)}%",f"{away_btts_delta}% league avg ({l5_league_avg_btts}%)")
            win_cols_a[1].metric(label="Clean Sheet %", value=f"{round(clean_sheet_a*100)}%",delta=f"{round(l5AwayCS_delta*100)}% league avg ({l5AwayLeagueCleanSheet*100}%)")
            
            win_cols_a[0].metric("Total Shots",Last5AwayAvergeTotalShots,f"{round(l5awaytotalshots_delta,2)} league avg({round(l5_away_for_league_avg_shots,2)}).")
            win_cols_a[1].metric("Shots on Goal",Last5AwayAvergeTotalShotsOnGoal,f"{round(l5awaysot_delta,2)} league avg({round(l5_away_for_league_avg_sot,2)}).")

            win_cols_a[0].metric("Fouls",Last5AwayAvergeTotalFouls,f"{round(l5awayfouls_delta,2)} league avg({round(l5_away_for_league_avg_fouls,2)}).","inverse")
            
            win_cols_a[1].metric("Total Corners",Last5AwayAvergeTotalcorners,f"{round(l5awaytotalcorner_delta,2)} league avg ({round(l5_away_for_league_avg_corners,2)}).")
            
            win_cols_a[0].metric("Total Yellows",Last5AwayAvergeTotalYellowCards,f"{round(l5awaytotalyellows_delta,2)} league avg({round(l5_away_for_league_avg_yellow_cards,2)}).","inverse")
            # win_cols_h[1].metric("Total Reds",Last5AwayAvergeTotalRedCards,f"{round(l5awaytotalreds_delta,2)} league avg.")

        st.markdown("---") # Separator

    # Goals Tab
    # with tabs[2]:
        g_stats_cols = st.columns(2)

        with g_stats_cols[0]:
            st.markdown("#### Goal Statistics")
            st.markdown("**Average Goals Scored vs Conceded per Game**")
            try:
                # Prepare data in a 'long' format suitable for Altair color mapping
                home_team_label = selected_match_data.get('home_team', 'Home')
                away_team_label = selected_match_data.get('away_team', 'Away')
                # Use abbreviations for potentially long labels
                home_abbr = "".join([word[0] for word in home_team_label.split()[:2]])
                away_abbr = "".join([word[0] for word in away_team_label.split()[:2]])


                goals_h = float(selected_match_data.get('goals_h', 0.0))
                conc_h = float(selected_match_data.get('conceded_h', 0.0))
                goals_a = float(selected_match_data.get('goals_a', 0.0))
                conc_a = float(selected_match_data.get('conceded_a', 0.0))

                # Create list of dictionaries for DataFrame
                goal_data_long = [
                    {'Metric': f"{home_team_label} Scored", 'Value': goals_h, 'TeamType': 'Home'},
                    {'Metric': f"{away_team_label} Scored", 'Value': goals_a, 'TeamType': 'Away'},
                    {'Metric': f"{home_team_label} Conceded", 'Value': conc_h, 'TeamType': 'Home'},
                    {'Metric': f"{away_team_label} Conceded", 'Value': conc_a, 'TeamType': 'Away'}
                ]
                goal_df_long = pd.DataFrame(goal_data_long)

                # Define specific colors
                home_color = "#5e993c" #8bc34a" # Light Green
                away_color = "#c47704" #ff9800" # Orange

                # 1. Base chart definition (common encoding)
                base = alt.Chart(goal_df_long).encode(
                    x=alt.X('Metric', sort=None, title=None, axis=alt.Axis(labelAngle=0)), # Keep defined order, remove axis title
                    y=alt.Y('Value', title="Goals per Game"),
                    color=alt.Color('TeamType',
                                    scale=alt.Scale(domain=['Home', 'Away'], range=[home_color, away_color]),
                                    legend=alt.Legend(title="Team")
                                ),
                    tooltip=['Metric', alt.Tooltip('Value', format='.2f')] # Format tooltip value
                )

                # 2. Bar layer
                bar_chart = base.mark_bar()

                # 3. Text layer for labels
                text_labels = base.mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,  # Adjust vertical offset slightly above the bar
                    # Optional: Change text color for better visibility if needed
                    # color='black'
                ).encode(
                    # Encode the text channel with the 'Value', formatted to 2 decimal places
                    text=alt.Text('Value', format='.2f'),
                    # Important: Remove color encoding from text or set explicitly if needed,
                    # otherwise text might inherit bar colors making it hard to read on some backgrounds.
                    # Let's remove it here to default to black/dark text.
                    color=alt.value('black') # Force text color or remove the line altogether for default
                )

                # 4. Combine the layers
                final_chart = (bar_chart + text_labels).properties(
                    # title='Avg Goals Scored/Conceded' # Optional title
                ).interactive()

                # Display using st.altair_chart
                st.altair_chart(final_chart, use_container_width=True)

            except (ValueError, TypeError, KeyError, ImportError) as e:
                # Catch ImportError if altair isn't installed
                st.caption(f"Could not plot goal averages: {e}")
                if isinstance(e, ImportError):
                    st.warning("Please install altair: pip install altair")
        with g_stats_cols[1]:
            # --- NEW: Actual vs Expected Goals (xG) Visualization ---
            st.markdown("#### xG Statistics")
            st.markdown("**Average xG/xGA For and Aginst Per Game**")

            # --- End xG Visualization ---
            try:
                # Get data, providing defaults and converting safely
                home_team_label = selected_match_data.get('home_team', 'Home')
                away_team_label = selected_match_data.get('away_team', 'Away')

                g_h = selected_match_data.get('goals_h') # Home GS
                xg_h = selected_match_data.get('xg_h') # Home xG
                c_h = selected_match_data.get('conceded_h') # Home conceded = Opponent goals
                xga_h = selected_match_data.get('xga_h') # Home xGA = Opponent xG

                g_a = selected_match_data.get('goals_a') # Away GS
                xg_a = selected_match_data.get('xg_a') # Away xG
                c_a = selected_match_data.get('conceded_a') # Away conceded = Opponent goals
                xga_a = selected_match_data.get('xga_a') # Away xGA = Opponent xG

                # Add a 'Location' column based on the Category string
                def get_location(category_name):
                    if home_team_label in category_name:
                        return "Home"
                    elif away_team_label in category_name:
                        return "Away"
                    else:
                        return "Unknown" # Fallback
                # Check if all necessary values are present and numeric
                if all(v is not None for v in [g_h, xg_h, c_h, xga_h, g_a, xg_a, c_a, xga_a]):
                    # Convert to float after check
                    g_h, xg_h, c_h, xga_h = float(g_h), float(xg_h), float(c_h), float(xga_h)
                    g_a, xg_a, c_a, xga_a = float(g_a), float(xg_a), float(c_a), float(xga_a)

                    # Prepare data for GROUPED bar chart
                    xg_data = pd.DataFrame({
                        'Actual': [g_h, c_h, g_a, c_a],
                        'Expected': [xg_h, xga_h, xg_a, xga_a]
                    },
                        index=[f"{home_team_label} Attack",
                            f"{home_team_label} Defense",
                            f"{away_team_label} Attack",
                            f"{away_team_label} Defense"]
                    )
                    xg_data_reset = xg_data.reset_index()
                    xg_data_reset = xg_data_reset.rename(columns={'index': 'Category'})

                    xg_data_long = pd.melt(
                        xg_data_reset,
                        id_vars=['Category'],
                        var_name='MetricType',
                        value_name='Goals'
                    )
                    # st.dataframe(xg_data_long) # Keep for debugging if needed

                    xg_data_long['Location'] = xg_data_long['Category'].apply(get_location)

                    category_order = [
                        f"{home_team_label} Attack", f"{home_team_label} Defense",
                        f"{away_team_label} Attack", f"{away_team_label} Defense"
                    ]

                    # --- Create the Altair Chart ---

                    # 1. Define the base chart for bars (this includes the xOffset)
                    base_bars = alt.Chart(xg_data_long).encode(
                        x=alt.X('Category:N',
                                sort=category_order,
                                axis=alt.Axis(title=None, labelAngle=0)),
                        y=alt.Y('Goals:Q',
                                axis=alt.Axis(title='Goals (Actual vs Expected)')),
                        color=alt.Color('Location:N',
                                        scale=alt.Scale(domain=['Home', 'Away'],
                                                        range=['#5e993c', '#c47704']),
                                        legend=alt.Legend(title="Location")),
                        xOffset=alt.XOffset('MetricType:N'), # Group by Actual/Expected
                        tooltip=[
                            alt.Tooltip('Category', title='Focus'),
                            alt.Tooltip('MetricType', title='Metric'),
                            alt.Tooltip('Goals', format='.2f'),
                            alt.Tooltip('Location')
                        ]
                    )

                    # 2. Create the bar layer
                    bars = base_bars.mark_bar()

                    # 3. Create the text layer
                    #    IMPORTANT: The text layer also needs the xOffset to align correctly
                    #    OR, if we base it on the same 'base_bars', it will inherit the offset.
                    #    We also need to make sure it uses the 'Goals' field for the text.
                    text = base_bars.mark_text( # Inherit x, y, xOffset, color from base_bars
                        align='center',
                        baseline='bottom',
                        dy=-5,  # Nudge text slightly above the bar
                        # color='black' # Set text color explicitly if needed
                    ).encode(
                        text=alt.Text('Goals:Q', format='.2f'), # Use the 'Goals' column and format
                        # We need to override the color encoding from base_bars if we want a fixed text color
                        # If we don't, text will be colored like the bars, which might be hard to read.
                        color=alt.value('black') # Force text color to black (or choose another)
                    ).transform_filter( # Optional: Don't show labels for zero or very small values
                        alt.datum.Goals > 0.01
                    )

                    # 4. Combine the layers
                    final_chart = (bars + text).properties(
                        # title='Goal Comparison' # Optional title
                    ).interactive()

                    # Display using st.altair_chart
                    st.altair_chart(final_chart, use_container_width=True)
                else:
                    st.caption("xG/xGA data incomplete or missing, cannot plot comparison chart.")
                    # Optionally display raw values if available
                    xg_col1, xg_col2 = st.columns(2)
                    with xg_col1:
                        st.caption(f"**xG (H):** {selected_match_data.get('xg_h', '--')} | **xGA (H):** {selected_match_data.get('xga_h', '--')}")
                    with xg_col2:
                        st.caption(f"**xG (A):** {selected_match_data.get('xg_a', '--')} | **xGA (A):** {selected_match_data.get('xga_a', '--')}")

            except (ValueError, TypeError, KeyError) as e:
                st.caption(f"Could not plot xG comparison chart: {e}")

        st.markdown("---") # Separator
        
        
        # st.markdown("---")
        stats_cols = st.columns(4)
        with stats_cols[0]:
            st.markdown("#### Goal Trends")
            h_halves_text = selected_match_data.get('halves_o05_h', '')
            h1_pct = selected_match_data.get('1h_o05_h', '')*100  # parse_specific_percent(h_halves_text, '1H', 0)
            h2_pct = selected_match_data.get('2h_o05_h', '')*100  # parse_specific_percent(h_halves_text, '2H', 0)
            st.markdown(f"##### {selected_match_data.get('home_team','Home')}")#(H): 1H={h1_pct}% | 2H={h2_pct}%

            st.markdown("**Halves > 0.5 Goals %**")
            # st.progress(h1_pct / 100.0, text=f"1H {h1_pct}%")
            # st.progress(h2_pct / 100.0, text=f"2H {h2_pct}%")
            st.markdown("**First Half  (1H):**")
            st.markdown(create_colored_progress_bar(h1_pct, text_label="1H"), unsafe_allow_html=True)
            st.markdown("**Second Half (2H):**")
            st.markdown(create_colored_progress_bar(h2_pct, text_label="2H"), unsafe_allow_html=True)
            st.markdown("---")

            st.markdown("**Matches Over X Goals %**")
            h_match_goals_text = selected_match_data.get('match_goals_h', '')
            o15_h_pct = selected_match_data.get('match_goals_1_5_h', '')*100#parse_specific_percent(h_match_goals_text, 'O1.5', 0)
            o25_h_pct = selected_match_data.get('match_goals_2_5_h', '')*100#parse_specific_percent(h_match_goals_text, 'O2.5', 0)
            # st.markdown(f**"{selected_match_data.get('home_team','H')} (H): O1.5={o15_h_pct}% | O2.5={o25_h_pct}%**")
            # st.progress(o15_h_pct / 100.0, text=f"O1.5 {o15_h_pct}%")
            # st.progress(o25_h_pct / 100.0, text=f"O2.5 {o25_h_pct}%")
            st.markdown("**Over 1.5:**")
            st.markdown(create_colored_progress_bar(o15_h_pct, text_label="O1.5"), unsafe_allow_html=True)
            st.markdown("**Over 2.5:**")
            st.markdown(create_colored_progress_bar(o25_h_pct, text_label="O2.5"), unsafe_allow_html=True)

            st.markdown("---")
            
            st.markdown("**Home Away Team Scored Over X Goals %**")
            h_team_goals_text = selected_match_data.get('team_goals_h', 'Over 0.5: 0% | O1.5: 0%')
            o05_h_pct = selected_match_data.get('team_goals_0_5_h', '')*100 #parse_specific_percent(h_team_goals_text, 'Over 0.5', 0)
            o15_h_pct_team = selected_match_data.get('team_goals_1_5_h', '')*100 #parse_specific_percent(h_team_goals_text, 'O1.5', 0)
            st.markdown("**Over 0.5:**")
            st.markdown(create_colored_progress_bar(o05_h_pct, text_label="O0.5"), unsafe_allow_html=True)
            # --- END REPLACE ---
            st.markdown("**Over 1.5:**")
            # --- REPLACE st.progress ---
            st.markdown(create_colored_progress_bar(o15_h_pct_team, text_label="O1.5"), unsafe_allow_html=True)

        with stats_cols[1]:
            st.markdown("#### ")
            a_match_goals_text = selected_match_data.get('match_goals_a', '')
            o15_a_pct = selected_match_data.get('1h_o05_a', '')*100#parse_specific_percent(a_match_goals_text, 'O1.5', 0)
            o25_a_pct = selected_match_data.get('2h_o05_a', '')*100#parse_specific_percent(a_match_goals_text, 'O2.5', 0)
            st.markdown(f"##### {selected_match_data.get('away_team','Away')}") # (A): O1.5={o15_a_pct}% | O2.5={o25_a_pct}%
            st.markdown("**Halves > 0.5 Goals %**")
            # st.progress(o15_a_pct / 100.0, text=f"O1.5 {o15_a_pct}%")
            # st.progress(o25_a_pct / 100.0, text=f"O2.5 {o25_a_pct}%")
            st.markdown("**First Half  (1H):**")
            st.markdown(create_colored_progress_bar(o15_a_pct, text_label="O1.5"), unsafe_allow_html=True)
            st.markdown("**Second Half (2H):**")
            st.markdown(create_colored_progress_bar(o25_a_pct, text_label="O2.5"), unsafe_allow_html=True)
            st.markdown("---")

            st.markdown("**Matches Over X Goals %**")
            a_halves_text = selected_match_data.get('halves_o05_a', '')
            a1_pct = selected_match_data.get('match_goals_1_5_a', '')*100#parse_specific_percent(a_halves_text, '1H', 0)
            a2_pct = selected_match_data.get('match_goals_2_5_a', '')*100#parse_specific_percent(a_halves_text, '2H', 0)
            # st.markdown(f"{selected_match_data.get('away_team','A')} (A): 1H={a1_pct}% | 2H={a2_pct}%")
            # st.progress(a1_pct / 100.0, text=f"1H {a1_pct}%")
            # st.progress(a2_pct / 100.0, text=f"2H {a2_pct}%")
            st.markdown("**Over 1.5:**")
            st.markdown(create_colored_progress_bar(a1_pct, text_label="1H"), unsafe_allow_html=True)
            st.markdown("**Over 2.5:**")
            st.markdown(create_colored_progress_bar(a2_pct, text_label="2H"), unsafe_allow_html=True)
            st.markdown("---")

            st.markdown("**Away Team Scored Over X Goals %**")
            a_team_goals_text = selected_match_data.get('team_goals_a', 'Over 0.5: 0% | O1.5: 0%')
            o05_a_pct = selected_match_data.get('team_goals_0_5_a', '')*100#parse_specific_percent(a_team_goals_text, 'Over 0.5', 0)
            o15_a_pct_team = selected_match_data.get('team_goals_1_5_a', '')*100#parse_specific_percent(a_team_goals_text, 'O1.5', 0)
            st.markdown("**Over 0.5:**")
            st.markdown(create_colored_progress_bar(o05_a_pct, text_label="O0.5"), unsafe_allow_html=True)
            # --- END REPLACE ---
            st.markdown("**Over 1.5:**")
            # --- REPLACE st.progress ---
            st.markdown(create_colored_progress_bar(o15_a_pct_team, text_label="O1.5"), unsafe_allow_html=True)
            # --- END REPLACE ---

        with stats_cols[2]:
            st.markdown("#### Corners and Cards")
            st.markdown(f"##### {selected_match_data.get('home_team','Home')}") 
            st.markdown("**Corners (O/U)**")

            st.markdown("**Over 7.5 Corners:**")
            st.markdown(create_colored_progress_bar(Last5HomeOver7Corners, text_label="O7.5"), unsafe_allow_html=True)
            st.markdown("**Over 8.5 Corners:**")
            st.markdown(create_colored_progress_bar(Last5HomeOver8Corners, text_label="O8.5"), unsafe_allow_html=True)
            st.markdown("**Over 9.5 Corners:**")
            st.markdown(create_colored_progress_bar(Last5HomeOver9Corners, text_label="O9.5"), unsafe_allow_html=True)
            st.markdown("**Over 10.5 Corners:**")
            st.markdown(create_colored_progress_bar(Last5HomeOver10Corners, text_label="O10.5"), unsafe_allow_html=True)

            st.markdown("---")

            st.markdown("**Cards (O/U)**")
            st.markdown("**Over 1.5 Cards:**")
            st.markdown(create_colored_progress_bar(Last5HomeOver1YellowCards, text_label="O1.5"), unsafe_allow_html=True)
            st.markdown("**Over 2.5 Cards:**")
            st.markdown(create_colored_progress_bar(Last5HomeOver2YellowCards, text_label="O2.5"), unsafe_allow_html=True)
            st.markdown("**Over 3.5 Cards:**")
            st.markdown(create_colored_progress_bar(Last5HomeOver3YellowCards, text_label="O3.5"), unsafe_allow_html=True)
            st.markdown("**Over 4.5 Cards:**")
            st.markdown(create_colored_progress_bar(Last5HomeOver4YellowCards, text_label="O4.5"), unsafe_allow_html=True)

        with stats_cols[3]:
            st.markdown("#### ")
            st.markdown(f"##### {selected_match_data.get('away_team','Away')}")
            st.markdown("**Corners (O/U)**")

            st.markdown("**Over 7.5 Corners:**")
            st.markdown(create_colored_progress_bar(Last5AwayOver7Corners, text_label="O7.5"), unsafe_allow_html=True)
            st.markdown("**Over 8.5 Corners:**")
            st.markdown(create_colored_progress_bar(Last5AwayOver8Corners, text_label="O8.5"), unsafe_allow_html=True)
            st.markdown("**Over 9.5 Corners:**")
            st.markdown(create_colored_progress_bar(Last5AwayOver9Corners, text_label="O9.5"), unsafe_allow_html=True)
            st.markdown("**Over 10.5 Corners:**")
            st.markdown(create_colored_progress_bar(Last5AwayOver10Corners, text_label="O10.5"), unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("**Cards (O/U)**")

            st.markdown("**Over 1.5 Cards:**")
            st.markdown(create_colored_progress_bar(Last5AwayOver1YellowCards, text_label="O1.5"), unsafe_allow_html=True)
            st.markdown("**Over 2.5 Cards:**")
            st.markdown(create_colored_progress_bar(Last5AwayOver2YellowCards, text_label="O2.5"), unsafe_allow_html=True)
            st.markdown("**Over 3.5 Cards:**")
            st.markdown(create_colored_progress_bar(Last5AwayOver3YellowCards, text_label="O3.5"), unsafe_allow_html=True)
            st.markdown("**Over 4.5 Cards:**")
            st.markdown(create_colored_progress_bar(Last5AwayOver4YellowCards, text_label="O4.5"), unsafe_allow_html=True)


    # H2H Tab
    def display_h2h_stats(metric_label, h2h_val,team_overall_avg,league_avg_context,team,inverse_flag):
        # h2h_val = float(selected_match_data.get('h2h_home_shots_against_avg', 0.0)) # Shots conceded by Home in H2H
        # team_overall_avg = float(selected_match_data.get('shots_against_home_avg', 0.0)) # Team's overall avg AGAINST @ Home
        delta_vs_team = h2h_val - team_overall_avg
        # league_avg_context = float(selected_match_data.get('shots_against_league_home_avg', 0.0)) # League avg AGAINST @ Home
        if inverse_flag == 1:
            inverse_value = "inverse"
        else:
            inverse_value = "normal"
        st.metric(label=metric_label,
                value=f"{h2h_val:.2f}",
                delta=f"{delta_vs_team:+.2f} vs Team Avg ({team_overall_avg})",
                delta_color=inverse_value # Lower is better for AGAINST
                ) 
        st.caption(f"League Avg FOR @ {team}: {league_avg_context:.2f}") # Context

    with tabs[2]:
        st.markdown("#### Head-to-Head (H2H)")
        # ... (Keep H2H records display) ...
        st.markdown("##### Home vs Away Averages (in H2H Games)")
        HeadToHeadBTTS = round(selected_match_data.get('HeadToHeadBTTS'),2) * 100 if selected_match_data.get('HeadToHeadBTTS') is not None else 0

        cols1,cols2,cols3 = st.columns([1,1.5,2])
        with cols1:
            h2h_cols = st.columns(2)
            h2h_cols[0].metric(label="Home vs Away Record", value=selected_match_data.get('h2h_hva_record', '--').strip("()"))
            h2h_cols[0].metric(label="All Time H2H Record", value=selected_match_data.get('h2h_all_record', '--').strip("()"))
            h2h_cols[0].metric(label="Home xG", value=HeadToHeadHomeXG, delta=f"{HeadToHeadHomeXG-HeadToHeadAwayXG} vs Away xG")
            h2h_cols[0].metric(label="H2H GG", value=f"{HeadToHeadBTTS}%")
        
            h2h_cols[1].metric(label="Matches", value=selected_match_data.get('h2h_hva_games', '--'))
            h2h_cols[1].metric(label="Matches", value=selected_match_data.get('h2h_all_games', '--'))
            h2h_cols[1].metric(label="Away xG", value=HeadToHeadAwayXG, delta=f"{HeadToHeadAwayXG-HeadToHeadHomeXG} vs Home xG")

        with cols2:
            # st.markdown("##### H2H Stats")
            # st.markdown("")
            h2h_stats_cols = st.columns(2)
            
            with h2h_stats_cols[0]:
                display_h2h_stats("**Home Total Shots:**", HeadToHeadHomeTotalShots, Last5HomeAvergeTotalShots,l5_home_for_league_avg_shots,"Home",0)
                display_h2h_stats("**Home Shots On Target:**", HeadToHeadHomeShotsOnTarget, Last5HomeAvergeTotalShotsOnGoal, l5_home_for_league_avg_sot,"Home",0)
                display_h2h_stats("**Home Fouls:**", HeadToHeadHomeFouls, Last5HomeAvergeTotalFouls, l5_home_for_league_avg_fouls,"Home",1)
                
            with h2h_stats_cols[1]:
                
                display_h2h_stats("**Away Total Shots:**", HeadToHeadAwayTotalShots, Last5AwayAvergeTotalShots, l5_away_for_league_avg_shots,"Away",0)
                display_h2h_stats("**Away Shots On Target:**", HeadToHeadAwayShotsOnTarget, Last5AwayAvergeTotalShotsOnGoal,l5_away_for_league_avg_sot,"Away",0 )
                display_h2h_stats("**Away Fouls:**", HeadToHeadAwayFouls, Last5AwayAvergeTotalFouls, l5_away_for_league_avg_fouls,"Away",1)

        with cols3:
            try:
                # Prepare data in 'long' format
                home_team_label = selected_match_data.get('home_team', 'Home')
                away_team_label = selected_match_data.get('away_team', 'Away')
                home_abbr = "".join([word[0] for word in home_team_label.split()[:2]])
                away_abbr = "".join([word[0] for word in away_team_label.split()[:2]])

                h2h_ppg_h = selected_match_data.get('h2h_h_ppg') #parse_h2h_value(, 'H', default=0.0)
                h2h_ppg_a = selected_match_data.get('h2h_a_ppg') #parse_h2h_value(, 'A', default=0.0)
                h2h_goals_h = selected_match_data.get('h2h_h_goals_scored') #parse_h2h_value(, 'H', default=0.0)
                h2h_goals_a = selected_match_data.get('h2h_a_goals_scored') #parse_h2h_value(, 'A', default=0.0)

                # Create list of dictionaries for DataFrame
                h2h_data_long = [
                    {'Metric': f"{home_team_label} PPG", 'Value': h2h_ppg_h, 'TeamType': 'Home'},
                    {'Metric': f"{away_team_label} PPG", 'Value': h2h_ppg_a, 'TeamType': 'Away'},
                    {'Metric': f"{home_team_label} Goals", 'Value': h2h_goals_h, 'TeamType': 'Home'},
                    {'Metric': f"{away_team_label} Goals", 'Value': h2h_goals_a, 'TeamType': 'Away'}
                ]
                h2h_df_long = pd.DataFrame(h2h_data_long)

                # Define specific colors
                home_color = "#8bc34a" # Light Green
                away_color = "#ff9800" # Orange

                # Create Altair chart
                chart_h2h = alt.Chart(h2h_df_long).mark_bar().encode(
                    x=alt.X('Metric', sort=None, title=None,axis=alt.Axis(title=None, labelAngle=0)), # Keep defined order, remove axis title
                    y=alt.Y('Value', title="Avg Value"),
                    color=alt.Color('TeamType',
                                    scale=alt.Scale(domain=['Home', 'Away'], range=[home_color, away_color]),
                                    legend=alt.Legend(title="Team")
                                ),
                    tooltip=['Metric', alt.Tooltip('Value', format='.2f')]
                )
                # 2. Bar layer
                bar_chart = chart_h2h.mark_bar()

                # 3. Text layer for labels
                text_labels = chart_h2h.mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,  # Adjust vertical offset slightly above the bar
                    # Optional: Change text color for better visibility if needed
                    # color='black'
                ).encode(
                    # Encode the text channel with the 'Value', formatted to 2 decimal places
                    text=alt.Text('Value', format='.2f'),
                    # Important: Remove color encoding from text or set explicitly if needed,
                    # otherwise text might inherit bar colors making it hard to read on some backgrounds.
                    # Let's remove it here to default to black/dark text.
                    color=alt.value('black') # Force text color or remove the line altogether for default
                )

                # 4. Combine the layers
                final_chart = (bar_chart + text_labels).properties(
                    # title='Avg Goals Scored/Conceded' # Optional title
                ).interactive()

                # Display using st.altair_chart
                st.altair_chart(final_chart, use_container_width=True)

            except (ValueError, TypeError, KeyError, ImportError) as e:
                st.caption(f"Error plotting H2H averages: {e}")
                if isinstance(e, ImportError):
                    st.warning("Please install altair: pip install altair")

        st.markdown("---")
        st.markdown("##### Home vs Away Over/Under Goals (in H2H Games)")
        # Parse H2H Over/Under - more complex string potentially
        h2h_ou_text = selected_match_data.get('h2h_hva_ou', '')
        o15_h2h = int((selected_match_data.get('h2h_hva_o1_5') or 0) * 100) #parse_specific_percent(h2h_ou_text, 'O1.5', 0)
        o25_h2h = int((selected_match_data.get('h2h_hva_o2_5') or 0) * 100) #parse_specific_percent(h2h_ou_text, 'O2.5', 0)
        u25_h2h = int((selected_match_data.get('h2h_hva_u2_5') or 0) * 100) #parse_specific_percent(h2h_ou_text, 'U2.5', 0)
        u35_h2h = int((selected_match_data.get('h2h_hva_u3_5') or 0) * 100) #parse_specific_percent(h2h_ou_text, 'U3.5', 0)
        h2h_ou_cols = st.columns(3)
        with h2h_ou_cols[0]:
            st.markdown("##### Goal Stats")
            st.markdown("1st & 2nd Half Goals Trends")
            half_cols = st.columns(2)
            with half_cols[0]:
                st.metric("Home 1H",selected_match_data.get('HeadToHeadHomeFirstHalfGoalsScored') or '--')
                st.metric("Away 1H",selected_match_data.get('HeadToHeadAwayFirstHalfGoalsScored') or '--')
            with half_cols[1]:
                st.metric("Home 2H",selected_match_data.get('HeadToHeadHomeSecondHalfGoalsScored') or '--')
                st.metric("Away 2H",selected_match_data.get('HeadToHeadAwaySecondHalfGoalsScored') or '--')

        with h2h_ou_cols[1]:
            st.markdown("##### Corner Stats")
            st.markdown("Corners Trends")
            corner_stats_cols = st.columns(2)
            with corner_stats_cols[0]:
                # st.metric("**Home Corners:**", )
                display_h2h_stats("**Home Corners:**", HeadToHeadHomeCorners, Last5HomeAvergeTotalcorners,l5_home_for_league_avg_corners,"Home",0)

            with corner_stats_cols[1]:
                # st.metric("**Away Corners:**", )
                display_h2h_stats("**Away Corners:**", HeadToHeadAwayCorners, Last5AwayAvergeTotalcorners,l5_away_for_league_avg_corners,"Away",0)
        
        with h2h_ou_cols[2]:
            st.markdown("##### Card Stats")
            st.markdown("Cards Trends")
            card_stats_cols = st.columns(2)
            with card_stats_cols[0]:
                display_h2h_stats("**Home Yellows:**", HeadToHeadHomeYellowCards, Last5HomeAvergeTotalYellowCards,l5_home_for_league_avg_yellow_cards,"Home",1)
                # st.metric("**Home Yellow Cards:**", selected_match_data.get('HeadToHeadHomeYellowCards') or '--')
                # st.metric("**Home Red Cards:**", selected_match_data.get('HeadToHeadHomeRedCards') or '--')
            with card_stats_cols[1]:
                # st.metric("**Away Yellow Cards:**", selected_match_data.get('HeadToHeadAwayYellowCards') or '--')
                # st.metric("**Away Red Cards:**", selected_match_data.get('HeadToHeadAwayRedCards') or '--')            
                display_h2h_stats("**Away Yellows:**", HeadToHeadAwayYellowCards, Last5AwayAvergeTotalYellowCards,l5_away_for_league_avg_yellow_cards,"Away",1)
            
        h2h_col = st.columns(3)

        with h2h_col[0]:
            st.markdown("---")
            st.markdown("Goals (O/U)")
            st.write("")
            st.markdown("Over 1.5:")
            # st.progress(o15_h2h / 100.0)
            st.markdown(create_colored_progress_bar(o15_h2h), unsafe_allow_html=True)
            st.markdown("Over 2.5:")
            # st.progress(o25_h2h / 100.0)
            st.markdown(create_colored_progress_bar(o25_h2h), unsafe_allow_html=True)
            st.markdown("Under 2.5:")
            # st.progress(u25_h2h / 100.0)
            st.markdown(create_colored_progress_bar(u25_h2h), unsafe_allow_html=True)
            st.markdown("Under 3.5:")
            # st.progress(u35_h2h / 100.0)
            st.markdown(create_colored_progress_bar(u35_h2h), unsafe_allow_html=True)
        
        with h2h_col[1]:
            st.markdown("---")
            st.markdown("Corners (O/U)")
            st.write(" ")
            o7c = int((selected_match_data.get('HeadToHeadOver7Corners') or 0)*100)    
            o8c = int((selected_match_data.get('HeadToHeadOver8Corners') or 0)*100)    
            o9c = int((selected_match_data.get('HeadToHeadOver9Corners') or 0)*100)    
            o10c = int((selected_match_data.get('HeadToHeadOver10Corners') or 0)*100)    
            
            st.markdown("Over 7.5 corners:")
            st.markdown(create_colored_progress_bar(o7c), unsafe_allow_html=True)
            st.markdown("Over 8.5 corners:")
            st.markdown(create_colored_progress_bar(o8c), unsafe_allow_html=True)
            st.markdown("Over 9.5 corners:")
            st.markdown(create_colored_progress_bar(o9c), unsafe_allow_html=True)
            st.markdown("Over 10.5 corners:")
            st.markdown(create_colored_progress_bar(o10c), unsafe_allow_html=True)
        with h2h_col[2]:
            st.markdown("---")
            st.markdown("Cards (O/U)")
            st.write(" ")
            o1c = int((selected_match_data.get('HeadToHeadOver1YellowCards') or 0)*100) 
            o2c = int((selected_match_data.get('HeadToHeadOver2YellowCards') or 0)*100) 
            o3c = int((selected_match_data.get('HeadToHeadOver3YellowCards') or 0)*100) 
            o4c = int((selected_match_data.get('HeadToHeadOver4YellowCards') or 0)*100) 
            
            st.markdown("Over 1.5 yellow cards:")
            st.markdown(create_colored_progress_bar(o1c), unsafe_allow_html=True)
            st.markdown("Over 2.5 yellow cards:")
            st.markdown(create_colored_progress_bar(o2c), unsafe_allow_html=True)
            st.markdown("Over 3.5 yellow cards:")
            st.markdown(create_colored_progress_bar(o3c), unsafe_allow_html=True)
            st.markdown("Over 4.5 yellow cards:")
            st.markdown(create_colored_progress_bar(o4c), unsafe_allow_html=True)
                
        # with h2h_ou_cols[3]:

    # Insights Tab
    with tabs[3]:
        st.markdown("#### Insights Visualization")

        # Parse all insight blocks
        insights_home_parsed = parse_insights_string(selected_match_data.get('insights_home'))
        insights_away_parsed = parse_insights_string(selected_match_data.get('insights_away'))
        insights_total_h_parsed = parse_insights_string(selected_match_data.get('insights_total_h'))
        insights_total_a_parsed = parse_insights_string(selected_match_data.get('insights_total_a'))

        # Display Team Specific Insights
        st.markdown("**Team Specific Insights vs League Average**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{selected_match_data['home_team']} (Home)**")
            if not insights_home_parsed: 
                st.caption("No home insights.")
            for insight in insights_home_parsed:
                if isinstance(insight, dict) and insight.get('delta_str'):
                    st.metric(label=insight['label'], value=insight['value'], delta=insight['delta_str'])
                elif insight.get('value'): 
                    st.metric(insight['label'],insight['value'])
                else: 
                    st.caption(f"{insight['label']} (No data)")
        with col2:
            st.markdown(f"**{selected_match_data['away_team']} (Away)**")
            if not insights_away_parsed: 
                st.caption("No away insights.")
            for insight in insights_away_parsed:
                if insight.get('delta_str'): 
                    st.metric(label=insight['label'], value=insight['value'], delta=insight['delta_str'])
                elif insight.get('value'): 
                    st.metric(insight['label'],insight['value'])
                else: 
                    st.caption(f"{insight['label']} (No data)")

        st.markdown("---")
        # Display Total Match Insights
        st.markdown("**Total Match Insights vs League Average**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**(Based on {selected_match_data['home_team']} Matches)**")
            if not insights_total_h_parsed: st.caption("No total match insights (Home perspective).")
            for insight in insights_total_h_parsed:
                if insight.get('delta_str'): 
                    st.metric(label=insight['label'], value=insight['value'], delta=insight['delta_str'])
                elif insight.get('value'): 
                    st.markdown(f"**{insight['label']}:** {insight['value']}")
                else: 
                    st.caption(f"{insight['label']} (No data)")

        with col2:
            st.markdown(f"**(Based on {selected_match_data['away_team']} Matches)**")
            if not insights_total_a_parsed: st.caption("No total match insights (Away perspective).")
            for insight in insights_total_a_parsed:
                if insight.get('delta_str'): 
                    st.metric(label=insight['label'], value=insight['value'], delta=insight['delta_str'])
                elif insight.get('value'): 
                    st.markdown(f"**{insight['label']}:** {insight['value']}")
                else: 
                    st.caption(f"{insight['label']} (No data)")
