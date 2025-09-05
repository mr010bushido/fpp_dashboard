import math
import os
import re

import numpy as np
import pandas as pd
import streamlit as st

from config import CSV_FILE_PATH, DB_PARAMS, TEXT_FILE_PATH
from utils import add_transient_message, clean_prediction_string


# --- Data Loading Functions ---
def load_weekly_data(file_path):
    try:
        if os.path.exists(file_path):
            return load_data_from_csv(file_path)
        else:
            st.error(f"File not found: {file_path}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading weekly file {file_path}: {e}")
        return pd.DataFrame()


def remove_duplicate_records(df) -> pd.DataFrame:
    df_deduplicated = df.drop_duplicates(subset=["match_id"], keep="first")
    cleaned_data = df_deduplicated.astype(object).where(
        pd.notnull(df_deduplicated), None
    )
    return cleaned_data


@st.cache_data
def load_data_from_text(filepath):
    st.info(f"Loading data from Text file: {filepath}")
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

    match_blocks = re.split(r"(?=📅)", content)

    for i, block in enumerate(match_blocks):
        block = block.strip()
        if not block or not block.startswith("📅"):
            continue

        match = {"raw_block": block}
        lines = block.strip().split("\n")
        current_insight_type = None
        insight_buffer = ""

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
                "match_id": None,
            }
        )

        home_team_buffer = None

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            try:
                if line.startswith("📅"):
                    m = re.search(r"📅\s*([\d/]+),\s*🕛\s*([\d:]+)", line)
                    if m:
                        match["date"], match["time"] = m.groups()
                elif re.match(
                    r"^[🌍🌎🌏🗺️⚽🏀🏈⚾🥎🎾🏐🏉🎱🔮🎮👾🏆🥇🥈🥉🏅🎖️🏵️🎗️🎀🎁🎂🎃🎄🎅🎆🎇✨🎈🎉🎊🎋🎍🎎🎏🎐🎑🧧🎀🎁🎗️🎟️🎫",
                    line,
                ):
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        match["league"] = parts
                        country_parts = parts.split(",", 1)
                        match["country"] = country_parts.strip()
                        if len(country_parts) > 1:
                            league_part = re.sub(
                                r"\s*\(\s*\d+\s*\)\s*$", "", country_parts
                            ).strip()
                            match["league_name"] = league_part
                        else:
                            match["league_name"] = match["country"]
                elif line.startswith("⚡"):
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
                        home_team_buffer = match["home_team"]

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
                    match["advice"] = line.split(":", 1).strip()
                elif line.startswith("🎯"):
                    match["value_bets"] = line.split(":", 1).strip()

                elif line.startswith("📊 *H/All Form*:"):
                    form_line = line.split(": ", 1)
                    parts = form_line.split("//")
                    home_parts = parts.split("║") if "║" in parts else [parts, ""]
                    away_parts = (
                        parts.split("║")
                        if len(parts) > 1 and "║" in parts
                        else [parts if len(parts) > 1 else "", ""]
                    )
                    match["form_home"] = home_parts.strip()
                    match["form_away"] = away_parts[0].strip()
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
                        xg_a_val = m_goals.group(4).strip().rstrip(")")
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
                        xga_a_val = m_conc.group(4).strip().rstrip(")")
                        match["xga_a"] = (
                            float(xga_a_val) if xga_a_val and xga_a_val != "" else None
                        )
                elif line.startswith("🥅 *Halves Over 0.5:"):
                    parts = line.split(": ", 1).split(" ║ ")
                    match["halves_o05_h"] = parts.strip()
                    match["halves_o05_a"] = parts.strip()
                elif line.startswith("⚽ *Team Goals:"):
                    parts = line.split(": ", 1).split(" ║ ")
                    match["team_goals_h"] = parts.strip()
                    match["team_goals_a"] = parts.strip()
                elif line.startswith("🥅 *Match Goals:"):
                    parts = line.split(": ", 1).split(" ║ ")
                    match["match_goals_h"] = parts.strip()
                    match["match_goals_a"] = parts.strip()
                elif line.startswith("🧼"):
                    parts = line.split(": ", 1).split(" | ")
                    cs_h = parts.replace("*A*", "").strip()
                    cs_a = parts.replace("*A*", "").strip() if len(parts) > 1 else None
                    match["clean_sheet_h"] = cs_h if cs_h != "nan" else None
                    match["clean_sheet_a"] = cs_a if cs_a and cs_a != "nan" else None
                elif line.startswith("🏆"):
                    parts = line.split(": ", 1).split(" | *A*: ")
                    match["win_rates_h"] = parts.strip()
                    match["win_rates_a"] = parts.strip() if len(parts) > 1 else None

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
                    match["h2h_hva_ppg_str"] = line.split(": ", 1)
                elif line.startswith("⚽ *H2H Goals Scored:"):
                    match["h2h_hva_goals_str"] = line.split(": ", 1)
                elif line.startswith("🥅 *H2H HvA Over/Under*:"):
                    match["h2h_hva_ou"] = line.split(": ", 1)

                elif line.startswith("✨ *Home Insights*:"):
                    if current_insight_type:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                    current_insight_type = "home"
                    insight_buffer = (
                        line.split(":", 1).strip() + "\n" if ":" in line else "\n"
                    )
                elif line.startswith("✨ *Away Insights*:"):
                    if current_insight_type:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                    current_insight_type = "away"
                    insight_buffer = (
                        line.split(":", 1).strip() + "\n" if ":" in line else "\n"
                    )
                elif line.startswith("✨ *Total Match Insights*:"):
                    if current_insight_type:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                    current_insight_type = None
                    insight_buffer = ""
                elif line.startswith("⚡*"):
                    if insight_buffer and current_insight_type in [
                        "home",
                        "away",
                    ]:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                    insight_buffer = ""
                    team_name_match = re.match(r"⚡\*(.*?)\s*\(.*?\):", line)
                    if team_name_match:
                        team_name_in_line = team_name_match.group(1).strip()
                        if home_team_buffer and team_name_in_line == home_team_buffer:
                            current_insight_type = "total_h"
                        else:
                            current_insight_type = "total_a"
                        insight_buffer = (
                            line.split("):", 1).strip() + "\n" if "):" in line else ""
                        )
                    else:
                        if current_insight_type:
                            insight_buffer += line + "\n"

                elif current_insight_type and line.startswith("   -"):
                    insight_buffer += line.strip() + "\n"
                elif current_insight_type and not re.match(
                    r"^(?:🎲|Match Outcome:|Over/Under Goals:|Over/Under Corners:|Recommended Prediction:)",
                    line,
                ):
                    insight_buffer += line.strip() + "\n"

                elif line.startswith("🎲"):
                    if insight_buffer and current_insight_type:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )
                        insight_buffer = ""
                        current_insight_type = None
                    m_conf = re.search(r"Score:\s*(\d+)", line)
                    if m_conf:
                        try:
                            match["confidence_score"] = int(m_conf.group(1))
                        except:
                            pass
                elif line.startswith("Match Outcome:"):
                    m_pred = re.search(r":\s*(.*?)(?:\s*\((\d+)/10\))?$", line)
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
                    match["rec_prediction"] = line.split(":", 1).strip()

                elif line_num == len(lines) - 1:
                    if insight_buffer and current_insight_type:
                        match[f"insights_{current_insight_type}"] = (
                            insight_buffer.strip()
                        )

            except Exception as e_line:
                st.warning(
                    f"Error parsing line {line_num + 1} in block {i + 1}: '{line}' - {e_line}"
                )
                continue

        if match.get("home_team") and match.get("date"):
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
    add_transient_message("info", f"Loading data from CSV file: {filepath}")

    try:
        df = pd.read_csv(filepath)

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
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for col in int_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

        string_cols = df.select_dtypes(include="object").columns
        df[string_cols] = df[string_cols].fillna("")

        if "match_id" not in df.columns:
            st.error("CSV file is missing the required 'match_id' column.")
            add_transient_message(
                "error", "CSV file is missing the required 'match_id' column."
            )
            return []

        duplicates_count = df.duplicated(subset=["match_id"]).sum()
        if duplicates_count > 0:
            add_transient_message(
                "warning",
                f"Found {duplicates_count} duplicate match_id entries in the CSV. Keeping the first occurrence of each.",
            )

        df_deduplicated = df.drop_duplicates(subset=["match_id"], keep="first")

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
        return []
    except Exception as e:
        add_transient_message("error", f"Error loading data from CSV '{filepath}': {e}")
        return []


@st.cache_data
def load_data_from_postgres(db_params):
    st.info("Simulating data loading from PostgreSQL...")
    st.warning("Returning sample data instead of connecting to DB.")
    # sample_df = create_sample_dataframe() # Assuming this function exists elsewhere
    # return sample_df.to_dict("records")
    return []  # Return empty for now as create_sample_dataframe is not defined
