import glob  # For finding weekly files
import io
import math
import os
import re
import time  # Needed for timestamps
import traceback  # For detailed error logging
from collections import defaultdict  # For grouping by league
from datetime import datetime
from pathlib import Path

# import psycopg2 # Optional
# from psycopg2 import sql # Optional
import altair as alt  # Keep altair import
import emoji
import numpy as np  # For NaN handling
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Match Analysis",  # You can have a page-specific title
    page_icon="⚽",  # <<< USE THE SAME ICON HERE
    layout="wide",  # Or whatever layout you prefer for this page
)
# --- Configuration ---
# If pages/1_🏠_Match_Analysis.py is in PROJECT_ROOT/pages/1_🏠_Match_Analysis.py
# and your data is in PROJECT_ROOT/data/
PROJECT_ROOT = Path(
    __file__
).parent.parent  # Goes up one level from 'pages' to the root
WEEKLY_PREDICTIONS_DIR = PROJECT_ROOT / "data" / "pre_match"
COMBINED_RESULTS_FILE = PROJECT_ROOT / "data" / "combined_results.csv"
# WEEKLY_PREDICTIONS_DIR = "data/pre_match/"
# COMBINED_RESULTS_FILE = "data/combined_results.csv"
# WEEKLY_PREDICTIONS_DIR = "fpp_dashboard/data/pre_match/"
# COMBINED_RESULTS_FILE = "fpp_dashboard/data/combined_results.csv"

DATA_SOURCE = "csv"
# Placeholder for DB connection (replace with actuals if using postgres)
DB_PARAMS = {
    "dbname": "football_db",
    "user": "user",
    "password": "password",
    "host": "localhost",
    "port": "5432",
}
TEXT_FILE_PATH = "Confidence-7.txt"
CSV_FILE_PATH = "dashboard/dashboard_data.csv"  # Path for saving/loading simulated CSV

# Map country names (as they appear in your data) to their flag codes
COUNTRY_CODE_MAP = {
    # media.api-sports.io
    "UEFA Champions League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/2.png",
    "UEFA Europa Conference League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/848.png",
    "UEFA Europa League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/3.png",
    "World": "https://fpp-dashboard-media.b-cdn.net/football/leagues/17.png",
    "Albania": "https://fpp-dashboard-media.b-cdn.net/flags/al.svg",
    "Algeria": "https://fpp-dashboard-media.b-cdn.net/flags/dz.svg",
    "Andorra": "https://fpp-dashboard-media.b-cdn.net/flags/ad.svg",
    "Angola": "https://fpp-dashboard-media.b-cdn.net/flags/ao.svg",
    "Antigua-And-Barbuda": "https://fpp-dashboard-media.b-cdn.net/flags/ag.svg",
    "Argentina": "https://fpp-dashboard-media.b-cdn.net/flags/ar.svg",
    "Armenia": "https://fpp-dashboard-media.b-cdn.net/flags/am.svg",
    "Aruba": "https://fpp-dashboard-media.b-cdn.net/flags/aw.svg",
    "Australia": "https://fpp-dashboard-media.b-cdn.net/flags/au.svg",
    "Austria": "https://fpp-dashboard-media.b-cdn.net/flags/at.svg",
    "Azerbaijan": "https://fpp-dashboard-media.b-cdn.net/flags/az.svg",
    "Bahrain": "https://fpp-dashboard-media.b-cdn.net/flags/bh.svg",
    "Bangladesh": "https://fpp-dashboard-media.b-cdn.net/flags/bd.svg",
    "Barbados": "https://fpp-dashboard-media.b-cdn.net/flags/bb.svg",
    "Belarus": "https://fpp-dashboard-media.b-cdn.net/flags/by.svg",
    "Belgium": "https://fpp-dashboard-media.b-cdn.net/flags/be.svg",
    "Belize": "https://fpp-dashboard-media.b-cdn.net/flags/bz.svg",
    "Benin": "https://fpp-dashboard-media.b-cdn.net/flags/bj.svg",
    "Bermuda": "https://fpp-dashboard-media.b-cdn.net/flags/bm.svg",
    "Bhutan": "https://fpp-dashboard-media.b-cdn.net/flags/bt.svg",
    "Bolivia": "https://fpp-dashboard-media.b-cdn.net/flags/bo.svg",
    "Bosnia": "https://fpp-dashboard-media.b-cdn.net/flags/ba.svg",
    "Botswana": "https://fpp-dashboard-media.b-cdn.net/flags/bw.svg",
    "Brazil": "https://fpp-dashboard-media.b-cdn.net/flags/br.svg",
    "Bulgaria": "https://fpp-dashboard-media.b-cdn.net/flags/bg.svg",
    "Burkina-Faso": "https://fpp-dashboard-media.b-cdn.net/flags/bf.svg",
    "Burundi": "https://fpp-dashboard-media.b-cdn.net/flags/bi.svg",
    "Cambodia": "https://fpp-dashboard-media.b-cdn.net/flags/kh.svg",
    "Cameroon": "https://fpp-dashboard-media.b-cdn.net/flags/cm.svg",
    "Canada": "https://fpp-dashboard-media.b-cdn.net/flags/ca.svg",
    "Chile": "https://fpp-dashboard-media.b-cdn.net/flags/cl.svg",
    "China": "https://fpp-dashboard-media.b-cdn.net/flags/cn.svg",
    "Chinese-Taipei": "https://fpp-dashboard-media.b-cdn.net/flags/tw.svg",
    "Colombia": "https://fpp-dashboard-media.b-cdn.net/flags/co.svg",
    "Congo": "https://fpp-dashboard-media.b-cdn.net/flags/cd.svg",
    "Congo-DR": "https://fpp-dashboard-media.b-cdn.net/flags/cg.svg",
    "Costa-Rica": "https://fpp-dashboard-media.b-cdn.net/flags/cr.svg",
    "Crimea": "https://fpp-dashboard-media.b-cdn.net/flags/ua.svg",
    "Croatia": "https://fpp-dashboard-media.b-cdn.net/flags/hr.svg",
    "Cuba": "https://fpp-dashboard-media.b-cdn.net/flags/cu.svg",
    "Curacao": "https://fpp-dashboard-media.b-cdn.net/flags/cw.svg",
    "Cyprus": "https://fpp-dashboard-media.b-cdn.net/flags/cy.svg",
    "Czech-Republic": "https://fpp-dashboard-media.b-cdn.net/flags/cz.svg",
    "Denmark": "https://fpp-dashboard-media.b-cdn.net/flags/dk.svg",
    "Dominican-Republic": "https://fpp-dashboard-media.b-cdn.net/flags/do.svg",
    "Ecuador": "https://fpp-dashboard-media.b-cdn.net/flags/ec.svg",
    "Egypt": "https://fpp-dashboard-media.b-cdn.net/flags/eg.svg",
    "El-Salvador": "https://fpp-dashboard-media.b-cdn.net/flags/sv.svg",
    "England": "https://fpp-dashboard-media.b-cdn.net/flags/gb-eng.svg",
    "Estonia": "https://fpp-dashboard-media.b-cdn.net/flags/ee.svg",
    "Eswatini": "https://fpp-dashboard-media.b-cdn.net/flags/sz.svg",
    "Ethiopia": "https://fpp-dashboard-media.b-cdn.net/flags/et.svg",
    "Faroe-Islands": "https://fpp-dashboard-media.b-cdn.net/flags/fo.svg",
    "Fiji": "https://fpp-dashboard-media.b-cdn.net/flags/fj.svg",
    "Finland": "https://fpp-dashboard-media.b-cdn.net/flags/fi.svg",
    "France": "https://fpp-dashboard-media.b-cdn.net/flags/fr.svg",
    "Gabon": "https://fpp-dashboard-media.b-cdn.net/flags/ga.svg",
    "Gambia": "https://fpp-dashboard-media.b-cdn.net/flags/gm.svg",
    "Georgia": "https://fpp-dashboard-media.b-cdn.net/flags/ge.svg",
    "Germany": "https://fpp-dashboard-media.b-cdn.net/flags/de.svg",
    "Ghana": "https://fpp-dashboard-media.b-cdn.net/flags/gh.svg",
    "Gibraltar": "https://fpp-dashboard-media.b-cdn.net/flags/gi.svg",
    "Greece": "https://fpp-dashboard-media.b-cdn.net/flags/gr.svg",
    "Grenada": "https://fpp-dashboard-media.b-cdn.net/flags/gd.svg",
    "Guadeloupe": "https://fpp-dashboard-media.b-cdn.net/flags/gp.svg",
    "Guatemala": "https://fpp-dashboard-media.b-cdn.net/flags/gt.svg",
    "Guinea": "https://fpp-dashboard-media.b-cdn.net/flags/gn.svg",
    "Haiti": "https://fpp-dashboard-media.b-cdn.net/flags/ht.svg",
    "Honduras": "https://fpp-dashboard-media.b-cdn.net/flags/hn.svg",
    "Hong-Kong": "https://fpp-dashboard-media.b-cdn.net/flags/hk.svg",
    "Hungary": "https://fpp-dashboard-media.b-cdn.net/flags/hu.svg",
    "Iceland": "https://fpp-dashboard-media.b-cdn.net/flags/is.svg",
    "India": "https://fpp-dashboard-media.b-cdn.net/flags/in.svg",
    "Indonesia": "https://fpp-dashboard-media.b-cdn.net/flags/id.svg",
    "Iran": "https://fpp-dashboard-media.b-cdn.net/flags/ir.svg",
    "Iraq": "https://fpp-dashboard-media.b-cdn.net/flags/iq.svg",
    "Ireland": "https://fpp-dashboard-media.b-cdn.net/flags/ie.svg",
    "Israel": "https://fpp-dashboard-media.b-cdn.net/flags/il.svg",
    "Italy": "https://fpp-dashboard-media.b-cdn.net/flags/it.svg",
    "Ivory-Coast": "https://fpp-dashboard-media.b-cdn.net/flags/ci.svg",
    "Jamaica": "https://fpp-dashboard-media.b-cdn.net/flags/jm.svg",
    "Japan": "https://fpp-dashboard-media.b-cdn.net/flags/jp.svg",
    "Jordan": "https://fpp-dashboard-media.b-cdn.net/flags/jo.svg",
    "Kazakhstan": "https://fpp-dashboard-media.b-cdn.net/flags/kz.svg",
    "Kenya": "https://fpp-dashboard-media.b-cdn.net/flags/ke.svg",
    "Kosovo": "https://fpp-dashboard-media.b-cdn.net/flags/xk.svg",
    "Kuwait": "https://fpp-dashboard-media.b-cdn.net/flags/kw.svg",
    "Kyrgyzstan": "https://fpp-dashboard-media.b-cdn.net/flags/kg.svg",
    "Laos": "https://fpp-dashboard-media.b-cdn.net/flags/la.svg",
    "Latvia": "https://fpp-dashboard-media.b-cdn.net/flags/lv.svg",
    "Lebanon": "https://fpp-dashboard-media.b-cdn.net/flags/lb.svg",
    "Lesotho": "https://fpp-dashboard-media.b-cdn.net/flags/ls.svg",
    "Liberia": "https://fpp-dashboard-media.b-cdn.net/flags/lr.svg",
    "Libya": "https://fpp-dashboard-media.b-cdn.net/flags/ly.svg",
    "Liechtenstein": "https://fpp-dashboard-media.b-cdn.net/flags/li.svg",
    "Lithuania": "https://fpp-dashboard-media.b-cdn.net/flags/lt.svg",
    "Luxembourg": "https://fpp-dashboard-media.b-cdn.net/flags/lu.svg",
    "Macao": "https://fpp-dashboard-media.b-cdn.net/flags/mo.svg",
    "Macedonia": "https://fpp-dashboard-media.b-cdn.net/flags/mk.svg",
    "Malawi": "https://fpp-dashboard-media.b-cdn.net/flags/mw.svg",
    "Malaysia": "https://fpp-dashboard-media.b-cdn.net/flags/my.svg",
    "Maldives": "https://fpp-dashboard-media.b-cdn.net/flags/mv.svg",
    "Mali": "https://fpp-dashboard-media.b-cdn.net/flags/ml.svg",
    "Malta": "https://fpp-dashboard-media.b-cdn.net/flags/mt.svg",
    "Mauritania": "https://fpp-dashboard-media.b-cdn.net/flags/mr.svg",
    "Mauritius": "https://fpp-dashboard-media.b-cdn.net/flags/mu.svg",
    "Mexico": "https://fpp-dashboard-media.b-cdn.net/flags/mx.svg",
    "Moldova": "https://fpp-dashboard-media.b-cdn.net/flags/md.svg",
    "Mongolia": "https://fpp-dashboard-media.b-cdn.net/flags/mn.svg",
    "Montenegro": "https://fpp-dashboard-media.b-cdn.net/flags/me.svg",
    "Morocco": "https://fpp-dashboard-media.b-cdn.net/flags/ma.svg",
    "Myanmar": "https://fpp-dashboard-media.b-cdn.net/flags/mm.svg",
    "Namibia": "https://fpp-dashboard-media.b-cdn.net/flags/na.svg",
    "Nepal": "https://fpp-dashboard-media.b-cdn.net/flags/np.svg",
    "Netherlands": "https://fpp-dashboard-media.b-cdn.net/flags/nl.svg",
    "New-Zealand": "https://fpp-dashboard-media.b-cdn.net/flags/nz.svg",
    "Nicaragua": "https://fpp-dashboard-media.b-cdn.net/flags/ni.svg",
    "Nigeria": "https://fpp-dashboard-media.b-cdn.net/flags/ng.svg",
    "Northern-Ireland": "https://fpp-dashboard-media.b-cdn.net/flags/gb-nir.svg",
    "Norway": "https://fpp-dashboard-media.b-cdn.net/flags/no.svg",
    "Oman": "https://fpp-dashboard-media.b-cdn.net/flags/om.svg",
    "Pakistan": "https://fpp-dashboard-media.b-cdn.net/flags/pk.svg",
    "Palestine": "https://fpp-dashboard-media.b-cdn.net/flags/ps.svg",
    "Panama": "https://fpp-dashboard-media.b-cdn.net/flags/pa.svg",
    "Paraguay": "https://fpp-dashboard-media.b-cdn.net/flags/py.svg",
    "Peru": "https://fpp-dashboard-media.b-cdn.net/flags/pe.svg",
    "Philippines": "https://fpp-dashboard-media.b-cdn.net/flags/ph.svg",
    "Poland": "https://fpp-dashboard-media.b-cdn.net/flags/pl.svg",
    "Portugal": "https://fpp-dashboard-media.b-cdn.net/flags/pt.svg",
    "Qatar": "https://fpp-dashboard-media.b-cdn.net/flags/qa.svg",
    "Romania": "https://fpp-dashboard-media.b-cdn.net/flags/ro.svg",
    "Russia": "https://fpp-dashboard-media.b-cdn.net/flags/ru.svg",
    "Rwanda": "https://fpp-dashboard-media.b-cdn.net/flags/rw.svg",
    "San-Marino": "https://fpp-dashboard-media.b-cdn.net/flags/sm.svg",
    "Saudi-Arabia": "https://fpp-dashboard-media.b-cdn.net/flags/sa.svg",
    "Scotland": "https://fpp-dashboard-media.b-cdn.net/flags/gb-sct.svg",
    "Senegal": "https://fpp-dashboard-media.b-cdn.net/flags/sn.svg",
    "Serbia": "https://fpp-dashboard-media.b-cdn.net/flags/rs.svg",
    "Singapore": "https://fpp-dashboard-media.b-cdn.net/flags/sg.svg",
    "Slovakia": "https://fpp-dashboard-media.b-cdn.net/flags/sk.svg",
    "Slovenia": "https://fpp-dashboard-media.b-cdn.net/flags/si.svg",
    "Somalia": "https://fpp-dashboard-media.b-cdn.net/flags/so.svg",
    "South-Africa": "https://fpp-dashboard-media.b-cdn.net/flags/za.svg",
    "South-Korea": "https://fpp-dashboard-media.b-cdn.net/flags/kr.svg",
    "Spain": "https://fpp-dashboard-media.b-cdn.net/flags/es.svg",
    "Sudan": "https://fpp-dashboard-media.b-cdn.net/flags/sd.svg",
    "Suriname": "https://fpp-dashboard-media.b-cdn.net/flags/sr.svg",
    "Sweden": "https://fpp-dashboard-media.b-cdn.net/flags/se.svg",
    "Switzerland": "https://fpp-dashboard-media.b-cdn.net/flags/ch.svg",
    "Syria": "https://fpp-dashboard-media.b-cdn.net/flags/sy.svg",
    "Tajikistan": "https://fpp-dashboard-media.b-cdn.net/flags/tj.svg",
    "Tanzania": "https://fpp-dashboard-media.b-cdn.net/flags/tz.svg",
    "Thailand": "https://fpp-dashboard-media.b-cdn.net/flags/th.svg",
    "Togo": "https://fpp-dashboard-media.b-cdn.net/flags/tg.svg",
    "Trinidad-And-Tobago": "https://fpp-dashboard-media.b-cdn.net/flags/tt.svg",
    "Tunisia": "https://fpp-dashboard-media.b-cdn.net/flags/tn.svg",
    "Turkey": "https://fpp-dashboard-media.b-cdn.net/flags/tr.svg",
    "Turkmenistan": "https://fpp-dashboard-media.b-cdn.net/flags/tm.svg",
    "Uganda": "https://fpp-dashboard-media.b-cdn.net/flags/ug.svg",
    "Ukraine": "https://fpp-dashboard-media.b-cdn.net/flags/ua.svg",
    "United-Arab-Emirates": "https://fpp-dashboard-media.b-cdn.net/flags/ae.svg",
    "Uruguay": "https://fpp-dashboard-media.b-cdn.net/flags/uy.svg",
    "USA": "https://fpp-dashboard-media.b-cdn.net/flags/us.svg",
    "Uzbekistan": "https://fpp-dashboard-media.b-cdn.net/flags/uz.svg",
    "Venezuela": "https://fpp-dashboard-media.b-cdn.net/flags/ve.svg",
    "Vietnam": "https://fpp-dashboard-media.b-cdn.net/flags/vn.svg",
    "Wales": "https://fpp-dashboard-media.b-cdn.net/flags/gb-wls.svg",
    "Yemen": "https://fpp-dashboard-media.b-cdn.net/flags/ye.svg",
    "Zambia": "https://fpp-dashboard-media.b-cdn.net/flags/zm.svg",
    "Zimbabwe": "https://fpp-dashboard-media.b-cdn.net/flags/zw.svg",
}

LEAGUE_CODE_MAP = {  # media.api-sports.io
    "World, AFC Champions League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/17.png",
    "World, UEFA Champions League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/2.png",
    "World, UEFA Europa Conference League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/848.png",
    "World, UEFA Europa League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/3.png",
    "Algeria, Ligue 1": "https://fpp-dashboard-media.b-cdn.net/football/leagues/186.png",
    "Egypt, Premier League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/233.png",
    "South-Africa, Premier Soccer League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/288.png",
    "Tanzania, Ligi kuu Bara": "https://fpp-dashboard-media.b-cdn.net/football/leagues/567.png",
    "Australia, A-League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/188.png",
    "China, Super League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/169.png",
    "China, League One": "https://fpp-dashboard-media.b-cdn.net/football/leagues/170.png",
    "India, Indian Super League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/323.png",
    "Indonesia, Liga 1": "https://fpp-dashboard-media.b-cdn.net/football/leagues/274.png",
    "Iran, Persian Gulf Pro League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/290.png",
    "Japan, J1 League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/98.png",
    "Japan, J2 League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/99.png",
    "Malaysia, Super League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/278.png",
    "Saudi-Arabia, Pro League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/307.png",
    "Singapore, Premier League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/368.png",
    "South-Korea, K League 1": "https://fpp-dashboard-media.b-cdn.net/football/leagues/292.png",
    "South-Korea, K League 2": "https://fpp-dashboard-media.b-cdn.net/football/leagues/293.png",
    "Vietnam, V.League 1": "https://fpp-dashboard-media.b-cdn.net/football/leagues/340.png",
    "Austria, Bundesliga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/218.png",
    "Austria, 2. Liga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/219.png",
    "Azerbaijan, Premyer Liqa": "https://fpp-dashboard-media.b-cdn.net/football/leagues/419.png",
    "Belarus, Premier League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/116.png",
    "Belgium, Jupiler Pro League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/144.png",
    "Croatia, HNL": "https://fpp-dashboard-media.b-cdn.net/football/leagues/210.png",
    "Czech-Republic, Czech Liga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/345.png",
    "Denmark, Superliga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/119.png",
    "England, Premier League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/39.png",
    "England, Championship": "https://fpp-dashboard-media.b-cdn.net/football/leagues/40.png",
    "England, League One": "https://fpp-dashboard-media.b-cdn.net/football/leagues/41.png",
    "England, League Two": "https://fpp-dashboard-media.b-cdn.net/football/leagues/42.png",
    "Faroe-Islands, Meistaradeildin": "https://fpp-dashboard-media.b-cdn.net/football/leagues/367.png",
    "Finland, Veikkausliiga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/244.png",
    "France, Ligue 1": "https://fpp-dashboard-media.b-cdn.net/football/leagues/61.png",
    "France, Ligue 2": "https://fpp-dashboard-media.b-cdn.net/football/leagues/62.png",
    "Germany, Bundesliga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/78.png",
    "Germany, 2. Bundesliga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/79.png",
    "Iceland, Úrvalsdeild": "https://fpp-dashboard-media.b-cdn.net/football/leagues/164.png",
    "Iceland, 1. Deild": "https://fpp-dashboard-media.b-cdn.net/football/leagues/165.png",
    "Italy, Serie A": "https://fpp-dashboard-media.b-cdn.net/football/leagues/135.png",
    "Italy, Serie B": "https://fpp-dashboard-media.b-cdn.net/football/leagues/136.png",
    "Ireland, Premier Division": "https://fpp-dashboard-media.b-cdn.net/football/leagues/357.png",
    "Ireland, First Division": "https://fpp-dashboard-media.b-cdn.net/football/leagues/358.png",
    "Latvia, Virsliga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/365.png",
    "Latvia, 1. Liga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/364.png",
    "Lithuania, A Lyga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/362.png",
    "Netherlands, Eredivisie": "https://fpp-dashboard-media.b-cdn.net/football/leagues/88.png",
    "Netherlands, Eerste Divisie": "https://fpp-dashboard-media.b-cdn.net/football/leagues/89.png",
    "Norway, Eliteserien": "https://fpp-dashboard-media.b-cdn.net/football/leagues/103.png",
    "Norway, 1. Division": "https://fpp-dashboard-media.b-cdn.net/football/leagues/104.png",
    "Portugal, Primeira Liga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/94.png",
    "Poland, Ekstraklasa": "https://fpp-dashboard-media.b-cdn.net/football/leagues/106.png",
    "Russia, Premier League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/235.png",
    "Scotland, Premiership": "https://fpp-dashboard-media.b-cdn.net/football/leagues/179.png",
    "Spain, La Liga": "https://fpp-dashboard-media.b-cdn.net/football/leagues/140.png",
    "Spain, Segunda División": "https://fpp-dashboard-media.b-cdn.net/football/leagues/141.png",
    "Sweden, Allsvenskan": "https://fpp-dashboard-media.b-cdn.net/football/leagues/113.png",
    "Sweden, Superettan": "https://fpp-dashboard-media.b-cdn.net/football/leagues/114.png",
    "Switzerland, Super League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/207.png",
    "Turkey, Süper Lig": "https://fpp-dashboard-media.b-cdn.net/football/leagues/203.png",
    "Turkey, 1. Lig": "https://fpp-dashboard-media.b-cdn.net/football/leagues/204.png",
    "Ukraine, Premier League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/333.png",
    "Wales, Premier League": "https://fpp-dashboard-media.b-cdn.net/football/leagues/110.png",
    "Argentina, Liga Profesional Argentina": "https://fpp-dashboard-media.b-cdn.net/football/leagues/128.png",
    "Argentina, Primera B Metropolitana": "https://fpp-dashboard-media.b-cdn.net/football/leagues/131.png",
    "Brazil, Serie A": "https://fpp-dashboard-media.b-cdn.net/football/leagues/71.png",
    "Brazil, Serie B": "https://fpp-dashboard-media.b-cdn.net/football/leagues/72.png",
    "Chile, Primera División": "https://fpp-dashboard-media.b-cdn.net/football/leagues/265.png",
    "Colombia, Primera A": "https://fpp-dashboard-media.b-cdn.net/football/leagues/239.png",
    "Colombia, Primera B": "https://fpp-dashboard-media.b-cdn.net/football/leagues/240.png",
    "Costa-Rica, Primera División": "https://fpp-dashboard-media.b-cdn.net/football/leagues/162.png",
    "Ecuador, Liga Pro": "https://fpp-dashboard-media.b-cdn.net/football/leagues/242.png",
    "Mexico, Liga MX": "https://fpp-dashboard-media.b-cdn.net/football/leagues/262.png",
    "Uruguay, Primera División - Apertura": "https://fpp-dashboard-media.b-cdn.net/football/leagues/268.png",
    "USA, Major League Soccer": "https://fpp-dashboard-media.b-cdn.net/football/leagues/253.png",
}
# Base URL for the flags
FLAG_BASE_URL = "https://fpp-dashboard-media.b-cdn.net/flags/"  # media.api-sports.io

MESSAGE_TIMEOUT_SECONDS = 7  # How long messages should persist (in seconds)

# --- Define Default Values for New Filters (use these in reset) ---
DEFAULT_TIME_RANGE = (0, 23)
DEFAULT_RANK_RANGE = (1, 50)  # A sensible wide default for ranks
DEFAULT_ODDS_RANGE = (1.01, 25.0)  # A sensible wide default for odds

# --- Define colors ---
GREEN: str = "#57D58D"  # "#A1FF0A"  # "#A5BE00"  # "#A7C957"


# --- Session State Initialization ---
# Ensure the message list exists in session state
if "transient_messages" not in st.session_state:
    st.session_state.transient_messages = []


# --- Helper Functions (Keep from previous version) ---
def load_weekly_data(file_path):
    try:
        if os.path.exists(file_path):
            return load_data_from_csv(file_path)
            # return pd.read_csv(file_path)
        else:
            st.error(f"File not found: {file_path}")
            return pd.DataFrame()  # Return empty dataframe
    except Exception as e:
        st.error(f"Error loading weekly file {file_path}: {e}")
        return pd.DataFrame()


def remove_duplicate_records(df) -> pd.DataFrame:
    # duplicates_count = df.duplicated(subset=['match_id']).sum()
    # if duplicates_count > 0:
    #     # st.warning(f"Found {duplicates_count} duplicate match_id entries in the CSV. Keeping the first occurrence of each.")
    #     add_transient_message("warning", f"Found {duplicates_count} duplicate match_id entries in the CSV. Keeping the first occurrence of each.")

    # Drop duplicates based on 'match_id', keeping the first instance
    df_deduplicated = df.drop_duplicates(subset=["match_id"], keep="first")

    # --- Convert back to list of dictionaries ---
    # This format seems expected by the rest of your app
    # Handle potential NaN values properly during conversion
    cleaned_data = df_deduplicated.astype(object).where(
        pd.notnull(df_deduplicated), None
    )  # .to_dict('records')
    return cleaned_data


# parse_percent, parse_specific_percent, parse_insights_string, parse_h2h_value
def parse_percent(text_value, default=0):
    if not isinstance(text_value, str):
        return default
    try:
        match = re.search(r"(\d+(\.\d+)?)\s*%", text_value)
        return int(float(match.group(1))) if match else default
    except:
        return default


def parse_specific_percent(text_value, label_prefix, default=0):
    if not isinstance(text_value, str):
        return default
    try:
        # Prioritize exact label match with colon/hyphen
        pattern_exact = rf"^{re.escape(label_prefix)}\s*[:\-]?\s*(\d+(\.\d+)?)\s*%"
        match = re.search(pattern_exact, text_value.strip(), re.IGNORECASE)
        if match:
            return int(float(match.group(1)))

        # Fallback: Look for label within parts separated by '|'
        parts = text_value.split("|")
        if len(parts) > 1:
            for part in parts:
                cleaned_part = part.strip().lower()
                cleaned_label = label_prefix.strip().lower()
                # Check if label like "HT" or "FT" or "O1.5" is at the start or followed by ':'
                pattern_part = (
                    rf"^{re.escape(cleaned_label)}\s*[:\-]?\s*(\d+(\.\d+)?)\s*%"
                )
                match = re.search(pattern_part, cleaned_part, re.IGNORECASE)
                if match:
                    return int(float(match.group(1)))
        # Fallback: if no parts and no exact match, try simple search anywhere
        pattern_simple = rf"{re.escape(label_prefix)}\s*[:\-]?\s*(\d+(\.\d+)?)\s*%"
        match = re.search(pattern_simple, text_value, re.IGNORECASE)
        if match:
            return int(float(match.group(1)))

        return default  # Return default if nothing found
    except:
        return default


def parse_insights_string(text_block):
    parsed_insights = []
    if not isinstance(text_block, str):
        return parsed_insights
    lines = text_block.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip lines that are just hyphens or similar separators if any
        if line.startswith("---") or line.startswith("==="):
            continue
        insight = {
            "label": line,
            "value": None,
            "delta_str": None,
            "delta_val": None,
            "direction": None,
        }
        try:
            # Regex: Label (often ending with '/game' or 'goals' etc): Value (Delta% Direction avg)
            # Allow label to contain spaces. Value is numeric. Delta is optional.
            pattern = r"^(.*?):\s*([\d.]+)\%?\s*(?:\(\s*([+\-]?[\d.]+)\s*%?\s*([🔼🔻])\s*avg\s*\))?"
            match = re.match(pattern, line, re.IGNORECASE)

            if match:
                insight["label"] = match.group(1).strip()
                insight["value"] = match.group(2).strip()
                if match.group(3):  # Delta part exists
                    insight["delta_str"] = (
                        f"{match.group(3).strip()}% {match.group(4)} league average"
                    )
                    try:
                        insight["delta_val"] = float(match.group(3).strip())
                    except ValueError:
                        pass
                    insight["direction"] = match.group(4)
            elif ":" in line:  # Simpler fallback: Label: Value (string value)
                parts = line.split(":", 1)
                insight["label"] = parts[0].strip()
                insight["value"] = parts[1].strip()  # Value could be text here

            # Only add if label is meaningful
            if insight["label"]:
                parsed_insights.append(insight)
        except Exception as e:
            # Optionally log the error: print(f"Error parsing insight line: {line} -> {e}")
            if insight["label"]:  # Add even if parsing failed partially
                parsed_insights.append(insight)
    return parsed_insights


def parse_h2h_value(text_value, key_label, is_numeric=True, default=None):
    """Extracts H or A value from strings like 'H:1.125 | A:1.5'"""
    if not isinstance(text_value, str):
        return default
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
                    return default  # Failed numeric conversion
            else:
                return val_str  # Return as string
        return default  # Label not found
    except Exception:
        return default


def get_progress_color(value):
    """Determines a color based on the percentage value (0-100)."""
    if value < 33:
        return "#f44336"  # Red
    elif value < 66:
        return "#ff9800"  # Orange
    else:
        return "#8bc34a"  # Light Green


