import re
import time
import math
import pandas as pd
import streamlit as st
import emoji
import numpy as np
from datetime import datetime

from config import MESSAGE_TIMEOUT_SECONDS, GREEN, COUNTRY_CODE_MAP, LEAGUE_CODE_MAP

# --- Helper Functions ---
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
        pattern_exact = rf"^{re.escape(label_prefix)}\s*[:\-]?\s*(\d+(\.\d+)?)\s*%"
        match = re.search(pattern_exact, text_value.strip(), re.IGNORECASE)
        if match:
            return int(float(match.group(1)))

        parts = text_value.split("|")
        if len(parts) > 1:
            for part in parts:
                cleaned_part = part.strip().lower()
                cleaned_label = label_prefix.strip().lower()
                pattern_part = rf"^{re.escape(cleaned_label)}\s*[:\-]?\s*(\d+(\.\d+)?)\s*%"
                match = re.search(pattern_part, cleaned_part, re.IGNORECASE)
                if match:
                    return int(float(match.group(1)))
        pattern_simple = rf"{re.escape(label_prefix)}\s*[:\-]?\s*(\d+(\.\d+)?)\s*%"
        match = re.search(pattern_simple, text_value, re.IGNORECASE)
        if match:
            return int(float(match.group(1)))

        return default
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
            pattern = r"^(.*?):\s*([\d.]+)\%?\s*(?:\(\s*([+\-]?[\d.]+)\s*%?\s*([🔼🔻])\s*avg\s*\))?"
            match = re.match(pattern, line, re.IGNORECASE)

            if match:
                insight["label"] = match.group(1).strip()
                insight["value"] = match.group(2).strip()
                if match.group(3):
                    insight["delta_str"] = (
                        f"{match.group(3).strip()}% {match.group(4)} league average"
                    )
                    try:
                        insight["delta_val"] = float(match.group(3).strip())
                    except ValueError:
                        pass
                    insight["direction"] = match.group(4)
            elif ":" in line:
                parts = line.split(":", 1)
                insight["label"] = parts.strip()
                insight["value"] = parts.strip()

            if insight["label"]:
                parsed_insights.append(insight)
        except Exception as e:
            if insight["label"]:
                parsed_insights.append(insight)
    return parsed_insights

def parse_h2h_value(text_value, key_label, is_numeric=True, default=None):
    if not isinstance(text_value, str):
        return default
    try:
        pattern = rf"{key_label}\s*:\s*([\d.]+)"
        match = re.search(pattern, text_value, re.IGNORECASE)
        if match:
            val_str = match.group(1)
            if is_numeric:
                try:
                    return float(val_str)
                except ValueError:
                    return default
            else:
                return val_str
        return default
    except Exception:
        return default

def get_progress_color(value):
    if value < 33:
        return "#f44336"
    elif value < 66:
        return "#ff9800"
    else:
        return "#8bc34a"

def create_colored_progress_bar(value, text_label=None):
    if value is None or not isinstance(value, (int, float)):
        value = 0
    value = max(0, min(100, value))

    color = get_progress_color(value)
    text_color = "#ffffff" if value >= 33 else "#000000"

    display_text = f"{int(value)}%"

    bar_html = f"""
    <div style="background-color: #e0e0e0; border-radius: 5px; height: 20px; width: 100%; overflow: hidden; position: relative;">
        <div style="width: {value}%; background-color: {color}; height: 100%; border-radius: 5px 0 0 5px; text-align: center; color: {text_color}; font-weight: bold; line-height: 20px; font-size: 12px; position: absolute; left: 0; top: 0;">
        </div>
        <div style="width: 100%; text-align: center; color: #424242; font-weight: bold; line-height: 20px; font-size: 12px; position: absolute; left: 0; top: 0; z-index: 0;">
            {display_text}
        </div>
    </div>
    """
    return bar_html

def add_transient_message(msg_type, text):
    if "transient_messages" not in st.session_state:
        st.session_state.transient_messages = []
    msg_id = f"{msg_type}_{time.time()}_{len(st.session_state.transient_messages)}"
    st.session_state.transient_messages.append(
        {
            "id": msg_id,
            "type": msg_type,
            "text": text,
            "timestamp": time.time(),
        }
    )

def display_transient_messages():
    message_placeholder = st.empty()
    current_time = time.time()
    st.session_state.transient_messages = [
        msg
        for msg in st.session_state.transient_messages
        if (current_time - msg["timestamp"]) < MESSAGE_TIMEOUT_SECONDS
    ]
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

    debug_prediction_check = False
    debug_target_pred_str = "home team over 1.5 goals"
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
    temp_potential_preds = [
        p.strip().lower() for p in prediction_str.split(",")
    ]
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
        return (
            "PENDING" if is_prediction_format_outcome_market else "PENDING"
        )

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
            dc_symbols = "".join(
                sorted(dc_explicit_match.group(1))
            )
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

def colorize_performance(performance):
    colored_performance = ""
    for char in performance:
        if char == "W":
            colored_performance += f"{emoji.emojize('🟩')}"
        elif char == "D":
            colored_performance += f"{emoji.emojize('⬜')}"
        elif char == "L":
            colored_performance += f"{emoji.emojize('🟥')}"
    return colored_performance

