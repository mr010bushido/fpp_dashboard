import glob  # For finding weekly files
import math  # Added for math.isnan
import os
import re

import pandas as pd
import streamlit as st

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEEKLY_PREDICTIONS_DIR = os.path.join(PROJECT_ROOT, "data", "pre_match")


# --- Helper Functions (Copied from 1_Match_Analysis.py) ---
def clean_prediction_string(prediction_str: str) -> str:
    if not isinstance(prediction_str, str) or not prediction_str.strip():
        return ""
    clean_str = prediction_str.strip()
    prefixes_to_remove = [
        "Match Outcome: ",
    ]
    for prefix in prefixes_to_remove:
        if clean_str.startswith(prefix):
            clean_str = clean_str[len(prefix) :].strip()
            break
    if (
        "OverUnderCards: " in clean_str
        or "OverUnderCorners: " in clean_str
        or "OverUnderGoals: " in clean_str
    ):
        first, second = clean_str.split(": ", 1)
        first_lower = first.lower()
        if "cards" in first_lower:
            clean_str = f"{second} Cards"
        elif "corners" in first_lower:
            clean_str = f"{second} Corners"
        elif "goals" in first_lower:
            clean_str = f"{second} Goals"
        else:
            clean_str = f"{second}"
    if "Home or Draw (1X)" in clean_str:
        clean_str = re.sub(r"^Home or Draw \(1X\)", "Home Win or Draw", clean_str)
    elif "Away or Draw (X2)" in clean_str:
        clean_str = re.sub(r"^Away or Draw \(X2\)", "Away Win or Draw", clean_str)
    clean_str = re.sub(r"\b(\w+)\s+\1\b", r"\1", clean_str)
    clean_str = re.sub(r"\s+", " ", clean_str).strip()
    return clean_str


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

    scores_valid = (
        isinstance(home_goals, (int, float))
        and not math.isnan(home_goals)
        and isinstance(away_goals, (int, float))
        and not math.isnan(away_goals)
    )
    corners_valid = isinstance(total_corners, (int, float)) and not math.isnan(
        total_corners
    )
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

    actual_home_win = False
    actual_away_win = False
    actual_draw = False
    total_actual_goals = 0

    if scores_valid:
        actual_home_win = home_goals > away_goals
        actual_away_win = away_goals > home_goals
        actual_draw = home_goals == away_goals
        total_actual_goals = home_goals + away_goals

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

        predicted_winner = None
        if team_part == "home win" or team_part == home_team_lower:
            predicted_winner = "home"
        elif team_part == "away win" or team_part == away_team_lower:
            predicted_winner = "away"

        win_condition_met = (predicted_winner == "home" and actual_home_win) or (
            predicted_winner == "away" and actual_away_win
        )

        ou_condition_met = (ou_type == "over" and total_actual_goals > line_val) or (
            ou_type == "under" and total_actual_goals < line_val
        )

        if win_condition_met and ou_condition_met:
            return "WIN"
        else:
            return "LOSS"

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

    team_win_match = re.match(
        r"^(.*?)(?:\s+win)(?:\s*\(\d+\/10\))?$", pred_cleaned, re.IGNORECASE
    )
    if team_win_match:
        if not scores_valid:
            return "PENDING"
        team_name_pred = team_win_match.group(1).strip().lower()
        if team_name_pred == home_team_lower or team_name_pred == "home":
            return "WIN" if actual_home_win else "LOSS"
        elif team_name_pred == away_team_lower or team_name_pred == "away":
            return "WIN" if actual_away_win else "LOSS"
        return "PENDING"

    combo_dc_under_match = re.search(
        r"^(.*?)\s*(?:&|and)\s*under\s*(\d+\.\d+)\s*goals?$", pred_lower
    )
    if combo_dc_under_match:
        if not scores_valid:
            return "PENDING"
        dc_part, line_val_str = combo_dc_under_match.groups()
        line_val = float(line_val_str)
        dc_part = dc_part.strip()

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

        under_condition_met = total_actual_goals < line_val

        if dc_condition_met and under_condition_met:
            return "WIN"
        else:
            return "LOSS"

    ah_match = re.search(
        r"^(.*?)\s*([+-]\d+\.\d+)\s*(?:asian\s*)?handicap$", pred_lower
    )
    if ah_match:
        if not scores_valid:
            return "PENDING"
        team_part, handicap_str = ah_match.groups()
        handicap = float(handicap_str)
        team_part = team_part.strip()

        if team_part == "home" or team_part == home_team_lower:
            return "WIN" if (home_goals + handicap) > away_goals else "LOSS"
        elif team_part == "away" or team_part == away_team_lower:
            return "WIN" if (away_goals + handicap) > home_goals else "LOSS"

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
        return "PENDING"

    total_card_ou_match = re.search(
        r"\b(o|u|over|under)\s*(\d+(?:\.\d+)?)\s*(?:yellow\s*)?cards?\b",
        pred_lower,
    )
    if total_card_ou_match:
        if not all_cards_valid:
            return "PENDING"
        ou_type, line_val_str = (
            total_card_ou_match.group(1).lower(),
            total_card_ou_match.group(2),
        )
        line_val = float(line_val_str)

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
        return "PENDING"

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

    ht_keyword_ou_match = re.search(
        r"\b(home\s*team)\s+(o|u|over|under)\s*(\d+(?:\.\d+)?)(?:\s*goals?)?",
        pred_lower,
    )
    if ht_keyword_ou_match:
        if not scores_valid:
            return "PENDING"
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
        return "PENDING"

    at_keyword_ou_match = re.search(
        r"\b(away\s*team)\s+(o|u|over|under)\s*(\d+(?:\.\d+)?)(?:\s*goals?)?",
        pred_lower,
    )
    if at_keyword_ou_match:
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

    if home_team_lower:
        actual_ht_ou_match = re.search(
            rf"(?:^|\s)({re.escape(home_team_lower)})\s+(o|u|over|under)\s*(\d+(?:\.\d+)?)(?:\s*goals?)?",
            pred_lower,
        )
        if actual_ht_ou_match:
            if not scores_valid:
                return "PENDING"
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

    if away_team_lower:
        actual_at_ou_match = re.search(
            rf"(?:^|\s)({re.escape(away_team_lower)})\s+(o|u|over|under)\s*(\d+(?:\.\d+)?)(?:\s*goals?)?",
            pred_lower,
        )
        if actual_at_ou_match:
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

    is_prediction_format_outcome_market = False
    temp_potential_preds = [p.strip().lower() for p in prediction_str.split(",")]
    for temp_part_pred in temp_potential_preds:
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
        return "PENDING" if is_prediction_format_outcome_market else "PENDING"

    actual_home_win = home_goals > away_goals
    actual_away_win = away_goals > home_goals
    actual_draw = home_goals == away_goals

    for part_pred_dc in temp_potential_preds:
        hax_match = re.fullmatch(r"([hax])(?:\s*\(.+\))?", part_pred_dc)
        if hax_match:
            bet_char = hax_match.group(1)
            if (
                (bet_char == "h" and actual_home_win)
                or (bet_char == "x" and actual_draw)
                or (bet_char == "a" and actual_away_win)
            ):
                return "WIN"
            if len(temp_potential_preds) == 1:
                return "LOSS"
            continue

        dc_explicit_match = re.search(
            r"\b(?:double\s*chance|dc)\s*([1x2]{2})\b", part_pred_dc
        )
        if dc_explicit_match:
            dc_symbols = "".join(sorted(dc_explicit_match.group(1)))
            if (
                (dc_symbols == "1x" and (actual_home_win or actual_draw))
                or (dc_symbols == "2x" and (actual_away_win or actual_draw))
                or (dc_symbols == "12" and (actual_home_win or actual_away_win))
            ):
                return "WIN"
            return "LOSS"

        if (
            len(part_pred_dc) == 2
            and all(c in "12x" for c in part_pred_dc)
            and (
                "x" in part_pred_dc
                or (part_pred_dc.isdigit() and part_pred_dc.isdigit())
            )
        ):
            dc_symbols = "".join(sorted(part_pred_dc))
            if (
                (dc_symbols == "1x" and (actual_home_win or actual_draw))
                or (dc_symbols == "2x" and (actual_away_win or actual_draw))
                or (dc_symbols == "12" and (actual_home_win or actual_away_win))
            ):
                return "WIN"
            if len(temp_potential_preds) == 1:
                return "LOSS"
            continue

        if (
            re.search(r"\bhome\b", part_pred_dc)
            and re.search(r"\bor\s+draw\b", part_pred_dc)
        ) or (
            home_team_lower
            and re.search(re.escape(home_team_lower), part_pred_dc)
            and re.search(r"\bor\s+draw\b", part_pred_dc)
        ):
            return "WIN" if actual_home_win or actual_draw else "LOSS"
        if (
            re.search(r"\baway\b", part_pred_dc)
            and re.search(r"\bor\s+draw\b", part_pred_dc)
        ) or (
            away_team_lower
            and re.search(re.escape(away_team_lower), part_pred_dc)
            and re.search(r"\bor\s+draw\b", part_pred_dc)
        ):
            return "WIN" if actual_away_win or actual_draw else "LOSS"
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

    if is_prediction_format_outcome_market:
        return "LOSS"

    return "PENDING"