def create_colored_progress_bar(value, text_label=None):
    """Generates HTML for a progress bar with color based on value."""
    # st.write(value)
    if value is None or not isinstance(value, (int, float)):
        value = 0  # Default to 0 if invalid input
    value = max(0, min(100, value))  # Clamp value between 0 and 100

    color = get_progress_color(value)
    # Text color based on background for better readability
    text_color = (
        "#ffffff" if value >= 33 else "#000000"
    )  # White text for orange/green, black for red

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
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        st.error(f"Error: Data file '{filepath}' not found.")
        return []
    except Exception as e:
        st.error(f"Error reading file '{filepath}': {e}")
        return []

    # Split into match blocks - assumes '📅' starts a new match
    # Use positive lookahead (?=...) to keep the delimiter
    match_blocks = re.split(r"(?=📅)", content)

    for i, block in enumerate(match_blocks):
        block = block.strip()
        if not block or not block.startswith("📅"):
            continue  # Skip empty blocks or fragments

        match = {"raw_block": block}  # Store raw block for debugging if needed
        lines = block.strip().split("\n")
        current_insight_type = None
        insight_buffer = ""

        # Initialize with defaults (important!)
        match.update(
            {
                "date": None,
                "time": None,
                "country": None,
                "league": None,
                "league_name": None,
                "home_team": None,
                "home_rank": "",
                "away_team": None,
                "away_rank": "",
                "exp_val_h": None,
                "exp_val_d": None,
                "exp_val_a": None,
                "advice": None,
                "value_bets": None,
                "form_home": None,
                "form_away": None,
                "ppg_h": None,
                "ppg_h_all": None,
                "ppg_a": None,
                "ppg_a_all": None,
                "goals_h": None,
                "xg_h": None,
                "goals_a": None,
                "xg_a": None,
                "conceded_h": None,
                "xga_h": None,
                "conceded_a": None,
                "xga_a": None,
                "halves_o05_h": None,
                "halves_o05_a": None,
                "team_goals_h": None,
                "team_goals_a": None,
                "match_goals_h": None,
                "match_goals_a": None,
                "clean_sheet_h": None,
                "clean_sheet_a": None,
                "win_rates_h": None,
                "win_rates_a": None,
                "h2h_hva_record": None,
                "h2h_hva_games": None,
                "h2h_all_record": None,
                "h2h_all_games": None,
                "h2h_hva_ppg_str": None,
                "h2h_hva_goals_str": None,
                "h2h_hva_ou": None,
                "insights_home": "",
                "insights_away": "",
                "insights_total_h": "",
                "insights_total_a": "",
                "confidence_score": None,
                "pred_outcome": None,
                "pred_outcome_conf": None,
                "pred_goals": None,
                "pred_goals_conf": None,
                "pred_corners": None,
                "pred_corners_conf": None,
                "rec_prediction": None,
                "match_id": None,  # Will be generated at the end
            }
        )

        home_team_buffer = None  # Buffer to identify total insights block

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            try:  # Wrap line parsing in try-except
                # --- Parse Core Info ---
                if line.startswith("📅"):
                    m = re.search(r"📅\s*([\d/]+),\s*🕛\s*([\d:]+)", line)
                    if m:
                        match["date"], match["time"] = m.groups()
                elif re.match(
                    r"^[🌍🌎🌏🗺️⚽🏀🏈⚾🥎🎾🏐🏉🎱🔮🎮👾🏆🥇🥈🥉🏅🎖️🏵️🎗️🎀🎁🎂🎃🎄🎅🎆🎇✨🎈🎉🎊🎋🎍🎎🎏🎐🎑🧧🎀🎁🎗️🎟️🎫",
                    line,
                ):  # Match most common flags/emojis used for league
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        match["league"] = parts[1]
                        country_parts = parts[1].split(",", 1)
                        match["country"] = country_parts[0].strip()
                        if len(country_parts) > 1:
                            # Remove parentheses and content inside like ( 24 )
                            league_part = re.sub(
                                r"\s*\(\s*\d+\s*\)\s*$", "", country_parts[1]
                            ).strip()
                            match["league_name"] = league_part
                        else:
                            match["league_name"] = match[
                                "country"
                            ]  # Fallback if no comma
                elif line.startswith("⚡"):
                    # Make rank optional with (?:...)?
                    m = re.search(
                        r"\*(.*?)(?:\s*\((.*?)\))?\s*v\s*(.*?)(?:\s*\((.*?)\))?\*", line
                    )
                    if m:
                        (
                            match["home_team"],
                            match["home_rank"],
                            match["away_team"],
                            match["away_rank"],
                        ) = [g.strip() if g else "" for g in m.groups()]
                        home_team_buffer = match["home_team"]  # Store home team name

                # --- Parse Predictions & Values ---
                elif line.startswith("✨ *Expected Value*:"):
                    match["exp_val_h"] = (
                        re.search(r"H\*:\s*([\d.]+%)", line).group(1)
                        if re.search(r"H\*:\s*([\d.]+%)", line)
                        else None
                    )
                    match["exp_val_d"] = (
                        re.search(r"D\*:\s*([\d.]+%)", line).group(1)
                        if re.search(r"D\*:\s*([\d.]+%)", line)
                        else None
                    )
                    match["exp_val_a"] = (
                        re.search(r"A\*:\s*([\d.]+%)", line).group(1)
                        if re.search(r"A\*:\s*([\d.]+%)", line)
                        else None
                    )
                elif line.startswith("✨ *Advice*:"):
                    match["advice"] = line.split(":", 1)[1].strip()
                elif line.startswith("🎯"):
                    match["value_bets"] = line.split(":", 1)[1].strip()

                # --- Parse Stats ---
                elif line.startswith("📊 *H/All Form*:"):
                    form_line = line.split(": ", 1)[1]
                    parts = form_line.split("//")  # Split current form and all form
                    home_parts = (
                        parts[0].split("║") if "║" in parts[0] else [parts[0], ""]
                    )
                    away_parts = (
                        parts[1].split("║")
                        if len(parts) > 1 and "║" in parts[1]
                        else [parts[1] if len(parts) > 1 else "", ""]
                    )
                    match["form_home"] = home_parts[0].strip()
                    match["form_away"] = away_parts[
                        0
                    ].strip()  # Adjusted splitting needed if format changes
                elif line.startswith("📈 *PPG:"):
                    m_ppg = re.search(
                        r"H\*:\s*([\d.]+)\s*\|\s*All:\s*([\d.]+)\s*║\s*\*A\*:\s*([\d.]+)\s*\|\s*All:\s*([\d.]+)",
                        line,
                    )
                    if m_ppg:
                        try:
                            match["ppg_h"] = float(m_ppg.group(1))
                        except:
                            pass
                        try:
                            match["ppg_h_all"] = float(m_ppg.group(2))
                        except:
                            pass
                        try:
                            match["ppg_a"] = float(m_ppg.group(3))
                        except:
                            pass
                        try:
                            match["ppg_a_all"] = float(m_ppg.group(4))
                        except:
                            pass
                elif line.startswith("⚽ *Goals/g:"):
                    m_goals = re.search(
                        r"H\*:\s*([\d.]+)\s*\(xG:\s*(.*?)\)\s*\|\s*\*A\*:\s*([\d.]+)\s*\(xG:\s*(.*?)\)",
                        line,
                    )
                    if m_goals:
                        try:
                            match["goals_h"] = float(m_goals.group(1))
                        except:
                            pass
                        xg_h_val = m_goals.group(2).strip()
                        match["xg_h"] = (
                            float(xg_h_val) if xg_h_val and xg_h_val != "" else None
                        )
                        try:
                            match["goals_a"] = float(m_goals.group(3))
                        except:
                            pass
                        xg_a_val = (
                            m_goals.group(4).strip().rstrip(")")
                        )  # Strip trailing ')'
                        match["xg_a"] = (
                            float(xg_a_val) if xg_a_val and xg_a_val != "" else None
                        )
                elif line.startswith("⚽ *Conceded/g:"):
                    m_conc = re.search(
                        r"H\*:\s*([\d.]+)\s*\(xGA:\s*(.*?)\)\s*\|\s*\*A\*:\s*([\d.]+)\s*\(xGA:\s*(.*?)\)",
                        line,
                    )
                    if m_conc:
                        try:
                            match["conceded_h"] = float(m_conc.group(1))
                        except:
                            pass
                        xga_h_val = m_conc.group(2).strip()
                        match["xga_h"] = (
                            float(xga_h_val) if xga_h_val and xga_h_val != "" else None
                        )
                        try:
                            match["conceded_a"] = float(m_conc.group(3))
                        except:
                            pass
                        xga_a_val = (
                            m_conc.group(4).strip().rstrip(")")
                        )  # Strip trailing ')'
                        match["xga_a"] = (
                            float(xga_a_val) if xga_a_val and xga_a_val != "" else None
                        )
                elif line.startswith("🥅 *Halves Over 0.5:"):
                    parts = line.split(": ", 1)[1].split(" ║ ")
                    match["halves_o05_h"] = parts[0].strip()
                    match["halves_o05_a"] = parts[1].strip()
                elif line.startswith("⚽ *Team Goals:"):
                    parts = line.split(": ", 1)[1].split(" ║ ")
                    match["team_goals_h"] = parts[0].strip()
                    match["team_goals_a"] = parts[1].strip()
                elif line.startswith("🥅 *Match Goals:"):
                    parts = line.split(": ", 1)[1].split(" ║ ")
                    match["match_goals_h"] = parts[0].strip()
                    match["match_goals_a"] = parts[1].strip()
                elif line.startswith("🧼"):
                    parts = line.split(": ", 1)[1].split(" | ")
                    cs_h = parts[0].replace("*A*", "").strip()
                    cs_a = (
                        parts[1].replace("*A*", "").strip() if len(parts) > 1 else None
                    )
                    match["clean_sheet_h"] = cs_h if cs_h != "nan" else None
                    match["clean_sheet_a"] = cs_a if cs_a and cs_a != "nan" else None
                elif line.startswith("🏆"):
                    parts = line.split(": ", 1)[1].split(" | *A*: ")
                    match["win_rates_h"] = parts[0].strip()
                    match["win_rates_a"] = parts[1].strip() if len(parts) > 1 else None

                # --- Parse H2H ---
                elif line.startswith("📉 *HvA H2H Record*:"):
                    m_h2h_hva = re.search(r":\s*([\d\-]+)\/(\d+)", line)
                    if m_h2h_hva:
                        match["h2h_hva_record"] = m_h2h_hva.group(1)
                        try:
                            match["h2h_hva_games"] = int(m_h2h_hva.group(2))
                        except:
                            pass
                elif line.startswith("📉 *All H2H Record*:"):
                    m_h2h_all = re.search(r":\s*([\d\-]+)\/(\d+)", line)
                    if m_h2h_all:
                        match["h2h_all_record"] = m_h2h_all.group(1)
                        try:
                            match["h2h_all_games"] = int(m_h2h_all.group(2))
                        except:
                            pass
                elif line.startswith("📈 *H2H PPG:"):
                    match["h2h_hva_ppg_str"] = line.split(": ", 1)[1]
                elif line.startswith("⚽ *H2H Goals Scored:"):
                    match["h2h_hva_goals_str"] = line.split(": ", 1)[1]
                elif line.startswith("🥅 *H2H HvA Over/Under*:"):
                    match["h2h_hva_ou"] = line.split(": ", 1)[1]

                # --- Parse Insights (Improved Buffering) ---
                elif line.startswith("✨ *Home Insights*:"):
                    if current_insight_type:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                    current_insight_type = "home"
                    insight_buffer = (
                        line.split(":", 1)[1].strip() + "\n" if ":" in line else "\n"
                    )
                elif line.startswith("✨ *Away Insights*:"):
                    if current_insight_type:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                    current_insight_type = "away"
                    insight_buffer = (
                        line.split(":", 1)[1].strip() + "\n" if ":" in line else "\n"
                    )
                elif line.startswith("✨ *Total Match Insights*:"):
                    if current_insight_type:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                    current_insight_type = None  # Stop basic insight capture
                    insight_buffer = ""
                elif line.startswith("⚡*"):  # Start of Total Match Insights block
                    if insight_buffer and current_insight_type in [
                        "home",
                        "away",
                    ]:  # Save previous basic block
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                    insight_buffer = ""  # Reset buffer for total insights
                    team_name_match = re.match(r"⚡\*(.*?)\s*\(.*?\):", line)
                    if team_name_match:
                        team_name_in_line = team_name_match.group(1).strip()
                        # Assign to total_h or total_a based on home_team_buffer
                        if home_team_buffer and team_name_in_line == home_team_buffer:
                            current_insight_type = "total_h"
                        else:
                            current_insight_type = "total_a"
                        # Start buffer with content after the team name part
                        insight_buffer = (
                            line.split("):", 1)[1].strip() + "\n"
                            if "):" in line
                            else ""
                        )
                    else:  # If pattern fails, assume it's a continuation
                        if current_insight_type:
                            insight_buffer += line + "\n"

                elif current_insight_type and line.startswith(
                    "   -"
                ):  # Indented lines belong to current block
                    insight_buffer += line.strip() + "\n"
                elif current_insight_type and not re.match(
                    r"^(?:🎲|Match Outcome:|Over/Under Goals:|Over/Under Corners:|Recommended Prediction:)",
                    line,
                ):
                    # Capture non-indented lines if we are inside an insight block, before confidence section starts
                    insight_buffer += line.strip() + "\n"

                # --- Parse Confidence & Final Predictions ---
                elif line.startswith("🎲"):
                    if (
                        insight_buffer and current_insight_type
                    ):  # Store last insight block
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                        insight_buffer = ""
                        current_insight_type = None  # Reset type after storing
                    m_conf = re.search(r"Score:\s*(\d+)", line)
                    if m_conf:
                        try:
                            match["confidence_score"] = int(m_conf.group(1))
                        except:
                            pass
                elif line.startswith("Match Outcome:"):
                    m_pred = re.search(
                        r":\s*(.*?)(?:\s*\((\d+)/10\))?$", line
                    )  # Make confidence optional
                    if m_pred:
                        match["pred_outcome"] = m_pred.group(1).strip()
                        if m_pred.group(2):
                            try:
                                match["pred_outcome_conf"] = int(m_pred.group(2))
                            except:
                                pass
                elif line.startswith("Over/Under Goals:"):
                    m_pred = re.search(r":\s*(.*?)(?:\s*\((\d+)/10\))?$", line)
                    if m_pred:
                        match["pred_goals"] = m_pred.group(1).strip()
                        if m_pred.group(2):
                            try:
                                match["pred_goals_conf"] = int(m_pred.group(2))
                            except:
                                pass
                elif line.startswith("Over/Under Corners:"):
                    m_pred = re.search(r":\s*(.*?)(?:\s*\((\d+)/10\))?$", line)
                    if m_pred:
                        match["pred_corners"] = m_pred.group(1).strip()
                        if m_pred.group(2):
                            try:
                                match["pred_corners_conf"] = int(m_pred.group(2))
                            except:
                                pass
                elif line.startswith("Recommended Prediction:"):
                    match["rec_prediction"] = line.split(":", 1)[1].strip()

                # --- Fallback/End of block ---
                elif line_num == len(lines) - 1:  # Last line check
                    if insight_buffer and current_insight_type:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )

            except Exception as e_line:
                st.warning(
                    f"Error parsing line {line_num + 1} in block {i + 1}: '{line}' - {e_line}"
                )
                continue  # Skip to next line on error

        # --- Post-processing & ID ---
        if match.get("home_team") and match.get(
            "date"
        ):  # Only add if core info was parsed
            # Ensure all insight keys exist even if empty
            for k in [
                "insights_home",
                "insights_away",
                "insights_total_h",
                "insights_total_a",
            ]:
                if k not in match:
                    match[k] = ""
            match["match_id"] = (
                f"{match['home_team']}_{match['away_team']}_{match['date']}_{i}"
            )
            all_matches.append(match)
        else:
            st.warning(f"Skipped block {i + 1} due to missing core info (team/date).")

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
        float_cols = [
            "exp_val_h",
            "exp_val_d",
            "exp_val_a",
            "ppg_h",
            "ppg_h_all",
            "ppg_a",
            "ppg_a_all",
            "goals_h",
            "xg_h",
            "goals_a",
            "xg_a",
            "conceded_h",
            "xga_h",
            "conceded_a",
            "xga_a",
            "1h_o05_h",
            "1h_o05_a",
            "2h_o05_h",
            "2h_o05_a",
            "team_goals_0_5_h",
            "team_goals_1_5_h",
            "team_goals_0_5_a",
            "team_goals_1_5_a",
            "match_goals_1_5_a",
            "match_goals_2_5_h",
            "match_goals_1_5_h",
            "match_goals_2_5_a",
            "clean_sheet_h",
            "clean_sheet_a",
            "ht_win_rates_h",
            "ft_win_rates_h",
            "ht_win_rates_a",
            "ft_win_rates_a",
            "h2h_hva_ppg_str",
            "h2h_hva_ppg_str",
            "h2h_h_goals_str",
            "HeadToHeadHomeXG",
            "h2h_a_goals_str",
            "HeadToHeadAwayXG",
            "h2h_hva_o1_5",
            "h2h_hva_o2_5",
            # "confidence_score",
            "pred_outcome_conf",
            "pred_goals_conf",
            "pred_corners_conf",
            "pred_cards_conf",
            "pred_alt_conf",
            "model_success_rate",
            "Last5_HomeBothTeamsToScore",
            "Last5HomeAvergeTotalShots",
            "Last5HomeAvergeTotalShotsOnGoal",
            "Last5HomeAvergeTotalFouls",
            "Last5HomeAvergeTotalcorners",
            "Last5HomeAvergeTotalYellowCards",
            "Last5HomeAvergeTotalRedCards",
            "Last5_AwayBothTeamsToScore",
            "Last5AwayAvergeTotalShots",
            "Last5AwayAvergeTotalShotsOnGoal",
            "Last5AwayAvergeTotalFouls",
            "Last5AwayAvergeTotalcorners",
            "Last5AwayAvergeTotalYellowCards",
            "Last5AwayAvergeTotalRedCards",
            "l5_home_for_league_avg_shots",
            "l5_home_for_league_avg_sot",
            "l5_home_for_league_avg_corners",
            "l5_home_for_league_avg_fouls",
            "l5_home_for_league_avg_yellow_cards",
            "l5_home_for_league_avg_red_cards",
            "l5_away_for_league_avg_shots",
            "l5_away_for_league_avg_sot",
            "l5_away_for_league_avg_corners",
            "l5_away_for_league_avg_fouls",
            "l5_away_for_league_avg_yellow_cards",
            "l5_away_for_league_avg_red_cards",
            "l5_away_against_league_avg_shots",
            "l5_away_against_league_avg_sot",
            "l5_away_against_league_avg_corners",
            "l5_away_against_league_avg_fouls",
            "l5_away_against_league_avg_yellow_cards",
            "l5_away_against_league_avg_red_cards",
            "l5_home_against_league_avg_shots",
            "l5_home_against_league_avg_sot",
            "l5_home_against_league_avg_corners",
            "l5_home_against_league_avg_fouls",
            "l5_home_against_league_avg_yellow_cards",
            "l5_home_against_league_avg_red_cards",
            "HeadToHeadBTTS",
            "HeadToHeadHomeTotalShots",
            "HeadToHeadAwayTotalShots",
            "HeadToHeadHomeShotsOnTarget",
            "HeadToHeadAwayShotsOnTarget",
            "HeadToHeadHomeFouls",
            "HeadToHeadAwayFouls",
            "HeadToHeadHomeCorners",
            "HeadToHeadAwayCorners",
            "HeadToHeadHomeYellowCards",
            "HeadToHeadAwayYellowCards",
            "HeadToHeadHomeRedCards",
            "HeadToHeadAwayRedCards",
            "HeadToHeadOver7Corners",
            "HeadToHeadOver8Corners",
            "HeadToHeadOver9Corners",
            "HeadToHeadOver10Corners",
            "HeadToHeadOver1YellowCards",
            "HeadToHeadOver2YellowCards",
            "HeadToHeadOver3YellowCards",
            "HeadToHeadOver4YellowCards",
            "HomeGoals",
            "AwayGoals",
            "Corners",
            "YellowCards",
            "RedCards",
            "HTRHome",
            "HTRDraw",
            "HTRAway",
            "FTTotalGoalsOver0.5",
            "FTTotalGoalsOver1.5",
            "FTTotalGoalsOver2.5",
            "FTTotalGoalsOver3.5",
            "FTBTTS",
            "FHTTotalGoalsOver0.5",
            "FHTTotalGoalsOver1.5",
            "FHTTotalGoalsOver2.5",
            "FHTTotalGoalsOver3.5",
            "SHTTotalGoalsOver0.5",
            "SHTTotalGoalsOver1.5",
            "SHTTotalGoalsOver2.5",
            "SHTTotalGoalsOver3.5",
            "HomeWinToNil",
            "AwayWinToNil",
            "ScoredFirstTime",
            "HomeSOTResults",
            "HomeShotsResults",
            "HomeFoulsResults",
            "HomeCornersResults",
            "HomeOffsidesResults",
            "HomeYellowsResults",
            "HomeRedsResults",
            "HomeGoalKeeperSavesResults",
            "HomeXGResults",
            "AwaySOTResults",
            "AwayShotsResults",
            "AwayFoulsResults",
            "AwayCornersResults",
            "AwayOffsidesResults",
            "AwayYellowsResults",
            "AwayRedsResults",
            "AwayGoalKeeperSavesResults",
            "AwayXGResults",
            "HomeGoals",
            "AwayGoals",
            "Corners",
            "YellowCards",
            "RedCards",
            "HTRHome",
            "HTRDraw",
            "HTRAway",
            "FTTotalGoalsOver0.5 ",
            "FTTotalGoalsOver1.5 ",
            "FTTotalGoalsOver2.5 ",
            "FTTotalGoalsOver3.5 ",
            "FTBTTS",
            "FHTTotalGoalsOver0.5",
            "FHTTotalGoalsOver1.5",
            "FHTTotalGoalsOver2.5",
            "FHTTotalGoalsOver3.5",
            "SHTTotalGoalsOver0.5",
            "SHTTotalGoalsOver1.5",
            "SHTTotalGoalsOver2.5",
            "SHTTotalGoalsOver3.5",
            "HomeWinToNil",
            "AwayWinToNil",
            "ScoredFirstTime",
            "Last5HomeOver7Corners",
            "Last5HomeOver8Corners",
            "Last5HomeOver9Corners",
            "Last5HomeOver10Corners",
            "Last5HomeAvergeTotalYellowCards",
            "Last5HomeOver1YellowCards",
            "Last5HomeOver2YellowCards",
            "Last5HomeOver3YellowCards",
            "Last5HomeOver4YellowCards",
            "Last5HomeAvergeTotalRedCards",
            "Last5AwayOver7Corners",
            "Last5AwayOver8Corners",
            "Last5AwayOver9Corners",
            "Last5AwayOver10Corners",
            "Last5AwayAvergeTotalYellowCards",
            "Last5AwayOver1YellowCards",
            "Last5AwayOver2YellowCards",
            "Last5AwayOver3YellowCards",
            "Last5AwayOver4YellowCards",
            "Last5AwayAvergeTotalRedCards",
            "l5_league_avg_btts",
            "l5HomeLeagueCleanSheet",
            "l5AwayLeagueCleanSheet",
        ]

        int_cols = ["h2h_hva_games", "h2h_all_games", "match_id"]

        for col in float_cols:
            if col in df.columns:
                # Coerce errors during conversion, then fill NaN with None (or 0 if appropriate)
                # df[col] = df[col].fillna(pd.NA) # Replace NaN with pandas NA for better handling
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for col in int_cols:
            if col in df.columns:
                # Coerce errors during conversion, then fill NaN with None (or 0 if appropriate)
                # df[col] = df[col].fillna(pd.NA) # Replace NaN with pandas NA for better handling
                df[col] = pd.to_numeric(df[col], errors="coerce").astype(
                    "Int64"
                )  # Use nullable Int

        # Fill NaN in string columns with None or empty string
        string_cols = df.select_dtypes(include="object").columns
        df[string_cols] = df[string_cols].fillna(
            ""
        )  # Fill NaNs in object columns with empty strings

        # Typecast HomeGoals and AwayGoals to int if they exist and are not NaN

        # if 'HomeGoals' in df.columns:
        #     df['HomeGoals'] = pd.to_numeric(df['HomeGoals'], errors='coerce')
        #     df.loc[df['HomeGoals'].notna(), 'HomeGoals'] = df['HomeGoals'].astype(int)
        # if 'AwayGoals' in df.columns:
        #     df['AwayGoals'] = pd.to_numeric(df['AwayGoals'], errors='coerce')
        #     df.loc[df['AwayGoals'].notna(), 'AwayGoals'] = df['AwayGoals'].astype(int)

        # --- !!! Deduplication Step !!! ---
        # Check if 'match_id' column exists
        if "match_id" not in df.columns:
            st.error("CSV file is missing the required 'match_id' column.")
            add_transient_message(
                "error", "CSV file is missing the required 'match_id' column."
            )
            return []  # Return empty list

        # Count duplicates before dropping (optional info)
        # initial_rows = len(df)
        duplicates_count = df.duplicated(subset=["match_id"]).sum()
        if duplicates_count > 0:
            # st.warning(f"Found {duplicates_count} duplicate match_id entries in the CSV. Keeping the first occurrence of each.")
            add_transient_message(
                "warning",
                f"Found {duplicates_count} duplicate match_id entries in the CSV. Keeping the first occurrence of each.",
            )

        # Drop duplicates based on 'match_id', keeping the first instance
        df_deduplicated = df.drop_duplicates(subset=["match_id"], keep="first")

        # --- Convert back to list of dictionaries ---
        # This format seems expected by the rest of your app
        # Handle potential NaN values properly during conversion
        cleaned_data = (
            df_deduplicated.astype(object)
            .where(pd.notnull(df_deduplicated), None)
            .to_dict("records")
        )
        cleaned_data_df = pd.DataFrame(cleaned_data)

        if "rec_prediction" in cleaned_data_df.columns:
            cleaned_data_df["rec_prediction"] = cleaned_data_df["rec_prediction"].apply(
                clean_prediction_string
            )

        # Optional: Log how many rows remain
        # st.info(f"Loaded {len(cleaned_data)} unique matches from {initial_rows} rows in CSV.")
        # st.success(f"Successfully loaded {len(cleaned_data)} matches from '{filepath}'.")
        add_transient_message(
            "success",
            f"Successfully loaded {len(cleaned_data)} matches from '{filepath}'.",
        )
        return cleaned_data_df

    except FileNotFoundError:
        st.error(
            f"Error: CSV file '{filepath}' not found. Please create it or change DATA_SOURCE."
        )
        add_transient_message(
            "error",
            f"CSV file '{filepath}' not found. Please create it or change DATA_SOURCE.",
        )
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
    return sample_df.to_dict("records")


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
        "Europe": "🇪🇺",
        # Add more country mappings as needed
    }

    country_code = country_name.title()
    return country_code_mapping.get(country_code, emoji.emojize(f":{country_code}:"))


def get_flag_url(country_name, league_name):
    """Looks up the country code and returns the full flag URL."""
    if not isinstance(country_name, str):
        return None  # Return None if input is not a string

    # Attempt lookup (consider case-insensitivity if needed)
    # code = COUNTRY_CODE_MAP.get(country_name)
    # Case-insensitive example:
    # if country_name not in ['UEFA Champions League','UEFA Europa Conference League','UEFA Europa League','AFC Champions League']:
    league_string = f"{country_name}, {league_name}"
    # url = COUNTRY_CODE_MAP.get(country_name.title()) # Match title case keys
    url = LEAGUE_CODE_MAP.get(league_string)  # Use original case for key lookup
    # else:
    #     url = COUNTRY_CODE_MAP.get(country_name)

    if url:
        return url
    else:
        url = get_country_emoji(country_name)
        # Optional: Log or warn about missing countries
        # print(f"Warning: No flag code found for country: {country_name}")
        return None  # Return None if country not found in map


def handle_week_change():
    """Resets dependent filters when the selected week changes."""
    st.info("Week changed, resetting dependent filters...")  # Optional debug message
    st.session_state.day_filter = "All Dates"
    st.session_state.country_filter = "All"
    st.session_state.league_filter = "All"
    st.session_state.rec_bet_filter = ["All"]
    st.session_state.select_all_rec_bets_cb = False
    # Value Bet options are static, no need to reset typically
    st.session_state.value_bet_filter = ["All"]
    # Reset confidence based on a fixed default or stored overall default
    # Avoid calculating min/max within callback as data isn't loaded yet in this exact step
    st.session_state.include_no_score = True  # Reset checkbox to default state
    st.session_state.confidence_filter = st.session_state.get(
        "global_default_confidence_range", (0, 10)
    )  # Use a fixed default here
    # st.session_state.confidence_filter = st.session_state.get('default_confidence_range', (0, 10))
    # Crucially, also clear the selected match ID when the week changes

    # NEW FILTERS - Reset to their "All Inclusive" states
    st.session_state.time_range_filter = DEFAULT_TIME_RANGE
    st.session_state.home_rank_range_filter = DEFAULT_RANK_RANGE
    st.session_state.away_rank_range_filter = DEFAULT_RANK_RANGE
    st.session_state.value_bet_odds_range_filter = DEFAULT_ODDS_RANGE

    if "selected_match_id" in st.session_state:
        st.session_state.selected_match_id = None


# --- Reset Filters Function (for the reset button) ---
def reset_all_filters():
    # This can now potentially call the week change handler if you want
    # Or keep it separate if it needs slightly different logic (like resetting the week selector itself)
    handle_week_change()  # Call the common reset logic
    # If you want the Reset button to also reset the week selector to latest:
    # This requires storing the key/value of the latest week option
    # if 'latest_week_key' in st.session_state:
    #     st.session_state.week_selector_key = st.session_state.latest_week_key


def add_transient_message(msg_type, text):
    """Adds a message with type and timestamp to the session state list."""
    # Assign a unique ID just in case (optional but can be useful)
    msg_id = f"{msg_type}_{time.time()}_{len(st.session_state.transient_messages)}"
    st.session_state.transient_messages.append(
        {
            "id": msg_id,
            "type": msg_type,  # 'info', 'warning', 'success', 'error'
            "text": text,
            "timestamp": time.time(),
        }
    )


def clean_prediction_string(prediction_str: str) -> str:
    """
    Cleans and standardizes a raw prediction string to facilitate easier parsing.

    Handles issues like:
    - Removing leading/trailing whitespace and converting to lowercase.
    - Removing common useless prefixes like "match outcome:".
    - Splitting compound words like "overundercards:" into "over/under cards ".
    - Removing duplicate adjacent words like "goals goals".
    - Standardizing abbreviations and terms (e.g., "&" to "and", "o/u" to "over/under").

    :param prediction_str: The raw prediction string from your source.
    :return: A cleaned and standardized prediction string.
    """
    if not isinstance(prediction_str, str) or not prediction_str.strip():
        return ""  # Return empty string for invalid input

    # 1. Initial cleanup: lowercase and strip whitespace
    clean_str = prediction_str.strip()  # .lower()

    # 2. Remove common prefixes
    prefixes_to_remove = [
        "Match Outcome: ",
        # "prediction:",
        # "alternative pick:",
        # "alternative signal:",
        # "pick:",
        # "signal:",
    ]
    for prefix in prefixes_to_remove:
        if clean_str.startswith(prefix):
            clean_str = clean_str[len(prefix) :].strip()
            break  # Assume only one prefix needs removal

    # 3. Handle compound words and insert spaces
    # Turns "overundercards:4.5" into "over/under cards : 4.5"
    # Turns "o1.5" into "o 1.5"
    # Turns "home-1.5" into "home -1.5"
    # This uses regex lookarounds to insert spaces without consuming the characters.
    # Insert space between words and numbers/colons/hyphens
    # clean_str = re.sub(r'([a-zA-Z])([:\-0-9])', r'\1 \2', clean_str)
    # # Insert space between numbers and words
    # clean_str = re.sub(r'([0-9])([a-zA-Z])', r'\1 \2', clean_str)

    # 4. Split specific compound words and append context if needed
    # If the string contains ": ", split into two parts
    if (
        "OverUnderCards: " in clean_str
        or "OverUnderCorners: " in clean_str
        or "OverUnderGoals: " in clean_str
    ):
        first, second = clean_str.split(": ", 1)
        first_lower = first.lower()
        # If "cards" in first part, append " cards" to second part
        if "cards" in first_lower:
            clean_str = f"{second} Cards"
        # If "corners" in first part, append " corners" to second part
        elif "corners" in first_lower:
            clean_str = f"{second} Corners"
        # If "goals" in first part, append " goals" to second part
        elif "goals" in first_lower:
            clean_str = f"{second} Goals"
        else:
            clean_str = f"{second}"

    if "Home or Draw (1X)" in clean_str:
        # Replace "Home or Draw (1X)" at the start of the string, possibly followed by confidence in parentheses
        clean_str = re.sub(r"^Home or Draw \(1X\)", "Home Win or Draw", clean_str)

    elif "Away or Draw (X2)" in clean_str:
        # Replace "Away or Draw (X2)" at the start of the string, possibly followed by confidence in parentheses
        clean_str = re.sub(r"^Away or Draw \(X2\)", "Away Win or Draw", clean_str)

    # 5. Standardize terms and abbreviations
    # term_replacements = {
    #     "&": " and ",
    #     "o/u": "over under",
    #     " o ": " over ", # Pad with spaces to avoid replacing 'o' in words like 'home'
    #     " u ": " under ",
    #     " to win": " win", # "Urawa to win" -> "Urawa win"
    #     " to score": "",  # "Team to score over 1.5" -> "Team over 1.5"
    #     " team goals": " goals", # "home team goals over 1.5" -> "home goals over 1.5"
    # }
    # for term, replacement in term_replacements.items():
    #     clean_str = clean_str.replace(term, replacement)

    # 6. Remove duplicate adjacent words
    # Uses a regex with a backreference (\1) to find a word (\b\w+\b)
    # followed by one or more spaces (\s+) and then the exact same word.
    clean_str = re.sub(r"\b(\w+)\s+\1\b", r"\1", clean_str)

    # 7. Final cleanup: normalize whitespace (replace multiple spaces with a single one)
    clean_str = re.sub(r"\s+", " ", clean_str).strip()

    return clean_str