def sort_data(df):
    if "date" not in df.columns or "time" not in df.columns:
        st.warning("Missing 'date' or 'time' column for sorting.")
        return df

    date_format = "%d/%m/%Y"
    time_format = "%H:%M"
    datetime_format = f"{date_format} {time_format}"

    df["datetime_obj"] = pd.to_datetime(
        df["date"].astype(str) + " " + df["time"].astype(str),
        format=datetime_format,
        errors="coerce",
    )

    original_rows = len(df)
    df = df.dropna(subset=["datetime_obj"])
    if len(df) < original_rows:
        st.caption(
            f"Dropped {original_rows - len(df)} rows with invalid date/time format."
        )

    df = df.sort_values(by="datetime_obj", ascending=True)

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
    col1, col2, col3 = st.columns() # Adjusted columns for display_stat_row

    if label in ["Expected Goals (xG)", "Possession (%)"]:
        home_display = str(home_value) if home_value is not None else "--"
        away_display = str(away_value) if away_value is not None else "--"
    else:
        home_display = int(home_value) if home_value is not None else "--"
        away_display = int(away_value) if away_value is not None else "--"

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

def get_country_emoji(country_name):
    country_code_mapping = {
        "Europe": "🇪🇺",
    }
    country_code = country_name.title()
    return country_code_mapping.get(country_code, emoji.emojize(f":{country_code}:"))

def get_flag_url(country_name, league_name):
    if not isinstance(country_name, str):
        return None

    league_string = f"{country_name}, {league_name}"
    url = LEAGUE_CODE_MAP.get(league_string)

    if url:
        return url
    else:
        url = COUNTRY_CODE_MAP.get(country_name.title())
        if url:
            return url
        return None

def parse_rank_to_int(rank_str):
    if pd.isna(rank_str) or not isinstance(rank_str, str):
        return None

    match = re.match(r"(\d+)(?:st|nd|rd|th)?", rank_str.lower())
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None

def display_h2h_stats(
    metric_label, h2h_val, team_overall_avg, league_avg_context, team, inverse_flag
):
    delta_vs_team = h2h_val - team_overall_avg
    if inverse_flag == 1:
        inverse_value = "inverse"
    else:
        inverse_value = "normal"
    st.metric(
        label=metric_label,
        value=f"{h2h_val:.2f}",
        delta=f"{delta_vs_team:+.2f} vs Team Avg ({team_overall_avg})",
        delta_color=inverse_value,
    )
    st.caption(f"League Avg FOR @ {team}: {league_avg_context:.2f}")

def prepare_discipline_data(
    card_spread_str, foul_spread_str, num_recent_games=5
):
    if not card_spread_str or not foul_spread_str:
        return pd.DataFrame()

    default_spread = "0,0,0,0,0"

    if str(foul_spread_str).strip() == "0" or str(foul_spread_str).strip() == "0.0":
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
    referee_avg_total_cards_game: float,
    chart_title: str,
    card_color: str = "darkorange",
    foul_color: str = "steelblue",
    ref_line_color: str = "firebrick",
):
    import altair as alt
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
        ),
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
        ),
        tooltip=[
            alt.Tooltip("Game:N"),
            alt.Tooltip("Cards Given by Referee:Q", title="Referee Cards"),
        ],
    )

    layers = [bar_cards, line_fouls]
    if (
        pd.notna(referee_avg_total_cards_game)
        and referee_avg_total_cards_game >= 0
    ):
        ref_avg_rule = (
            alt.Chart(
                pd.DataFrame({"ref_avg_total": [referee_avg_total_cards_game]})
            )
            .mark_rule(
                strokeDash=, # Fixed: Added value for strokeDash
                strokeWidth=2,
                color=ref_line_color,
                opacity=0.9,
            )
            .encode(
                y="ref_avg_total:Q"
            )
        )
        layers.append(ref_avg_rule)

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
        y_max = max(y_max, referee_avg_total_cards_game)

    y_domain = [0, y_max + 2]

    layered_chart = (
        alt.layer(*layers)
        .resolve_scale(y="shared")
        .encode(
            alt.Y(scale=alt.Scale(domain=y_domain))
        )
        .properties(
            title=alt.TitleParams(
                text=chart_title, anchor="middle", fontSize=13
            ),
            height=275,
        )
        .configure_axis(labelFontSize=10, titleFontSize=11)
        .configure_legend(
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

def parse_odds_field_name(field_name):
    if not field_name.endswith("Odds"):
        return None
    parts = field_name[:-4].split("_")
    if not parts:
        return None
    market = parts # Fixed: Changed to parts
    bet_specific_parts = parts[1:]
    bet_specific = " ".join(bet_specific_parts)
    return {
        "market": market,
        "bet_specific": bet_specific,
        "raw_bet_type": "_".join(bet_specific_parts) + "Odds",
    }

def group_odds_by_market(match_data):
    from collections import defaultdict
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
        "Both Teams Score - First Half": ["Yes", "No"],
        "Draw No Bet (1st Half)": ["Home", "Away"],
        "Draw No Bet (2nd Half)": ["Home", "Away"],
    }
    display_label_map = {
        "Match Winner": {"Home": "1", "Draw": "X", "Away": "2"},
        "Double Chance": {"Home/Draw": "1X", "Home/Away": "12", "Draw/Away": "X2"},
        "First Half Winner": {"Home": "1", "Draw": "X", "Away": "2"},
        "Second Half Winner": {"Home": "1", "Draw": "X", "Away": "2"},
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
        sorted(grouped_odds.items(), key=lambda item: market_order.get(item, 999)) # Fixed: Changed to item
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
        ):
            def sort_key_ou(bet_item):
                label = bet_item["bet_label"].lower()
                is_over = "over" in label or label.startswith("o ")
                line_match = re.search(r"(\d+(?:\.\d+)?)", label)
                line_val = float(line_match.group(1)) if line_match else float("inf")
                return (line_val, not is_over)

            bets.sort(key=sort_key_ou)
        else:
            bets.sort(key=lambda x: x["display_label"])
    return sorted_grouped_odds