@st.cache_data
def load_data_from_csv(filepath) -> pd.DataFrame:
    """Loads match data from a CSV file."""
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
            "HomeGoals",
            "AwayGoals",
            "Corners",
            "YellowCards",
            "RedCards",
            "HomeYellowsResults",
            "AwayYellowsResults",
            "HomeRedResults",
            "AwayRedResults",
        ]
        for col in float_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        string_cols = df.select_dtypes(include="object").columns
        df[string_cols] = df[string_cols].fillna("")
        return df
    except FileNotFoundError:
        st.error(f"Error: CSV file '{filepath}' not found.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data from CSV '{filepath}': {e}")
        return pd.DataFrame()


@st.cache_data  # CRITICAL: Cache the loading of the combined results file
def load_combined_results():  # Removed file_path parameter
    all_files = glob.glob(os.path.join(WEEKLY_PREDICTIONS_DIR, "[0-9]*.csv"))
    if not all_files:
        st.error("No weekly prediction files found to combine.")
        return pd.DataFrame()

    df_list = []
    for f_path in all_files:
        df = load_data_from_csv(f_path)
        if not df.empty:
            df_list.append(df)

    if not df_list:
        st.error("No data loaded from weekly prediction files.")
        return pd.DataFrame()

    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df


def display_success_rate_for_selected_gameweek():
    st.subheader("Gameweek Success Rate Analysis")

    # 1. Find all available gameweek files
    raw_files = glob.glob(os.path.join(WEEKLY_PREDICTIONS_DIR, "[0-9]*.csv"))
    if not raw_files:
        st.info("No weekly match files found in 'data/pre_match/'.")
        return

    week_path_pairs = []
    for f_path in raw_files:
        basename = os.path.basename(f_path)
        match = re.match(r"(\d+)\.csv$", basename)
        if match:
            try:
                week_num = int(match.group(1))
                week_path_pairs.append((week_num, f_path))
            except ValueError:
                continue

    if not week_path_pairs:
        st.info("No valid weekly match files found for success rate calculation.")
        return

    # Sort gameweeks in descending order (latest first)
    week_path_pairs.sort(key=lambda item: item, reverse=True)

    gameweek_options = {
        f"Gameweek {week_num}": path for week_num, path in week_path_pairs
    }
    
    # Add "All Gameweeks" option for combined analysis
    gameweek_options["All Gameweeks"] = "combined"

    selected_gameweek_display_name = st.selectbox(
        "Select Gameweek for Analysis:",
        options=list(gameweek_options.keys()),
        key="selected_gameweek_for_analysis",
    )

    if not selected_gameweek_display_name:
        st.info("Please select a gameweek.")
        return

    selected_file_path = gameweek_options[selected_gameweek_display_name]
    
    if selected_gameweek_display_name == "All Gameweeks":
        st.write("Analyzing: All Gameweeks (Combined Data)")
        # 2. Load combined data for all gameweeks
        selected_df = load_combined_results()
    else:
        st.write(f"Analyzing: {os.path.basename(selected_file_path)}")
        # 2. Load the data for the selected gameweek
        selected_df = load_data_from_csv(selected_file_path)

    if selected_df.empty:
        st.warning("Could not load data for the selected gameweek.")
        return

    # 3. Calculate success rate by league
    league_stats = {}
    overall_total = 0
    overall_successful = 0

    for index, match in selected_df.iterrows():
        if (
            pd.notna(match.get("rec_prediction"))
            and match.get("rec_prediction").strip() != "--"
        ):
            league_name = match.get("league_name", "Unknown League")
            country = match.get("country", "Unknown Country")
            league_key = f"{country} - {league_name}"
            
            if league_key not in league_stats:
                league_stats[league_key] = {
                    "total": 0,
                    "successful": 0,
                    "country": country,
                    "league": league_name
                }
            
            league_stats[league_key]["total"] += 1
            overall_total += 1
            
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
            if result == "WIN":
                league_stats[league_key]["successful"] += 1
                overall_successful += 1

    if overall_total > 0:
        # Display overall success rate
        overall_success_rate = (overall_successful / overall_total) * 100
        st.metric(
            label=f"Overall Success Rate ({selected_gameweek_display_name})",
            value=f"{overall_success_rate:.2f}%",
            delta=f"{overall_successful}/{overall_total} WINs",
        )
        
        st.markdown("---")
        st.subheader("Success Rate by League")
        
        # Sort leagues by success rate (descending)
        sorted_leagues = sorted(
            league_stats.items(),
            key=lambda x: (x[1]["successful"] / x[1]["total"]) if x[1]["total"] > 0 else 0,
            reverse=True
        )
        
        # Display league statistics in columns
        cols = st.columns(3)
        for idx, (league_key, stats) in enumerate(sorted_leagues):
            with cols[idx % 3]:
                if stats["total"] > 0:
                    league_success_rate = (stats["successful"] / stats["total"]) * 100
                    st.metric(
                        label=league_key,
                        value=f"{league_success_rate:.1f}%",
                        delta=f"{stats['successful']}/{stats['total']}",
                    )
                    
        # Create a summary table
        st.markdown("---")
        st.subheader("League Summary Table")
        
        league_summary = []
        for league_key, stats in sorted_leagues:
            if stats["total"] > 0:
                success_rate = (stats["successful"] / stats["total"]) * 100
                league_summary.append({
                    "Country": stats["country"],
                    "League": stats["league"],
                    "Success Rate": f"{success_rate:.1f}%",
                    "Wins": stats["successful"],
                    "Total": stats["total"],
                    "Win Rate": success_rate
                })
        
        if league_summary:
            summary_df = pd.DataFrame(league_summary)
            summary_df = summary_df.sort_values("Win Rate", ascending=False)
            summary_df = summary_df.drop("Win Rate", axis=1)  # Remove helper column
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
    else:
        st.info(
            f"No valid recommended predictions found for {selected_gameweek_display_name} to calculate success rate."
        )