# This is a simplified version, adjust based on your exact prediction strings
# --- NEW Helper function to check ALL prediction types ---
def check_prediction_success(
    prediction_str,
    home_goals,
    away_goals,
    total_corners,
    total_yellow_cards,
    home_team_name,
    away_team_name,
    home_yellow_cards,
    away_yellow_cards,
    home_red_cards,
    away_red_cards,
) -> str | None:
    if (
        not prediction_str
        or not isinstance(prediction_str, str)
        or prediction_str.strip() == "--"
    ):
        return "PENDING"

    pred_cleaned = clean_prediction_string(prediction_str.strip())
    pred_lower = pred_cleaned.lower()

    # --- Data Validity ---
    scores_valid = (
        isinstance(home_goals, (int, float))
        and not math.isnan(home_goals)
        and isinstance(away_goals, (int, float))
        and not math.isnan(away_goals)
    )
    corners_valid = isinstance(total_corners, (int, float)) and not math.isnan(
        total_corners
    )
    # Check for individual team card validity
    home_cards_valid = (
        isinstance(home_yellow_cards, (int, float))
        and not math.isnan(home_yellow_cards)
        and (
            home_red_cards is None
            or (
                isinstance(home_red_cards, (int, float))
                and not math.isnan(home_red_cards)
            )
        )
    )
    away_cards_valid = (
        isinstance(away_yellow_cards, (int, float))
        and not math.isnan(away_yellow_cards)
        and (
            away_red_cards is None
            or (
                isinstance(away_red_cards, (int, float))
                and not math.isnan(away_red_cards)
            )
        )
    )

    all_cards_valid = home_cards_valid and away_cards_valid

    corners_valid = isinstance(total_corners, (int, float)) and not math.isnan(
        total_corners
    )

    home_team_lower = home_team_name.lower().strip() if home_team_name else ""
    away_team_lower = away_team_name.lower().strip() if away_team_name else ""

    # --- Helper variables for outcomes ---
    if scores_valid:
        actual_home_win = home_goals > away_goals
        actual_away_win = away_goals > home_goals
        actual_draw = home_goals == away_goals
        total_actual_goals = home_goals + away_goals

    # --- 1. Team to Win AND Over/Under Goals ---
    # Catches "Urawa to Win and Over 1.5 Goals", "Home Win & Under 3.5 Goals"
    combo_win_ou_match = re.search(
        r"^(.*?)(?:\s+to\s+win)?\s*(?:&|and)\s*(over|under)\s*(\d+\.\d+)\s*goals?$",
        pred_lower,
    )
    if combo_win_ou_match:
        if not scores_valid:
            return "PENDING"
        team_part, ou_type, line_val_str = combo_win_ou_match.groups()
        line_val = float(line_val_str)
        team_part = team_part.strip()

        # Determine which team is predicted to win
        predicted_winner = None
        if team_part == "home win" or team_part == home_team_lower:
            predicted_winner = "home"
        elif team_part == "away win" or team_part == away_team_lower:
            predicted_winner = "away"

        # Check win condition
        win_condition_met = (predicted_winner == "home" and actual_home_win) or (
            predicted_winner == "away" and actual_away_win
        )

        # Check Over/Under condition
        ou_condition_met = (ou_type == "over" and total_actual_goals > line_val) or (
            ou_type == "under" and total_actual_goals < line_val
        )

        if win_condition_met and ou_condition_met:
            return "WIN"
        else:
            return "LOSS"

    # --- 1a. Team to Score Over/Under Goals ---
    # Catches "Home Team to Score Over 1.5 Goals", "Away Team to Score Under 2.5 Goals"
    team_score_ou_match = re.search(
        r"^(home|away)\s*team\s*to\s*score\s*(over|under)\s*(\d+\.\d+)\s*goals?$",
        pred_lower,
    )
    if team_score_ou_match:
        team_side, ou_type, line_val_str = team_score_ou_match.groups()
        line_val = float(line_val_str)
        if not scores_valid:
            return "PENDING"
        if team_side == "home":
            team_goals = home_goals
        else:
            team_goals = away_goals
        if ou_type == "over":
            return "WIN" if team_goals > line_val else "LOSS"
        else:
            return "WIN" if team_goals < line_val else "LOSS"

    # --- 1b. Team to Win
    # Catches {Actual Home Team Name} Win e.g."Hebei Kungfu Win(7/10)", "Home Win", "Away Win", "TeamName Win"
    team_win_match = re.match(
        r"^(.*?)(?:\s+win)(?:\s*\(\d+\/10\))?$", pred_cleaned, re.IGNORECASE
    )
    if team_win_match:
        if not scores_valid:
            return "PENDING"
        team_name_pred = team_win_match.group(1).strip().lower()
        # Check if predicted team matches home or away team
        if team_name_pred == home_team_lower or team_name_pred == "home":
            return "WIN" if actual_home_win else "LOSS"
        elif team_name_pred == away_team_lower or team_name_pred == "away":
            return "WIN" if actual_away_win else "LOSS"
        # If team name doesn't match either, treat as pending or loss
        return "PENDING"

    # --- 2. Double Chance AND Under Goals ---
    # Catches "Away Team Win or Draw and Under 3.5 Goals"
    combo_dc_under_match = re.search(
        r"^(.*?)\s*(?:&|and)\s*under\s*(\d+\.\d+)\s*goals?$", pred_lower
    )
    if combo_dc_under_match:
        if not scores_valid:
            return "PENDING"
        dc_part, line_val_str = combo_dc_under_match.groups()
        line_val = float(line_val_str)
        dc_part = dc_part.strip()

        # Determine which double chance is predicted
        dc_condition_met = False
        if (
            "home" in dc_part
            or "1x" in dc_part
            or (home_team_lower and home_team_lower in dc_part)
        ):
            dc_condition_met = actual_home_win or actual_draw
        elif (
            "away" in dc_part
            or "x2" in dc_part
            or (away_team_lower and away_team_lower in dc_part)
        ):
            dc_condition_met = actual_away_win or actual_draw

        # Check Under condition
        under_condition_met = total_actual_goals < line_val

        if dc_condition_met and under_condition_met:
            return "WIN"
        else:
            return "LOSS"

    # --- 3. Asian Handicap ---
    # Catches "Home -1.5 Asian Handicap", "Yunnan Yukun -1.5 Asian Handicap"
    ah_match = re.search(
        r"^(.*?)\s*([+-]\d+\.\d+)\s*(?:asian\s*)?handicap$", pred_lower
    )
    if ah_match:
        if not scores_valid:
            return "PENDING"
        team_part, handicap_str = ah_match.groups()
        handicap = float(handicap_str)
        team_part = team_part.strip()

        # Determine which team the handicap applies to
        if team_part == "home" or team_part == home_team_lower:
            return "WIN" if (home_goals + handicap) > away_goals else "LOSS"
        elif team_part == "away" or team_part == away_team_lower:
            return "WIN" if (away_goals + handicap) > home_goals else "LOSS"

    # --- 4. Team Clean Sheet / Win to Nil ---
    # Catches "Vitoria Clean Sheet Yes", "Home Team to Win to Nil"
    if "clean sheet" in pred_lower:
        if not scores_valid:
            return "PENDING"
        team_part = pred_lower.replace("clean sheet", "").replace("yes", "").strip()
        if "home" in team_part or (home_team_lower and home_team_lower in team_part):
            return "WIN" if away_goals == 0 else "LOSS"
        elif "away" in team_part or (away_team_lower and away_team_lower in team_part):
            return "WIN" if home_goals == 0 else "LOSS"

    if "win to nil" in pred_lower:
        if not scores_valid:
            return "PENDING"
        team_part = pred_lower.replace("to win to nil", "").strip()
        if "home" in team_part or (home_team_lower and home_team_lower in team_part):
            return "WIN" if actual_home_win and away_goals == 0 else "LOSS"
        elif "away" in team_part or (away_team_lower and away_team_lower in team_part):
            return "WIN" if actual_away_win and home_goals == 0 else "LOSS"

    # --- 5. Team Total Cards Over/Under ---
    # Catches "Home Team Total Cards Over 1.5"
    # team_card_ou_match = re.search(
    #     r"^(home\s*team|away\s*team)\s*(?:total\s*)?cards\s*(over|under)\s*(\d+(?:\.\d+)?)$",
    #     pred_lower,
    # )
    # if team_card_ou_match:
    #     team_part, ou_type, line_val_str = team_card_ou_match.groups()
    #     line_val = float(line_val_str)

    #     target_team_cards = 0
    #     if team_part == "home team":
    #         if not home_cards_valid:
    #             return "PENDING"
    #         # Using booking points: Yellow=1, Red=2. Adjust if your source uses different rules.
    #         target_team_cards = (home_yellow_cards or 0) + ((home_red_cards or 0) * 2)
    #     elif team_part == "away team":
    #         if not away_cards_valid:
    #             return "PENDING"
    #         target_team_cards = (away_yellow_cards or 0) + ((away_red_cards or 0) * 2)

    #     if ou_type == "over":
    #         return "WIN" if target_team_cards > line_val else "LOSS"
    #     elif ou_type == "under":
    #         return "WIN" if target_team_cards < line_val else "LOSS"

    # --- 6. Over/Under CORNERS ---
    corner_ou_match = re.search(
        r"\b(o|u|over|under)\s*(\d+(?:\.\d+)?)\s*(?:corners?|c\b)", pred_lower
    )
    if corner_ou_match:
        if not corners_valid:
            return "PENDING"
        ou_type, line_val_str = (
            corner_ou_match.group(1).lower(),
            corner_ou_match.group(2),
        )
        line_val = float(line_val_str)
        if total_corners == line_val:
            return "PUSH"
        if ou_type.startswith("o"):
            return "WIN" if total_corners > line_val else "LOSS"
        elif ou_type.startswith("u"):
            return "WIN" if total_corners < line_val else "LOSS"
        return "PENDING"  # Should not be reached

    # --- 7. Over/Under YELLOW CARDS ---
    # This pattern looks for "over/under X.Y cards" but specifically avoids "home team" or "away team".
    # Accepts "Over 4.5 Yellow Cards", "Under 3.5 Yellow Cards", "O 2.5 Yellow Cards", etc. (with or without "yellow")
    total_card_ou_match = re.search(
        r"\b(o|u|over|under)\s*(\d+(?:\.\d+)?)\s*(?:yellow\s*)?cards?\b",  # 'yellow' is optional
        pred_lower,
    )
    # st.caption(
    #     f"Total card ou match: {total_card_ou_match}, valid: {all_cards_valid} | HY:{home_yellow_cards} is {home_cards_valid}, AY:{away_yellow_cards} is {away_cards_valid}"
    # )
    if total_card_ou_match:
        if not all_cards_valid:
            return "PENDING"
        ou_type, line_val_str = (
            total_card_ou_match.group(1).lower(),
            total_card_ou_match.group(2),
        )
        line_val = float(line_val_str)

        # Calculate total match booking points
        total_card_points = (
            (home_yellow_cards or 0)
            + (away_yellow_cards or 0)
            + ((home_red_cards or 0) * 2)
            + ((away_red_cards or 0) * 2)
        )

        if total_card_points == line_val:
            return "PUSH"
        if ou_type.startswith("o") or ou_type == "over":
            return "WIN" if total_card_points > line_val else "LOSS"
        elif ou_type.startswith("u") or ou_type == "under":
            return "WIN" if total_card_points < line_val else "LOSS"

    # --- 8. BTTS (Both Teams To Score) ---
    is_btts_yes_pred = re.search(
        r"\b(btts|both\s*teams\s*to\s*score)\s*(yes)?\b|\bgg\b", pred_lower
    ) and not re.search(r"\b(btts|both\s*teams\s*to\s*score)\s*no\b|\bng\b", pred_lower)
    is_btts_no_pred = re.search(
        r"\b(btts|both\s*teams\s*to\s*score)\s*no\b|\bng\b|\bno\s*goal\b", pred_lower
    )
    if is_btts_yes_pred:
        if not scores_valid:
            return "PENDING"
        return "WIN" if home_goals > 0 and away_goals > 0 else "LOSS"
    elif is_btts_no_pred:
        if not scores_valid:
            return "PENDING"
        return "WIN" if not (home_goals > 0 and away_goals > 0) else "LOSS"

    # --- 9. Team-Specific Over/Under Goals (Simplified and Explicit) ---
    # This section will now look for "home team over/under X.Y" or "away team over/under X.Y"
    # OR "{Actual Team Name} over/under X.Y"
    debug_prediction_check = False
    debug_target_pred_str = "home team over 1.5 goals"
    # Pattern 4a: "home team over 1.5 goals" or "home team u 0.5"
    ht_keyword_ou_match = re.search(
        r"\b(home\s*team)\s+(o|u|over|under)\s*(\d+(?:\.\d+)?)(?:\s*goals?)?",
        pred_lower,
    )
    if ht_keyword_ou_match:
        if debug_prediction_check and pred_lower == debug_target_pred_str.lower():
            print(
                f"Matched: Keyword Home Team O/U - Groups: {ht_keyword_ou_match.groups()}"
            )
        if not scores_valid:
            return "PENDING"
        # Group 1 is "home team", Group 2 is o/u, Group 3 is number
        ou_type, line_val_str = (
            ht_keyword_ou_match.group(2).lower(),
            ht_keyword_ou_match.group(3),
        )
        line_val = float(line_val_str)
        if home_goals == line_val:
            return "PUSH"
        if ou_type.startswith("o"):
            return "WIN" if home_goals > line_val else "LOSS"
        elif ou_type.startswith("u"):
            return "WIN" if home_goals < line_val else "LOSS"
        return "PENDING"  # Fallback for this block

    # Pattern 9b: "away team over 1.5 goals" or "away team u 0.5"
    at_keyword_ou_match = re.search(
        r"\b(away\s*team)\s+(o|u|over|under)\s*(\d+(?:\.\d+)?)(?:\s*goals?)?",
        pred_lower,
    )
    if at_keyword_ou_match:
        if debug_prediction_check and pred_lower == debug_target_pred_str.lower():
            print(
                f"Matched: Keyword Away Team O/U - Groups: {at_keyword_ou_match.groups()}"
            )
        if not scores_valid:
            return "PENDING"
        ou_type, line_val_str = (
            at_keyword_ou_match.group(2).lower(),
            at_keyword_ou_match.group(3),
        )
        line_val = float(line_val_str)
        if away_goals == line_val:
            return "PUSH"
        if ou_type.startswith("o"):
            return "WIN" if away_goals > line_val else "LOSS"
        elif ou_type.startswith("u"):
            return "WIN" if away_goals < line_val else "LOSS"
        return "PENDING"

    # Pattern 9c: "{Actual Home Team Name} over 1.5 goals" (if home_team_name is provided)
    if home_team_lower:
        actual_ht_ou_match = re.search(
            rf"(?:^|\s)({re.escape(home_team_lower)})\s+(o|u|over|under)\s*(\d+(?:\.\d+)?)(?:\s*goals?)?",
            pred_lower,
        )
        if actual_ht_ou_match:
            if debug_prediction_check and pred_lower == debug_target_pred_str.lower():
                print(
                    f"Matched: Actual Home Team ({home_team_lower}) O/U - Groups: {actual_ht_ou_match.groups()}"
                )
            if not scores_valid:
                return "PENDING"
            # Group 1 is team name, Group 2 is o/u, Group 3 is number
            ou_type, line_val_str = (
                actual_ht_ou_match.group(2).lower(),
                actual_ht_ou_match.group(3),
            )
            line_val = float(line_val_str)
            if home_goals == line_val:
                return "PUSH"
            if ou_type.startswith("o"):
                return "WIN" if home_goals > line_val else "LOSS"
            elif ou_type.startswith("u"):
                return "WIN" if home_goals < line_val else "LOSS"
            return "PENDING"

    # Pattern 9d: "{Actual Away Team Name} over 1.5 goals" (if away_team_name is provided)
    if away_team_lower:
        actual_at_ou_match = re.search(
            rf"(?:^|\s)({re.escape(away_team_lower)})\s+(o|u|over|under)\s*(\d+(?:\.\d+)?)(?:\s*goals?)?",
            pred_lower,
        )
        if actual_at_ou_match:
            if debug_prediction_check and pred_lower == debug_target_pred_str.lower():
                print(
                    f"Matched: Actual Away Team ({away_team_lower}) O/U - Groups: {actual_at_ou_match.groups()}"
                )
            if not scores_valid:
                return "PENDING"
            ou_type, line_val_str = (
                actual_at_ou_match.group(2).lower(),
                actual_at_ou_match.group(3),
            )
            line_val = float(line_val_str)
            if away_goals == line_val:
                return "PUSH"
            if ou_type.startswith("o"):
                return "WIN" if away_goals > line_val else "LOSS"
            elif ou_type.startswith("u"):
                return "WIN" if away_goals < line_val else "LOSS"
            return "PENDING"

    # --- 10. General Over/Under GOALS ---
    goal_ou_match = re.fullmatch(
        r"(o|u|over|under)\s*(\d+(?:\.\d+)?)(?:\s*goals?)?", pred_lower
    )
    if goal_ou_match:
        if not scores_valid:
            return "PENDING"
        total_actual_goals = home_goals + away_goals
        ou_type, line_val_str = goal_ou_match.group(1).lower(), goal_ou_match.group(2)
        line_val = float(line_val_str)
        if total_actual_goals == line_val:
            return "PUSH"
        if ou_type.startswith("o"):
            return "WIN" if total_actual_goals > line_val else "LOSS"
        elif ou_type.startswith("u"):
            return "WIN" if total_actual_goals < line_val else "LOSS"
        return "PENDING"

    # --- 11. WDL / HAX / Double Chance / Team Name Match Result ---
    # This is the most complex section due to varied formats.
    # Scores must be valid to determine win/loss for these markets.

    is_prediction_format_outcome_market = (
        False  # Heuristic: does it look like an outcome market?
    )
    temp_potential_preds = [
        p.strip().lower() for p in prediction_str.split(",")
    ]  # Comma separated values like "H, X"
    for temp_part_pred in temp_potential_preds:
        # Check for keywords that strongly indicate an outcome market
        if (
            re.search(r"\b(double\s*chance|dc)\b", temp_part_pred)
            or re.fullmatch(r"([hax12])([x12])?", temp_part_pred)
            or re.fullmatch(r"([hax])\s*\(.+\)", temp_part_pred)
            or any(
                kw in temp_part_pred
                for kw in [
                    "home or draw",
                    "away or draw",
                    "home or away",
                    "draw or home",
                    "draw or away",
                    "away or home",
                    "home win",
                    "away win",
                ]
            )
            or temp_part_pred in ["home", "draw", "away", "1", "2", "x"]
            or (home_team_lower and temp_part_pred == home_team_lower)
            or (away_team_lower and temp_part_pred == away_team_lower)
        ):
            is_prediction_format_outcome_market = True
            break

    if not scores_valid:
        return (
            "PENDING" if is_prediction_format_outcome_market else "PENDING"
        )  # Default if scores missing

    actual_home_win = home_goals > away_goals
    actual_away_win = away_goals > home_goals
    actual_draw = home_goals == away_goals

    # Process each part of a potentially comma-separated prediction (e.g., "H, X" for a WDL bet covering two outcomes)
    for part_pred_dc in temp_potential_preds:  # Use a different iterator variable name
        # A. HAX format (e.g., "H(1.5)", "X", "A")
        hax_match = re.fullmatch(r"([hax])(?:\s*\(.+\))?", part_pred_dc)
        if hax_match:
            bet_char = hax_match.group(1)
            if (
                (bet_char == "h" and actual_home_win)
                or (bet_char == "x" and actual_draw)
                or (bet_char == "a" and actual_away_win)
            ):
                return "WIN"
            # If it's a single HAX prediction and it didn't win, it's a loss.
            # If part of a combo, we continue to check other parts.
            if len(temp_potential_preds) == 1:
                return "LOSS"
            continue  # To check next part of a combo HAX bet

        # B. Explicit "Double Chance 1X", "DC X2", etc.
        dc_explicit_match = re.search(
            r"\b(?:double\s*chance|dc)\s*([1x2]{2})\b", part_pred_dc
        )
        if dc_explicit_match:
            dc_symbols = "".join(
                sorted(dc_explicit_match.group(1))
            )  # e.g. "x1" -> "1x"
            if (
                (dc_symbols == "1x" and (actual_home_win or actual_draw))
                or (dc_symbols == "2x" and (actual_away_win or actual_draw))
                or (dc_symbols == "12" and (actual_home_win or actual_away_win))
            ):
                return "WIN"
            return "LOSS"  # If explicitly "double chance X" and it lost

        # C. Symbolic Double Chance (e.g., "1X", "X2", "12" without "double chance" prefix)
        # Ensure it's exactly two chars and valid DC symbols.
        if (
            len(part_pred_dc) == 2
            and all(c in "12x" for c in part_pred_dc)
            and (
                "x" in part_pred_dc
                or (part_pred_dc[0].isdigit() and part_pred_dc[1].isdigit())
            )
        ):
            dc_symbols = "".join(sorted(part_pred_dc))
            if (
                (dc_symbols == "1x" and (actual_home_win or actual_draw))
                or (dc_symbols == "2x" and (actual_away_win or actual_draw))
                or (dc_symbols == "12" and (actual_home_win or actual_away_win))
            ):
                return "WIN"
            # If it was a 2-char DC symbol and didn't win, it's a loss
            # (unless part of a larger comma-separated string not yet fully evaluated)
            if len(temp_potential_preds) == 1:
                return "LOSS"
            continue

        # D. Textual Double Chance ("Home or Draw", "Team A or Draw")
        # Home or Draw
        if (
            re.search(r"\bhome\b", part_pred_dc)
            and re.search(r"\bor\s+draw\b", part_pred_dc)
        ) or (
            home_team_lower
            and re.search(re.escape(home_team_lower), part_pred_dc)
            and re.search(r"\bor\s+draw\b", part_pred_dc)
        ):
            return "WIN" if actual_home_win or actual_draw else "LOSS"
        # Away or Draw
        if (
            re.search(r"\baway\b", part_pred_dc)
            and re.search(r"\bor\s+draw\b", part_pred_dc)
        ) or (
            away_team_lower
            and re.search(re.escape(away_team_lower), part_pred_dc)
            and re.search(r"\bor\s+draw\b", part_pred_dc)
        ):
            return "WIN" if actual_away_win or actual_draw else "LOSS"
        # Home or Away (No Draw)
        if (
            (
                re.search(r"\bhome\b", part_pred_dc)
                and re.search(r"\bor\s+away\b", part_pred_dc)
            )
            or (
                home_team_lower
                and re.search(re.escape(home_team_lower), part_pred_dc)
                and (
                    re.search(r"\bor\s+away\b", part_pred_dc)
                    or (
                        away_team_lower
                        and re.search(
                            r"\bor\s+" + re.escape(away_team_lower), part_pred_dc
                        )
                    )
                )
            )
            or (
                away_team_lower
                and re.search(re.escape(away_team_lower), part_pred_dc)
                and (
                    re.search(r"\bor\s+home\b", part_pred_dc)
                    or (
                        home_team_lower
                        and re.search(
                            r"\bor\s+" + re.escape(home_team_lower), part_pred_dc
                        )
                    )
                )
            )
        ):
            return "WIN" if actual_home_win or actual_away_win else "LOSS"

        # E. Single WDL Keywords/Numbers/Team Names
        # Using re.fullmatch for exact matches of these terms
        if (
            (re.fullmatch(r"home\s*win", part_pred_dc) and actual_home_win)
            or (re.fullmatch(r"home", part_pred_dc) and actual_home_win)
            or (re.fullmatch(r"1", part_pred_dc) and actual_home_win)
        ):
            return "WIN"

        if (
            (re.fullmatch(r"away\s*win", part_pred_dc) and actual_away_win)
            or (re.fullmatch(r"away", part_pred_dc) and actual_away_win)
            or (re.fullmatch(r"2", part_pred_dc) and actual_away_win)
        ):
            return "WIN"

        if (re.fullmatch(r"draw", part_pred_dc) and actual_draw) or (
            re.fullmatch(r"x", part_pred_dc) and actual_draw
        ):
            return "WIN"

        if (
            home_team_lower
            and re.fullmatch(home_team_lower, part_pred_dc)
            and actual_home_win
        ):
            return "WIN"
        if (
            away_team_lower
            and re.fullmatch(away_team_lower, part_pred_dc)
            and actual_away_win
        ):
            return "WIN"

    # If we iterated through all parts of a potential WDL/DC combo (like "H, X")
    # and none of them resulted in a "WIN" (due to `return "WIN"` above),
    # AND the format was indeed identified as an outcome market, then it's a LOSS.
    if is_prediction_format_outcome_market:  # and we haven't returned "WIN"
        return "LOSS"

    # print(f"Debug: Prediction '{prediction_str}' did not match any known betting pattern for WIN/LOSS/PUSH.")
    return "PENDING"


def colorize_performance(performance):
    colored_performance = ""
    for char in performance:
        if char == "W":
            colored_performance += f"{emoji.emojize('🟩')}"  # W{RESET}"
        elif char == "D":
            colored_performance += f"{emoji.emojize('⬜')}"  # D{RESET}"🟨
        elif char == "L":
            colored_performance += f"{emoji.emojize('🟥')}"  # L{RESET}"
    return colored_performance


def sort_data(df):
    # Ensure 'date' and 'time' columns exist
    if "date" not in df.columns or "time" not in df.columns:
        st.warning("Missing 'date' or 'time' column for sorting.")
        return df  # Return unsorted if columns missing

    # Combine date and time, convert to datetime object
    date_format = "%d/%m/%Y"
    time_format = "%H:%M"
    datetime_format = f"{date_format} {time_format}"

    # Combine, coercing errors (invalid formats become NaT - Not a Time)
    df["datetime_obj"] = pd.to_datetime(
        df["date"].astype(str) + " " + df["time"].astype(str),
        format=datetime_format,
        errors="coerce",
    )

    # Optional: Drop rows where datetime conversion failed
    original_rows = len(df)
    df = df.dropna(subset=["datetime_obj"])
    if len(df) < original_rows:
        st.caption(
            f"Dropped {original_rows - len(df)} rows with invalid date/time format."
        )

    # --- Sorting Step ---
    df = df.sort_values(by="datetime_obj", ascending=True)

    # Optional: Drop the helper column if no longer needed
    # df = df.drop(columns=['datetime_obj'])

    return df


def display_stat_row(
    label,
    home_value,
    away_value,
    home_align="right",
    label_align="center",
    away_align="left",
    label_weight="bold",
):
    """Displays a single row, handling None values by showing '--'."""
    col1, col2, col3 = st.columns([2, 3, 2])  # Adjust ratios as needed

    if label in ["Expected Goals (xG)", "Possession (%)"]:
        # Explicitly handle None before creating the final string
        home_display = str(home_value) if home_value is not None else "--"
        away_display = str(away_value) if away_value is not None else "--"
    else:
        home_display = int(home_value) if home_value is not None else "--"
        away_display = int(away_value) if away_value is not None else "--"

    # Use the display strings in markdown
    with col1:
        st.markdown(
            f"<div style='text-align: {home_align};'>{home_display}</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"<div style='text-align: {label_align}; font-weight: {label_weight};'>{label}</div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"<div style='text-align: {away_align};'>{away_display}</div>",
            unsafe_allow_html=True,
        )


# def parse_odds_field_name(field_name):
#     if not field_name.endswith("Odds"): return None
#     parts = field_name[:-4].split('_');
#     if not parts: return None
#     market = parts[0]; bet_specific_parts = parts[1:]
#     bet_specific = " ".join(bet_specific_parts)
#     return {'market': market, 'bet_specific': bet_specific, 'raw_bet_type': "_".join(parts[1:]) + "Odds"}

# def group_odds_by_market(match_data):
#     grouped_odds = defaultdict(list)
#     market_order = {} # To maintain a rough order of markets

#     # Define a preferred order for bet specifics within common markets
#     bet_specific_order = {
#         "Match Winner": ["Home", "Draw", "Away"],
#         "Double Chance": ["Home/Draw", "Home/Away", "Draw/Away"],
#         "Home/Away": ["Home", "Away"], # Draw No Bet essentially
#         "Both Teams Score": ["Yes", "No"],
#         "First Half Winner": ["Home", "Draw", "Away"],
#         "Second Half Winner": ["Home", "Draw", "Away"],
#         # For O/U, sorting will be mostly numerical based on the line
#     }

#     i = 0
#     for field, value in match_data.items():
#         parsed = parse_odds_field_name(field)
#         if parsed:
#             if parsed['market'] not in market_order:
#                 market_order[parsed['market']] = i
#                 i += 1

#             grouped_odds[parsed['market']].append({
#                 'bet_label': parsed['bet_specific'],
#                 'odds_value': value if pd.notna(value) else "--", # Handle NaN odds
#                 'original_field': field
#             })

#     # Sort markets by their appearance order (or define a custom market order)
#     sorted_grouped_odds = dict(sorted(grouped_odds.items(), key=lambda item: market_order.get(item[0], 999)))

#     # Sort bets within each market
#     for market, bets in sorted_grouped_odds.items():
#         if market in bet_specific_order:
#             order_list = bet_specific_order[market]
#             bets.sort(key=lambda x: order_list.index(x['bet_label']) if x['bet_label'] in order_list else 999)
#         elif "Over/Under" in market or "Over Under" in market:
#             # Custom sort for Over/Under: Over X.X then Under X.X, then by X.X value
#             def sort_key_ou(bet_item):
#                 label = bet_item['bet_label']
#                 is_over = label.lower().startswith('over') or label.lower().startswith('o ')
#                 line_match = re.search(r'(\d+(?:\.\d+)?)', label)
#                 line_val = float(line_match.group(1)) if line_match else float('inf')
#                 return (line_val, not is_over) # Sort by line, then Over before Under
#             bets.sort(key=sort_key_ou)
#         else:
#             bets.sort(key=lambda x: x['bet_label']) # Default alphabetical

#     return sorted_grouped_odds

# def parse_odds_field_name(field_name):
# if not field_name.endswith("Odds"): return None
# parts = field_name[:-4].split('_');
# if not parts: return None
# market = parts[0]; bet_specific_parts = parts[1:]
# bet_specific = " ".join(bet_specific_parts)
# return {'market': market, 'bet_specific': bet_specific, 'raw_bet_type': "_".join(parts[1:]) + "Odds"}

# def group_odds_by_market(match_data):
#     grouped_odds = defaultdict(list)
#     market_order = {}
#     bet_specific_order = {
#         "Match Winner": ["Home", "Draw", "Away"], # Corresponds to 1, X, 2
#         "Double Chance": ["Home/Draw", "Home/Away", "Draw/Away"], # Corresponds to 1X, 12, X2
#         "Home/Away": ["Home", "Away"],
#         "Both Teams Score": ["Yes", "No"],
#         "Result & BTTS": [ # Define a specific order for this complex market
#             "Home Yes", "Away Yes", "Draw Yes",
#             "Home No", "Away No", "Draw No"
#         ],
#         # Add other markets with specific outcome orders if needed
#     }
#     # Mapping for display labels if different from bet_label
#     display_label_map = {
#         "Match Winner": {"Home": "1", "Draw": "X", "Away": "2"},
#         "Double Chance": {"Home/Draw": "1X", "Home/Away": "12", "Draw/Away": "X2"}
#     }
#     i = 0
#     for field, value in match_data.items():
#         parsed = parse_odds_field_name(field)
#         if parsed:
#             if parsed['market'] not in market_order:
#                 market_order[parsed['market']] = i; i += 1

#             display_bet_label = parsed['bet_specific']
#             # Check if there's a specific display label for this market and bet
#             if parsed['market'] in display_label_map and parsed['bet_specific'] in display_label_map[parsed['market']]:
#                 display_bet_label = display_label_map[parsed['market']][parsed['bet_specific']]