# --- Streamlit App Layout (using tabs example) ---

st.set_page_config(
    page_title="Results Analysis",  # You can have a page-specific title
    page_icon="⚽",  # <<< USE THE SAME ICON HERE
    layout="wide",  # Or whatever layout you prefer for this page
)

st.title("Results Analysis")

# tab1, tab2 = st.tabs(["📅 Pre-Match Analysis", "📊 Results Analysis"])
st.header("Historical Results Analysis")

# Load the combined data (will be cached after first load)
combined_df = load_combined_results()

if not combined_df.empty:
    # Display key statistics about the combined data
    st.subheader("Dataset Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_matches = len(combined_df)
        st.metric("Total Matches", total_matches)
    
    with col2:
        valid_predictions = len(combined_df[combined_df['rec_prediction'].notna() & (combined_df['rec_prediction'].str.strip() != "--")])
        st.metric("Valid Predictions", valid_predictions)
    
    with col3:
        unique_leagues = combined_df['league_name'].nunique()
        st.metric("Unique Leagues", unique_leagues)
    
    with col4:
        unique_countries = combined_df['country'].nunique()
        st.metric("Unique Countries", unique_countries)
    
    st.markdown("---")
    st.subheader("Sample Data")
    
    # Show a more meaningful sample with key columns
    sample_columns = ['date', 'country', 'league_name', 'home_team', 'away_team', 
                     'HomeGoals', 'AwayGoals', 'rec_prediction', 'confidence_score']
    available_columns = [col for col in sample_columns if col in combined_df.columns]
    
    if available_columns:
        st.dataframe(combined_df[available_columns].head(10), use_container_width=True)
    else:
        st.dataframe(combined_df.head())
    
    # Add basic analysis options for future enhancement
    st.markdown("---")
    st.subheader("Analysis Options")
    st.info("""
    **Future Analysis Features**:
    - Overall accuracy trends over time
    - Profit/loss calculations with odds data
    - League performance comparison charts
    - Team-specific performance analysis
    - Confidence score vs. actual success correlation
    """)
else:
    st.info("Combined results data not available or failed to load.")

st.markdown("---")
display_success_rate_for_selected_gameweek()