#             grouped_odds[parsed['market']].append({
#                 'bet_label': parsed['bet_specific'], # Original label for sorting/logic
#                 'display_label': display_bet_label,  # Label for display
#                 'odds_value': value if pd.notna(value) else "N/A",
#                 'original_field': field
#             })
#     sorted_grouped_odds = dict(sorted(grouped_odds.items(), key=lambda item: market_order.get(item[0], 999)))
#     for market, bets in sorted_grouped_odds.items():
#         if market in bet_specific_order:
#             order_list = bet_specific_order[market]
#             # Sort using the original 'bet_label' for consistency with the order_list keys
#             bets.sort(key=lambda x: order_list.index(x['bet_label']) if x['bet_label'] in order_list else 999)
#         elif "Over/Under" in market or "Over Under" in market: # Keep O/U sorting
#             def sort_key_ou(bet_item):
#                 label = bet_item['bet_label'].lower()
#                 is_over = label.startswith('over') or label.startswith('o ')
#                 line_match = re.search(r'(\d+(?:\.\d+)?)', label)
#                 line_val = float(line_match.group(1)) if line_match else float('inf')
#                 return (line_val, not is_over)
#             bets.sort(key=sort_key_ou)
#         else:
#             bets.sort(key=lambda x: x['display_label']) # Default alphabetical on display_label
#     return sorted_grouped_odds


def parse_odds_field_name(field_name):
    if not field_name.endswith("Odds"):
        return None
    parts = field_name[:-4].split("_")
    if not parts:
        return None
    market = parts[0]
    bet_specific_parts = parts[1:]
    bet_specific = " ".join(bet_specific_parts)
    return {
        "market": market,
        "bet_specific": bet_specific,
        "raw_bet_type": "_".join(parts[1:]) + "Odds",
    }


def group_odds_by_market(match_data):
    grouped_odds = defaultdict(list)
    market_order = {}
    bet_specific_order = {
        "Match Winner": ["Home", "Draw", "Away"],
        "Double Chance": ["Home/Draw", "Home/Away", "Draw/Away"],
        "Home/Away": ["Home", "Away"],
        "Both Teams Score": ["Yes", "No"],
        "Result & BTTS": [
            "Home Yes",
            "Away Yes",
            "Draw Yes",
            "Home No",
            "Away No",
            "Draw No",
        ],
        "First Half Winner": ["Home", "Draw", "Away"],
        "Second Half Winner": ["Home", "Draw", "Away"],
        "Both Teams Score - First Half": ["Yes", "No"],  # Added
        "Draw No Bet (1st Half)": ["Home", "Away"],  # Added
        "Draw No Bet (2nd Half)": ["Home", "Away"],  # Added
        # Add more fixed outcome markets here if they have a clear, limited set of outcomes
    }
    display_label_map = {
        "Match Winner": {"Home": "1", "Draw": "X", "Away": "2"},
        "Double Chance": {"Home/Draw": "1X", "Home/Away": "12", "Draw/Away": "X2"},
        "First Half Winner": {"Home": "1", "Draw": "X", "Away": "2"},  # (FH)
        "Second Half Winner": {"Home": "1", "Draw": "X", "Away": "2"},  # (SH)
        "Draw No Bet (1st Half)": {"Home": "Home (DNB)", "Away": "Away (DNB)"},
        "Draw No Bet (2nd Half)": {"Home": "Home (DNB)", "Away": "Away (DNB)"},
    }
    i = 0
    for field, value in match_data.items():
        parsed = parse_odds_field_name(field)
        if parsed:
            if parsed["market"] not in market_order:
                market_order[parsed["market"]] = i
                i += 1
            display_bet_label = parsed["bet_specific"]
            if (
                parsed["market"] in display_label_map
                and parsed["bet_specific"] in display_label_map[parsed["market"]]
            ):
                display_bet_label = display_label_map[parsed["market"]][
                    parsed["bet_specific"]
                ]
            grouped_odds[parsed["market"]].append(
                {
                    "bet_label": parsed["bet_specific"],
                    "display_label": display_bet_label,
                    "odds_value": value if pd.notna(value) else "--",
                    "original_field": field,
                }
            )
    sorted_grouped_odds = dict(
        sorted(grouped_odds.items(), key=lambda item: market_order.get(item[0], 999))
    )
    for market, bets in sorted_grouped_odds.items():
        if market in bet_specific_order:
            order_list = bet_specific_order[market]
            bets.sort(
                key=lambda x: order_list.index(x["bet_label"])
                if x["bet_label"] in order_list
                else 999
            )
        elif (
            "Over/Under" in market or "Over Under" in market or "Total" in market
        ):  # For O/U type markets

            def sort_key_ou(bet_item):
                label = bet_item["bet_label"].lower()
                is_over = "over" in label or label.startswith("o ")
                line_match = re.search(r"(\d+(?:\.\d+)?)", label)
                line_val = float(line_match.group(1)) if line_match else float("inf")
                return (line_val, not is_over)  # Sort by line, then Over before Under

            bets.sort(key=sort_key_ou)
        else:
            bets.sort(key=lambda x: x["display_label"])
    return sorted_grouped_odds


# --- Streamlit App ---
# st.set_page_config(layout="wide")

# Initialize session state
# if 'transient_messages' not in st.session_state:
#     st.session_state.transient_messages = []
if "day_filter" not in st.session_state:
    st.session_state.day_filter = "All Dates"  # Default value
if "country_filter" not in st.session_state:
    st.session_state.country_filter = "All"
if "league_filter" not in st.session_state:
    st.session_state.league_filter = "All"
if "rec_bet_filter" not in st.session_state:
    st.session_state.rec_bet_filter = "All"
if "select_all_rec_bets_cb" not in st.session_state:
    # This will store the state of the "Select All" checkbox.
    # Initialize based on whether rec_bet_filter initially includes all options or is just ["All"]
    st.session_state.select_all_rec_bets_cb = (
        "All" in st.session_state.rec_bet_filter
        and len(st.session_state.rec_bet_filter) == 1
    ) or (
        len(st.session_state.rec_bet_filter) > 1
        and "All" not in st.session_state.rec_bet_filter
    )
if "value_bet_filter" not in st.session_state:
    st.session_state.value_bet_filter = "All"
if "confidence_filter" not in st.session_state:
    # st.session_state.confidence_filter = (0, 10) # Initial default range
    st.session_state.global_default_confidence_range = (0, 10)  # Initial default range
if "include_no_score" not in st.session_state:
    st.session_state.include_no_score = (
        True  # Default to including matches without scores
    )
min_hour = 0
max_hour = 23

# Initialize session state for time range if it doesn't exist
if "time_range_filter" not in st.session_state:
    st.session_state.time_range_filter = (min_hour, max_hour)  # Default to full day

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
message_placeholder = st.empty()  # Create an empty placeholder
display_messages: list[dict] = []
current_time = time.time()

# Filter out expired messages and prepare list of messages to show
st.session_state.transient_messages = [
    msg
    for msg in st.session_state.transient_messages
    if (current_time - msg["timestamp"]) < MESSAGE_TIMEOUT_SECONDS
]

# Create a container within the placeholder to hold multiple messages if needed
with message_placeholder.container():
    for msg in st.session_state.transient_messages:
        if msg["type"] == "info":
            st.info(msg["text"], icon="ℹ️")
        elif msg["type"] == "warning":
            st.warning(msg["text"], icon="⚠️")
        elif msg["type"] == "error":
            st.error(msg["text"], icon="🚨")
        elif msg["type"] == "success":
            st.success(msg["text"], icon="✅")
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
selected_week_display_name = None  # Initialize
if not weekly_file_options:
    st.sidebar.warning("No weekly match files (e.g., 43.csv) found.")
    # Handle case where no files are found - perhaps disable subsequent actions
else:
    selected_week_display_name = st.sidebar.selectbox(
        "Select Match Week:",
        options=list(weekly_file_options.keys()),  # Display "Week 43", "Week 42", etc.
        key="week_selector_key",  # Assign a key to the selector itself
        on_change=handle_week_change,  # *** Attach the callback ***
    )

# --- End Modified Weekly File Selection ---

# --- Load Data for Selected Week ---
# Load data only if a valid week was selected
weekly_df = pd.DataFrame()  # Default to empty DataFrame
selected_file_path = None

# Use the session state key which reflects the *current* selection after any change
current_selected_week_key = st.session_state.get(
    "week_selector_key"
)  # Get value using key

if current_selected_week_key and current_selected_week_key in weekly_file_options:
    selected_file_path = weekly_file_options[current_selected_week_key]
    weekly_df_raw = load_weekly_data(selected_file_path)
    weekly_df = sort_data(weekly_df_raw)  # Sort the DataFrame by date/time

# if selected_week_display_name:
#     selected_file_path = weekly_file_options[selected_week_display_name]
#     weekly_df = load_weekly_data(selected_file_path) # Function is cached

# --- !!! NEW Day Filter based on Loaded Data !!! ---
date_filter_options = ["All Dates"]  # Start with 'All Dates'
valid_dates_in_week = []
date_format = "%d/%m/%Y"  # Define your expected date format

if not weekly_df.empty and "date" in weekly_df.columns:
    # Attempt to parse and validate dates
    unique_dates_str = weekly_df["date"].dropna().unique()
    for d_str in unique_dates_str:
        try:
            # Validate format and convert to datetime object for sorting
            date_obj = datetime.strptime(str(d_str), date_format)
            valid_dates_in_week.append(date_obj)
        except (ValueError, TypeError):
            # st.sidebar.caption(f"Ignoring invalid date format: {d_str}")
            continue  # Skip invalid formats

    # Sort dates chronologically and format back to string for display
    if valid_dates_in_week:
        valid_dates_in_week.sort()
        date_filter_options.extend(
            [d.strftime(date_format) for d in valid_dates_in_week]
        )

# Create the Day filter selectbox
# Ensure the current session state value exists in the options
current_day_selection = st.session_state.day_filter
if current_day_selection not in date_filter_options:
    st.session_state.day_filter = "All Dates"  # Reset if invalid

st.sidebar.selectbox(
    "Date:", options=date_filter_options, key="day_filter"
)  # Use session state key

# Attempt to create it if 'Time' column exists
if "time" in weekly_df.columns:

    def get_hour(time_val):
        if pd.isna(time_val):
            return -1
        if isinstance(time_val, str) and ":" in time_val:
            try:
                return int(time_val.split(":")[0])
            except ValueError:
                return -1
        elif isinstance(time_val, time):  # datetime.time object
            return time_val.hour
        return -1

    weekly_df["Hour"] = weekly_df["time"].apply(get_hour)
else:
    weekly_df["Hour"] = -1  # Default if no Time column
    st.sidebar.warning("Time column not found for hourly filter.")


selected_time_range = st.sidebar.slider(
    "Match Time (Hour of Day):",
    min_value=min_hour,
    max_value=max_hour,
    value=st.session_state.time_range_filter,  # Use value from session state
    step=1,
    key="time_slider",
)
# Update session state when slider changes
if selected_time_range != st.session_state.time_range_filter:
    st.session_state.time_range_filter = selected_time_range

filter_countries_options = ["All"]
if not weekly_df.empty and "country" in weekly_df.columns:
    unique_countries = sorted(weekly_df["country"].dropna().unique())
    filter_countries_options.extend(unique_countries)

# Determine default index for country, ensuring "All" is an option
default_country_index = 0
if st.session_state.country_filter in filter_countries_options:
    default_country_index = filter_countries_options.index(
        st.session_state.country_filter
    )
else:  # If persisted state is somehow invalid, default to "All"
    st.session_state.country_filter = "All"


def country_changed():
    # When country changes, reset the selected league to "All" for that country
    # and update the available league options.
    # The actual selected_country is already in st.session_state.country_filter_cascade
    # This function primarily handles the side effects of that change.
    st.session_state.league_filter = "All"  # Reset league selection


# Store the selected country in its own session state variable for clarity and direct use
# The selectbox widget itself will also store its value under its key ('country_filter_cascade')
selected_country_value = st.sidebar.selectbox(
    "Country:",
    options=filter_countries_options,
    index=default_country_index,
    key="country_filter_cascade",  # Use a unique key for this specific selectbox
    on_change=country_changed,  # Callback to reset league when country changes
)

# Update our specific session state variable if it differs from the widget's state
# This helps ensure our logic uses the most up-to-date value consistently.
if st.session_state.country_filter != selected_country_value:
    st.session_state.country_filter = selected_country_value
    # No need to call country_changed() here again if on_change is used,
    # but if on_change is not used, you'd put the reset logic here.

# --- League Filter (Dynamically Populated) ---
leagues_for_selected_country = [
    "All"
]  # Default if no country or "All" countries selected

if st.session_state.country_filter != "All":
    # Filter weekly_df for the selected country
    country_specific_df = weekly_df[
        weekly_df["country"] == st.session_state.country_filter
    ]
    if not country_specific_df.empty and "league_name" in country_specific_df.columns:
        unique_leagues_in_country = sorted(
            country_specific_df["league_name"].dropna().unique()
        )
        leagues_for_selected_country.extend(unique_leagues_in_country)
elif (
    not weekly_df.empty and "league_name" in weekly_df.columns
):  # If "All" countries is selected
    # Show all unique leagues from the entire DataFrame
    all_unique_leagues = sorted(weekly_df["league_name"].dropna().unique())
    leagues_for_selected_country.extend(all_unique_leagues)


# Determine default index for league
default_league_index = 0
# If the previously selected league is still in the new list of options, keep it.
# Otherwise, default to "All".
if st.session_state.league_filter in leagues_for_selected_country:
    default_league_index = leagues_for_selected_country.index(
        st.session_state.league_filter
    )
else:
    st.session_state.league_filter = (
        "All"  # Reset to "All" if previous selection invalid
    )

selected_league_value = st.sidebar.selectbox(
    "League:",
    options=leagues_for_selected_country,
    index=default_league_index,
    key="league_filter_cascade",  # Use a unique key
)

# Update our specific session state variable for league if it differs
if st.session_state.league_filter != selected_league_value:
    st.session_state.league_filter = selected_league_value


# --- Apply Filters to your DataFrame for Display/Processing ---
filtered_display_df = weekly_df.copy()

# Apply country filter
if st.session_state.country_filter != "All":
    filtered_display_df = filtered_display_df[
        filtered_display_df["country"] == st.session_state.country_filter
    ]

# Apply league filter
if st.session_state.league_filter != "All":
    filtered_display_df = filtered_display_df[
        filtered_display_df["league_name"] == st.session_state.league_filter
    ]


# Extract Recommended Bet options
rec_bet_options = ["All"]
if not weekly_df.empty and "rec_prediction" in weekly_df.columns:
    rec_bet_options = ["All"] + sorted(weekly_df["rec_prediction"].dropna().unique())
# Validate current selection (for multiselect)
current_rec_bet_selection = st.session_state.rec_bet_filter
# Check if all selected items are still valid options OR if the selection is empty (which we also want to reset)
# Validate current selection (for multiselect)
current_rec_bet_selection = st.session_state.rec_bet_filter
is_rec_bet_valid = all(item in rec_bet_options for item in current_rec_bet_selection)
if not is_rec_bet_valid:
    # !!! This is the crucial fix !!!
    st.session_state.rec_bet_filter = ["All"]  # Reset to default if invalid

# Now create the widget
st.sidebar.multiselect(
    "Recommended Bet:", options=rec_bet_options, key="rec_bet_filter"
)

all_rec_bet_options_for_multiselect = []
if not weekly_df.empty and "rec_prediction" in weekly_df.columns:
    # Get unique, non-null prediction types
    all_possible_rec_bets = sorted(weekly_df["rec_prediction"].dropna().unique())
    all_rec_bet_options_for_multiselect = all_possible_rec_bets
else:
    st.sidebar.caption("No recommended bets found in data.")

# st.sidebar.markdown("###### Recommended Bet Type:")


# --- "Select All" Checkbox Logic ---
# This function will be called when the checkbox state changes
def toggle_all_rec_bets():
    if st.session_state.select_all_rec_bets_cb:  # If checkbox is now True (checked)
        # If actual options are available, select them all
        if all_rec_bet_options_for_multiselect:
            st.session_state.rec_bet_filter = (
                all_rec_bet_options_for_multiselect.copy()
            )  # Select all actual options
        else:  # No options to select, so default to "All" signifying no filter
            st.session_state.rec_bet_filter = ["All"]
        st.session_state.select_all_rec_bets_cb = True  # Sync internal state
    else:  # If checkbox is now False (unchecked)
        st.session_state.rec_bet_filter = [
            "All"
        ]  # Default to "All" (meaning no specific filter)
        st.session_state.select_all_rec_bets_cb = False  # Sync internal state


# Display the checkbox
# The key for the checkbox widget itself should be different from the session_state variable
# that holds its logical state, to avoid conflicts during reruns.
st.sidebar.checkbox(
    "Toggle All Recommended Bets",
    value=st.session_state.select_all_rec_bets_cb,  # Controlled by our internal state variable
    key="select_all_rec_bets_cb",  # Widget key
    on_change=toggle_all_rec_bets,
    disabled=not all_rec_bet_options_for_multiselect,  # Disable if no actual bets to select
)


# --- Recommended Bets Multiselect ---
# The options for multiselect should NOT include "All" if we have a separate checkbox for it.
# If all_rec_bet_options_for_multiselect is empty, provide a placeholder.
multiselect_options = (
    all_rec_bet_options_for_multiselect
    if all_rec_bet_options_for_multiselect
    else ["No specific bets available"]
)

# The default value for the multiselect should be what's in st.session_state.rec_bet_filter,
# BUT if "All" is in rec_bet_filter (meaning no specific filter), multiselect should show nothing selected.
current_multiselect_selection = [
    bet for bet in st.session_state.rec_bet_filter if bet != "All"
]


def rec_bet_multiselect_changed():
    # When multiselect changes, update the main session state for the filter
    # And also update the "Select All" checkbox state accordingly
    selected_options = (
        st.session_state.rec_bet_multiselect_widget
    )  # Get value from widget

    if not selected_options:  # If user deselects everything in multiselect
        st.session_state.rec_bet_filter = ["All"]
        st.session_state.select_all_rec_bets_cb = False
    else:
        st.session_state.rec_bet_filter = selected_options
        # Check if all available options are selected
        if all_rec_bet_options_for_multiselect and set(selected_options) == set(
            all_rec_bet_options_for_multiselect
        ):
            st.session_state.select_all_rec_bets_cb = True
        else:
            st.session_state.select_all_rec_bets_cb = False


# selected_rec_bets_from_multiselect = st.sidebar.multiselect(
#     "Filter by Recommended Bet:",
#     options=multiselect_options,
#     default=current_multiselect_selection, # What's actually selected (excluding "All")
#     key='rec_bet_multiselect_widget', # Widget key
#     on_change=rec_bet_multiselect_changed,
#     disabled=not all_rec_bet_options_for_multiselect # Disable if no options
# )

# Value Bet Filter (Hardcoded options H/X/A)
value_bet_filter_options = ["All", "H", "X", "A"]
st.sidebar.multiselect(
    "Value Bet (H/X/A):", options=value_bet_filter_options, key="value_bet_filter"
)
# --- Now define other filters based *on the loaded weekly_df* ---
# Example: Calculate confidence range based on the selected week's data

# --- 3. Value Bet Odds Filter ---
# st.sidebar.markdown("###### Value Bet Odds:")
if (
    "value_bets" in weekly_df.columns
):  # Assuming this column holds "H(1.80)" or "Market (Odds)"
    # Function to extract odds from the ValueBet string
    def extract_odds_from_value_bet(value_bet_str):
        if pd.isna(value_bet_str) or not isinstance(value_bet_str, str):
            return None
        # Look for a number in parentheses, possibly with decimals
        match = re.search(r"\((\d+(?:\.\d+)?)\)", value_bet_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        # Fallback for simple odds strings without market if needed
        try:  # if string is just "1.80"
            return float(value_bet_str)
        except ValueError:
            return None

    # Apply this function once to create a new column for efficient filtering
    if "ValueBetOddsNumeric" not in weekly_df.columns:
        weekly_df["ValueBetOddsNumeric"] = weekly_df["value_bets"].apply(
            extract_odds_from_value_bet
        )

    # Determine min/max odds from the data for slider range
    valid_odds = weekly_df["ValueBetOddsNumeric"].dropna()
    min_odds = float(valid_odds.min()) if not valid_odds.empty else 1.0
    max_odds = float(valid_odds.max()) if not valid_odds.empty else 5.0
    # Ensure min_odds is at least 1.01 or similar if that's typical
    min_odds = max(1.01, min_odds)
    max_odds = max(min_odds + 0.1, max_odds)  # Ensure max > min

    if "value_bet_odds_range_filter" not in st.session_state:
        st.session_state.value_bet_odds_range_filter = (min_odds, max_odds)

    # Ensure the current session state value is within the new dynamic range
    current_vb_range = st.session_state.value_bet_odds_range_filter
    valid_vb_range_start = max(min_odds, current_vb_range[0])
    valid_vb_range_end = min(max_odds, current_vb_range[1])
    if valid_vb_range_start > valid_vb_range_end:  # If range becomes invalid
        valid_vb_range_start = min_odds
        valid_vb_range_end = max_odds
    st.session_state.value_bet_odds_range_filter = (
        valid_vb_range_start,
        valid_vb_range_end,
    )

    selected_value_bet_odds_range = st.sidebar.slider(
        "Value Bet Odds:",
        min_value=min_odds,
        max_value=max_odds,
        value=st.session_state.value_bet_odds_range_filter,
        step=0.01,  # For fine control over odds
        format="%.2f",  # Display odds with 2 decimal places
        key="value_bet_odds_slider",
    )
    if selected_value_bet_odds_range != st.session_state.value_bet_odds_range_filter:
        st.session_state.value_bet_odds_range_filter = selected_value_bet_odds_range
else:
    st.sidebar.caption("ValueBet column not found for odds filtering.")

min_conf = 0
max_conf = 10  # Default scale
if not weekly_df.empty and "confidence_score" in weekly_df.columns:
    valid_scores = pd.to_numeric(
        weekly_df["confidence_score"], errors="coerce"
    ).dropna()
    if not valid_scores.empty:
        min_conf = int(valid_scores.min())
        max_conf = int(valid_scores.max())
    min_conf = max(0, min_conf)
    max_conf = max(min_conf, max_conf)  # Ensure max >= min

# Initialize/Adjust session state for confidence slider based on loaded data range
if "confidence_filter" not in st.session_state:
    st.session_state.confidence_filter = (min_conf, max_conf)
else:  # Ensure current state value is within the actual data range for this week
    current_conf_range = st.session_state.confidence_filter
    st.session_state.confidence_filter = (
        max(min_conf, current_conf_range[0]),
        min(max_conf, current_conf_range[1]),
    )
    if st.session_state.confidence_filter[0] > st.session_state.confidence_filter[1]:
        st.session_state.confidence_filter = (min_conf, max_conf)

st.sidebar.slider(
    "Confidence Score Range:",
    min_value=min_conf,
    max_value=max_conf,
    value=st.session_state.confidence_filter,
    key="confidence_filter",
)

# --- !!! NEW Checkbox !!! ---
st.sidebar.checkbox(
    "Include matches with no score",
    key="include_no_score",  # Link to session state
)
# --- End New Checkbox ---


# --- 2. Rank Filters (Home Rank and Away Rank) ---
# st.sidebar.markdown("###### Team Rank:")
def parse_rank_to_int(rank_str):
    """Converts rank strings like '1st', '2nd', '9th' to integers."""
    if pd.isna(rank_str) or not isinstance(rank_str, str):
        return None  # Or a very high number like 99 if you want unranked at the end

    # Use regex to extract the number part
    match = re.match(r"(\d+)(?:st|nd|rd|th)?", rank_str.lower())
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None  # Or handle error
    return None  # Or handle error if format i


# --- Pre-process Rank Columns ---
if "home_rank" in weekly_df.columns:
    weekly_df["HomeRankNumeric"] = weekly_df["home_rank"].apply(parse_rank_to_int)
else:
    st.warning("HomeRank column not found for rank filtering.")
    weekly_df["HomeRankNumeric"] = pd.NA  # Or some default if you want to proceed

if "away_rank" in weekly_df.columns:
    weekly_df["AwayRankNumeric"] = weekly_df["away_rank"].apply(parse_rank_to_int)
else:
    st.warning("AwayRank column not found for rank filtering.")
    weekly_df["AwayRankNumeric"] = pd.NA

# Check if numeric rank columns were successfully created and have valid data
home_rank_col_exists = (
    "HomeRankNumeric" in weekly_df.columns
    and not weekly_df["HomeRankNumeric"].dropna().empty
)
away_rank_col_exists = (
    "AwayRankNumeric" in weekly_df.columns
    and not weekly_df["AwayRankNumeric"].dropna().empty
)

if home_rank_col_exists and away_rank_col_exists:
    min_rank_possible = 1

    # Determine max rank dynamically from the numeric columns
    max_rank_home = int(weekly_df["HomeRankNumeric"].dropna().max())
    max_rank_away = int(weekly_df["AwayRankNumeric"].dropna().max())
    max_rank_overall = max(
        max_rank_home, max_rank_away, 20
    )  # Ensure at least 20, or a sensible league max

    # Initialize session state for rank ranges if they don't exist
    if "home_rank_range_filter" not in st.session_state:
        st.session_state.home_rank_range_filter = (min_rank_possible, max_rank_overall)
    if "away_rank_range_filter" not in st.session_state:
        st.session_state.away_rank_range_filter = (min_rank_possible, max_rank_overall)

    # Validate current session state values against dynamic range
    current_home_rank_range = st.session_state.home_rank_range_filter
    valid_home_start = max(min_rank_possible, current_home_rank_range[0])
    valid_home_end = min(max_rank_overall, current_home_rank_range[1])
    if valid_home_start > valid_home_end:  # If range becomes invalid
        valid_home_start, valid_home_end = min_rank_possible, max_rank_overall
    st.session_state.home_rank_range_filter = (valid_home_start, valid_home_end)

    current_away_rank_range = st.session_state.away_rank_range_filter
    valid_away_start = max(min_rank_possible, current_away_rank_range[0])
    valid_away_end = min(max_rank_overall, current_away_rank_range[1])
    if valid_away_start > valid_away_end:  # If range becomes invalid
        valid_away_start, valid_away_end = min_rank_possible, max_rank_overall
    st.session_state.away_rank_range_filter = (valid_away_start, valid_away_end)

    selected_home_rank_range = st.sidebar.slider(
        "Home Team Rank Range:",
        min_value=min_rank_possible,
        max_value=max_rank_overall,
        value=st.session_state.home_rank_range_filter,  # Use validated session state value
        step=1,
        key="home_rank_slider",
    )
    if selected_home_rank_range != st.session_state.home_rank_range_filter:
        st.session_state.home_rank_range_filter = selected_home_rank_range

    selected_away_rank_range = st.sidebar.slider(
        "Away Team Rank Range:",
        min_value=min_rank_possible,
        max_value=max_rank_overall,
        value=st.session_state.away_rank_range_filter,  # Use validated session state value
        step=1,
        key="away_rank_slider",
    )
    if selected_away_rank_range != st.session_state.away_rank_range_filter:
        st.session_state.away_rank_range_filter = selected_away_rank_range
else:
    st.sidebar.caption("Numeric rank data not available or empty for filtering.")

# --- Apply filters ---
selected_day = st.session_state.day_filter
selected_country = st.session_state.country_filter
selected_league = st.session_state.league_filter
selected_rec_bets = st.session_state.rec_bet_filter
selected_value_bets = st.session_state.value_bet_filter
selected_confidence_range = st.session_state.confidence_filter
include_no_score_flag = st.session_state.include_no_score  # Get checkbox state
selected_time_range = st.session_state.get(
    "time_range_filter", (0, 23)
)  # Default full day
selected_home_rank_range = st.session_state.get(
    "home_rank_range_filter", (1, 99)
)  # Default wide range
selected_away_rank_range = st.session_state.get(
    "away_rank_range_filter", (1, 99)
)  # Default wide range
selected_value_bet_odds_range = st.session_state.get(
    "value_bet_odds_range_filter", (1.0, 10.0)
)  # Default

# Start with the loaded weekly dataframe
filtered_df = weekly_df.copy()

# Apply filters sequentially (if data exists)
if not filtered_df.empty:
    if selected_day != "All Dates":
        # Ensure consistent format comparison if dates were loaded as strings
        filtered_df = filtered_df[
            filtered_df["date"] == str(selected_day)
        ]  # Filter based on the selected date string

    if selected_country != "All":
        filtered_df = filtered_df[filtered_df["country"] == selected_country]
    if selected_league != "All":
        filtered_df = filtered_df[filtered_df["league_name"] == selected_league]
    # if "All" not in selected_rec_bets:
    #     filtered_df = filtered_df[filtered_df['rec_prediction'].isin(selected_rec_bets)]
    if "rec_prediction" in filtered_df.columns:
        if (
            "All" not in st.session_state.rec_bet_filter
        ):  # If specific bets are selected
            filtered_df = filtered_df[
                filtered_df["rec_prediction"].isin(st.session_state.rec_bet_filter)
            ]
    else:
        if (
            "All" not in st.session_state.rec_bet_filter
        ):  # If specific bets selected but column missing
            st.warning("rec_prediction column for filtering not found.")
    # --- !!! MODIFIED Value Bet Filter Logic !!! ---
    if "All" not in selected_value_bets:
        # Create a boolean mask based on the first character check
        # 1. Convert 'value_bets' column to string type
        # 2. Access the first character using .str[0]
        # 3. Convert to uppercase using .str.upper()
        # 4. Check if this character is in the user's selection ('H', 'X', or 'A') using .isin()
        # 5. Handle potential errors or missing values (e.g., empty strings) by filling NaN with False
        value_mask = (
            filtered_df["value_bets"]
            .astype(str)
            .str[0]
            .str.upper()
            .isin(selected_value_bets)
            .fillna(False)
        )
        filtered_df = filtered_df[value_mask]
    # else: value is None, empty string, not a string, or 'All' wasn't selected -> keep value_bet_match = False

    # Confidence Score Filter
    # Convert score to numeric, handle errors, then apply range
    # Apply Confidence Score Filter (Include rows with NaN scores)
    # --- !!! MODIFIED Confidence Score Filter Logic !!! ---
    # Convert score column to numeric, coercing errors to NaN
    # Extract the first number (before any '/' or non-digit) from confidence_score
    scores_numeric = pd.to_numeric(
        filtered_df["confidence_score"].astype(str).str.extract(r"(\d+)")[0],
        errors="coerce",
    )

    # Create mask for rows that are WITHIN the selected score range
    range_mask = (scores_numeric >= selected_confidence_range[0]) & (
        scores_numeric <= selected_confidence_range[1]
    )

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
    # 1. Time Filter
    if "Hour" in filtered_df.columns:  # Check if 'Hour' helper column exists
        start_hour, end_hour = selected_time_range
        # Ensure we only filter if there are valid hour values to compare against
        # NaNs in 'Hour' column (e.g., from failed parsing) will not satisfy the condition.
        time_condition = (filtered_df["Hour"] >= start_hour) & (
            filtered_df["Hour"] <= end_hour
        )
        filtered_df = filtered_df[
            time_condition | filtered_df["Hour"].isna()
        ]  # Keep NaNs or filter them out:
        # If you want to EXCLUDE rows where Hour is NaN (e.g. time couldn't be parsed):
        # filtered_df = filtered_df[filtered_df['Hour'].notna() & time_condition]
        # Current logic keeps rows if Hour is NaN. For strict filtering:
        # filtered_df = filtered_df[filtered_df['Hour'].between(start_hour, end_hour, inclusive='both')]
    else:
        # Only warn if the user actually tried to filter by time beyond the default "all day"
        if selected_time_range != (0, 23):
            st.warning("Helper 'Hour' column for time filtering not found.")

    # 2. Rank Filters
    if (
        "HomeRankNumeric" in filtered_df.columns
        and "AwayRankNumeric" in filtered_df.columns
    ):
        start_home_rank, end_home_rank = selected_home_rank_range
        start_away_rank, end_away_rank = selected_away_rank_range

        # Apply conditions, NaNs in numeric rank columns will be excluded by .between()
        home_rank_condition = filtered_df["HomeRankNumeric"].between(
            start_home_rank, end_home_rank, inclusive="both"
        )
        away_rank_condition = filtered_df["AwayRankNumeric"].between(
            start_away_rank, end_away_rank, inclusive="both"
        )

        filtered_df = filtered_df[home_rank_condition & away_rank_condition]
    else:
        # Only warn if rank filters are not at their widest possible range
        # This requires knowing the actual max rank from data for default range check.
        # For simplicity, let's assume if numeric columns aren't there, we just skip.
        pass  # Or st.warning("Numeric rank columns for filtering not found.") if user changed from default

    # 3. Value Bet ODDS Filter
    if "ValueBetOddsNumeric" in filtered_df.columns:
        start_vb_odds, end_vb_odds = selected_value_bet_odds_range
        # .between() will exclude NaNs in ValueBetOddsNumeric
        odds_condition = filtered_df["ValueBetOddsNumeric"].between(
            start_vb_odds, end_vb_odds, inclusive="both"
        )
        filtered_df = filtered_df[odds_condition]
    else:
        # Only warn if odds filter is not at its widest possible range
        pass  # Or st.warning("Numeric value bet odds column for
    # st.sidebar.metric("Rows After Filtering (filtered_df)", filtered_df.shape[0] if not filtered_df.empty else 0)
# --- Main Page Content ---


st.title("Match Analysis")

# Use 'selected_week_display_name' for subheader
if selected_week_display_name:
    st.subheader(f"{selected_week_display_name} - {selected_day}")
else:
    st.subheader("Please select a week")

# Convert filtered DataFrame back to list of dicts for existing display logic
# Or adapt display logic to use the filtered_df directly
filtered_matches_list = {}
if not filtered_df.empty:
    # Replace NaN with None for compatibility if needed by display code
    filtered_matches_list = (
        filtered_df.astype(object)
        .where(pd.notnull(filtered_df), None)
        .to_dict("records")
    )


# Now use filtered_matches_list in your existing overview/detail display logic
selected_match_id = st.session_state.get("selected_match_id")
selected_match_data: dict | None = None
# ---Debugging start ---
# st.write("--- Debug Match Finding ---")
# st.write(f"Weekly Df count: {len(weekly_df)}")
# st.write(f"Session State selected_match_id: {selected_match_id} (Type: {type(selected_match_id)})")
# st.write(f"Number of items in filtered_matches_list: {len(filtered_matches_list)}")
# if filtered_matches_list:
#     ids_in_list = [m.get('match_id') for m in filtered_matches_list[:10]] # Show first 10 IDs
#     st.write(f"First IDs in current filtered list: {ids_in_list}")
# # --- Debugging End ---
match_found_flag = False  # Flag to check if loop found it
# --- Handle Cases After Loop ---
if selected_match_id is not None and not match_found_flag:
    # An ID was selected, but it wasn't found in the *current* filtered list
    # st.warning(f"Match details for ID {selected_match_id} are not visible with the current filters. Displaying overview.", icon="⚠️")
    # Decide if you want to automatically clear the selection when filters hide the match
    # Option 1: Keep selection, user might change filters back
    # Option 2: Clear selection automatically
    # clear_selected_match()
    selected_match_data = None  # Ensure it's None if not found
# Find selected match data (search in the filtered list)
if selected_match_id:
    for match in filtered_matches_list:
        if isinstance(match, dict) and match.get("match_id") == selected_match_id:
            selected_match_data = match
            break
    # ... (logic if selected match not found in filtered list) ...

# --- Display Overview or Details using filtered_matches_list ---
if not selected_match_data:
    # Overview Display
    overview_header_cols = st.columns([3, 1])
    with overview_header_cols[0]:
        st.write("")  # Placeholder instead of header, already have subheader
    with overview_header_cols[1]:
        st.button(
            "Reset Filters", on_click=reset_all_filters, use_container_width=True
        )  # Keep reset button

    if not filtered_matches_list:
        st.info("No matches found matching your filter criteria for this week.")
    else:
        # --- Display matches grouped by league using filtered_matches_list ---
        matches_by_league = defaultdict(list)
        for match in filtered_matches_list:
            if isinstance(match, dict):
                league_key = (
                    match.get("country", "Unknown Country"),
                    match.get("league_name", "Unknown League"),
                )
                matches_by_league[league_key].append(match)

        if not matches_by_league:
            st.info(
                "No matches found matching filter criteria."
            )  # Should be caught earlier
        else:
            sorted_leagues = sorted(matches_by_league.keys())
            for league_key in sorted_leagues:
                country, league_name = league_key
                league_matches = matches_by_league[league_key]
                league_matches_played = [
                    match
                    for match in league_matches
                    if match.get("HomeGoals") is not None
                    and match.get("AwayGoals") is not None
                    and match.get("rec_prediction")
                ]

                # Count WINs for rec_prediction in league_matches_played
                win_count = 0
                for match in league_matches_played:
                    result = check_prediction_success(
                        match.get("rec_prediction"),
                        match.get("HomeGoals"),
                        match.get("AwayGoals"),
                        match.get("Corners"),
                        match.get("YellowCards"),
                        match.get("home_team"),
                        match.get("away_team"),
                        match.get("HomeYellowsResults"),
                        match.get("AwayYellowsResults"),
                        match.get("HomeRedResults"),
                        match.get("AwayRedResults"),
                    )
                    # st.caption(result)
                    if result == "WIN":
                        win_count += 1

                # Display count of WINs
                # st.caption(f"Best Bet WINs: {win_count} / {len(league_matches_played)}")

                if (
                    league_matches_played
                ):  # league_matches and "model_success_rate" in league_matches[0]:
                    sr = win_count / len(
                        league_matches_played
                    )  # league_matches[0].get("model_success_rate")
                else:
                    sr = None

                # Display League Header with country emoji and league name in one row
                col1, col2 = st.columns([0.1, 4])  # Adjust column widths as needed
                with col1:
                    flag_url_from_data = None
                    if (
                        league_matches
                    ):  # Check if there are matches in this league group
                        first_match_in_league = league_matches[0]
                        if isinstance(first_match_in_league, dict):
                            # --- Adjust this key name if needed ---
                            flag_url_from_data = first_match_in_league.get(
                                "country_logo"
                            )

                    # if flag_url_from_data:
                    #     st.image(flag_url_from_data, width=25) # Display image if URL found
                    # else:
                    # Optional: Placeholder if no flag URL found in data or no matches
                    # This might happen if the key is missing or the league_matches list is empty
                    # if league_name in ['UEFA Champions League', 'UEFA Europa Conference League', 'UEFA Europa League', 'AFC Champions League']:
                    #     flag_url = get_flag_url(league_name)
                    #     if flag_url:
                    #         st.image(flag_url, width=25)

                    flag_url = get_flag_url(
                        country, league_name
                    )  # Get emoji for country
                    if flag_url:
                        st.image(flag_url, width=25)
                with col2:
                    if sr is not None:
                        st.markdown(
                            f"##### {country} - {league_name} (Success Rate: {sr * 100:.1f}%)"
                        )
                    else:
                        st.markdown(
                            f"##### {country} - {league_name} (Success Rate: --)"
                        )

                # Display matches within the league
                for match in league_matches:
                    # --- Get match data ---
                    if match is not None and isinstance(match, dict):
                        home_goals = match.get("HomeGoals", "?")
                        away_goals = match.get("AwayGoals", "?")
                        corners = match.get("Corners")  # Get corners count
                        home_team = match.get("home_team", "?")
                        away_team = match.get("away_team", "?")
                        rec_pred = match.get("rec_prediction")
                        alt_pred = match.get("pred_alt", "--")  # ,
                        alt_pred_conf = match.get("pred_alt_conf", "--")  # ,
                        value_bet = match.get("value_bets")
                        match_time = match.get("time", "--")
                        confidence_score = match.get("confidence_score")
                        cards = match.get("YellowCards", "--")
                        outcome_conf = match.get("pred_outcome_conf")
                        outcome_val_raw = match.get("pred_outcome", "--").split("(")
                        advice = match.get("advice", "--")

                    else:
                        home_goals = away_goals = corners = home_team = away_team = (
                            rec_pred
                        ) = value_bet = match_time = confidence_score = cards = (
                            outcome_conf
                        ) = outcome_val_raw = None
                    # print(rec_pred)
                    # --- Determine Result Status ---
                    result_status = None
                    scores_available = isinstance(
                        home_goals, (int, float)
                    ) and isinstance(away_goals, (int, float))  # More specific check

                    if scores_available:
                        if home_goals > away_goals:
                            result_status = "Home Win"
                        elif away_goals > home_goals:
                            result_status = "Away Win"
                        else:
                            result_status = "Draw"

                    with st.container():
                        col0, col1, col2, col3, col4, col5, col6, col7, col8 = (
                            st.columns([0.1, 0.3, 0.2, 0.7, 0.1, 0.4, 0.5, 0.9, 0.4])
                        )

                        with col0:
                            try:
                                # Extract the first number from confidence_score (handles formats like "5/10", "[4/10]", or text)
                                conf_match = re.search(r"(\d+)", str(confidence_score))
                                conf_val = (
                                    int(conf_match.group(1)) if conf_match else None
                                )
                                if conf_val is not None and conf_val >= 7:
                                    st.markdown("⭐", unsafe_allow_html=True)
                                else:
                                    st.markdown(" ", unsafe_allow_html=True)
                            except (ValueError, TypeError):
                                pass

                        with col1:
                            st.markdown(
                                f"**{match.get('date', '--')}**", unsafe_allow_html=True
                            )
                            st.markdown(f"**{match_time}**", unsafe_allow_html=True)

                        with col2:
                            home_logo = (
                                match.get("home_team_logo", None)
                                or "https://placehold.co/25x25/000000/FFF"
                            )
                            away_logo = (
                                match.get("away_team_logo", None)
                                or "https://placehold.co/25x25/000000/FFF"
                            )
                            st.image(home_logo, width=25)
                            st.image(away_logo, width=25)

                        with col3:
                            home_rank = match.get("home_rank", None) or "--"
                            away_rank = match.get("away_rank", None) or "--"
                            st.markdown(
                                f"**{home_team} ({home_rank})**", unsafe_allow_html=True
                            )
                            st.markdown(
                                f"**{away_team} ({away_rank})**", unsafe_allow_html=True
                            )

                        with col4:
                            # Apply bold styling to the winning score
                            # Display Score with Highlighting
                            if scores_available:
                                home_score_display = f"{int(home_goals)}"
                                away_score_display = f"{int(away_goals)}"

                                # Apply bold styling to the winning score
                                if result_status == "Home Win":
                                    home_score_display = f"**{int(home_goals)}**"
                                    st.markdown(
                                        f"{home_score_display}", unsafe_allow_html=True
                                    )
                                    st.caption(
                                        f"{away_score_display}", unsafe_allow_html=True
                                    )
                                elif result_status == "Away Win":
                                    away_score_display = f"**{int(away_goals)}**"
                                    st.caption(
                                        f"{home_score_display}", unsafe_allow_html=True
                                    )
                                    st.markdown(
                                        f"{away_score_display}", unsafe_allow_html=True
                                    )

                                else:
                                    st.markdown(
                                        f"{home_score_display}", unsafe_allow_html=True
                                    )
                                    st.markdown(
                                        f"{away_score_display}", unsafe_allow_html=True
                                    )

                        with col5:
                            # --- NEW: Display Stats if available ---
                            corners = match.get("Corners")
                            yellow_cards = match.get("YellowCards")
                            red_cards = match.get("RedCards")
                            stats_display = []
                            if corners is not None:
                                # st.markdown(
                                #     f"<div style='font-size: 1em'>🚩 {int(corners)}</div>",
                                #     unsafe_allow_html=True,
                                # )
                                stats_display.append(f"🚩 {int(corners)}")
                            if yellow_cards is not None:
                                # Using a unicode character for yellow card
                                # st.markdown(
                                #     f"<div style='font-size: 1em'>🟨 {int(yellow_cards)}</div>",
                                #     unsafe_allow_html=True,
                                # )
                                stats_display.append(f"🟨 {int(yellow_cards)}")
                            if red_cards is not None:
                                # Using a unicode character for red card
                                # st.markdown(
                                #     f"<div style='font-size: 1em'>🟥 {int(red_cards)}</div>",
                                #     unsafe_allow_html=True,
                                # )
                                stats_display.append(f"🟥 {int(red_cards)}")

                            if stats_display:
                                # Join the stats with a separator and display
                                st.markdown(f"{' '.join(stats_display)}")
                            else:
                                st.markdown("")

                        with col6:
                            home_xg: str = match.get("xg_h")
                            away_xg: str = match.get("xg_a")
                            home_xg_display = (
                                f"xG: {home_xg:.2f}"
                                if isinstance(home_xg, (int, float))
                                else ""
                            )
                            away_xg_display = (
                                f"xG: {away_xg:.2f}"
                                if isinstance(away_xg, (int, float))
                                else ""
                            )
                            home_xga: str = match.get("xga_h")
                            away_xga: str = match.get("xga_a")
                            home_xga_display = (
                                f"xGA: {home_xga:.2f}"
                                if isinstance(home_xga, (int, float))
                                else ""
                            )
                            away_xga_display = (
                                f"xGA: {away_xga:.2f}"
                                if isinstance(away_xga, (int, float))
                                else ""
                            )
                            st.markdown(
                                f"<div style='text-align:center; font-size:1em;'>{home_xg_display} &ndash; {home_xga_display}</div>",
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f"<div style='text-align:center; font-size:1em;'>{away_xg_display} &ndash; {away_xga_display}</div>",
                                unsafe_allow_html=True,
                            )

                        with col7:
                            confidence_text = (
                                f" ({confidence_score}/10)"
                                if confidence_score is not None
                                else ""
                            )

                            # --- Check and Display Best Bet ---
                            # Pass necessary stats to the check function
                            # rec_pred_parts = rec_pred.split("(")
                            # rec_pred_only = rec_pred_parts[0].strip()
                            rec_pred_won = check_prediction_success(
                                rec_pred,
                                home_goals,
                                away_goals,
                                corners,
                                cards,
                                home_team,
                                away_team,
                                match.get("HomeYellowsResults", None),
                                match.get("AwayYellowsResults", None),
                                match.get("HomeRedResults", 0),
                                match.get("HomeRedResults", 0),
                            )
                            # st.info(f"Cards: {cards}")
                            if rec_pred and rec_pred != "--":
                                pred_display = (
                                    f"Best Bet: {rec_pred}({confidence_score})"
                                )
                                if rec_pred_won == "WIN":
                                    pred_display = f"Best Bet: <span style='color:{GREEN}; '>{rec_pred}({confidence_score}) ✅</span>"  # Added checkmark
                                    st.markdown(
                                        f"<div style='text-align:left; font-size:1em; font-weight:normal;text-decoration: overline;'>{pred_display}</div>",
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(
                                        f"<div style='text-align:left; font-size:1em; font-weight:normal;text-decoration: overline;'>{pred_display}</div>",
                                        unsafe_allow_html=True,
                                    )

                            else:
                                st.caption("")

                            # --- Check and Display Value Tip ---
                            # Pass necessary stats to the check function
                            value_bet_won = check_prediction_success(
                                value_bet,
                                home_goals,
                                away_goals,
                                corners,
                                cards,
                                home_team,
                                away_team,
                                match.get("HomeYellowsResults", None),
                                match.get("AwayYellowsResults", None),
                                match.get("HomeRedResults", 0),
                                match.get("HomeRedResults", 0),
                            )

                            # st.info(value_bet_won)
                            if value_bet:
                                value_display = f"Value Tip: {value_bet}"
                                if value_bet_won == "WIN":
                                    value_display = f"Value Tip: <span style='color:{GREEN};'>{value_bet} ✅</span>"
                                    st.markdown(
                                        f"<div style='text-align:left; font-size:1em; font-weight:normal;'>{value_display}</div>",
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(
                                        f"<div style='text-align:left; font-size:1em; font-weight:normal;'>{value_display}</div>",
                                        unsafe_allow_html=True,
                                    )

                                    # st.caption("")
                            else:
                                st.caption("")

                            # --- Check and Display Alternative Bet ---
                            # Pass necessary stats to the check function
                            alt_bet_won = check_prediction_success(
                                alt_pred,
                                home_goals,
                                away_goals,
                                corners,
                                cards,
                                home_team,
                                away_team,
                                match.get("HomeYellowsResults", None),
                                match.get("AwayYellowsResults", None),
                                match.get("HomeRedResults", 0),
                                match.get("HomeRedResults", 0),
                            )

                            # st.info(alt_bet_won)
                            if alt_pred:
                                alt_bet_display = f"Alt. Bet: {alt_pred}"
                                if alt_bet_won == "WIN":
                                    alt_bet_display = f"Alt. Bet: <span style='color:{GREEN};'>{alt_pred} ✅</span>"
                                #     st.markdown(
                                #         f"<div style='text-align:left; font-size:1em; font-weight:bold;text-decoration: overline;'>{alt_bet_display}</div>",
                                #         unsafe_allow_html=True,
                                #     )
                                # else:
                                #     st.markdown(
                                #         f"<div style='text-align:left; font-size:1em; font-weight:bold;text-decoration: overline;'>{alt_bet_display}</div>",
                                #         unsafe_allow_html=True,
                                #     )

                                # st.caption("")
                            # else:
                            #     st.caption("")

                            # --- Check and Display Match outcome ---
                            # Pass necessary stats to the check function
                            outcome_conf = (
                                f"({outcome_val_raw[-1].strip()}"
                                if outcome_val_raw[-1].strip()
                                else ""
                            )
                            outcome_val = f"{outcome_val_raw[0].strip()}{outcome_conf}"

                            outcome_bet_won = check_prediction_success(
                                outcome_val,
                                home_goals,
                                away_goals,
                                corners,
                                cards,
                                home_team,
                                away_team,
                                match.get("HomeYellowsResults", None),
                                match.get("AwayYellowsResults", None),
                                match.get("HomeRedResults", 0),
                                match.get("HomeRedResults", 0),
                            )

                            if outcome_val:
                                outcome_display = f"Match outcome: {outcome_val}"  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{outcome_val}</span>"
                                if outcome_bet_won == "WIN":
                                    outcome_display = f"Match outcome: <span style='color:{GREEN};'>{outcome_val} ✅</span>"
                                    st.markdown(
                                        f"<div style='text-align:left; font-size:1em; font-weight:normal;text-decoration: none;'>{outcome_display}</div>",
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(
                                        f"<div style='text-align:left; font-size:1em; font-weight:normal;text-decoration: none;'>{outcome_display}</div>",
                                        unsafe_allow_html=True,
                                    )
                                    # st.caption("")
                            else:
                                st.caption("")

                        with col8:
                            st.button(
                                "View Details",
                                key=match["match_id"],
                                on_click=set_selected_match,
                                args=(match["match_id"],),
                                use_container_width=True,
                            )
                            # st.text("View Details")

                st.markdown("---", unsafe_allow_html=True)  # Divider between leagues

    # else:
    #     # Handles case where selected_date is None (no valid dates found)
    #     st.info("Please select filters to view matches.")

else:
    # Display Dashboard
    st.sidebar.divider()
    st.sidebar.button("⬅️ Back to Overview", on_click=clear_selected_match)
    overview_header_cols = st.columns([3, 1])
    with overview_header_cols[0]:
        st.write("")  # Placeholder instead of header, already have subheader
    with overview_header_cols[1]:
        st.button(
            "⬅️ Back to Overview",
            on_click=clear_selected_match,
            use_container_width=True,
        )  #

    # st.text(f"📅 {selected_match_data.get('date','--')} 🕛 {selected_match_data.get('time','--')}")
    # st.text(f"🌍 {selected_match_data.get('country','--')} - {selected_match_data.get('league_name','--')}")
    # st.header(f"{selected_match_data.get('home_team','?')} vs {selected_match_data.get('away_team','?')}")
    # match_cols1,match_cols2,match_cols3, match_cols4, match_cols5 = st.columns([1,2, 1, 2, 1])
    # col1, match_cols2 = st.columns([1, 4])
    # Arrange the columns as per the requirement
    # Define columns - adjust ratios if needed
    country = selected_match_data.get("country", "--")
    league_name = selected_match_data.get("league_name", "--")
    home_goals = selected_match_data.get("HomeGoals", "?")
    away_goals = selected_match_data.get("AwayGoals", "?")
    corners = selected_match_data.get("Corners")
    yellow_cards = selected_match_data.get("YellowCards")
    red_cards = selected_match_data.get("RedCards")

    scores_available = isinstance(home_goals, (int, float)) and isinstance(
        away_goals, (int, float)
    )  # More

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

    home_logo = selected_match_data.get(
        "home_team_logo", "https://placehold.co/100x100/000000/FFF"
    )
    away_logo = selected_match_data.get(
        "away_team_logo", "https://placehold.co/100x100/000000/FFF"
    )

    (
        match_cols0,
        match_cols1,
        match_cols2,
        match_cols3,
        match_cols4,
        match_cols5,
        match_cols6,
    ) = st.columns(
        [0.5, 1, 0.5, 2, 0.5, 1, 0.5]  # Example ratios: Adjust based on content width
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
            unsafe_allow_html=True,
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
                <span style="font-weight: bold; font-size: 1.5em; display: block; margin-bottom: 0.2em;">{selected_match_data.get("home_team", "--")}</span>
                <span style="font-weight: bold; font-size: 1.2em; display: block; margin-bottom: 0.2em;">{selected_match_data.get("home_rank", "--")}</span>
                PPG: {selected_match_data.get("ppg_h", "--")}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with match_cols2:
        # st.markdown(f"# {home_score_display}", unsafe_allow_html=True)
        st.markdown(
            f"""
            
            <div style="text-align: center;">
                <span style="font-weight: bold; font-size: 3em; display: block; margin-top: 0.2em;margin-bottom: 0.2em;">{home_score_display}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with match_cols3:
        # --- Column 3: Text, Center-aligned ---
        flag_url = get_flag_url(country, league_name)  # Get emoji for country

        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="{flag_url}" width="50">
            </div>
            <div style="text-align: center;">
                {country} - {selected_match_data.get("league_name", "--")}
                </div>
            <div style="text-align: center;">
                {selected_match_data.get("date", "--")} | {selected_match_data.get("time", "--")}
            </div>
            <br>
            <div style="text-align: center;">
                {stats}
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("📊 Match Report", expanded=False):
            # Expected Goals (xG) - Needs specific formatting
            home_xg = selected_match_data.get("HomeXGResults")
            away_xg = selected_match_data.get("AwayXGResults")
            # Format only if it's a number (float or int), otherwise pass None to the helper
            home_xg_display = (
                f"{home_xg:.2f}" if isinstance(home_xg, (int, float)) else home_xg
            )
            away_xg_display = (
                f"{away_xg:.2f}" if isinstance(away_xg, (int, float)) else away_xg
            )
            display_stat_row("Expected Goals (xG)", home_xg_display, away_xg_display)

            # Shots - No special format, just handle None
            home_shots = selected_match_data.get("HomeShotsResults")
            away_shots = selected_match_data.get("AwayShotsResults")
            display_stat_row(
                "Shots", home_shots, away_shots
            )  # Helper handles None -> '--'

            # Shots on Target - No special format
            home_sot = selected_match_data.get("HomeSOTResults")
            away_sot = selected_match_data.get("AwaySOTResults")
            display_stat_row("Shots on Target", home_sot, away_sot)

            # Possession (%) - Needs '%' sign added
            home_poss = selected_match_data.get("HomeBallPossessionResults")
            away_poss = selected_match_data.get("AwayBallPossessionResults")
            # Add '%' only if value is not None
            home_poss_display = f"{home_poss}" if home_poss is not None else home_poss
            away_poss_display = f"{away_poss}" if away_poss is not None else away_poss
            display_stat_row("Possession (%)", home_poss_display, away_poss_display)

            # Corners - No special format
            home_cor = selected_match_data.get("HomeCornersResults")
            away_cor = selected_match_data.get("AwayCornersResults")
            display_stat_row("Corners", home_cor, away_cor)

            # Fouls Committed - No special format
            home_fouls = selected_match_data.get("HomeFoulsResults")
            away_fouls = selected_match_data.get("AwayFoulsResults")
            display_stat_row("Fouls Committed", home_fouls, away_fouls)

            # Goalkeeper Saves - No special format
            home_saves = selected_match_data.get("HomeGoalKeeperSavesResults")
            away_saves = selected_match_data.get("AwayGoalKeeperSavesResults")
            display_stat_row("Goalkeeper Saves", home_saves, away_saves)

            # Offsides - No special format
            home_offs = selected_match_data.get("HomeOffsidesResults")
            away_offs = selected_match_data.get("AwayOffsidesResults")
            display_stat_row("Offsides", home_offs, away_offs)

            # Yellow Cards - No special format
            home_yellows = selected_match_data.get("HomeYellowsResults")
            away_yellows = selected_match_data.get("AwayYellowsResults")
            display_stat_row("Yellow Cards", home_yellows, away_yellows)

            # Red Cards - No special format
            home_reds = selected_match_data.get("HomeRedsResults")
            away_reds = selected_match_data.get("AwayRedsResults")
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
            unsafe_allow_html=True,
        )

    with match_cols5:
        # --- Column 4: Text, Right-aligned ---
        st.markdown(
            f"""
            <div style="text-align: right;">
                <span style="font-weight: bold; font-size: 1.5em; display: block; margin-bottom: 0.2em;">{selected_match_data.get("away_team", "--")}</span>
                <span style="font-weight: bold; font-size: 1.2em; display: block; margin-bottom: 0.2em;">{selected_match_data.get("away_rank", "--")}</span>
                PPG: {selected_match_data.get("ppg_a", "--")}
            </div>
            """,
            unsafe_allow_html=True,
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
            unsafe_allow_html=True,
        )

        # st.image(selected_match_data.get('away_logo_url', ''), width=60)
        # Using st.image directly also works here as left is default. HTML wrapper is for consistency. actual path or URL

    st.markdown("---")
    confidence_score = selected_match_data.get("confidence_score", "--")
    confidence_text = (
        f" ({confidence_score}/10)" if confidence_score is not None else ""
    )
    home_goals = selected_match_data.get("HomeGoals", "?")
    away_goals = selected_match_data.get("AwayGoals", "?")
    corners = selected_match_data.get("Corners")  # Get corners count
    cards = selected_match_data.get("YellowCards", "--")
    home_team = selected_match_data.get("home_team", "?")
    away_team = selected_match_data.get("away_team", "?")
    rec_pred = selected_match_data.get("rec_prediction")
    value_bet = selected_match_data.get("value_bets")
    match_time = selected_match_data.get("time", "--")
    card_pred = selected_match_data.get("pred_card", "--")

    Last5_HomeBothTeamsToScore = (
        selected_match_data.get("Last5_HomeBothTeamsToScore", "--") * 100
    )
    Last5HomeAvergeTotalShots = (
        selected_match_data.get("Last5HomeAvergeTotalShots") or 0
    )
    Last5HomeAvergeTotalShotsOnGoal = (
        selected_match_data.get("Last5HomeAvergeTotalShotsOnGoal") or 0
    )
    Last5HomeAvergeTotalFouls = (
        selected_match_data.get("Last5HomeAvergeTotalFouls") or 0
    )
    Last5HomeAvergeTotalcorners = (
        selected_match_data.get("Last5HomeAvergeTotalcorners") or 0
    )
    Last5HomeAvergeTotalYellowCards = (
        selected_match_data.get("Last5HomeAvergeTotalYellowCards") or 0
    )
    # Last5HomeAvergeTotalRedCards  = selected_match_data.get('Last5HomeAvergeTotalRedCards') or 0

    Last5_AwayBothTeamsToScore = (
        selected_match_data.get("Last5_AwayBothTeamsToScore", "--") * 100
    )
    Last5AwayAvergeTotalShots = (
        selected_match_data.get("Last5AwayAvergeTotalShots") or 0
    )
    Last5AwayAvergeTotalShotsOnGoal = (
        selected_match_data.get("Last5AwayAvergeTotalShotsOnGoal") or 0
    )
    Last5AwayAvergeTotalFouls = (
        selected_match_data.get("Last5AwayAvergeTotalFouls") or 0
    )
    Last5AwayAvergeTotalcorners = (
        selected_match_data.get("Last5AwayAvergeTotalcorners") or 0
    )
    Last5AwayAvergeTotalYellowCards = (
        selected_match_data.get("Last5AwayAvergeTotalYellowCards") or 0
    )
    # Last5AwayAvergeTotalRedCards  = selected_match_data.get('Last5AwayAvergeTotalRedCards') or 0

    l5_home_for_league_avg_shots = (
        selected_match_data.get("l5_home_for_league_avg_shots") or 0
    )
    l5_home_for_league_avg_sot = (
        selected_match_data.get("l5_home_for_league_avg_sot") or 0
    )
    l5_home_for_league_avg_fouls = (
        selected_match_data.get("l5_home_for_league_avg_fouls") or 0
    )
    l5_home_for_league_avg_corners = (
        selected_match_data.get("l5_home_for_league_avg_corners") or 0
    )
    l5_home_for_league_avg_yellow_cards = (
        selected_match_data.get("l5_home_for_league_avg_yellow_cards") or 0
    )
    l5_home_for_league_avg_red_cards = (
        selected_match_data.get("l5_home_for_league_avg_red_cards") or 0
    )

    l5_home_against_league_avg_shots = (
        selected_match_data.get("l5_home_against_league_avg_shots") or 0
    )
    l5_home_against_league_avg_sot = (
        selected_match_data.get("l5_home_against_league_avg_sot") or 0
    )
    l5_home_against_league_avg_corners = (
        selected_match_data.get("l5_home_against_league_avg_corners") or 0
    )
    l5_home_against_league_avg_fouls = (
        selected_match_data.get("l5_home_against_league_avg_fouls") or 0
    )
    l5_home_against_league_avg_yellow_cards = (
        selected_match_data.get("l5_home_against_league_avg_yellow_cards") or 0
    )
    l5_home_against_league_avg_red_cards = (
        selected_match_data.get("l5_home_against_league_avg_red_cards") or 0
    )

    l5_away_for_league_avg_shots = (
        selected_match_data.get("l5_away_for_league_avg_shots") or 0
    )
    l5_away_for_league_avg_sot = (
        selected_match_data.get("l5_away_for_league_avg_sot") or 0
    )
    l5_away_for_league_avg_fouls = (
        selected_match_data.get("l5_away_for_league_avg_fouls") or 0
    )
    l5_away_for_league_avg_corners = (
        selected_match_data.get("l5_away_for_league_avg_corners") or 0
    )
    l5_away_for_league_avg_yellow_cards = (
        selected_match_data.get("l5_away_for_league_avg_yellow_cards") or 0
    )
    l5_away_for_league_avg_red_cards = (
        selected_match_data.get("l5_away_for_league_avg_red_cards") or 0
    )

    l5_away_against_league_avg_shots = (
        selected_match_data.get("l5_away_against_league_avg_shots") or 0
    )
    l5_away_against_league_avg_sot = (
        selected_match_data.get("l5_away_against_league_avg_sot") or 0
    )
    l5_away_against_league_avg_corners = (
        selected_match_data.get("l5_away_against_league_avg_corners") or 0
    )
    l5_away_against_league_avg_fouls = (
        selected_match_data.get("l5_away_against_league_avg_fouls") or 0
    )
    l5_away_against_league_avg_yellow_cards = (
        selected_match_data.get("l5_away_against_league_avg_yellow_cards") or 0
    )
    l5_away_against_league_avg_red_cards = (
        selected_match_data.get("l5_away_against_league_avg_red_cards") or 0
    )

    HeadToHeadHomeXG = selected_match_data.get("HeadToHeadHomeXG") or 0
    HeadToHeadAwayXG = selected_match_data.get("HeadToHeadAwayXG") or 0
    HeadToHeadHomeTotalShots = selected_match_data.get("HeadToHeadHomeTotalShots") or 0
    HeadToHeadHomeShotsOnTarget = (
        selected_match_data.get("HeadToHeadHomeShotsOnTarget") or 0
    )
    HeadToHeadHomeFouls = selected_match_data.get("HeadToHeadHomeFouls") or 0
    HeadToHeadHomeCorners = selected_match_data.get("HeadToHeadHomeCorners") or 0
    HeadToHeadHomeYellowCards = (
        selected_match_data.get("HeadToHeadHomeYellowCards") or 0
    )
    HeadToHeadHomeRedCards = selected_match_data.get("HeadToHeadHomeRedCards") or 0

    HeadToHeadAwayTotalShots = selected_match_data.get("HeadToHeadAwayTotalShots") or 0
    HeadToHeadAwayShotsOnTarget = (
        selected_match_data.get("HeadToHeadAwayShotsOnTarget") or 0
    )
    HeadToHeadAwayFouls = selected_match_data.get("HeadToHeadAwayFouls") or 0
    HeadToHeadAwayCorners = selected_match_data.get("HeadToHeadAwayCorners") or 0
    HeadToHeadAwayYellowCards = (
        selected_match_data.get("HeadToHeadAwayYellowCards") or 0
    )
    HeadToHeadAwayRedCards = selected_match_data.get("HeadToHeadAwayRedCards") or 0

    Last5HomeOver7Corners = (
        selected_match_data.get("Last5HomeOver7Corners") or 0
    ) * 100
    Last5HomeOver8Corners = (
        selected_match_data.get("Last5HomeOver8Corners") or 0
    ) * 100
    Last5HomeOver9Corners = (
        selected_match_data.get("Last5HomeOver9Corners") or 0
    ) * 100
    Last5HomeOver10Corners = (
        selected_match_data.get("Last5HomeOver10Corners") or 0
    ) * 100
    Last5HomeAvergeTotalYellowCards = (
        selected_match_data.get("Last5HomeAvergeTotalYellowCards") or 0
    )
    Last5HomeOver1YellowCards = (
        selected_match_data.get("Last5HomeOver1YellowCards") or 0
    ) * 100
    Last5HomeOver2YellowCards = (
        selected_match_data.get("Last5HomeOver2YellowCards") or 0
    ) * 100
    Last5HomeOver3YellowCards = (
        selected_match_data.get("Last5HomeOver3YellowCards") or 0
    ) * 100
    Last5HomeOver4YellowCards = (
        selected_match_data.get("Last5HomeOver4YellowCards") or 0
    ) * 100
    Last5HomeAvergeTotalRedCards = (
        selected_match_data.get("Last5HomeAvergeTotalRedCards") or 0
    )

    Last5AwayOver7Corners = (
        selected_match_data.get("Last5AwayOver7Corners") or 0
    ) * 100
    Last5AwayOver8Corners = (
        selected_match_data.get("Last5AwayOver8Corners") or 0
    ) * 100
    Last5AwayOver9Corners = (
        selected_match_data.get("Last5AwayOver9Corners") or 0
    ) * 100
    Last5AwayOver10Corners = (
        selected_match_data.get("Last5AwayOver10Corners") or 0
    ) * 100
    Last5AwayAvergeTotalYellowCards = (
        selected_match_data.get("Last5AwayAvergeTotalYellowCards") or 0
    )
    Last5AwayOver1YellowCards = (
        selected_match_data.get("Last5AwayOver1YellowCards") or 0
    ) * 100
    Last5AwayOver2YellowCards = (
        selected_match_data.get("Last5AwayOver2YellowCards") or 0
    ) * 100
    Last5AwayOver3YellowCards = (
        selected_match_data.get("Last5AwayOver3YellowCards") or 0
    ) * 100
    Last5AwayOver4YellowCards = (
        selected_match_data.get("Last5AwayOver4YellowCards") or 0
    ) * 100
    Last5AwayAvergeTotalRedCards = (
        selected_match_data.get("Last5AwayAvergeTotalRedCards") or 0
    )

    l5_league_avg_btts = (selected_match_data.get("l5_league_avg_btts") or 0) * 100
    l5HomeLeagueCleanSheet = selected_match_data.get("l5HomeLeagueCleanSheet") or 0
    l5AwayLeagueCleanSheet = selected_match_data.get("l5AwayLeagueCleanSheet") or 0

    pred_display = ""
    rec_pred_parts = rec_pred.split("(")
    rec_pred_only = rec_pred_parts[0].strip()
    rec_pred_conf = f"({rec_pred_parts[-1].strip()})" if len(rec_pred_parts) > 1 else ""
    rec_pred_won = check_prediction_success(
        rec_pred_only,
        home_goals,
        away_goals,
        corners,
        cards,
        home_team,
        away_team,
        match.get("HomeYellowsResults", None),
        match.get("AwayYellowsResults", None),
        match.get("HomeRedResults", 0),
        match.get("HomeRedResults", 0),
    )

    if rec_pred:
        pred_display = f"{rec_pred}({confidence_score})"
        if rec_pred_won == "WIN":
            pred_display = f"{rec_pred}({confidence_score}) ✅"  # <span style='color:{GREEN}; font-size=1.5em font-weight:bold;'></span>" # Added checkmark
        # st.caption(f"**Best Bet:** {pred_display}", unsafe_allow_html=True)
        # st.success(f"**Best Bet:** {pred_display}")

    # else:
    #     st.caption("")

    # --- Check and Display Value Tip ---
    # Pass necessary stats to the check function
    value_display = ""
    value_bet_won = check_prediction_success(
        value_bet,
        home_goals,
        away_goals,
        corners,
        cards,
        home_team,
        away_team,
        match.get("HomeYellowsResults", None),
        match.get("AwayYellowsResults", None),
        match.get("HomeRedResults", 0),
        match.get("HomeRedResults", 0),
    )
    if value_bet:
        value_display = f"{value_bet}"
        if value_bet_won == "WIN":
            value_display = f"{value_bet} ✅"  # <span style='color:{GREEN}; font-weight:bold;'></span>" # Added checkmark
        # st.caption(f"**Value Tip:** {value_display}", unsafe_allow_html=True)
    # else:
    #     st.caption("")

    if confidence_score != "--" and not pd.isna(confidence_score):
        try:
            # Extract the first number from confidence_score (handles formats like "5/10", "[4/10]", or text)
            conf_match = re.search(r"(\d+)", str(confidence_score))
            conf_val = int(conf_match.group(1)) if conf_match else None
            if conf_val is not None:  # and conf_val >= 7
                confidence_score = conf_val
        except (ValueError, TypeError):
            pass

    pred_cols1, pred_cols2, pred_cols3, pred_cols4 = st.columns([1, 2, 2, 3])
    pred_cols1.metric("Overall Confidence", f"{confidence_score}")  # /10
    pred_cols2.success(f"**Best Bet:** {pred_display}")
    pred_cols3.warning(f"**Value Bets:** {value_display}")
    pred_cols4.info(f"**Advice:** {selected_match_data.get('advice', '--')}")

    # --- Tabs for Detailed Stats (Added Recommendations Tab) ---
    tab_titles = [
        "🎯 Recommendations",
        "📈 Performance & Goals",
        "🤝 H2H",
        "✨ Insights",
    ]  # , "🎲 Odds"
    tabs = st.tabs(tab_titles)

    # Match report
    # with tabs[0]:
    # st.markdown("#### ⭐ Prediction Overview")
    # Retrieve and display each stat using the helper function

    # st.markdown("---") # Divider after the report
    # Recommendations Tab (New)
    with tabs[0]:
        st.markdown("#### ⭐ Prediction Overview")
        rec_col1, rec_col2 = st.columns([3, 2])
        with rec_col1:
            st.metric("Overall Confidence", f"{confidence_score}")  # /10
            st.success(f"**Best Bet:** {pred_display}")
            st.markdown("---")

            predictions_for_table = []
            # pred_col1, pred_col2 = st.columns([2,1])#, pred_col3
            # with pred_col1:
            st.markdown("##### Detailed Predictions")
            outcome_display = ""
            outcome_conf = selected_match_data.get("pred_outcome_conf")
            outcome_conf_text = (
                f"{round(outcome_conf)}/10" if outcome_conf is not None else "--"
            )
            outcome_val_raw = selected_match_data.get("pred_outcome", "--").split("(")
            outcome_val = outcome_val_raw[0].strip()
            outcome_bet_won = check_prediction_success(
                outcome_val,
                home_goals,
                away_goals,
                corners,
                cards,
                home_team,
                away_team,
                match.get("HomeYellowsResults", None),
                match.get("AwayYellowsResults", None),
                match.get("HomeRedResults", 0),
                match.get("HomeRedResults", 0),
            )
            if outcome_val:
                outcome_display = None  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{outcome_val}</span>"
                if outcome_bet_won:
                    outcome_display = "WIN"  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{outcome_val} ✅</span>" #color:{GREEN};
            predictions_for_table.append(
                {
                    "Market": "Match Outcome",
                    "Bet": outcome_val,
                    "Confidence": outcome_conf_text,
                    "_result_raw": outcome_bet_won,  # outcome_display # Store raw for potential later use
                }
            )

            # st.markdown("Match Outcome:") # f"{outcome_conf}/10" if outcome_conf is not None else None)
            # st.markdown(f"{outcome_display}", unsafe_allow_html=True) # f"{outcome_conf}/10" if outcome_conf is not None else None)
            # st.markdown("---")

            alt_display = ""
            alt_conf = selected_match_data.get("pred_alt_conf")
            alt_conf_text = f"{round(alt_conf)}/10" if alt_conf is not None else "--"
            alt_val_raw = selected_match_data.get("pred_alt", "--").split("(")
            alt_val = alt_val_raw[0].strip()
            alt_bet_won = check_prediction_success(
                alt_val,
                home_goals,
                away_goals,
                corners,
                cards,
                home_team,
                away_team,
                match.get("HomeYellowsResults", None),
                match.get("AwayYellowsResults", None),
                match.get("HomeRedResults", 0),
                match.get("HomeRedResults", 0),
            )
            if alt_val:
                alt_display = None  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{alt_val}</span>"
                if alt_bet_won:
                    alt_display = "WIN"  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{alt_val} ✅</span>" #color:{GREEN};
            predictions_for_table.append(
                {
                    "Market": "Alternative Prediction",
                    "Bet": alt_val,
                    "Confidence": alt_conf_text,
                    "_result_raw": alt_bet_won,  # alt_display # Store raw for potential later use
                }
            )

            # st.markdown("Alternative Prediction:") # f"{alt_conf}/10" if alt_conf is not None else None)
            # st.markdown(f"{alt_display}", unsafe_allow_html=True)
            # st.caption("`Alternative bet with a good chance.`") # f"{alt_conf}/10" if alt_conf is not None else None)
            # with pred_col2:
            goals_display = ""
            goals_conf = selected_match_data.get("pred_goals_conf")
            goals_conf_text = (
                f"{round(goals_conf)}/10" if goals_conf is not None else "--"
            )
            goals_val_raw = selected_match_data.get("pred_goals", "--").split("(")
            goals_val = f"{goals_val_raw[0].strip()} goals" if goals_val_raw else None
            goals_bet_won = check_prediction_success(
                goals_val,
                home_goals,
                away_goals,
                corners,
                cards,
                home_team,
                away_team,
                match.get("HomeYellowsResults", None),
                match.get("AwayYellowsResults", None),
                match.get("HomeRedResults", 0),
                match.get("HomeRedResults", 0),
            )
            if goals_val:
                goals_display = None  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{goals_val}</span>"
                if goals_bet_won:
                    goals_display = "WIN"  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{goals_val} ✅</span>" #color:{GREEN};
            predictions_for_table.append(
                {
                    "Market": "Goals (O/U)",
                    "Bet": goals_val,
                    "Confidence": goals_conf_text,
                    "_result_raw": goals_bet_won,  # goals_display # Store raw for potential later use
                }
            )

            # st.markdown("Goals (O/U):") # f"{outcome_conf}/10" if outcome_conf is not None else None)
            # st.markdown(f"{goals_display}", unsafe_allow_html=True) #, f"{goals_conf}/10" if goals_conf is not None else None)
            # st.markdown("---")

            cards_display = ""
            cards_conf = selected_match_data.get("pred_cards_conf")
            cards_conf_text = (
                f"{round(cards_conf)}/10" if cards_conf is not None else "--"
            )
            pred_cards_val = selected_match_data.get("pred_cards")
            if pred_cards_val is not None:
                cards_val_raw = pred_cards_val.split("(")
            else:
                cards_val_raw = ["--"]
            cards_val = (
                f"{cards_val_raw[0].strip()} Yellow Cards" if cards_val_raw else None
            )
            cards_bet_won = check_prediction_success(
                cards_val,
                home_goals,
                away_goals,
                corners,
                cards,
                home_team,
                away_team,
                match.get("HomeYellowsResults", None),
                match.get("AwayYellowsResults", None),
                match.get("HomeRedResults", 0),
                match.get("HomeRedResults", 0),
            )
            if cards_val:
                cards_display = None  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{cards_val} ({cards_conf}/10)</span>"
                if cards_bet_won:
                    cards_display = "WIN"  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{cards_val} ({cards_conf}/10) ✅</span>" #color:{GREEN};
            predictions_for_table.append(
                {
                    "Market": "Cards (O/U)",
                    "Bet": cards_val,
                    "Confidence": cards_conf_text,
                    "_result_raw": cards_bet_won,  # cards_display # Store raw for potential later use
                }
            )
            # st.markdown("Cards (O/U):") # f"{outcome_conf}/10" if outcome_conf is not "WIN" else None)
            # st.markdown(f"{cards_display}", unsafe_allow_html=True) #, f"{cards_conf}/10" if goals_conf is not None else None)
            # with pred_col3:
            corners_display = ""
            corners_conf = selected_match_data.get("pred_corners_conf")
            corners_conf_text = (
                f"{round(corners_conf)}/10" if corners_conf is not None else "--"
            )
            corners_val_raw = selected_match_data.get("pred_corners", "--").split("(")
            corners_val = (
                f"{corners_val_raw[0].strip()} Corners" if corners_val_raw else None
            )
            corners_bet_won = check_prediction_success(
                corners_val,
                home_goals,
                away_goals,
                corners,
                cards,
                home_team,
                away_team,
                match.get("HomeYellowsResults", None),
                match.get("AwayYellowsResults", None),
                match.get("HomeRedResults", 0),
                match.get("HomeRedResults", 0),
            )
            # Check if corner prediction is meaningful before showing
            if corners_val:
                corners_display = None  # f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{corners_val} ({corners_conf}/10)</span>"
            if corners_bet_won:
                corners_display = "WIN"  # = f"<span style='font-size: 2em; display: block; margin-bottom: 0.2em;'>{corners_val} ({corners_conf}/10) ✅</span>" #color:{GREEN};
            predictions_for_table.append(
                {
                    "Market": "Corners (O/U)",
                    "Bet": corners_val,
                    "Confidence": corners_conf_text,
                    "_result_raw": corners_bet_won,  # corners_display # Store raw for potential later use
                }
            )
            # st.markdown("Corners (O/U):") # f"" if outcome_conf is not None else None)
            # st.markdown(f"{corners_display}", unsafe_allow_html=True)
            # --- Create and display the table ---
            if predictions_for_table:
                display_table_data = []
                for item in predictions_for_table:
                    result_raw = item.get(
                        "_result_raw", "PENDING"
                    )  # Assuming _result_raw is 'WIN', 'LOSS', etc.
                    result_display_text = "⏳ PENDING"
                    if result_raw == "WIN":
                        result_display_text = "✅ WIN"
                    elif result_raw == "LOSS":
                        result_display_text = "❌ LOSS"
                    elif result_raw == "PUSH":
                        result_display_text = "🅿️ PUSH"

                    confidence_display_text = (
                        f"{item.get('Confidence')}"
                        if item.get("Confidence") is not None
                        else "-"
                    )

                    display_table_data.append(
                        {
                            "Market": item["Market"],
                            "Prediction": item[
                                "Bet"
                            ],  # Changed column name for clarity
                            "Confidence": confidence_display_text,
                            "Result": result_display_text,
                        }
                    )

                df_display_predictions = pd.DataFrame(display_table_data)

                # Use one column for the table for better width control
                st.dataframe(
                    df_display_predictions,
                    use_container_width=True,
                    hide_index=True,
                    column_config={  # Optional: Adjust widths and alignment
                        "Market": st.column_config.TextColumn(width="medium"),
                        "Prediction": st.column_config.TextColumn(width="medium"),
                        "Confidence": st.column_config.TextColumn(
                            width="small", help="Confidence score out of 10"
                        ),
                        "Result": st.column_config.TextColumn(width="small"),
                    },
                )
            else:
                st.info("No detailed predictions available for this match.")
            # with pred_col2:

            st.markdown("---")
            st.markdown("##### Expected Value")
            ev_h = (
                f"{selected_match_data.get('exp_val_h') * 100:.2f}%"
                if selected_match_data.get("exp_val_h") is not None
                else None
            )
            ev_d = (
                f"{selected_match_data.get('exp_val_d') * 100:.2f}%"
                if selected_match_data.get("exp_val_d") is not None
                else None
            )
            ev_a = (
                f"{selected_match_data.get('exp_val_a') * 100:.2f}%"
                if selected_match_data.get("exp_val_a") is not None
                else None
            )

            pred_col4, pred_col5, pred_col6 = st.columns(3)
            if any([ev_h, ev_d, ev_a]):
                with pred_col4:
                    # st.caption(f"**EV (Home):** {ev_h or '--'}")
                    st.metric("EV (Home)", ev_h or "--")
                with pred_col5:
                    # st.caption(f"**EV (Draw):** {ev_d or '--'}")
                    st.metric("EV (Draw)", ev_d or "--")
                with pred_col6:
                    # st.caption(f"**EV (Away):** {ev_a or '--'}")
                    st.metric("EV (Away)", ev_a or "--")
                #  st.caption(f"**EV:** H: {ev_h or '--'} | D: {ev_d or '--'} | A: {ev_a or '--'}")
            else:
                st.caption("No Expected Value data.")

        with rec_col2:
            st.markdown("#####  Odds")

            # #4A5568        #384d67 #1e44d6
            custom_css = """
            <style>
                .odds-table-cell-label {
                    background-color: #20283e;
                    color: white;
                    padding: 1px;
                    text-align: center;
                    font-weight: bold;
                    border: 1px solid #2D3748;
                    min-height: 15px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .odds-table-cell-value {
                    background-color: #2C5282; /*#ac4e31#6ab190 #1da54b*/
                    color: white;
                    padding: 1px;
                    text-align: center;
                    border: 1px solid #2D3748;
                    font-size: 0.9em;
                    min-height: 15px;
                    display: flex;
                    align-items: center; justify-content: center;
                }
                .market-title-main { /* For titles inside the main expander */
                    font-size: 0.9em; /* Slightly smaller than expander title */
                    font-weight: bold;
                    margin-top: 2px;
                    margin-bottom: 4px;
                    /* border-bottom: 1px solid #4A5568; */ /* Optional separator */
                    /* padding-bottom: 4px; */
                }
                .odds-expander .stButton>button { /* Target buttons inside expanders if needed */
                    /* Example: st.button("Bet Now", key=...) */
                }
                 .ou-header-label { /* Specific for O/U table headers "Line", "Over", "Under" */
                    background-color: #20283e; 
                    color: white; 
                    padding: 4px; 
                    text-align: center;
                    font-weight: bold; 
                    border: 1px solid #2D3748; 
                    min-height: 15px;
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    font-size: 0.9em;
                }
                /*.ou-table-header div, .ou-table-row div {
                    text-align: center;
                    padding: 6px 4px; /* Reduced padding */
                    font-size: 0.95em; /* Slightly smaller font */
                    border-bottom: 1px solid #4A5568; /* Separator line for rows */
                }
                .ou-table-header div {
                    font-weight: bold;
                    background-color: #3a4556; /* Slightly different header bg */
                    color: white;
                }
                .ou-table-row div:first-child { /* Line column */
                    font-weight: bold;
                }*/
            </style>
            """
            st.markdown(custom_css, unsafe_allow_html=True)  # UNCOMMENT TO APPLY CSS

            if not selected_match_data:
                st.info("Select a match to view odds.")
            else:
                odds_by_market = group_odds_by_market(selected_match_data)

                if not odds_by_market:
                    st.info("No odds data available for this match.")
                else:
                    # Define markets that are suitable for the compact table display
                    # These typically have 2 or 3 outcomes, or 6 for Result&BTTS
                    compact_table_markets = [
                        "Match Winner",
                        "Double Chance",
                        "Home/Away",
                        "Both Teams Score",
                        "Result & BTTS",
                        "First Half Winner",
                        "Second Half Winner",
                        "Both Teams Score - First Half",
                        "Draw No Bet (1st Half)",
                        "Draw No Bet (2nd Half)",
                        # Add any other markets that fit this 2/3 outcome per row style
                    ]

                    # --- Main Expander for Key Table Markets ---
                    with st.expander(
                        "Key Betting Markets", expanded=True
                    ):  # Start expanded
                        has_content_in_main_expander = False
                        for market_name in (
                            compact_table_markets
                        ):  # Iterate in defined order if needed
                            if market_name in odds_by_market:
                                odds_list = odds_by_market[market_name]
                                if not odds_list:
                                    continue

                                has_content_in_main_expander = True
                                st.markdown(
                                    f"<div class='market-title-main'>{market_name}</div>",
                                    unsafe_allow_html=True,
                                )

                                if market_name == "Result & BTTS":
                                    if len(odds_list) == 6:  # Expecting 6 outcomes
                                        cols_yes = st.columns(3)
                                        for i in range(3):
                                            with cols_yes[i]:
                                                st.markdown(
                                                    f"<div class='odds-table-cell-label'>{odds_list[i]['display_label']}</div>",
                                                    unsafe_allow_html=True,
                                                )
                                                st.markdown(
                                                    f"<div class='odds-table-cell-value'>{odds_list[i]['odds_value']:.2f if isinstance(odds_list[i]['odds_value'], (int, float)) else odds_list[i]['odds_value']}</div>",
                                                    unsafe_allow_html=True,
                                                )
                                        cols_no = st.columns(3)
                                        for i in range(3):
                                            with cols_no[i]:
                                                st.markdown(
                                                    f"<div class='odds-table-cell-label'>{odds_list[i + 3]['display_label']}</div>",
                                                    unsafe_allow_html=True,
                                                )
                                                st.markdown(
                                                    f"<div class='odds-table-cell-value'>{odds_list[i + 3]['odds_value']:.2f if isinstance(odds_list[i+3]['odds_value'], (int, float)) else odds_list[i+3]['odds_value']}</div>",
                                                    unsafe_allow_html=True,
                                                )
                                    else:
                                        st.caption(
                                            f"Data format error for {market_name}."
                                        )
                                else:  # For other 2 or 3 outcome markets
                                    num_outcomes = len(odds_list)
                                    cols_labels = st.columns(num_outcomes)
                                    cols_values = st.columns(num_outcomes)
                                    for i, odd_item in enumerate(odds_list):
                                        with cols_labels[i]:
                                            st.markdown(
                                                f"<div class='odds-table-cell-label'>{odd_item['display_label']}</div>",
                                                unsafe_allow_html=True,
                                            )
                                        with cols_values[i]:
                                            st.markdown(
                                                f"<div class='odds-table-cell-value'>{odd_item['odds_value'] if isinstance(odd_item['odds_value'], (int, float)) else odd_item['odds_value']}</div>",
                                                unsafe_allow_html=True,
                                            )
                                st.write(
                                    ""
                                )  # Small vertical space after each market table

                        if not has_content_in_main_expander:
                            st.caption("No key market odds available.")

                    # --- Individual Expanders for Over/Under Markets ---
                    # for market_name, odds_list in odds_by_market.items():
                    #     if market_name not in compact_table_markets: # Process markets not handled above
                    #         # This will catch all "Goals Over/Under", "Corners Over Under", "Cards Over/Under", "Total - Home/Away", etc.
                    #         with st.expander(f"{market_name} Odds", expanded=False):
                    #             if not odds_list:
                    #                 st.caption("No odds for this market.")
                    #                 continue

                    #             # Display O/U pairs side-by-side using st.metric
                    #             for i in range(0, len(odds_list), 2): # Step by 2 for pairs
                    #                 cols_ou = st.columns(2)
                    #                 with cols_ou[0]:
                    #                     st.metric(label=odds_list[i]['display_label'],
                    #                                 value=f"{odds_list[i]['odds_value']:.2f}" if isinstance(odds_list[i]['odds_value'], (int, float)) else str(odds_list[i]['odds_value']))
                    #                 if i + 1 < len(odds_list):
                    #                     with cols_ou[1]:
                    #                         st.metric(label=odds_list[i+1]['display_label'],
                    #                                     value=f"{odds_list[i+1]['odds_value']:.2f}" if isinstance(odds_list[i+1]['odds_value'], (int, float)) else str(odds_list[i+1]['odds_value']))
                    #                 else: # Handle odd number of items if any (shouldn't happen for O/U)
                    #                     with cols_ou[1]: st.empty()

                    ou_market_categories = {
                        "Goals": ["Goals Over/Under", "Total - Home", "Total - Away"],
                        "Corners": ["Corners Over Under"],
                        "Cards": ["Cards Over/Under"],
                        "First Half": [
                            "Goals Over/Under First Half",
                            "Home Team Total Goals(1st Half)",
                            "Away Team Total Goals(1st Half)",
                            "Total Corners (1st Half)",
                        ],
                        "Second Half": [
                            "Goals Over/Under Second Half",
                            "Home Team Total Goals(2nd Half)",
                            "Away Team Total Goals(2nd Half)",
                            "Total Corners (2nd Half)",
                        ],
                    }

                    for (
                        category_title,
                        markets_in_category,
                    ) in ou_market_categories.items():
                        # Check if any market in this category has data to display
                        category_has_any_data = any(
                            m_key in odds_by_market and odds_by_market[m_key]
                            for m_key in markets_in_category
                        )

                        if category_has_any_data:
                            with st.expander(
                                f"{category_title} Over/Under Lines", expanded=False
                            ):
                                for market_name in markets_in_category:
                                    if (
                                        market_name in odds_by_market
                                        and odds_by_market[market_name]
                                    ):
                                        odds_list = odds_by_market[market_name]

                                        # Display market sub-title if it's not redundant with category
                                        # e.g., if category is "Goals", and market is "Total - Home"
                                        if (
                                            category_title.lower()
                                            not in market_name.lower()
                                        ):
                                            st.markdown(
                                                f"**{market_name.replace('Over/Under', '').replace('Over Under', '').strip()}**"
                                            )
                                        # else if only one market in category, no need for sub-title if same as category
                                        elif len(markets_in_category) > 1:
                                            st.markdown(
                                                f"**{market_name.replace('Over/Under', '').replace('Over Under', '').strip()}**"
                                            )

                                        # Table Header for O/U: Line | Over | Under
                                        header_cols = st.columns([1, 1, 1])
                                        with header_cols[0]:
                                            st.markdown(
                                                "<div class='ou-header-label'>Line</div>",
                                                unsafe_allow_html=True,
                                            )
                                        with header_cols[1]:
                                            st.markdown(
                                                "<div class='ou-header-label'>Over</div>",
                                                unsafe_allow_html=True,
                                            )
                                        with header_cols[2]:
                                            st.markdown(
                                                "<div class='ou-header-label'>Under</div>",
                                                unsafe_allow_html=True,
                                            )

                                        # Table Rows
                                        for i in range(0, len(odds_list), 2):
                                            if i + 1 < len(odds_list):
                                                over_item = odds_list[i]
                                                under_item = odds_list[i + 1]

                                                line_match_over = re.search(
                                                    r"(\d+(?:\.\d+)?)",
                                                    over_item["bet_label"],
                                                )
                                                line_match_under = re.search(
                                                    r"(\d+(?:\.\d+)?)",
                                                    under_item["bet_label"],
                                                )

                                                if (
                                                    line_match_over
                                                    and line_match_under
                                                    and line_match_over.group(1)
                                                    == line_match_under.group(1)
                                                ):
                                                    line_display = (
                                                        line_match_over.group(1)
                                                    )
                                                    row_cols = st.columns([1, 1, 1])
                                                    with row_cols[0]:
                                                        st.markdown(
                                                            f"<div class='odds-table-cell-label'>{line_display}</div>",
                                                            unsafe_allow_html=True,
                                                        )
                                                    with row_cols[1]:
                                                        over_odds_val = (
                                                            f"{over_item['odds_value']:.2f}"
                                                            if isinstance(
                                                                over_item["odds_value"],
                                                                (int, float),
                                                            )
                                                            else str(
                                                                over_item["odds_value"]
                                                            )
                                                        )
                                                        st.markdown(
                                                            f"<div class='odds-table-cell-value'>{over_odds_val}</div>",
                                                            unsafe_allow_html=True,
                                                        )
                                                    with row_cols[2]:
                                                        under_odds_val = (
                                                            f"{under_item['odds_value']:.2f}"
                                                            if isinstance(
                                                                under_item[
                                                                    "odds_value"
                                                                ],
                                                                (int, float),
                                                            )
                                                            else str(
                                                                under_item["odds_value"]
                                                            )
                                                        )
                                                        st.markdown(
                                                            f"<div class='odds-table-cell-value'>{under_odds_val}</div>",
                                                            unsafe_allow_html=True,
                                                        )
                                                else:
                                                    st.caption(
                                                        f"Data format/pairing issue: {over_item['bet_label']} / {under_item.get('bet_label', 'N/A')}"
                                                    )
                                            else:
                                                st.caption(
                                                    f"Orphaned O/U item: {odds_list[i]['bet_label']} - {odds_list[i]['odds_value']}"
                                                )
                                        st.markdown(
                                            "<hr style='margin-top:10px; margin-bottom:10px;'>",
                                            unsafe_allow_html=True,
                                        )  # Separator after each specific O/U market table

                    # Fallback for any markets not covered by compact_table_markets or ou_market_categories
                    # You can add a default display here if needed, e.g., using st.metric inside an expander
                    # st.markdown("---")
                    # st.markdown("##### Other Markets")
                    # for market_name, odds_list in odds_by_market.items():
                    #     is_compact = market_name in compact_table_markets
                    #     is_ou_category_market = any(market_name in cat_list for cat_list in ou_market_categories.values())
                    #     if not is_compact and not is_ou_category_market:
                    #         with st.expander(f"{market_name} (Other)", expanded=False):
                    #             if not odds_list: st.caption("No odds."); continue
                    #             for odd_item in odds_list:
                    #                 st.metric(label=odd_item['display_label'], value=str(odd_item['odds_value']))
    # Performance Tab
    with tabs[1]:
        st.markdown("#### Performance & Form - Last 5 Games")
        # ... (Keep existing Performance tab code, ensuring .get() is used) ...
        home_perf_col1, away_perf_col2 = st.columns(2)

        home_btts_delta = Last5_HomeBothTeamsToScore - l5_league_avg_btts
        away_btts_delta = Last5_AwayBothTeamsToScore - l5_league_avg_btts

        ppg_h = selected_match_data.get("ppg_h")
        ppg_h_all = selected_match_data.get("ppg_h_all")
        ppg_a = selected_match_data.get("ppg_a")
        ppg_a_all = selected_match_data.get("ppg_a_all")

        with home_perf_col1:
            st.markdown(
                f"**{selected_match_data.get('home_team', '?')} (Last 5 Home Games)**"
            )
            form_home = colorize_performance(
                selected_match_data.get("form_home", "--")
            )  # .split('//')r
            all_form_home = colorize_performance(
                selected_match_data.get("all_form_home", "--")
            )  # .split('//')
            # if len(all_form_home) > 1:
            form_cols_h = st.columns(2)
            form_cols_h[0].metric("Form (H)", form_home)  # [0]
            form_cols_h[1].metric("Form (Overall)", all_form_home)  # [1]
            # else:
            # st.metric(label="Form (H)", value=all_form_home[0])

            # st.caption(f"**Home Form:** `{selected_match_data.get('form_home', '--')}`")
            # st.caption(f"**Overall Form:** `{selected_match_data.get('all_form_home', '--')}`")

            delta_h_str = f"{ppg_h_all} (All)" if ppg_h_all is not None else None

            clean_sheet_h = int(selected_match_data.get("clean_sheet_h", "--") * 100)

            l5hometotalshots_delta = (
                Last5HomeAvergeTotalShots - l5_home_for_league_avg_shots
            )
            l5homesot_delta = (
                Last5HomeAvergeTotalShotsOnGoal - l5_home_for_league_avg_sot
            )
            lshomefouls_delta = Last5HomeAvergeTotalFouls - l5_home_for_league_avg_fouls
            l5hometotalcorner_delta = (
                Last5HomeAvergeTotalcorners - l5_home_for_league_avg_corners
            )
            l5hometotalyellows_delta = (
                Last5HomeAvergeTotalYellowCards - l5_home_for_league_avg_yellow_cards
            )
            # l5hometotalreds_delta = Last5HomeAvergeTotalRedCards - l5_home_for_league_avg_red_cards
            l5homeCS_delta = clean_sheet_h - l5HomeLeagueCleanSheet

            win_cols_h = st.columns(2)

            wr_h_text = selected_match_data.get("win_rates_h", "HT: 0% | FT: 0%")
            ht_wr_h = (
                int(selected_match_data.get("ht_win_rates_h", "--") * 100)
                if selected_match_data.get("ht_win_rates_h", "--") is not None
                else 0
            )  # parse_specific_percent(wr_h_text, 'HT', 0)
            ft_wr_h = (
                int(selected_match_data.get("ft_win_rates_h", "--") * 100)
                if selected_match_data.get("ft_win_rates_h", "--") is not None
                else 0
            )  # parse_specific_percent(wr_h_text, 'FT', 0)

            try:
                ppg_home_delta = ppg_h - ppg_a
                ppg_home_overall_delta = ppg_h_all - ppg_a_all
            except ValueError:
                ppg_home_delta = 0
                ppg_home_overall_delta = 0

            win_cols_h[0].metric(
                label="PPG (Home)",
                value=f"{ppg_h}/game" if ppg_h is not None else "--",
                delta=f"{round(ppg_home_delta, 2)} vs Opponent PPG ({ppg_a})",
            )
            win_cols_h[1].metric(
                label="PPG (Overall)",
                value=f"{ppg_h_all}/game" if ppg_h_all is not None else "--",
                delta=f"{round(ppg_home_overall_delta, 2)} vs Opponent Overall PPG ({ppg_a_all})",
            )

            win_cols_h[0].metric("Win Rate HT %", f"{ht_wr_h}%")
            win_cols_h[1].metric("Win Rate FT %", f"{ft_wr_h}%")

            win_cols_h[0].metric(
                "GG",
                f"{round(Last5_HomeBothTeamsToScore)}%",
                f"{round(home_btts_delta)}% league avg ({round(l5_league_avg_btts)}%)",
            )  # leagues average delata
            win_cols_h[1].metric(
                label="Clean Sheet %",
                value=f"{round(clean_sheet_h)}%",
                delta=f"{round(l5homeCS_delta)}% league avg ({round(l5HomeLeagueCleanSheet * 100)}%)",
            )  # nleague average clean sheet

            win_cols_h[0].metric(
                "Total Shots",
                Last5HomeAvergeTotalShots,
                f"{round(l5hometotalshots_delta, 2)} league avg({round(l5_home_for_league_avg_shots, 2)}).",
            )
            win_cols_h[1].metric(
                "Shots on Goal",
                Last5HomeAvergeTotalShotsOnGoal,
                f"{round(l5homesot_delta, 2)} league avg({round(l5_home_for_league_avg_sot, 2)}).",
            )

            win_cols_h[0].metric(
                "Fouls",
                Last5HomeAvergeTotalFouls,
                f"{round(lshomefouls_delta, 2)} league avg({round(l5_home_for_league_avg_fouls, 2)}).",
                "normal",
            )

            win_cols_h[1].metric(
                "Total Corners",
                Last5HomeAvergeTotalcorners,
                f"{round(l5hometotalcorner_delta, 2)} league avg({round(l5_home_for_league_avg_corners, 2)}).",
            )
            win_cols_h[0].metric(
                "Total Yellows",
                Last5HomeAvergeTotalYellowCards,
                f"{round(l5hometotalyellows_delta, 2)} league avg({round(l5_home_for_league_avg_yellow_cards, 2)}).",
                "inverse",
            )

            # win_cols_h[1].metric("Total Reds",Last5HomeAvergeTotalRedCards,f"{round(l5hometotalreds_delta,2)} league avg.")

        with away_perf_col2:
            st.markdown(
                f"**{selected_match_data.get('away_team', '?')} (Last 5 Away Games)**"
            )
            form_away = colorize_performance(
                selected_match_data.get("form_away", "--")
            )  # .split('//')r
            all_form_away = colorize_performance(
                selected_match_data.get("all_form_away", "--")
            )  # .split('//')
            # if len(all_form_away) > 1:
            clean_sheet_a = int(selected_match_data.get("clean_sheet_a", "--") * 100)
            l5AwayCS_delta = clean_sheet_a - l5AwayLeagueCleanSheet

            form_cols_a = st.columns(2)

            form_cols_a[0].metric("Form (A)", form_away)  # [0]
            form_cols_a[1].metric("Form (Overall)", all_form_away)  # [1]
            # st.caption(f"**Form (A/All):** `{selected_match_data.get('form_away', '--')}`")

            delta_a_str = f"{ppg_a_all} (All)" if ppg_a_all is not None else None

            l5awaytotalshots_delta = (
                Last5AwayAvergeTotalShots - l5_away_for_league_avg_shots
            )
            l5awaysot_delta = (
                Last5AwayAvergeTotalShotsOnGoal - l5_away_for_league_avg_sot
            )
            l5awayfouls_delta = Last5AwayAvergeTotalFouls - l5_away_for_league_avg_fouls
            l5awaytotalcorner_delta = (
                Last5AwayAvergeTotalcorners - l5_away_for_league_avg_corners
            )
            l5awaytotalyellows_delta = (
                Last5AwayAvergeTotalYellowCards - l5_away_for_league_avg_yellow_cards
            )
            # l5awaytotalreds_delta = Last5AwayAvergeTotalRedCards - l5_away_for_league_avg_red_cards

            ppg_away_delta = ppg_a - ppg_h
            ppg_away_overall_delta = ppg_a_all - ppg_h_all

            wr_a_text = selected_match_data.get("win_rates_a", "HT: 0% | FT: 0%")
            ht_wr_a = (
                int(selected_match_data.get("ht_win_rates_a", "--") * 100)
                if selected_match_data.get("ht_win_rates_a", "--") is not None
                else 0
            )  # parse_specific_percent(wr_a_text, 'HT', 0)
            ft_wr_a = (
                int(selected_match_data.get("ft_win_rates_a", "--") * 100)
                if selected_match_data.get("ft_win_rates_a", "--") is not None
                else 0
            )  # parse_specific_percent(wr_a_text, 'FT', 0)

            win_cols_a = st.columns(2)
            win_cols_a[0].metric(
                label="PPG (Away)",
                value=f"{ppg_a}/game" if ppg_a is not None else "--",
                delta=f"{round(ppg_away_delta, 2)} vs Opponent PPG ({ppg_h})",
            )
            win_cols_a[1].metric(
                label="PPG (Overall)",
                value=f"{ppg_a_all}/game" if ppg_a_all is not None else "--",
                delta=f"{round(ppg_away_overall_delta, 2)} vs Opponent Overall PPG ({ppg_h_all})",
            )

            win_cols_a[0].metric("Win Rate HT %", f"{ht_wr_a}%")
            win_cols_a[1].metric("Win Rate FT %", f"{ft_wr_a}%")

            win_cols_a[0].metric(
                "GG",
                f"{int(Last5_AwayBothTeamsToScore)}%",
                f"{away_btts_delta}% league avg ({round(l5_league_avg_btts)}%)",
            )
            win_cols_a[1].metric(
                label="Clean Sheet %",
                value=f"{round(clean_sheet_a)}%",
                delta=f"{round(l5AwayCS_delta)}% league avg ({round(l5AwayLeagueCleanSheet * 100)}%)",
            )

            win_cols_a[0].metric(
                "Total Shots",
                Last5AwayAvergeTotalShots,
                f"{round(l5awaytotalshots_delta, 2)} league avg({round(l5_away_for_league_avg_shots, 2)}).",
            )
            win_cols_a[1].metric(
                "Shots on Goal",
                Last5AwayAvergeTotalShotsOnGoal,
                f"{round(l5awaysot_delta, 2)} league avg({round(l5_away_for_league_avg_sot, 2)}).",
            )

            win_cols_a[0].metric(
                "Fouls",
                Last5AwayAvergeTotalFouls,
                f"{round(l5awayfouls_delta, 2)} league avg({round(l5_away_for_league_avg_fouls, 2)}).",
                "normal",
            )

            win_cols_a[1].metric(
                "Total Corners",
                Last5AwayAvergeTotalcorners,
                f"{round(l5awaytotalcorner_delta, 2)} league avg ({round(l5_away_for_league_avg_corners, 2)}).",
            )

            win_cols_a[0].metric(
                "Total Yellows",
                Last5AwayAvergeTotalYellowCards,
                f"{round(l5awaytotalyellows_delta, 2)} league avg({round(l5_away_for_league_avg_yellow_cards, 2)}).",
                "inverse",
            )
            # win_cols_h[1].metric("Total Reds",Last5AwayAvergeTotalRedCards,f"{round(l5awaytotalreds_delta,2)} league avg.")

        st.markdown("---")  # Separator

        # Goals Tab
        # with tabs[2]:
        goal_stats_cols = st.columns(2)

        with goal_stats_cols[0]:
            st.markdown("#### Goal Statistics")
            st.markdown("**Average Goals Scored vs Conceded per Game**")
            try:
                # Prepare data in a 'long' format suitable for Altair color mapping
                home_team_label = selected_match_data.get("home_team", "Home")
                away_team_label = selected_match_data.get("away_team", "Away")
                # Use abbreviations for potentially long labels
                home_abbr = "".join([word[0] for word in home_team_label.split()[:2]])
                away_abbr = "".join([word[0] for word in away_team_label.split()[:2]])

                goals_h = float(selected_match_data.get("goals_h", 0.0))
                conc_h = float(selected_match_data.get("conceded_h", 0.0))
                goals_a = float(selected_match_data.get("goals_a", 0.0))
                conc_a = float(selected_match_data.get("conceded_a", 0.0))

                # Create list of dictionaries for DataFrame
                goal_data_long = [
                    {
                        "Metric": f"{home_team_label} Scored",
                        "Value": goals_h,
                        "TeamType": "Home",
                    },
                    {
                        "Metric": f"{away_team_label} Scored",
                        "Value": goals_a,
                        "TeamType": "Away",
                    },
                    {
                        "Metric": f"{home_team_label} Conceded",
                        "Value": conc_h,
                        "TeamType": "Home",
                    },
                    {
                        "Metric": f"{away_team_label} Conceded",
                        "Value": conc_a,
                        "TeamType": "Away",
                    },
                ]
                goal_df_long = pd.DataFrame(goal_data_long)

                # Define specific colors
                home_color = "#5e993c"  # 8bc34a" # Light Green
                away_color = "#c47704"  # ff9800" # Orange

                # 1. Base chart definition (common encoding)
                base = alt.Chart(goal_df_long).encode(
                    x=alt.X(
                        "Metric", sort=None, title=None, axis=alt.Axis(labelAngle=0)
                    ),  # Keep defined order, remove axis title
                    y=alt.Y("Value", title="Goals per Game"),
                    color=alt.Color(
                        "TeamType",
                        scale=alt.Scale(
                            domain=["Home", "Away"], range=[home_color, away_color]
                        ),
                        legend=alt.Legend(title="Team"),
                    ),
                    tooltip=[
                        "Metric",
                        alt.Tooltip("Value", format=".2f"),
                    ],  # Format tooltip value
                )

                # 2. Bar layer
                bar_chart = base.mark_bar()

                # 3. Text layer for labels
                text_labels = base.mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-5,  # Adjust vertical offset slightly above the bar
                    # Optional: Change text color for better visibility if needed
                    # color='black'
                ).encode(
                    # Encode the text channel with the 'Value', formatted to 2 decimal places
                    text=alt.Text("Value", format=".2f"),
                    # Important: Remove color encoding from text or set explicitly if needed,
                    # otherwise text might inherit bar colors making it hard to read on some backgrounds.
                    # Let's remove it here to default to black/dark text.
                    color=alt.value(
                        "black"
                    ),  # Force text color or remove the line altogether for default
                )

                # 4. Combine the layers
                final_chart = (
                    (bar_chart + text_labels)
                    .properties(
                        # title='Avg Goals Scored/Conceded' # Optional title
                    )
                    .interactive()
                )

                # Display using st.altair_chart
                st.altair_chart(final_chart, use_container_width=True)

            except (ValueError, TypeError, KeyError, ImportError) as e:
                # Catch ImportError if altair isn't installed
                st.caption(f"Could not plot goal averages: {e}")
                if isinstance(e, ImportError):
                    st.warning("Please install altair: pip install altair")

        with goal_stats_cols[1]:
            # --- NEW: Actual vs Expected Goals (xG) Visualization ---
            st.markdown("#### xG Statistics")
            st.markdown("**Average xG/xGA For and Aginst Per Game**")

            # --- End xG Visualization ---
            try:
                # Get data, providing defaults and converting safely
                home_team_label = selected_match_data.get("home_team", "Home")
                away_team_label = selected_match_data.get("away_team", "Away")

                g_h = selected_match_data.get("goals_h")  # Home GS
                xg_h = selected_match_data.get("xg_h")  # Home xG
                c_h = selected_match_data.get(
                    "conceded_h"
                )  # Home conceded = Opponent goals
                xga_h = selected_match_data.get("xga_h")  # Home xGA = Opponent xG

                g_a = selected_match_data.get("goals_a")  # Away GS
                xg_a = selected_match_data.get("xg_a")  # Away xG
                c_a = selected_match_data.get(
                    "conceded_a"
                )  # Away conceded = Opponent goals
                xga_a = selected_match_data.get("xga_a")  # Away xGA = Opponent xG

                # Add a 'Location' column based on the Category string
                def get_location(category_name):
                    if home_team_label in category_name:
                        return "Home"
                    elif away_team_label in category_name:
                        return "Away"
                    else:
                        return "Unknown"  # Fallback

                # Check if all necessary values are present and numeric
                if all(
                    v is not None
                    for v in [g_h, xg_h, c_h, xga_h, g_a, xg_a, c_a, xga_a]
                ):
                    # Convert to float after check
                    g_h, xg_h, c_h, xga_h = (
                        float(g_h),
                        float(xg_h),
                        float(c_h),
                        float(xga_h),
                    )
                    g_a, xg_a, c_a, xga_a = (
                        float(g_a),
                        float(xg_a),
                        float(c_a),
                        float(xga_a),
                    )

                    # Prepare data for GROUPED bar chart
                    xg_data = pd.DataFrame(
                        {
                            "Actual": [g_h, c_h, g_a, c_a],
                            "Expected": [xg_h, xga_h, xg_a, xga_a],
                        },
                        index=[
                            f"{home_team_label} Attack",
                            f"{home_team_label} Defense",
                            f"{away_team_label} Attack",
                            f"{away_team_label} Defense",
                        ],
                    )
                    xg_data_reset = xg_data.reset_index()
                    xg_data_reset = xg_data_reset.rename(columns={"index": "Category"})

                    xg_data_long = pd.melt(
                        xg_data_reset,
                        id_vars=["Category"],
                        var_name="MetricType",
                        value_name="Goals",
                    )
                    # st.dataframe(xg_data_long) # Keep for debugging if needed

                    xg_data_long["Location"] = xg_data_long["Category"].apply(
                        get_location
                    )

                    category_order = [
                        f"{home_team_label} Attack",
                        f"{home_team_label} Defense",
                        f"{away_team_label} Attack",
                        f"{away_team_label} Defense",
                    ]

                    # --- Create the Altair Chart ---

                    # 1. Define the base chart for bars (this includes the xOffset)
                    base_bars = alt.Chart(xg_data_long).encode(
                        x=alt.X(
                            "Category:N",
                            sort=category_order,
                            axis=alt.Axis(title=None, labelAngle=0),
                        ),
                        y=alt.Y(
                            "Goals:Q", axis=alt.Axis(title="Goals (Actual vs Expected)")
                        ),
                        color=alt.Color(
                            "Location:N",
                            scale=alt.Scale(
                                domain=["Home", "Away"], range=["#5e993c", "#c47704"]
                            ),
                            legend=alt.Legend(title="Location"),
                        ),
                        xOffset=alt.XOffset("MetricType:N"),  # Group by Actual/Expected
                        tooltip=[
                            alt.Tooltip("Category", title="Focus"),
                            alt.Tooltip("MetricType", title="Metric"),
                            alt.Tooltip("Goals", format=".2f"),
                            alt.Tooltip("Location"),
                        ],
                    )

                    # 2. Create the bar layer
                    bars = base_bars.mark_bar()

                    # 3. Create the text layer
                    #    IMPORTANT: The text layer also needs the xOffset to align correctly
                    #    OR, if we base it on the same 'base_bars', it will inherit the offset.
                    #    We also need to make sure it uses the 'Goals' field for the text.
                    text = (
                        base_bars.mark_text(  # Inherit x, y, xOffset, color from base_bars
                            align="center",
                            baseline="bottom",
                            dy=-5,  # Nudge text slightly above the bar
                            # color='black' # Set text color explicitly if needed
                        )
                        .encode(
                            text=alt.Text(
                                "Goals:Q", format=".2f"
                            ),  # Use the 'Goals' column and format
                            # We need to override the color encoding from base_bars if we want a fixed text color
                            # If we don't, text will be colored like the bars, which might be hard to read.
                            color=alt.value(
                                "black"
                            ),  # Force text color to black (or choose another)
                        )
                        .transform_filter(  # Optional: Don't show labels for zero or very small values
                            alt.datum.Goals > 0.01
                        )
                    )

                    # 4. Combine the layers
                    final_chart = (
                        (bars + text)
                        .properties(
                            # title='Goal Comparison' # Optional title
                        )
                        .interactive()
                    )

                    # Display using st.altair_chart
                    st.altair_chart(final_chart, use_container_width=True)
                else:
                    st.caption(
                        "xG/xGA data incomplete or missing, cannot plot comparison chart."
                    )
                    # Optionally display raw values if available
                    xg_col1, xg_col2 = st.columns(2)
                    with xg_col1:
                        st.caption(
                            f"**xG (H):** {selected_match_data.get('xg_h', '--')} | **xGA (H):** {selected_match_data.get('xga_h', '--')}"
                        )
                    with xg_col2:
                        st.caption(
                            f"**xG (A):** {selected_match_data.get('xg_a', '--')} | **xGA (A):** {selected_match_data.get('xga_a', '--')}"
                        )

            except (ValueError, TypeError, KeyError) as e:
                st.caption(f"Could not plot xG comparison chart: {e}")

        st.markdown("---")  # Separator

        # Goals, Corners and Cards
        # def create_and_display_corner_chart(team_name_full, for_spread_str, against_spread_str, num_recent_games=5):
        #     if not for_spread_str or not against_spread_str:
        #         st.markdown(f"**{team_name_full}**")
        #         st.caption("Corner spread data N/A")
        #         return

        #     try:
        #         for_values = [int(float(x)) for x in for_spread_str.split(',')]
        #         against_values = [int(float(x)) for x in against_spread_str.split(',')]

        #         # Take the specified number of recent games
        #         for_values = for_values[:num_recent_games]
        #         against_values = against_values[:num_recent_games]

        #         actual_num_games = min(len(for_values), len(against_values))
        #         if actual_num_games == 0:
        #             st.markdown(f"**{team_name_full}**")
        #             st.caption("Insufficient corner spread data.")
        #             return

        #         # For st.line_chart, the index will be the x-axis.
        #         # We want to show "Game 1" to "Game N" representing the sequence.
        #         # If your data is "most recent first", G1 will be most recent.
        #         game_labels = [f"G{i+1}" for i in range(actual_num_games)]

        #         df_corners = pd.DataFrame({
        #             'For': for_values[:actual_num_games],
        #             'Against': against_values[:actual_num_games]
        #         }, index=game_labels) # Set game_labels as index

        #         st.markdown(f"**{team_name_full}**")
        #         st.line_chart(df_corners, height=200) # Adjust height as needed

        #         # Optionally, also display the raw numbers using st.code or st.caption
        #         # st.caption(f"For: {for_spread_str}")
        #         # st.caption(f"Against: {against_spread_str}")

        #     except (ValueError, TypeError) as e:
        #         st.markdown(f"**{team_name_full}**")
        #         st.caption(f"Error processing corner data: {e}")
        #         st.code(f"For: {for_spread_str}\nAgainst: {against_spread_str}", language=None)
        #     except Exception as e_gen: # Catch any other general exceptions
        #         st.markdown(f"**{team_name_full}**")
        #         st.caption(f"An unexpected error occurred: {e_gen}")

        #     except (ValueError, TypeError) as e:
        #         st.markdown(f"**{team_name_full}**")
        #         st.caption(f"Error processing corner data: {e}")
        #         st.code(f"For: {for_spread_str}\nAgainst: {against_spread_str}", language=None)

        # st.info(selected_match_data.get('l5_away_corners_for'))
        # st.info(selected_match_data.get('l5_away_corners_against'))

        # create_and_display_corner_chart(
        #     f"{away_team} (Away Games)",
        #     selected_match_data.get('l5_away_corners_for'),
        #     selected_match_data.get('l5_away_corners_against')
        # )

        def prepare_discipline_data(
            card_spread_str, foul_spread_str, num_recent_games=5
        ):
            # ... (same as before) ...
            if not card_spread_str or not foul_spread_str:
                return pd.DataFrame()

            default_spread = (
                "0,0,0,0,0"  # Default to all zeros for the specified length
            )

            # Explicitly check if the string is just "0"
            if foul_spread_str.strip() == "0" or foul_spread_str.strip() == 0:
                # print(f"Debug: Spread string is '0'. Defaulting to five zeros.")
                foul_spread_str = default_spread
            try:
                card_values = [int(x) for x in card_spread_str.split(",")]
                foul_values = [int(x) for x in foul_spread_str.split(",")]
                card_values = card_values[:num_recent_games]
                foul_values = foul_values[:num_recent_games]
                actual_num_games = min(len(card_values), len(foul_values))
                if actual_num_games == 0:
                    return pd.DataFrame()
                game_labels = [f"G{i + 1}" for i in range(actual_num_games)]
                df = pd.DataFrame(
                    {
                        "Game": game_labels,
                        "Cards Received by Team": card_values[:actual_num_games],
                        "Cards Given by Referee": foul_values[:actual_num_games],
                    }
                )
                return df
            except (ValueError, TypeError):
                return pd.DataFrame()

        def create_layered_discipline_chart(
            df_team_discipline: pd.DataFrame,
            referee_avg_total_cards_game: float,  # The ref's average *total cards* in a game
            chart_title: str,
            card_color: str = "darkorange",  # More distinct than 'orange'
            foul_color: str = "steelblue",
            ref_line_color: str = "firebrick",  # More distinct red
        ):
            if df_team_discipline.empty:
                st.caption("Insufficient data for discipline chart.")
                return

            base = alt.Chart(df_team_discipline).encode(
                x=alt.X(
                    "Game:N",
                    sort=None,
                    title=None,
                    axis=alt.Axis(labelAngle=0, labelPadding=5),
                )
            )

            bar_cards = base.mark_bar(size=18, opacity=0.8, color=card_color).encode(
                y=alt.Y(
                    "Cards Received by Team:Q",
                    title="Count",
                    axis=alt.Axis(grid=True, tickMinStep=1),
                ),  # Ensure integer ticks
                tooltip=[
                    alt.Tooltip("Game:N"),
                    alt.Tooltip("Cards Received by Team:Q", title="Team Cards"),
                ],
            )

            line_fouls = base.mark_line(
                point=alt.OverlayMarkDef(color=foul_color, size=50),
                strokeWidth=2.5,
                color=foul_color,
            ).encode(
                y=alt.Y(
                    "Cards Given by Referee:Q", axis=alt.Axis(tickMinStep=1)
                ),  # Uses the same y-axis
                tooltip=[
                    alt.Tooltip("Game:N"),
                    alt.Tooltip("Cards Given by Referee:Q", title="Referee Cards"),
                ],
            )

            # Horizontal rule for Referee's Average Total Cards in their games
            # Only add if the value is valid
            layers = [bar_cards, line_fouls]  #
            if (
                pd.notna(referee_avg_total_cards_game)
                and referee_avg_total_cards_game >= 0
            ):
                ref_avg_rule = (
                    alt.Chart(
                        pd.DataFrame({"ref_avg_total": [referee_avg_total_cards_game]})
                    )
                    .mark_rule(
                        strokeDash=[6, 4],
                        strokeWidth=2,
                        color=ref_line_color,
                        opacity=0.9,
                    )
                    .encode(
                        y="ref_avg_total:Q"
                        # Tooltip for rule can be tricky, better to use caption
                    )
                )
                layers.append(ref_avg_rule)

            # Determine Y-axis domain dynamically to include all data + ref line
            max_cards = (
                df_team_discipline["Cards Received by Team"].max()
                if not df_team_discipline.empty
                else 0
            )
            max_fouls = (
                df_team_discipline["Cards Given by Referee"].max()
                if not df_team_discipline.empty
                else 0
            )
            y_max = max(max_cards, max_fouls)
            if (
                pd.notna(referee_avg_total_cards_game)
                and referee_avg_total_cards_game >= 0
            ):
                y_max = max(y_max, referee_avg_total_cards_game)  # max_cards

            y_domain = [0, y_max + 2]  # Add some padding

            layered_chart = (
                alt.layer(*layers)
                .resolve_scale(y="shared")
                .encode(
                    alt.Y(scale=alt.Scale(domain=y_domain))  # Apply the dynamic domain
                )
                .properties(
                    title=alt.TitleParams(
                        text=chart_title, anchor="middle", fontSize=13
                    ),
                    height=275,
                )
                .configure_axis(labelFontSize=10, titleFontSize=11)
                .configure_legend(  # To create a custom legend for the lines/bars if needed
                    title=None,
                    orient="top",
                    padding=10,
                    labelFontSize=10,
                    symbolStrokeWidth=2,
                )
            )

            st.altair_chart(layered_chart, use_container_width=True)
            if (
                pd.notna(referee_avg_total_cards_game)
                and referee_avg_total_cards_game >= 0
            ):
                st.caption(
                    f"<span style='color:{ref_line_color}; font-weight:bold;'>⎯⎯</span> Referee Avg. Total Cards / Game: **{referee_avg_total_cards_game:.1f}**",
                    unsafe_allow_html=True,
                )

        # def prepare_expected_cards_data(
        #     card_spread_str,
        #     foul_spread_str,
        #     ref_cards_per_foul_for_this_team_context: float, # e.g., RefLast5CardsPerFoulHome
        #     num_recent_games=5
        # ):
        #     if not card_spread_str or not foul_spread_str or pd.isna(ref_cards_per_foul_for_this_team_context):
        #         return pd.DataFrame()

        #     try:
        #         card_values = [int(x) for x in card_spread_str.split(',')]
        #         foul_values = [int(x) for x in foul_spread_str.split(',')]

        #         card_values = card_values[:num_recent_games]
        #         foul_values = foul_values[:num_recent_games]

        #         actual_num_games = min(len(card_values), len(foul_values))
        #         if actual_num_games == 0: return pd.DataFrame()

        #         game_labels = [f"G{i+1}" for i in range(actual_num_games)]

        #         expected_card_values = [
        #             round(foul * ref_cards_per_foul_for_this_team_context) # Round to nearest whole card
        #             for foul in foul_values[:actual_num_games]
        #         ]

        #         df = pd.DataFrame({
        #             'Game': game_labels,
        #             'Actual Cards Received': card_values[:actual_num_games],
        #             'Expected Cards (based on Fouls & Ref C/F)': expected_card_values
        #         })
        #         return df
        #     except (ValueError, TypeError):
        #         return pd.DataFrame()

        # def create_actual_vs_expected_cards_chart(
        #     df_discipline_data: pd.DataFrame,
        #     referee_avg_total_cards_game: float,
        #     chart_title: str,
        #     actual_card_color: str = 'darkorange',
        #     expected_card_color: str = 'skyblue', # Different color for the line
        #     ref_line_color: str = 'firebrick'
        # ):
        #     if df_discipline_data.empty:
        #         st.caption("Insufficient data for discipline chart.")
        #         return

        #     base = alt.Chart(df_discipline_data).encode(
        #         x=alt.X('Game:N', sort=None, title=None, axis=alt.Axis(labelAngle=0, labelPadding=5))
        #     )

        #     bar_actual_cards = base.mark_bar(size=18, opacity=0.8, color=actual_card_color).encode(
        #         y=alt.Y('Actual Cards Received:Q', title='Cards', axis=alt.Axis(grid=True, tickMinStep=1)),
        #         tooltip=[alt.Tooltip('Game:N'), alt.Tooltip('Actual Cards Received:Q', title='Actual Cards')]
        #     )

        #     line_expected_cards = base.mark_line(point=alt.OverlayMarkDef(color=expected_card_color, size=50), strokeWidth=2.5, color=expected_card_color).encode(
        #         y=alt.Y('Expected Cards (based on Fouls & Ref C/F):Q', axis=alt.Axis(tickMinStep=1)), # Shared Y-axis
        #         tooltip=[alt.Tooltip('Game:N'), alt.Tooltip('Expected Cards (based on Fouls & Ref C/F):Q', title='Expected Cards')]
        #     )

        #     layers = [bar_actual_cards, line_expected_cards]
        #     if pd.notna(referee_avg_total_cards_game) and referee_avg_total_cards_game >= 0:
        #         ref_avg_rule = alt.Chart(pd.DataFrame({'ref_avg_total': [referee_avg_total_cards_game]})).mark_rule(
        #             strokeDash=[6,4], strokeWidth=2, color=ref_line_color, opacity=0.9
        #         ).encode(y='ref_avg_total:Q')
        #         layers.append(ref_avg_rule)

        #     max_actual = df_discipline_data['Actual Cards Received'].max() if 'Actual Cards Received' in df_discipline_data else 0
        #     max_expected = df_discipline_data['Expected Cards (based on Fouls & Ref C/F)'].max() if 'Expected Cards (based on Fouls & Ref C/F)' in df_discipline_data else 0
        #     y_max = max(max_actual, max_expected)
        #     if pd.notna(referee_avg_total_cards_game) and referee_avg_total_cards_game >=0:
        #         y_max = max(y_max, referee_avg_total_cards_game)
        #     y_domain = [0, y_max + 1.5] # Adjust padding

        #     layered_chart = alt.layer(*layers).resolve_scale(
        #         y='shared'
        #     ).encode(
        #     alt.Y(scale=alt.Scale(domain=y_domain,nice=False), axis=alt.Axis(tickMinStep=1))
        #     ).properties(
        #         title=alt.TitleParams(text=chart_title, anchor='middle', fontSize=13),
        #         height=275,
        #     ).configure_axis(labelFontSize=10, titleFontSize=11)

        #     st.altair_chart(layered_chart, use_container_width=True)
        #     if pd.notna(referee_avg_total_cards_game) and referee_avg_total_cards_game >=0:
        #         st.caption(f"<span style='color:{ref_line_color}; font-weight:bold;'>⎯⎯</span> Referee Avg. Total Cards / Game: **{referee_avg_total_cards_game:.1f}**", unsafe_allow_html=True)

        # --- Example Usage in Streamlit ---

        st.markdown("#### Team Discipline vs. Referee Tendencies")

        referee_name_for_title = selected_match_data.get(
            "Referee", "The Referee"
        )  # "RefereeFullName"

        ref_avg_total_cards = selected_match_data.get("RefLast5AvgTotalCards")

        ref_home_card_spread = selected_match_data.get("RefLast5HomeTeamCards")
        ref_away_card_spread = selected_match_data.get("RefLast5AwayTeamCards")
        # st.info(ref_home_card_spread)
        # st.info(ref_away_card_spread)

        col_home_disc, col_away_disc = st.columns(2)
        # 'RefSeasonAvgTotalCards','RefSeasonAvgHomeTeamCards','RefSeasonAvgAwayTeamCards',
        # 'RefLast5AvgTotalCards','RefLast5AvgHomeTeamCards','RefLast5AvgAwayTeamCards',
        # 'RefLast5HomeTeamCards','RefLast5AwayTeamCards',

        # HOME TEAM DISCIPLINE SECTION
        with col_home_disc:
            st.markdown(f"##### {home_team} (Last 5 Home Games)")

            # Key Metrics Display
            home_team_fouls_spread_l5 = selected_match_data.get(
                "l5_home_fouls_for", "0"
            )
            home_team_cards_spread_l5 = selected_match_data.get(
                "l5_home_cards_for", "0"
            )
            home_team_avg_fouls_l5 = (
                np.mean(
                    [
                        int(x)
                        for x in selected_match_data.get(
                            "l5_home_fouls_for", "0"
                        ).split(",")
                        if x
                    ]
                )
                if selected_match_data.get("l5_home_fouls_for")
                else np.nan
            )
            home_team_avg_cards_l5 = (
                np.mean(
                    [
                        int(x)
                        for x in selected_match_data.get(
                            "l5_home_cards_for", "0"
                        ).split(",")
                        if x
                    ]
                )
                if selected_match_data.get("l5_home_cards_for")
                else np.nan
            )

            ref_cards_per_foul_home_l5 = selected_match_data.get(
                "RefLast5CardsPerFoulHome"
            )  # Specific to ref for this team at home
            ref_strictness_label_home_l5 = selected_match_data.get(
                "RefLast5HomeLabel"
            )  # Ref's strictness for this team at home

            ref_home_average_l5 = selected_match_data.get("RefLast5AvgHomeTeamCards")

            if pd.notna(home_team_avg_fouls_l5):
                st.markdown(f"- Avg. Fouls Committed: **{home_team_avg_fouls_l5:.1f}**")
            if pd.notna(home_team_avg_cards_l5):
                st.markdown(f"- Avg. Cards Received: **{home_team_avg_cards_l5:.1f}**")
            # if ref_avg_total_cards:
            #     st.markdown(f"- {referee_name_for_title}'s Cards/Game (Overall avg, L5): **{ref_avg_total_cards}**")
            # if ref_home_average_l5:
            #     st.markdown(f"- {referee_name_for_title}'s Cards/Game (vs Home, L5): **{ref_home_average_l5}**")
            if pd.notna(ref_cards_per_foul_home_l5):
                st.markdown(
                    f"- {referee_name_for_title}'s Cards/Foul (vs Home, L5): **{ref_cards_per_foul_home_l5 / 100:.2f}**"
                )
            if ref_strictness_label_home_l5:
                st.markdown(
                    f"- {referee_name_for_title}'s Strictness (vs Home, L5): **{ref_strictness_label_home_l5}**"
                )

            # Chart
            df_home_disc_data = prepare_discipline_data(
                selected_match_data.get("l5_home_cards_for"),
                # selected_match_data.get('l5_home_fouls_for')
                ref_home_card_spread,
            )  #
            # Assuming you have a field for referee's average total cards in their games
            # ref_avg_total_cards = selected_match_data.get('RefSeasonTotalCardsAvg') # Or RefLast5TotalCardsAvg

            create_layered_discipline_chart(
                df_team_discipline=df_home_disc_data,
                referee_avg_total_cards_game=ref_avg_total_cards,  # This is total cards by ref in a game
                chart_title=f"{home_team} Discipline",
            )

            # df_home_exp_data = prepare_expected_cards_data( home_team_cards_spread_l5,home_team_fouls_spread_l5, ref_cards_per_foul_home_l5)

            # create_actual_vs_expected_cards_chart(
            #     df_discipline_data=df_home_exp_data,
            #     referee_avg_total_cards_game=ref_avg_total_cards,
            #     chart_title=f"{home_team} Actual vs. Expected Cards"
            # )
            st.caption(
                f"Bars: Cards Received by {home_team}. Line: Fouls Committed by {home_team}."
            )

        # AWAY TEAM DISCIPLINE SECTION (similar structure)
        with col_away_disc:
            st.markdown(f"##### {away_team} (Last 5 Away Games)")

            away_team_fouls_spread_l5 = selected_match_data.get(
                "l5_away_fouls_for", "0"
            )
            away_team_cards_spread_l5 = selected_match_data.get(
                "l5_away_cards_for", "0"
            )
            away_team_avg_fouls_l5 = (
                np.mean(
                    [
                        int(x)
                        for x in selected_match_data.get(
                            "l5_away_fouls_for", "0"
                        ).split(",")
                        if x
                    ]
                )
                if selected_match_data.get("l5_away_fouls_for")
                else np.nan
            )
            away_team_avg_cards_l5 = (
                np.mean(
                    [
                        int(x)
                        for x in selected_match_data.get(
                            "l5_away_cards_for", "0"
                        ).split(",")
                        if x
                    ]
                )
                if selected_match_data.get("l5_away_cards_for")
                else np.nan
            )
            ref_cards_per_foul_away_l5 = selected_match_data.get(
                "RefLast5CardsPerFoulAway"
            )
            ref_strictness_label_away_l5 = selected_match_data.get("RefLast5AwayLabel")
            ref_away_average_l5 = selected_match_data.get("RefLast5AvgAwayTeamCards")

            if pd.notna(away_team_avg_fouls_l5):
                st.markdown(f"- Avg. Fouls Committed: **{away_team_avg_fouls_l5:.1f}**")
            if pd.notna(away_team_avg_cards_l5):
                st.markdown(f"- Avg. Cards Received: **{away_team_avg_cards_l5:.1f}**")
            # if ref_avg_total_cards:
            #     st.markdown(f"- {referee_name_for_title}'s Cards/Game (Overall avg, L5): **{ref_avg_total_cards}**")
            # if ref_away_average_l5:
            #     st.markdown(f"- {referee_name_for_title}'s Cards/Game (vs Away, L5): **{ref_away_average_l5}**")
            if pd.notna(ref_cards_per_foul_away_l5):
                st.markdown(
                    f"- {referee_name_for_title}'s Cards/Foul (vs Away, L5): **{ref_cards_per_foul_away_l5 / 100:.2f}**"
                )
            if ref_strictness_label_away_l5:
                st.markdown(
                    f"- {referee_name_for_title}'s Strictness (vs Away, L5): **{ref_strictness_label_away_l5}**"
                )

            # Chart
            df_away_disc_data = prepare_discipline_data(
                selected_match_data.get("l5_away_cards_for"),
                # selected_match_data.get('l5_away_fouls_for')
                ref_away_card_spread,
            )  #
            # ref_avg_total_cards is the same for the match

            create_layered_discipline_chart(
                df_team_discipline=df_away_disc_data,
                referee_avg_total_cards_game=ref_avg_total_cards,
                chart_title=f"{away_team} Discipline",
            )

            # df_away_exp_data = prepare_expected_cards_data(away_team_cards_spread_l5,away_team_fouls_spread_l5,  ref_cards_per_foul_away_l5)

            # create_actual_vs_expected_cards_chart(
            #     df_discipline_data=df_away_exp_data,
            #     referee_avg_total_cards_game=ref_avg_total_cards,
            #     chart_title=f"{home_team} Actual vs. Expected Cards"
            # )

            st.caption(
                f"Bars: Cards Received by {away_team}. Line: Fouls Committed by {away_team}."
            )

        st.markdown("---")  # Main section divider

        stats_cols = st.columns(4)
        with stats_cols[0]:
            st.markdown("#### Goal Trends")
            h_halves_text = selected_match_data.get("halves_o05_h", "")
            h1_pct = (
                selected_match_data.get("1h_o05_h", "") * 100
            )  # parse_specific_percent(h_halves_text, '1H', 0)
            h2_pct = (
                selected_match_data.get("2h_o05_h", "") * 100
            )  # parse_specific_percent(h_halves_text, '2H', 0)

            st.markdown(
                f"##### {selected_match_data.get('home_team', 'Home')} (Last 5 Home Games)"
            )  # (H): 1H={h1_pct}% | 2H={h2_pct}%

            st.markdown("**Halves > 0.5 Goals %**")
            # st.progress(h1_pct / 100.0, text=f"1H {h1_pct}%")
            # st.progress(h2_pct / 100.0, text=f"2H {h2_pct}%")
            st.markdown("**First Half  (1H):**")
            st.markdown(
                create_colored_progress_bar(h1_pct, text_label="1H"),
                unsafe_allow_html=True,
            )
            st.markdown("**Second Half (2H):**")
            st.markdown(
                create_colored_progress_bar(h2_pct, text_label="2H"),
                unsafe_allow_html=True,
            )
            st.markdown("---")

            st.markdown("**Matches Over X Goals %**")
            h_match_goals_text = selected_match_data.get("match_goals_h", "")
            o15_h_pct = (
                selected_match_data.get("match_goals_1_5_h", "") * 100
            )  # parse_specific_percent(h_match_goals_text, 'O1.5', 0)
            o25_h_pct = (
                selected_match_data.get("match_goals_2_5_h", "") * 100
            )  # parse_specific_percent(h_match_goals_text, 'O2.5', 0)
            # st.markdown(f**"{selected_match_data.get('home_team','H')} (H): O1.5={o15_h_pct}% | O2.5={o25_h_pct}%**")
            # st.progress(o15_h_pct / 100.0, text=f"O1.5 {o15_h_pct}%")
            # st.progress(o25_h_pct / 100.0, text=f"O2.5 {o25_h_pct}%")
            st.markdown("**Over 1.5:**")
            st.markdown(
                create_colored_progress_bar(o15_h_pct, text_label="O1.5"),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 2.5:**")
            st.markdown(
                create_colored_progress_bar(o25_h_pct, text_label="O2.5"),
                unsafe_allow_html=True,
            )

            st.markdown("---")

            st.markdown("**Home Team Scored Over X Goals %**")
            h_team_goals_text = selected_match_data.get(
                "team_goals_h", "Over 0.5: 0% | O1.5: 0%"
            )
            o05_h_pct = (
                selected_match_data.get("team_goals_0_5_h", "") * 100
            )  # parse_specific_percent(h_team_goals_text, 'Over 0.5', 0)
            o15_h_pct_team = (
                selected_match_data.get("team_goals_1_5_h", "") * 100
            )  # parse_specific_percent(h_team_goals_text, 'O1.5', 0)
            st.markdown("**Over 0.5:**")
            st.markdown(
                create_colored_progress_bar(o05_h_pct, text_label="O0.5"),
                unsafe_allow_html=True,
            )
            # --- END REPLACE ---
            st.markdown("**Over 1.5:**")
            # --- REPLACE st.progress ---
            st.markdown(
                create_colored_progress_bar(o15_h_pct_team, text_label="O1.5"),
                unsafe_allow_html=True,
            )

        with stats_cols[1]:
            st.markdown("#### ")
            a_match_goals_text = selected_match_data.get("match_goals_a", "")
            o15_a_pct = (
                selected_match_data.get("1h_o05_a", "") * 100
            )  # parse_specific_percent(a_match_goals_text, 'O1.5', 0)
            o25_a_pct = (
                selected_match_data.get("2h_o05_a", "") * 100
            )  # parse_specific_percent(a_match_goals_text, 'O2.5', 0)

            st.markdown(
                f"##### {selected_match_data.get('away_team', 'Away')} (Last 5 Away Games)"
            )  # (A): O1.5={o15_a_pct}% | O2.5={o25_a_pct}%
            st.markdown("**Halves > 0.5 Goals %**")
            # st.progress(o15_a_pct / 100.0, text=f"O1.5 {o15_a_pct}%")
            # st.progress(o25_a_pct / 100.0, text=f"O2.5 {o25_a_pct}%")
            st.markdown("**First Half  (1H):**")
            st.markdown(
                create_colored_progress_bar(o15_a_pct, text_label="O1.5"),
                unsafe_allow_html=True,
            )
            st.markdown("**Second Half (2H):**")
            st.markdown(
                create_colored_progress_bar(o25_a_pct, text_label="O2.5"),
                unsafe_allow_html=True,
            )
            st.markdown("---")

            st.markdown("**Matches Over X Goals %**")
            a_halves_text = selected_match_data.get("halves_o05_a", "")
            a1_pct = (
                selected_match_data.get("match_goals_1_5_a", "") * 100
            )  # parse_specific_percent(a_halves_text, '1H', 0)
            a2_pct = (
                selected_match_data.get("match_goals_2_5_a", "") * 100
            )  # parse_specific_percent(a_halves_text, '2H', 0)
            # st.markdown(f"{selected_match_data.get('away_team','A')} (A): 1H={a1_pct}% | 2H={a2_pct}%")
            # st.progress(a1_pct / 100.0, text=f"1H {a1_pct}%")
            # st.progress(a2_pct / 100.0, text=f"2H {a2_pct}%")
            st.markdown("**Over 1.5:**")
            st.markdown(
                create_colored_progress_bar(a1_pct, text_label="1H"),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 2.5:**")
            st.markdown(
                create_colored_progress_bar(a2_pct, text_label="2H"),
                unsafe_allow_html=True,
            )
            st.markdown("---")

            st.markdown("**Away Team Scored Over X Goals %**")
            a_team_goals_text = selected_match_data.get(
                "team_goals_a", "Over 0.5: 0% | O1.5: 0%"
            )
            o05_a_pct = (
                selected_match_data.get("team_goals_0_5_a", "") * 100
            )  # parse_specific_percent(a_team_goals_text, 'Over 0.5', 0)
            o15_a_pct_team = (
                selected_match_data.get("team_goals_1_5_a", "") * 100
            )  # parse_specific_percent(a_team_goals_text, 'O1.5', 0)
            st.markdown("**Over 0.5:**")
            st.markdown(
                create_colored_progress_bar(o05_a_pct, text_label="O0.5"),
                unsafe_allow_html=True,
            )
            # --- END REPLACE ---
            st.markdown("**Over 1.5:**")
            # --- REPLACE st.progress ---
            st.markdown(
                create_colored_progress_bar(o15_a_pct_team, text_label="O1.5"),
                unsafe_allow_html=True,
            )
            # --- END REPLACE ---

        with stats_cols[2]:
            st.markdown("#### Corners and Cards")
            st.markdown(
                f"##### {selected_match_data.get('home_team', 'Home')} (Last 5 Home Games)"
            )
            st.markdown("**Corners (O/U)**")

            st.markdown("**Over 7.5 Corners:**")
            st.markdown(
                create_colored_progress_bar(Last5HomeOver7Corners, text_label="O7.5"),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 8.5 Corners:**")
            st.markdown(
                create_colored_progress_bar(Last5HomeOver8Corners, text_label="O8.5"),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 9.5 Corners:**")
            st.markdown(
                create_colored_progress_bar(Last5HomeOver9Corners, text_label="O9.5"),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 10.5 Corners:**")
            st.markdown(
                create_colored_progress_bar(Last5HomeOver10Corners, text_label="O10.5"),
                unsafe_allow_html=True,
            )

            st.markdown("---")

            st.markdown("**Cards (O/U)**")
            # st.metric(label="Referee Home Avg.", value=ref_l5_home_avg, )
            st.markdown("**Over 1.5 Cards:**")
            st.markdown(
                create_colored_progress_bar(
                    Last5HomeOver1YellowCards, text_label="O1.5"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 2.5 Cards:**")
            st.markdown(
                create_colored_progress_bar(
                    Last5HomeOver2YellowCards, text_label="O2.5"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 3.5 Cards:**")
            st.markdown(
                create_colored_progress_bar(
                    Last5HomeOver3YellowCards, text_label="O3.5"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 4.5 Cards:**")
            st.markdown(
                create_colored_progress_bar(
                    Last5HomeOver4YellowCards, text_label="O4.5"
                ),
                unsafe_allow_html=True,
            )

        with stats_cols[3]:
            st.markdown("#### ")
            st.markdown(
                f"##### {selected_match_data.get('away_team', 'Away')} (Last 5 Away Games)"
            )
            st.markdown("**Corners (O/U)**")

            st.markdown("**Over 7.5 Corners:**")
            st.markdown(
                create_colored_progress_bar(Last5AwayOver7Corners, text_label="O7.5"),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 8.5 Corners:**")
            st.markdown(
                create_colored_progress_bar(Last5AwayOver8Corners, text_label="O8.5"),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 9.5 Corners:**")
            st.markdown(
                create_colored_progress_bar(Last5AwayOver9Corners, text_label="O9.5"),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 10.5 Corners:**")
            st.markdown(
                create_colored_progress_bar(Last5AwayOver10Corners, text_label="O10.5"),
                unsafe_allow_html=True,
            )

            st.markdown("---")
            st.markdown("**Cards (O/U)**")

            st.markdown("**Over 1.5 Cards:**")
            st.markdown(
                create_colored_progress_bar(
                    Last5AwayOver1YellowCards, text_label="O1.5"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 2.5 Cards:**")
            st.markdown(
                create_colored_progress_bar(
                    Last5AwayOver2YellowCards, text_label="O2.5"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 3.5 Cards:**")
            st.markdown(
                create_colored_progress_bar(
                    Last5AwayOver3YellowCards, text_label="O3.5"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("**Over 4.5 Cards:**")
            st.markdown(
                create_colored_progress_bar(
                    Last5AwayOver4YellowCards, text_label="O4.5"
                ),
                unsafe_allow_html=True,
            )

    # H2H Tab
    def display_h2h_stats(
        metric_label, h2h_val, team_overall_avg, league_avg_context, team, inverse_flag
    ):
        # h2h_val = float(selected_match_data.get('h2h_home_shots_against_avg', 0.0)) # Shots conceded by Home in H2H
        # team_overall_avg = float(selected_match_data.get('shots_against_home_avg', 0.0)) # Team's overall avg AGAINST @ Home
        delta_vs_team = h2h_val - team_overall_avg
        # league_avg_context = float(selected_match_data.get('shots_against_league_home_avg', 0.0)) # League avg AGAINST @ Home
        if inverse_flag == 1:
            inverse_value = "inverse"
        else:
            inverse_value = "normal"
        st.metric(
            label=metric_label,
            value=f"{h2h_val:.2f}",
            delta=f"{delta_vs_team:+.2f} vs Team Avg ({team_overall_avg})",
            delta_color=inverse_value,  # Lower is better for AGAINST
        )
        st.caption(f"League Avg FOR @ {team}: {league_avg_context:.2f}")  # Context

    with tabs[2]:
        st.markdown("#### Head-to-Head (H2H)")
        # ... (Keep H2H records display) ...
        st.markdown("##### Home vs Away Averages (in H2H Games)")
        HeadToHeadBTTS = (
            round(selected_match_data.get("HeadToHeadBTTS"), 2) * 100
            if selected_match_data.get("HeadToHeadBTTS") is not None
            else 0
        )

        cols1, cols2, cols3 = st.columns([1, 1.5, 2])
        with cols1:
            h2h_cols = st.columns(2)
            h2h_cols[0].metric(
                label="Home vs Away Record",
                value=selected_match_data.get("h2h_hva_record", "--").strip("()"),
            )
            h2h_cols[0].metric(
                label="All Time H2H Record",
                value=selected_match_data.get("h2h_all_record", "--").strip("()"),
            )
            h2h_cols[0].metric(
                label="Home xG",
                value=HeadToHeadHomeXG,
                delta=f"{HeadToHeadHomeXG - HeadToHeadAwayXG} vs Away xG",
            )
            h2h_cols[0].metric(label="H2H GG", value=f"{HeadToHeadBTTS}%")

            h2h_cols[1].metric(
                label="Matches", value=selected_match_data.get("h2h_hva_games", "--")
            )
            h2h_cols[1].metric(
                label="Matches", value=selected_match_data.get("h2h_all_games", "--")
            )
            h2h_cols[1].metric(
                label="Away xG",
                value=HeadToHeadAwayXG,
                delta=f"{HeadToHeadAwayXG - HeadToHeadHomeXG} vs Home xG",
            )

        with cols2:
            # st.markdown("##### H2H Stats")
            # st.markdown("")
            h2h_stats_cols = st.columns(2)

            with h2h_stats_cols[0]:
                display_h2h_stats(
                    "**Home Total Shots:**",
                    HeadToHeadHomeTotalShots,
                    Last5HomeAvergeTotalShots,
                    l5_home_for_league_avg_shots,
                    "Home",
                    0,
                )
                display_h2h_stats(
                    "**Home Shots On Target:**",
                    HeadToHeadHomeShotsOnTarget,
                    Last5HomeAvergeTotalShotsOnGoal,
                    l5_home_for_league_avg_sot,
                    "Home",
                    0,
                )
                display_h2h_stats(
                    "**Home Fouls:**",
                    HeadToHeadHomeFouls,
                    Last5HomeAvergeTotalFouls,
                    l5_home_for_league_avg_fouls,
                    "Home",
                    1,
                )

            with h2h_stats_cols[1]:
                display_h2h_stats(
                    "**Away Total Shots:**",
                    HeadToHeadAwayTotalShots,
                    Last5AwayAvergeTotalShots,
                    l5_away_for_league_avg_shots,
                    "Away",
                    0,
                )
                display_h2h_stats(
                    "**Away Shots On Target:**",
                    HeadToHeadAwayShotsOnTarget,
                    Last5AwayAvergeTotalShotsOnGoal,
                    l5_away_for_league_avg_sot,
                    "Away",
                    0,
                )
                display_h2h_stats(
                    "**Away Fouls:**",
                    HeadToHeadAwayFouls,
                    Last5AwayAvergeTotalFouls,
                    l5_away_for_league_avg_fouls,
                    "Away",
                    1,
                )

        with cols3:
            try:
                # Prepare data in 'long' format
                home_team_label = selected_match_data.get("home_team", "Home")
                away_team_label = selected_match_data.get("away_team", "Away")
                home_abbr = "".join([word[0] for word in home_team_label.split()[:2]])
                away_abbr = "".join([word[0] for word in away_team_label.split()[:2]])

                h2h_ppg_h = selected_match_data.get(
                    "h2h_h_ppg"
                )  # parse_h2h_value(, 'H', default=0.0)
                h2h_ppg_a = selected_match_data.get(
                    "h2h_a_ppg"
                )  # parse_h2h_value(, 'A', default=0.0)
                h2h_goals_h = selected_match_data.get(
                    "h2h_h_goals_scored"
                )  # parse_h2h_value(, 'H', default=0.0)
                h2h_goals_a = selected_match_data.get(
                    "h2h_a_goals_scored"
                )  # parse_h2h_value(, 'A', default=0.0)

                # Create list of dictionaries for DataFrame
                h2h_data_long = [
                    {
                        "Metric": f"{home_team_label} PPG",
                        "Value": h2h_ppg_h,
                        "TeamType": "Home",
                    },
                    {
                        "Metric": f"{away_team_label} PPG",
                        "Value": h2h_ppg_a,
                        "TeamType": "Away",
                    },
                    {
                        "Metric": f"{home_team_label} Goals",
                        "Value": h2h_goals_h,
                        "TeamType": "Home",
                    },
                    {
                        "Metric": f"{away_team_label} Goals",
                        "Value": h2h_goals_a,
                        "TeamType": "Away",
                    },
                ]
                h2h_df_long = pd.DataFrame(h2h_data_long)

                # Define specific colors
                home_color = "#8bc34a"  # Light Green
                away_color = "#ff9800"  # Orange

                # Create Altair chart
                chart_h2h = (
                    alt.Chart(h2h_df_long)
                    .mark_bar()
                    .encode(
                        x=alt.X(
                            "Metric",
                            sort=None,
                            title=None,
                            axis=alt.Axis(title=None, labelAngle=0),
                        ),  # Keep defined order, remove axis title
                        y=alt.Y("Value", title="Avg Value"),
                        color=alt.Color(
                            "TeamType",
                            scale=alt.Scale(
                                domain=["Home", "Away"], range=[home_color, away_color]
                            ),
                            legend=alt.Legend(title="Team"),
                        ),
                        tooltip=["Metric", alt.Tooltip("Value", format=".2f")],
                    )
                )
                # 2. Bar layer
                bar_chart = chart_h2h.mark_bar()

                # 3. Text layer for labels
                text_labels = chart_h2h.mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-5,  # Adjust vertical offset slightly above the bar
                    # Optional: Change text color for better visibility if needed
                    # color='black'
                ).encode(
                    # Encode the text channel with the 'Value', formatted to 2 decimal places
                    text=alt.Text("Value", format=".2f"),
                    # Important: Remove color encoding from text or set explicitly if needed,
                    # otherwise text might inherit bar colors making it hard to read on some backgrounds.
                    # Let's remove it here to default to black/dark text.
                    color=alt.value(
                        "black"
                    ),  # Force text color or remove the line altogether for default
                )

                # 4. Combine the layers
                final_chart = (
                    (bar_chart + text_labels)
                    .properties(
                        # title='Avg Goals Scored/Conceded' # Optional title
                    )
                    .interactive()
                )

                # Display using st.altair_chart
                st.altair_chart(final_chart, use_container_width=True)

            except (ValueError, TypeError, KeyError, ImportError) as e:
                st.caption(f"Error plotting H2H averages: {e}")
                if isinstance(e, ImportError):
                    st.warning("Please install altair: pip install altair")

        st.markdown("---")
        st.markdown("##### Home vs Away Over/Under Goals (in H2H Games)")
        # Parse H2H Over/Under - more complex string potentially
        h2h_ou_text = selected_match_data.get("h2h_hva_ou", "")
        o15_h2h = int(
            (selected_match_data.get("h2h_hva_o1_5") or 0) * 100
        )  # parse_specific_percent(h2h_ou_text, 'O1.5', 0)
        o25_h2h = int(
            (selected_match_data.get("h2h_hva_o2_5") or 0) * 100
        )  # parse_specific_percent(h2h_ou_text, 'O2.5', 0)
        u25_h2h = int(
            (selected_match_data.get("h2h_hva_u2_5") or 0) * 100
        )  # parse_specific_percent(h2h_ou_text, 'U2.5', 0)
        u35_h2h = int(
            (selected_match_data.get("h2h_hva_u3_5") or 0) * 100
        )  # parse_specific_percent(h2h_ou_text, 'U3.5', 0)
        h2h_ou_cols = st.columns(3)
        with h2h_ou_cols[0]:
            st.markdown("##### Goal Stats")
            st.markdown("1st & 2nd Half Goals Trends")
            half_cols = st.columns(2)
            with half_cols[0]:
                st.metric(
                    "Home 1H",
                    selected_match_data.get("HeadToHeadHomeFirstHalfGoalsScored")
                    or "--",
                )
                st.metric(
                    "Away 1H",
                    selected_match_data.get("HeadToHeadAwayFirstHalfGoalsScored")
                    or "--",
                )
            with half_cols[1]:
                st.metric(
                    "Home 2H",
                    selected_match_data.get("HeadToHeadHomeSecondHalfGoalsScored")
                    or "--",
                )
                st.metric(
                    "Away 2H",
                    selected_match_data.get("HeadToHeadAwaySecondHalfGoalsScored")
                    or "--",
                )

        with h2h_ou_cols[1]:
            st.markdown("##### Corner Stats")
            st.markdown("Corners Trends")
            corner_stats_cols = st.columns(2)
            with corner_stats_cols[0]:
                # st.metric("**Home Corners:**", )
                display_h2h_stats(
                    "**Home Corners:**",
                    HeadToHeadHomeCorners,
                    Last5HomeAvergeTotalcorners,
                    l5_home_for_league_avg_corners,
                    "Home",
                    0,
                )

            with corner_stats_cols[1]:
                # st.metric("**Away Corners:**", )
                display_h2h_stats(
                    "**Away Corners:**",
                    HeadToHeadAwayCorners,
                    Last5AwayAvergeTotalcorners,
                    l5_away_for_league_avg_corners,
                    "Away",
                    0,
                )

        with h2h_ou_cols[2]:
            st.markdown("##### Card Stats")
            st.markdown("Cards Trends")
            card_stats_cols = st.columns(2)
            with card_stats_cols[0]:
                display_h2h_stats(
                    "**Home Yellows:**",
                    HeadToHeadHomeYellowCards,
                    Last5HomeAvergeTotalYellowCards,
                    l5_home_for_league_avg_yellow_cards,
                    "Home",
                    1,
                )
                # st.metric("**Home Yellow Cards:**", selected_match_data.get('HeadToHeadHomeYellowCards') or '--')
                # st.metric("**Home Red Cards:**", selected_match_data.get('HeadToHeadHomeRedCards') or '--')
            with card_stats_cols[1]:
                # st.metric("**Away Yellow Cards:**", selected_match_data.get('HeadToHeadAwayYellowCards') or '--')
                # st.metric("**Away Red Cards:**", selected_match_data.get('HeadToHeadAwayRedCards') or '--')
                display_h2h_stats(
                    "**Away Yellows:**",
                    HeadToHeadAwayYellowCards,
                    Last5AwayAvergeTotalYellowCards,
                    l5_away_for_league_avg_yellow_cards,
                    "Away",
                    1,
                )

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
            o7c = int((selected_match_data.get("HeadToHeadOver7Corners") or 0) * 100)
            o8c = int((selected_match_data.get("HeadToHeadOver8Corners") or 0) * 100)
            o9c = int((selected_match_data.get("HeadToHeadOver9Corners") or 0) * 100)
            o10c = int((selected_match_data.get("HeadToHeadOver10Corners") or 0) * 100)

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
            o1c = int(
                (selected_match_data.get("HeadToHeadOver1YellowCards") or 0) * 100
            )
            o2c = int(
                (selected_match_data.get("HeadToHeadOver2YellowCards") or 0) * 100
            )
            o3c = int(
                (selected_match_data.get("HeadToHeadOver3YellowCards") or 0) * 100
            )
            o4c = int(
                (selected_match_data.get("HeadToHeadOver4YellowCards") or 0) * 100
            )

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
        insights_home_parsed = parse_insights_string(
            selected_match_data.get("insights_home")
        )
        insights_away_parsed = parse_insights_string(
            selected_match_data.get("insights_away")
        )
        insights_total_h_parsed = parse_insights_string(
            selected_match_data.get("insights_total_h")
        )
        insights_total_a_parsed = parse_insights_string(
            selected_match_data.get("insights_total_a")
        )

        # Display Team Specific Insights
        st.markdown("**Team Specific Insights vs League Average**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{selected_match_data['home_team']} (Home)**")
            if not insights_home_parsed:
                st.caption("No home insights.")
            for insight in insights_home_parsed:
                if isinstance(insight, dict) and insight.get("delta_str"):
                    st.metric(
                        label=insight["label"],
                        value=insight["value"],
                        delta=insight["delta_str"],
                    )
                elif insight.get("value"):
                    st.metric(insight["label"], insight["value"])
                else:
                    st.caption(f"{insight['label']} (No data)")
        with col2:
            st.markdown(f"**{selected_match_data['away_team']} (Away)**")
            if not insights_away_parsed:
                st.caption("No away insights.")
            for insight in insights_away_parsed:
                if insight.get("delta_str"):
                    st.metric(
                        label=insight["label"],
                        value=insight["value"],
                        delta=insight["delta_str"],
                    )
                elif insight.get("value"):
                    st.metric(insight["label"], insight["value"])
                else:
                    st.caption(f"{insight['label']} (No data)")

        st.markdown("---")
        # Display Total Match Insights
        st.markdown("**Total Match Insights vs League Average**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**(Based on {selected_match_data['home_team']} Matches)**")
            if not insights_total_h_parsed:
                st.caption("No total match insights (Home perspective).")
            for insight in insights_total_h_parsed:
                if insight.get("delta_str"):
                    st.metric(
                        label=insight["label"],
                        value=insight["value"],
                        delta=insight["delta_str"],
                    )
                elif insight.get("value"):
                    st.markdown(f"**{insight['label']}:** {insight['value']}")
                else:
                    st.caption(f"{insight['label']} (No data)")

        with col2:
            st.markdown(f"**(Based on {selected_match_data['away_team']} Matches)**")
            if not insights_total_a_parsed:
                st.caption("No total match insights (Away perspective).")
            for insight in insights_total_a_parsed:
                if insight.get("delta_str"):
                    st.metric(
                        label=insight["label"],
                        value=insight["value"],
                        delta=insight["delta_str"],
                    )
                elif insight.get("value"):
                    st.markdown(f"**{insight['label']}:** {insight['value']}")
                else:
                    st.caption(f"{insight['label']} (No data)")

    # with tabs[4]:
    # st.markdown(f"### 🎲 Odds for {selected_match_data.get('HomeTeam', '')} vs {selected_match_data.get('AwayTeam', '')}")

    # if not selected_match_data:
    #     st.info("Select a match to view odds.")
    # else:
    #     # Group the odds from selected_match_data
    #     odds_by_market = group_odds_by_market(selected_match_data)

    #     if not odds_by_market:
    #         st.info("No odds data available for this match.")
    #     else:
    #         for market_name, odds_list in odds_by_market.items():
    #             with st.expander(f"{market_name}", expanded=False): # Start collapsed
    #                 # Determine number of columns based on odds_list length for that market
    #                 # Max 3 columns for readability, or fewer if fewer items
    #                 num_items = len(odds_list)
    #                 if num_items == 0:
    #                     st.caption("No odds for this market.")
    #                     continue

    #                 cols = st.columns(min(num_items, 3))
    #                 col_idx = 0
    #                 for odd_item in odds_list:
    #                     with cols[col_idx % len(cols)]:
    #                         bet_label = odd_item['bet_label']
    #                         odds_val = odd_item['odds_value']

    #                         # For Over/Under, try to make label more concise if it's long
    #                         if "Over/Under" in market_name or "Over Under" in market_name:
    #                             # 'bet_label' is already 'Over X.X' or 'Under X.X'
    #                             display_label = bet_label
    #                         elif market_name == "Total - Home" or market_name == "Total - Away":
    #                             display_label = bet_label # e.g. "Over 0.5"
    #                         else:
    #                             display_label = bet_label

    #                         # Display using st.metric or st.text_input (as placeholder)
    #                         if isinstance(odds_val, (int, float)):
    #                             st.metric(label=display_label, value=f"{odds_val:.2f}")
    #                         else: # For "N/A" or other non-numeric
    #                             st.metric(label=display_label, value=str(odds_val))

    #                         # If you want to use text_input as a placeholder for future editing:
    #                         # st.text_input(label=display_label, value=str(odds_val), key=odd_item['original_field'], disabled=True)
    #                     col_idx += 1
