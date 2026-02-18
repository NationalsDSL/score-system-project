import base64
import html
import io
import math
import os
import time

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dynamic Scoreboard", layout="wide")

# -----------------------------
# FILES
# -----------------------------
SCORES_FILE = "scores.csv"
USERS_FILE = "users.csv"
SCOREBOARD_BG_FILE = "scoreboard_bg.png"
HISTORY_FILE = "score_history.csv"
HISTORY_COLUMNS = ["timestamp", "player", "points_added", "total_after", "trend_note"]

TRANSLATIONS = {
    "es": {
        "language": "Idioma",
        "language_es": "Espanol",
        "language_en": "English",
        "dynamic_scoreboard": "Dynamic Scoreboard",
        "login_title": "Iniciar sesion",
        "username": "Username",
        "password": "Password",
        "login_button": "Login",
        "login_success": "Login successful!",
        "invalid_credentials": "Credenciales invalidas",
        "sidebar_user": "Usuario",
        "sidebar_role": "Rol",
        "logout": "Logout",
        "navigation": "Navegacion",
        "menu_admin_panel": "Admin Panel",
        "menu_scoreboard_general": "Scoreboard General",
        "menu_winners": "Winners",
        "menu_period_winners": "Period Winners",
        "menu_my_score": "My Score",
        "hero_dynamic_title": "Dynamic Scoreboard",
        "hero_dynamic_subtitle": "Accede para ver el ranking y el rendimiento del torneo.",
        "hero_admin_title": "Admin Control Center",
        "hero_admin_subtitle": "Gestiona jugadores, puntajes y cuentas en un solo lugar.",
        "hero_scoreboard_general_title": "Scoreboard General",
        "hero_scoreboard_general_subtitle": "Visualiza posiciones, tendencia y zonas calientes/frias.",
        "hero_winners_title": "Winners",
        "hero_winners_subtitle": "Los tres primeros del torneo.",
        "hero_period_winners_title": "Weekly and Monthly Winners",
        "hero_period_winners_subtitle": "Ganadores automaticos por semana y por mes basados en el historial de puntos.",
        "hero_my_score_title": "My Score",
        "hero_my_score_subtitle": "Revisa tus puntos y tu posicion actual en el torneo.",
        "hero_scoreboard_title": "Scoreboard",
        "hero_scoreboard_subtitle": "Compite, sube posiciones y mantente en la zona caliente.",
        "players_registered": "Players registrados",
        "total_points": "Puntos totales",
        "average_per_player": "Promedio por player",
        "current_leader": "Lider actual",
        "save_failed_title": "No se pudo guardar `{file_path}` porque esta en uso o bloqueado.",
        "save_failed_hint": "Cierra el archivo si esta abierto (por ejemplo, en Excel) e intenta de nuevo.",
        "technical_detail": "Detalle tecnico: {error}",
        "bg_expander": "Imagen de fondo para Scoreboard General",
        "bg_upload": "Sube una imagen PNG",
        "bg_saved": "Imagen de fondo guardada.",
        "bg_current_file": "Archivo actual: {file}",
        "no_players_scoreboard": "No hay players en el scoreboard todavia.",
        "leaderboard_tab": "Leaderboard",
        "last_7_days_tab": "Last 7 Days",
        "last_15_days_tab": "Last 15 Days",
        "last_30_days_tab": "Last 30 Days",
        "caption_total_tournament": "Total acumulado del torneo.",
        "caption_last_days": "Puntos ganados en los ultimos {days} dias.",
        "pdf_no_data": "No hay datos para exportar.",
        "pdf_missing_matplotlib": "No se pudo generar el PDF porque matplotlib no esta disponible.",
        "pdf_table_title": "Scoreboard Ranking Table",
        "pdf_generated_footer": "Generado: {datetime} | Players: {players} | Pagina {page}/{pages}",
        "download_pdf_table": "Download PDF table",
        "no_winners_yet": "Aun no hay ganadores porque no hay puntajes cargados.",
        "place_label": "Puesto {position}",
        "no_player": "Sin player",
        "points_short": "pts",
        "no_points_history": "Aun no hay historial de puntos. Agrega puntos para generar ganadores semanales y mensuales.",
        "select_month": "Select month",
        "week_highlight": "Week Highlight",
        "month_highlight": "Month Highlight",
        "tab_weekly_winners": "Weekly Winners",
        "tab_monthly_winners": "Monthly Winners",
        "weekly_winners_of_month": "Weekly winners of selected month",
        "monthly_winners_history": "Monthly winners history",
        "no_weekly_winner_for_month": "No weekly winner yet for this month.",
        "no_monthly_winner_for_month": "No monthly winner yet for this month.",
        "no_weekly_winners_month": "No weekly winners for this month.",
        "no_monthly_winners_history": "No monthly winners in history.",
        "weekly_period_label": "{week} Week {month} Winner",
        "monthly_period_label": "{month} Winner",
        "default_player_password": "Password por defecto para nuevas cuentas player",
        "tab_points_trends": "Points & Trends",
        "tab_reset_table": "Reset Table",
        "section_fast_points_update": "Fast Points Update",
        "target": "Target",
        "existing_player": "Existing player",
        "new_player": "New player",
        "select_player": "Select player",
        "no_existing_players": "No hay players existentes. Crea uno nuevo.",
        "new_player_name": "New player name",
        "quick_points": "Quick points",
        "custom_points_optional": "Custom points (optional)",
        "apply_points_button": "Apply +{points} points",
        "enter_player_name": "Enter a player name.",
        "section_automation": "Automatizaciones",
        "automation_caption": "Only creates accounts for players without an existing account.",
        "assign_accounts_new_only": "Assign Accounts to New Players Only",
        "new_accounts_created": "New player accounts created: {accounts}",
        "no_new_players_accounts": "No new players found. All current players already have an account.",
        "section_trend_updates": "Trend Updates",
        "tab_latest_by_player": "Latest by player",
        "tab_recent_updates": "Recent updates",
        "no_trends_by_player": "Aun no hay tendencias por jugador.",
        "no_recent_updates": "Aun no hay actualizaciones recientes.",
        "no_trend_note": "Sin nota de tendencia.",
        "section_ranking_preview": "Vista previa del ranking",
        "section_reset_points_table": "Reset Points Table",
        "reset_warning": "Esta accion reinicia todos los puntos a 0. Los players se mantienen en la tabla.",
        "reset_button": "Reset table points",
        "reset_confirm_required": "Confirmacion requerida: Quieres resetear la tabla de puntos?",
        "reset_confirm_button": "Yes, reset now",
        "cancel": "Cancel",
        "reset_cancelled": "Reset cancelado.",
        "reset_success": "Scoreboard reset: todos los puntos en 0.",
        "your_points": "Your Points",
        "average_points_week": "Average Points / Week",
        "weekly_target_position": "Weekly Target Position",
        "weekly_forecast_points": "Weekly Forecast (pts)",
        "zone": "Zone",
        "sessions_week_est": "Sessions / Week (est.)",
        "goal_per_session_points": "Goal per Session (pts)",
        "points_to_next_position": "Points to Next Position",
        "zone_hot": "HOT 🔥",
        "zone_cold": "COLD ❄️",
        "zone_run": "RUN 🏃",
        "weekly_goal_move_up": "Objetivo semanal: subir de #{current} a #{target}. {summary}",
        "weekly_goal_hold": "Objetivo semanal: consolidar la posicion #{current} y presionar el siguiente lugar. {summary}",
        "no_score_assigned": "No score assigned yet.",
        "summary_no_history": "Sin historial de sesiones. Necesitas registrar puntos para generar pronostico.",
        "summary_forecast": "Pronostico semanal: {forecast} pts. Objetivo por sesion: {session_goal} pts.",
        "trend_stable": "estable",
        "trend_up": "al alza",
        "trend_down": "a la baja",
        "trend_note_text": "{gain} pts. Total: {total}. Semana: {week} pts. Mes: {month} pts. Tendencia: {trend}.",
    },
    "en": {
        "language": "Language",
        "language_es": "Spanish",
        "language_en": "English",
        "dynamic_scoreboard": "Dynamic Scoreboard",
        "login_title": "Sign in",
        "username": "Username",
        "password": "Password",
        "login_button": "Login",
        "login_success": "Login successful!",
        "invalid_credentials": "Invalid credentials",
        "sidebar_user": "User",
        "sidebar_role": "Role",
        "logout": "Logout",
        "navigation": "Navigation",
        "menu_admin_panel": "Admin Panel",
        "menu_scoreboard_general": "Scoreboard General",
        "menu_winners": "Winners",
        "menu_period_winners": "Period Winners",
        "menu_my_score": "My Score",
        "hero_dynamic_title": "Dynamic Scoreboard",
        "hero_dynamic_subtitle": "Sign in to track ranking and tournament performance.",
        "hero_admin_title": "Admin Control Center",
        "hero_admin_subtitle": "Manage players, points, and accounts in one place.",
        "hero_scoreboard_general_title": "Scoreboard General",
        "hero_scoreboard_general_subtitle": "View standings, trends, and hot/cold zones.",
        "hero_winners_title": "Winners",
        "hero_winners_subtitle": "Top three players in the tournament.",
        "hero_period_winners_title": "Weekly and Monthly Winners",
        "hero_period_winners_subtitle": "Automatic weekly and monthly winners based on points history.",
        "hero_my_score_title": "My Score",
        "hero_my_score_subtitle": "Check your points and your current tournament position.",
        "hero_scoreboard_title": "Scoreboard",
        "hero_scoreboard_subtitle": "Compete, climb positions, and stay in the hot zone.",
        "players_registered": "Registered players",
        "total_points": "Total points",
        "average_per_player": "Average per player",
        "current_leader": "Current leader",
        "save_failed_title": "Could not save `{file_path}` because it is in use or locked.",
        "save_failed_hint": "Close the file if it is open (for example, in Excel) and try again.",
        "technical_detail": "Technical detail: {error}",
        "bg_expander": "Background image for Scoreboard General",
        "bg_upload": "Upload a PNG image",
        "bg_saved": "Background image saved.",
        "bg_current_file": "Current file: {file}",
        "no_players_scoreboard": "No players in the scoreboard yet.",
        "leaderboard_tab": "Leaderboard",
        "last_7_days_tab": "Last 7 Days",
        "last_15_days_tab": "Last 15 Days",
        "last_30_days_tab": "Last 30 Days",
        "caption_total_tournament": "Total accumulated tournament points.",
        "caption_last_days": "Points earned in the last {days} days.",
        "pdf_no_data": "No data available to export.",
        "pdf_missing_matplotlib": "Could not generate PDF because matplotlib is not available.",
        "pdf_table_title": "Scoreboard Ranking Table",
        "pdf_generated_footer": "Generated: {datetime} | Players: {players} | Page {page}/{pages}",
        "download_pdf_table": "Download PDF table",
        "no_winners_yet": "There are no winners yet because no scores were recorded.",
        "place_label": "Place {position}",
        "no_player": "No player",
        "points_short": "pts",
        "no_points_history": "No points history yet. Add points to generate weekly and monthly winners.",
        "select_month": "Select month",
        "week_highlight": "Week Highlight",
        "month_highlight": "Month Highlight",
        "tab_weekly_winners": "Weekly Winners",
        "tab_monthly_winners": "Monthly Winners",
        "weekly_winners_of_month": "Weekly winners of selected month",
        "monthly_winners_history": "Monthly winners history",
        "no_weekly_winner_for_month": "No weekly winner yet for this month.",
        "no_monthly_winner_for_month": "No monthly winner yet for this month.",
        "no_weekly_winners_month": "No weekly winners for this month.",
        "no_monthly_winners_history": "No monthly winners in history.",
        "weekly_period_label": "Week {week} {month} Winner",
        "monthly_period_label": "{month} Winner",
        "default_player_password": "Default password for new player accounts",
        "tab_points_trends": "Points & Trends",
        "tab_reset_table": "Reset Table",
        "section_fast_points_update": "Fast Points Update",
        "target": "Target",
        "existing_player": "Existing player",
        "new_player": "New player",
        "select_player": "Select player",
        "no_existing_players": "No existing players found. Create a new one.",
        "new_player_name": "New player name",
        "quick_points": "Quick points",
        "custom_points_optional": "Custom points (optional)",
        "apply_points_button": "Apply +{points} points",
        "enter_player_name": "Enter a player name.",
        "section_automation": "Automation",
        "automation_caption": "Only creates accounts for players without an existing account.",
        "assign_accounts_new_only": "Assign Accounts to New Players Only",
        "new_accounts_created": "New player accounts created: {accounts}",
        "no_new_players_accounts": "No new players found. All current players already have an account.",
        "section_trend_updates": "Trend Updates",
        "tab_latest_by_player": "Latest by player",
        "tab_recent_updates": "Recent updates",
        "no_trends_by_player": "No trends by player yet.",
        "no_recent_updates": "No recent updates yet.",
        "no_trend_note": "No trend note.",
        "section_ranking_preview": "Ranking preview",
        "section_reset_points_table": "Reset Points Table",
        "reset_warning": "This action resets all points to 0. Players remain in the table.",
        "reset_button": "Reset table points",
        "reset_confirm_required": "Confirmation required: do you really want to reset the points table?",
        "reset_confirm_button": "Yes, reset now",
        "cancel": "Cancel",
        "reset_cancelled": "Reset canceled.",
        "reset_success": "Scoreboard reset: all points set to 0.",
        "your_points": "Your Points",
        "average_points_week": "Average Points / Week",
        "weekly_target_position": "Weekly Target Position",
        "weekly_forecast_points": "Weekly Forecast (pts)",
        "zone": "Zone",
        "sessions_week_est": "Sessions / Week (est.)",
        "goal_per_session_points": "Goal per Session (pts)",
        "points_to_next_position": "Points to Next Position",
        "zone_hot": "HOT 🔥",
        "zone_cold": "COLD ❄️",
        "zone_run": "RUN 🏃",
        "weekly_goal_move_up": "Weekly target: move up from #{current} to #{target}. {summary}",
        "weekly_goal_hold": "Weekly target: hold position #{current} and push for the next place. {summary}",
        "no_score_assigned": "No score assigned yet.",
        "summary_no_history": "No session history yet. You need points updates to generate a forecast.",
        "summary_forecast": "Weekly forecast: {forecast} pts. Session goal: {session_goal} pts.",
        "trend_stable": "stable",
        "trend_up": "upward",
        "trend_down": "downward",
        "trend_note_text": "{gain} pts. Total: {total}. Week: {week} pts. Month: {month} pts. Trend: {trend}.",
    },
}


def tr(key, **kwargs):
    lang = st.session_state.get("lang", "es")
    data = TRANSLATIONS.get(lang, TRANSLATIONS["es"])
    template = data.get(key, TRANSLATIONS["es"].get(key, key))
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def render_language_selector(use_sidebar=False):
    options = ["es", "en"]
    labels = {
        "es": tr("language_es"),
        "en": tr("language_en"),
    }
    current = st.session_state.get("lang", "es")
    if current not in options:
        current = "es"

    index = options.index(current)
    if use_sidebar:
        selected = st.sidebar.selectbox(
            tr("language"),
            options,
            index=index,
            format_func=lambda code: labels.get(code, code),
        )
    else:
        selected = st.selectbox(
            tr("language"),
            options,
            index=index,
            format_func=lambda code: labels.get(code, code),
        )

    if selected != st.session_state.get("lang"):
        st.session_state.lang = selected
        st.rerun()

# -----------------------------
# CREATE FILES IF NOT EXIST
# -----------------------------
if not os.path.exists(SCORES_FILE):
    pd.DataFrame(columns=["Player", "Points"]).to_csv(SCORES_FILE, index=False)

if not os.path.exists(USERS_FILE):
    pd.DataFrame(columns=["username", "password", "role"]).to_csv(USERS_FILE, index=False)

if not os.path.exists(HISTORY_FILE):
    pd.DataFrame(columns=HISTORY_COLUMNS).to_csv(HISTORY_FILE, index=False)

# -----------------------------
# LOAD / SAVE DATA
# -----------------------------
def load_scores():
    return pd.read_csv(SCORES_FILE)


def _safe_to_csv(df, file_path, retries=6, base_delay=0.2):
    temp_path = f"{file_path}.tmp"
    last_error = None

    for attempt in range(retries):
        try:
            df.to_csv(temp_path, index=False)
            os.replace(temp_path, file_path)
            return True
        except PermissionError as error:
            last_error = error
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            time.sleep(base_delay * (attempt + 1))
        except Exception as error:
            last_error = error
            break

    st.error(
        f"{tr('save_failed_title', file_path=file_path)} "
        f"{tr('save_failed_hint')}"
    )
    if last_error:
        st.caption(tr("technical_detail", error=last_error))
    return False


def save_scores(df):
    return _safe_to_csv(df, SCORES_FILE)


def load_users():
    return pd.read_csv(USERS_FILE)


def save_users(df):
    return _safe_to_csv(df, USERS_FILE)


def load_history():
    history = pd.read_csv(HISTORY_FILE)
    changed = False

    default_values = {
        "timestamp": "",
        "player": "",
        "points_added": 0,
        "total_after": 0,
        "trend_note": "",
    }

    for col, default_value in default_values.items():
        if col not in history.columns:
            history[col] = default_value
            changed = True

    history = history[HISTORY_COLUMNS]
    if changed:
        _safe_to_csv(history, HISTORY_FILE)
    return history


def build_trend_note_from_history(history, player_name):
    player_history = history[history["player"] == player_name].sort_values("timestamp")
    if player_history.empty:
        return tr("summary_no_history")

    last_row = player_history.iloc[-1]
    last_gain = int(last_row["points_added"])
    total_after = int(last_row["total_after"]) if pd.notna(last_row["total_after"]) else 0
    current_time = last_row["timestamp"]

    week_points = int(player_history[player_history["timestamp"] >= (current_time - pd.Timedelta(days=7))]["points_added"].sum())
    month_points = int(
        player_history[
            (player_history["timestamp"].dt.year == current_time.year) &
            (player_history["timestamp"].dt.month == current_time.month)
        ]["points_added"].sum()
    )

    trend_label = tr("trend_stable")
    if len(player_history) >= 6:
        previous_block = int(player_history.iloc[-6:-3]["points_added"].sum())
        recent_block = int(player_history.iloc[-3:]["points_added"].sum())
        if recent_block > previous_block:
            trend_label = tr("trend_up")
        elif recent_block < previous_block:
            trend_label = tr("trend_down")
    elif len(player_history) >= 2:
        prev_gain = int(player_history.iloc[-2]["points_added"])
        if last_gain > prev_gain:
            trend_label = tr("trend_up")
        elif last_gain < prev_gain:
            trend_label = tr("trend_down")

    return tr(
        "trend_note_text",
        gain=f"{last_gain:+d}",
        total=total_after,
        week=week_points,
        month=month_points,
        trend=trend_label,
    )


def log_points_update(player_name, points_added, total_after):
    if points_added == 0:
        return ""

    history = load_history()
    now = pd.Timestamp.now()
    event = pd.DataFrame(
        [[now, player_name, int(points_added), int(total_after), ""]],
        columns=HISTORY_COLUMNS,
    )
    history = pd.concat([history, event], ignore_index=True)
    history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")

    trend_note = build_trend_note_from_history(history, player_name)
    history.loc[history.index[-1], "trend_note"] = trend_note
    history["timestamp"] = history["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    if not _safe_to_csv(history, HISTORY_FILE):
        return ""
    return trend_note


# -----------------------------
# HELPERS
# -----------------------------
def get_ranking(df):
    if df.empty:
        return pd.DataFrame(columns=["Player", "Points"])

    ranking = df.copy()
    ranking["Player"] = ranking["Player"].astype(str).str.strip()
    ranking = ranking[ranking["Player"] != ""]
    ranking["Points"] = pd.to_numeric(ranking["Points"], errors="coerce").fillna(0).astype(int)
    ranking = ranking.sort_values(by="Points", ascending=False).reset_index(drop=True)
    return ranking


def normalize_identity(value):
    return str(value).strip().casefold()


def create_player_account_if_missing(player_name, default_password):
    users = load_users()
    clean_player_name = str(player_name).strip()
    if clean_player_name == "":
        return False

    existing_usernames = set(users["username"].astype(str).map(normalize_identity).tolist())
    if normalize_identity(clean_player_name) in existing_usernames:
        return False

    new_user = pd.DataFrame(
        [[clean_player_name, default_password, "player"]],
        columns=["username", "password", "role"]
    )
    users = pd.concat([users, new_user], ignore_index=True)
    return save_users(users)


def assign_accounts_to_scoreboard_players(default_password):
    scores = load_scores()
    users = load_users()

    player_series = scores["Player"].dropna().astype(str).str.strip()
    players = [player for player in player_series.tolist() if player]

    seen_players = set()
    unique_players = []
    for player in players:
        player_key = normalize_identity(player)
        if player_key not in seen_players:
            seen_players.add(player_key)
            unique_players.append(player)

    existing_users = set(users["username"].astype(str).map(normalize_identity).tolist())
    missing_players = [
        player for player in unique_players
        if normalize_identity(player) not in existing_users
    ]

    if not missing_players:
        return []

    new_users = pd.DataFrame(
        [[player, default_password, "player"] for player in missing_players],
        columns=["username", "password", "role"]
    )
    users = pd.concat([users, new_users], ignore_index=True)
    if not save_users(users):
        return []
    return missing_players


def save_scoreboard_background(uploaded_file):
    with open(SCOREBOARD_BG_FILE, "wb") as file:
        file.write(uploaded_file.getbuffer())


def get_status_icon(position, total_players):
    if position <= 3:
        return "🔥"
    if position > total_players - 5:
        return "❄️"
    return "🏃"


def get_clean_history():
    history = load_history()
    if history.empty:
        return history

    history = history.copy()
    history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
    history["player"] = history["player"].astype(str).str.strip()
    history["points_added"] = pd.to_numeric(history["points_added"], errors="coerce").fillna(0).astype(int)
    history["total_after"] = pd.to_numeric(history["total_after"], errors="coerce").fillna(0).astype(int)
    history["trend_note"] = history["trend_note"].fillna("").astype(str)
    history = history.dropna(subset=["timestamp"])
    history = history[(history["player"] != "") & (history["points_added"] != 0)]
    return history


def compute_weekly_winners(history, year, month):
    if history.empty:
        return pd.DataFrame(columns=["Period", "Winner", "Points"])

    month_history = history[
        (history["timestamp"].dt.year == year) &
        (history["timestamp"].dt.month == month)
    ].copy()

    if month_history.empty:
        return pd.DataFrame(columns=["Period", "Winner", "Points"])

    month_history["week_of_month"] = ((month_history["timestamp"].dt.day - 1) // 7) + 1
    grouped = month_history.groupby(["week_of_month", "player"], as_index=False)["points_added"].sum()

    rows = []
    month_abbr = pd.Timestamp(year=year, month=month, day=1).strftime("%b")

    for week_number in sorted(grouped["week_of_month"].unique()):
        week_data = grouped[grouped["week_of_month"] == week_number]
        max_points = int(week_data["points_added"].max())
        winners = sorted(week_data[week_data["points_added"] == max_points]["player"].tolist())
        rows.append(
            {
                "Period": f"{week_number} Week {month_abbr} Winner",
                "Winner": ", ".join(winners),
                "Points": max_points,
            }
        )

    return pd.DataFrame(rows)


def compute_monthly_winners(history):
    if history.empty:
        return pd.DataFrame(columns=["Period", "Winner", "Points"])

    history = history.copy()
    history["month_period"] = history["timestamp"].dt.to_period("M")
    grouped = history.groupby(["month_period", "player"], as_index=False)["points_added"].sum()

    rows = []
    for month_period in sorted(grouped["month_period"].unique(), reverse=True):
        month_data = grouped[grouped["month_period"] == month_period]
        max_points = int(month_data["points_added"].max())
        winners = sorted(month_data[month_data["points_added"] == max_points]["player"].tolist())
        month_dt = month_period.to_timestamp()
        rows.append(
            {
                "Period": f"{month_dt.strftime('%B')} Winner",
                "Winner": ", ".join(winners),
                "Points": max_points,
            }
        )

    return pd.DataFrame(rows)


def inject_global_styles():
    st.markdown(
        """
        <style>
        :root {
            --nationals-navy: #14225a;
            --nationals-navy-deep: #0b1436;
            --nationals-red: #ab0003;
            --nationals-red-soft: #cf1020;
            --ink: #13213e;
            --muted: #4b5563;
            --card: #ffffff;
            --soft: #f6f8fc;
        }

        .stApp {
            background:
                radial-gradient(circle at 0% 0%, rgba(20,34,90,0.14) 0%, rgba(20,34,90,0.00) 46%),
                radial-gradient(circle at 100% 0%, rgba(171,0,3,0.10) 0%, rgba(171,0,3,0.00) 44%),
                linear-gradient(180deg, #f9fbff 0%, #eef2f9 100%);
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(158deg, var(--nationals-navy-deep) 0%, var(--nationals-navy) 62%, #213a84 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.12);
        }

        [data-testid="stSidebar"] * {
            color: #f3f4f6 !important;
        }

        [data-testid="stSidebar"] [data-baseweb="radio"] > div {
            background: rgba(255, 255, 255, 0.04);
            border-radius: 10px;
            padding: 4px 8px;
        }

        .hero {
            background:
                linear-gradient(118deg, rgba(11,20,54,0.96) 0%, rgba(20,34,90,0.95) 56%, rgba(171,0,3,0.84) 100%);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 18px;
            padding: 22px 24px;
            margin-bottom: 14px;
            box-shadow: 0 14px 32px rgba(20, 34, 90, 0.28);
            position: relative;
            overflow: hidden;
        }

        .hero-content {
            position: relative;
            z-index: 1;
        }

        .hero-text {
            min-width: 0;
            max-width: calc(100% - 126px);
        }

        .hero.with-logo::before {
            content: "";
            position: absolute;
            right: 22px;
            top: 50%;
            transform: translateY(-50%);
            width: 86px;
            height: 86px;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,0.35);
            background-color: rgba(255,255,255,0.12);
            background-image: var(--hero-logo);
            background-repeat: no-repeat;
            background-size: 68px 68px;
            background-position: center;
            z-index: 1;
        }

        .hero::after {
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            right: -80px;
            top: -90px;
            background: radial-gradient(circle, rgba(255,255,255,0.30) 0%, rgba(255,255,255,0.00) 72%);
        }

        .hero h1 {
            color: #f8fafc;
            margin: 0;
            font-size: 2rem;
            line-height: 1.1;
            letter-spacing: 0.2px;
        }

        .hero p {
            color: #e2e8f0;
            margin: 8px 0 0 0;
            font-size: 1rem;
            max-width: 72ch;
        }

        @media (max-width: 860px) {
            .hero-text {
                max-width: calc(100% - 98px);
            }

            .hero.with-logo::before {
                width: 64px;
                height: 64px;
                background-size: 50px 50px;
                right: 16px;
            }
        }

        .kpi-card {
            background: var(--card);
            border: 1px solid rgba(20, 34, 90, 0.12);
            border-radius: 15px;
            padding: 14px 16px;
            margin-bottom: 8px;
            box-shadow: 0 8px 20px rgba(20, 34, 90, 0.08);
            transition: transform 120ms ease, box-shadow 120ms ease;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(20, 34, 90, 0.12);
        }

        .kpi-label {
            color: var(--muted);
            font-size: 0.84rem;
            margin-bottom: 4px;
        }

        .kpi-value {
            color: var(--ink);
            font-size: 1.35rem;
            font-weight: 700;
            line-height: 1.1;
        }

        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(20, 34, 90, 0.10);
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: 0 8px 18px rgba(20, 34, 90, 0.08);
        }

        .podium-card {
            border-radius: 15px;
            border: 1px solid rgba(20, 34, 90, 0.12);
            background: #ffffff;
            padding: 16px;
            min-height: 130px;
            box-shadow: 0 10px 24px rgba(20, 34, 90, 0.11);
        }

        .podium-title {
            margin: 0;
            font-size: 1rem;
            color: var(--nationals-navy);
            font-weight: 700;
        }

        .podium-player {
            margin: 8px 0 2px 0;
            color: #111827;
            font-weight: 700;
            font-size: 1.15rem;
        }

        .podium-points {
            color: var(--nationals-red);
            font-size: 0.95rem;
        }

        .section-title {
            color: var(--nationals-navy);
            margin: 8px 0 10px 0;
            font-size: 1.2rem;
            font-weight: 700;
        }

        .winner-card {
            border-radius: 15px;
            border: 1px solid rgba(20, 34, 90, 0.12);
            background: rgba(255, 255, 255, 0.95);
            padding: 14px;
            margin-bottom: 10px;
            box-shadow: 0 10px 22px rgba(20, 34, 90, 0.09);
        }

        .winner-card .period {
            font-size: 0.9rem;
            color: #475569;
            margin-bottom: 8px;
        }

        .winner-card .winner {
            font-size: 1.1rem;
            color: var(--nationals-navy);
            font-weight: 700;
            margin-bottom: 6px;
        }

        .winner-card .points {
            font-size: 0.95rem;
            color: var(--nationals-red);
            font-weight: 700;
        }

        .trend-note-card {
            border-radius: 12px;
            border: 1px solid rgba(20, 34, 90, 0.10);
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 14px;
            margin-bottom: 8px;
        }

        .trend-note-time {
            color: #64748b;
            font-size: 0.82rem;
            margin-bottom: 4px;
        }

        .trend-note-text {
            color: var(--nationals-navy);
            font-size: 0.94rem;
            margin: 0;
        }

        .stButton > button {
            border-radius: 10px;
            border: 1px solid rgba(20, 34, 90, 0.18);
            background: linear-gradient(120deg, var(--nationals-red) 0%, var(--nationals-red-soft) 100%);
            color: #ffffff;
            font-weight: 700;
            transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
            box-shadow: 0 6px 16px rgba(171, 0, 3, 0.24);
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(1.03);
            box-shadow: 0 10px 20px rgba(171, 0, 3, 0.28);
        }

        [data-testid="stDataFrame"] {
            border: 1px solid rgba(20, 34, 90, 0.12);
            border-radius: 14px;
            box-shadow: 0 8px 20px rgba(20, 34, 90, 0.10);
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_header_logo_data_uri():
    if not os.path.exists(SCOREBOARD_BG_FILE):
        return None
    try:
        with open(SCOREBOARD_BG_FILE, "rb") as logo_file:
            encoded_logo = base64.b64encode(logo_file.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded_logo}"
    except OSError:
        return None


def render_hero(title, subtitle):
    logo_uri = get_header_logo_data_uri()
    hero_class = "hero with-logo" if logo_uri else "hero"
    hero_style = f" style=\"--hero-logo:url('{logo_uri}');\"" if logo_uri else ""

    st.markdown(
        f"""
        <div class="{hero_class}"{hero_style}>
            <div class="hero-content">
                <div class="hero-text">
                    <h1>{html.escape(title)}</h1>
                    <p>{html.escape(subtitle)}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_cards(df):
    ranking = get_ranking(df)
    total_players = len(ranking)
    total_points = int(ranking["Points"].sum()) if total_players else 0
    avg_points = round(total_points / total_players, 1) if total_players else 0

    if total_players:
        leader_name = ranking.iloc[0]["Player"]
        leader_points = int(ranking.iloc[0]["Points"])
    else:
        leader_name = "-"
        leader_points = 0

    cards = [
        ("Players registrados", total_players),
        ("Puntos totales", total_points),
        ("Promedio por player", avg_points),
        ("Lider actual", f"{leader_name} ({leader_points})"),
    ]

    columns = st.columns(4)
    for col, (label, value) in zip(columns, cards):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{html.escape(str(label))}</div>
                    <div class="kpi-value">{html.escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def apply_scoreboard_background(opacity=0.20):
    if not os.path.exists(SCOREBOARD_BG_FILE):
        return False

    with open(SCOREBOARD_BG_FILE, "rb") as file:
        image_base64 = base64.b64encode(file.read()).decode("utf-8")

    overlay = 1 - opacity
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image:
                linear-gradient(
                    rgba(248, 250, 252, {overlay}),
                    rgba(248, 250, 252, {overlay})
                ),
                url("data:image/png;base64,{image_base64}");
            background-repeat: no-repeat, no-repeat;
            background-position: center top 120px, center top 120px;
            background-size: auto, min(58vw, 720px);
            background-attachment: fixed, fixed;
        }}

        [data-testid="stDataFrame"] {{
            background: rgba(255, 255, 255, 0.92);
            border-radius: 12px;
            padding: 8px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return True


def render_scoreboard_background_uploader(uploader_key):
    with st.expander("Imagen de fondo para Scoreboard General"):
        uploaded_image = st.file_uploader(
            "Sube una imagen PNG",
            type=["png"],
            key=uploader_key,
        )

        if uploaded_image is not None:
            save_scoreboard_background(uploaded_image)
            st.success("Imagen de fondo guardada.")

        if os.path.exists(SCOREBOARD_BG_FILE):
            st.caption(f"Archivo actual: {SCOREBOARD_BG_FILE}")
            st.image(SCOREBOARD_BG_FILE, width=170)


def get_period_activity_ranking(df, days):
    base_ranking = get_ranking(df)
    if base_ranking.empty:
        return base_ranking

    base = base_ranking[["Player"]].copy()
    base["BaseOrder"] = range(len(base))
    base["Points"] = 0

    history = get_clean_history()
    if history.empty:
        return base[["Player", "Points"]]

    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    period_history = history[history["timestamp"] >= cutoff]
    if period_history.empty:
        return base[["Player", "Points"]]

    period_points = (
        period_history.groupby("player", as_index=False)["points_added"]
        .sum()
        .rename(columns={"player": "Player", "points_added": "Points"})
    )

    merged = base.drop(columns=["Points"]).merge(period_points, on="Player", how="left")
    merged["Points"] = pd.to_numeric(merged["Points"], errors="coerce").fillna(0).astype(int)
    merged = merged.sort_values(by=["Points", "BaseOrder"], ascending=[False, True]).reset_index(drop=True)
    return merged[["Player", "Points"]]


def render_scoreboard_table(ranking, caption_text=None):
    if ranking.empty:
        st.info("No hay players en el scoreboard todavia.")
        return

    if caption_text:
        st.caption(caption_text)

    total_players = len(ranking)

    board = ranking.copy()
    board.index = range(1, total_players + 1)
    board.index.name = "Position"
    board["Points"] = [
        f"{int(points)} {get_status_icon(pos, total_players)}"
        for pos, points in zip(board.index, board["Points"])
    ]

    def highlight_zone(row):
        if row.name <= 3:
            return ["background-color: rgba(244, 63, 94, 0.11);" for _ in row]
        if row.name > total_players - 5:
            return ["background-color: rgba(56, 189, 248, 0.11);" for _ in row]
        return ["" for _ in row]

    styled = board.style.apply(highlight_zone, axis=1)
    styled = styled.apply(
        lambda col: [
            "color: #be123c; font-weight: 700;" if idx <= 3 else ""
            for idx in col.index
        ],
        subset=["Points"],
    )

    height = 460 if total_players > 10 else None
    st.dataframe(styled, use_container_width=True, height=height)


def render_dynamic_scoreboard(df):
    total_ranking = get_ranking(df)
    if total_ranking.empty:
        st.info("No hay players en el scoreboard todavia.")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["Leaderboard", "Last 7 Days", "Last 15 Days", "Last 30 Days"])

    with tab1:
        render_scoreboard_table(total_ranking, "Total acumulado del torneo.")

    with tab2:
        ranking_7 = get_period_activity_ranking(df, 7)
        render_scoreboard_table(ranking_7, "Puntos ganados en los ultimos 7 dias.")

    with tab3:
        ranking_15 = get_period_activity_ranking(df, 15)
        render_scoreboard_table(ranking_15, "Puntos ganados en los ultimos 15 dias.")

    with tab4:
        ranking_30 = get_period_activity_ranking(df, 30)
        render_scoreboard_table(ranking_30, "Puntos ganados en los ultimos 30 dias.")


def build_scoreboard_pdf(df):
    ranking = get_ranking(df)
    if ranking.empty:
        return None, "No hay datos para exportar."

    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
    except Exception:
        return None, "No se pudo generar el PDF porque matplotlib no esta disponible."

    total_players = len(ranking)
    ranking_pdf = ranking.copy()
    ranking_pdf["Position"] = range(1, len(ranking_pdf) + 1)
    table_df = ranking_pdf[["Position", "Player", "Points"]].copy()
    rows_per_page = 28

    logo_image = None
    if os.path.exists(SCOREBOARD_BG_FILE):
        try:
            logo_image = plt.imread(SCOREBOARD_BG_FILE)
        except Exception:
            logo_image = None

    buffer = io.BytesIO()

    with PdfPages(buffer) as pdf:
        for start in range(0, total_players, rows_per_page):
            page_df = table_df.iloc[start:start + rows_per_page].copy()
            fig, ax = plt.subplots(figsize=(11.69, 8.27))  # A4 landscape
            ax.axis("off")
            ax.set_title("Scoreboard Ranking Table", fontsize=17, fontweight="bold", pad=16)

            page_number = (start // rows_per_page) + 1
            total_pages = ((total_players - 1) // rows_per_page) + 1

            fig.text(
                0.02,
                0.02,
                f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} | Players: {total_players} | Page {page_number}/{total_pages}",
                fontsize=9,
                color="#475569",
            )

            if logo_image is not None:
                logo_ax = fig.add_axes([0.885, 0.82, 0.09, 0.12])
                logo_ax.imshow(logo_image)
                logo_ax.axis("off")

            table = ax.table(
                cellText=page_df.values.tolist(),
                colLabels=page_df.columns.tolist(),
                loc="center",
                cellLoc="left",
                colLoc="left",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.45)

            for (row, col), cell in table.get_celld().items():
                if row == 0:
                    cell.set_text_props(weight="bold", color="white")
                    cell.set_facecolor("#1e3a8a")
                    continue

                global_position = int(page_df.iloc[row - 1]["Position"])
                if global_position <= 3:
                    cell.set_facecolor("#fecaca")
                elif global_position > total_players - 5:
                    cell.set_facecolor("#bfdbfe")
                else:
                    cell.set_facecolor("#f8fafc" if row % 2 == 0 else "#ffffff")

            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

    buffer.seek(0)
    return buffer.getvalue(), None


def render_score_pdf_download(df, button_key):
    pdf_bytes, error = build_scoreboard_pdf(df)
    if error:
        st.info(error)
        return

    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
    st.download_button(
        label="Download PDF table",
        data=pdf_bytes,
        file_name=f"scoreboard_table_{timestamp}.pdf",
        mime="application/pdf",
        key=button_key,
        use_container_width=True,
    )


def render_winners(df):
    ranking = get_ranking(df)
    render_hero("Winners", "Los tres primeros del torneo.")

    if ranking.empty:
        st.info("Aun no hay ganadores porque no hay puntajes cargados.")
        return

    medals = ["🥇", "🥈", "🥉"]
    cols = st.columns(3)

    for idx in range(3):
        with cols[idx]:
            if idx < len(ranking):
                player = ranking.iloc[idx]["Player"]
                points = int(ranking.iloc[idx]["Points"])
                st.markdown(
                    f"""
                    <div class="podium-card">
                        <p class="podium-title">{medals[idx]} Puesto {idx + 1}</p>
                        <p class="podium-player">{html.escape(str(player))}</p>
                        <p class="podium-points">{points} pts</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="podium-card">
                        <p class="podium-title">-</p>
                        <p class="podium-player">Sin player</p>
                        <p class="podium-points">0 pts</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_winner_cards(winners_df, empty_message):
    if winners_df.empty:
        st.info(empty_message)
        return

    columns = st.columns(2)
    for idx, row in winners_df.iterrows():
        with columns[idx % 2]:
            st.markdown(
                f"""
                <div class="winner-card">
                    <div class="period">{html.escape(str(row['Period']))}</div>
                    <div class="winner">🏅 {html.escape(str(row['Winner']))}</div>
                    <div class="points">{int(row['Points'])} pts</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_period_winners_panel():
    render_hero(
        "Weekly and Monthly Winners",
        "Ganadores automaticos por semana y por mes basados en el historial de puntos.",
    )

    history = get_clean_history()
    if history.empty:
        st.info("Aun no hay historial de puntos. Agrega puntos para generar ganadores semanales y mensuales.")
        return

    history["month_period"] = history["timestamp"].dt.to_period("M")
    available_periods = sorted(history["month_period"].unique(), reverse=True)
    period_options = [p.to_timestamp().strftime("%B %Y") for p in available_periods]
    selected_period_label = st.selectbox("Select month", period_options, index=0)
    selected_period = available_periods[period_options.index(selected_period_label)]

    weekly_winners = compute_weekly_winners(history, selected_period.year, selected_period.month)
    monthly_winners = compute_monthly_winners(history)

    highlight_week = weekly_winners.tail(1)
    selected_month_text = selected_period.to_timestamp().strftime("%B")
    highlight_month = monthly_winners[monthly_winners["Period"] == f"{selected_month_text} Winner"].head(1)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p class='section-title'>Week Highlight</p>", unsafe_allow_html=True)
        render_winner_cards(highlight_week, "No weekly winner yet for this month.")
    with col2:
        st.markdown("<p class='section-title'>Month Highlight</p>", unsafe_allow_html=True)
        render_winner_cards(highlight_month, "No monthly winner yet for this month.")

    tab1, tab2 = st.tabs(["Weekly Winners", "Monthly Winners"])
    with tab1:
        st.markdown("<p class='section-title'>Weekly winners of selected month</p>", unsafe_allow_html=True)
        render_winner_cards(weekly_winners, "No weekly winners for this month.")
    with tab2:
        st.markdown("<p class='section-title'>Monthly winners history</p>", unsafe_allow_html=True)
        render_winner_cards(monthly_winners, "No monthly winners in history.")


def get_player_trend_feed(player_name, limit=6):
    history = get_clean_history()
    if history.empty:
        return pd.DataFrame(columns=["timestamp", "trend_note", "points_added", "total_after"])

    player_history = history[history["player"] == player_name].sort_values("timestamp", ascending=False)
    if player_history.empty:
        return pd.DataFrame(columns=["timestamp", "trend_note", "points_added", "total_after"])
    return player_history.head(limit)


def get_latest_trend_by_player(limit=8):
    history = get_clean_history()
    if history.empty:
        return pd.DataFrame(columns=["timestamp", "player", "trend_note", "points_added", "total_after"])

    latest = history.sort_values("timestamp", ascending=False).drop_duplicates(subset=["player"], keep="first")
    return latest.head(limit)


def compute_player_week_projection(player_name, ranking):
    current_points = 0
    current_position = None

    if not ranking.empty and player_name in ranking["Player"].values:
        player_row = ranking[ranking["Player"] == player_name].iloc[0]
        current_points = int(player_row["Points"])
        current_position = int(ranking[ranking["Player"] == player_name].index[0] + 1)

    history = get_clean_history()
    player_history = history[history["player"] == player_name].sort_values("timestamp")

    if player_history.empty:
        return {
            "current_points": current_points,
            "current_position": current_position,
            "avg_points_week": 0,
            "sessions_per_week": 0,
            "forecast_week_points": 0,
            "target_position": current_position,
            "points_to_next_position": 0,
            "points_per_session_goal": 0,
            "summary": "Sin historial de sesiones. Necesitas registrar puntos para generar pronostico.",
        }

    week_totals = (
        player_history
        .groupby(player_history["timestamp"].dt.to_period("W"), as_index=False)["points_added"]
        .sum()
    )
    avg_points_week = float(week_totals["points_added"].mean()) if not week_totals.empty else 0.0
    best_week = int(week_totals["points_added"].max()) if not week_totals.empty else 0

    now = pd.Timestamp.now()
    last_7_points = int(player_history[player_history["timestamp"] >= (now - pd.Timedelta(days=7))]["points_added"].sum())
    prev_7_points = int(
        player_history[
            (player_history["timestamp"] < (now - pd.Timedelta(days=7))) &
            (player_history["timestamp"] >= (now - pd.Timedelta(days=14)))
        ]["points_added"].sum()
    )
    sessions_last_28 = int((player_history["timestamp"] >= (now - pd.Timedelta(days=28))).sum())
    sessions_per_week = sessions_last_28 / 4 if sessions_last_28 > 0 else max(1.0, len(player_history) / max(1, len(week_totals)))

    recent_session_avg = float(player_history.tail(min(8, len(player_history)))["points_added"].mean())
    trend_factor = 1.0
    if last_7_points > prev_7_points:
        trend_factor = 1.12
    elif last_7_points < prev_7_points:
        trend_factor = 0.95

    projected_by_sessions = recent_session_avg * sessions_per_week * trend_factor
    stretch_goal = best_week + 1 if best_week > 0 else projected_by_sessions
    forecast_week_points = int(max(projected_by_sessions, stretch_goal, avg_points_week))

    points_to_next_position = 0
    if current_position and current_position > 1:
        next_points = int(ranking.iloc[current_position - 2]["Points"])
        points_to_next_position = max(0, (next_points - current_points) + 1)
        forecast_week_points = max(forecast_week_points, points_to_next_position)

    target_position = current_position
    if current_position:
        target_total = current_points + forecast_week_points
        target_position = int((ranking["Points"] > target_total).sum() + 1)

    session_goal_divisor = max(1, int(round(sessions_per_week)))
    points_per_session_goal = int(math.ceil(forecast_week_points / session_goal_divisor)) if forecast_week_points > 0 else 0

    summary = (
        f"Pronostico semanal: {forecast_week_points} pts. "
        f"Objetivo por sesion: {points_per_session_goal} pts."
    )

    return {
        "current_points": current_points,
        "current_position": current_position,
        "avg_points_week": round(avg_points_week, 1),
        "sessions_per_week": round(sessions_per_week, 1),
        "forecast_week_points": forecast_week_points,
        "target_position": target_position,
        "points_to_next_position": points_to_next_position,
        "points_per_session_goal": points_per_session_goal,
        "summary": summary,
    }


# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

if "lang" not in st.session_state:
    st.session_state.lang = "es"


# -----------------------------
# AUTH
# -----------------------------
def login(username, password):
    users = load_users()
    user = users[(users["username"] == username) & (users["password"] == password)]

    if not user.empty:
        st.session_state.logged_in = True
        st.session_state.role = user.iloc[0]["role"]
        st.session_state.username = username
        return True
    return False


def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None


inject_global_styles()

# -----------------------------
# LOGIN SCREEN
# -----------------------------
if not st.session_state.logged_in:
    render_hero("Dynamic Scoreboard", "Accede para ver el ranking y el rendimiento del torneo.")

    left, center, right = st.columns([1, 1.1, 1])
    with center:
        st.markdown("<p class='section-title'>Iniciar sesion</p>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            if login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

# -----------------------------
# MAIN APP AFTER LOGIN
# -----------------------------
else:
    st.sidebar.markdown("## Dynamic Scoreboard")
    st.sidebar.write(f"User: `{st.session_state.username}`")
    st.sidebar.write(f"Role: `{st.session_state.role}`")

    if st.sidebar.button("Logout", use_container_width=True):
        logout()
        st.rerun()

    if st.session_state.role == "admin":
        menu = st.sidebar.radio(
            "Navegacion",
            ["Admin Panel", "Scoreboard General", "Winners", "Period Winners"],
        )

        if menu == "Admin Panel":
            render_hero("Admin Control Center", "Gestiona jugadores, puntajes y cuentas en un solo lugar.")
            df = load_scores()
            render_kpi_cards(df)

            default_player_password = st.text_input(
                "Password por defecto para nuevas cuentas player",
                value="player123",
                type="password",
                key="default_player_password",
            )

            admin_tab_ops, admin_tab_reset = st.tabs(["Points & Trends", "Reset Table"])

            with admin_tab_ops:
                col_left, col_right = st.columns([1.35, 1])

                with col_left:
                    st.markdown("<p class='section-title'>Fast Points Update</p>", unsafe_allow_html=True)
                    df["Points"] = pd.to_numeric(df["Points"], errors="coerce").fillna(0).astype(int)
                    admin_ranking = get_ranking(df)
                    existing_players = admin_ranking["Player"].tolist()
                    if "admin_points_delta" not in st.session_state:
                        st.session_state["admin_points_delta"] = 5

                    target_type = st.radio(
                        "Target",
                        ["Existing player", "New player"],
                        horizontal=True,
                        key="admin_target_type",
                    )

                    if target_type == "Existing player" and existing_players:
                        selected_player = st.selectbox("Select player", existing_players, key="admin_existing_player")
                        player_input_value = selected_player
                    else:
                        if target_type == "Existing player":
                            st.info("No hay players existentes. Crea uno nuevo.")
                        player_input_value = st.text_input("New player name", key="admin_new_player_name")

                    st.caption("Quick delta")
                    quick_delta_buttons = [
                        (-10, "m10"),
                        (-5, "m5"),
                        (-1, "m1"),
                        (1, "p1"),
                        (5, "p5"),
                        (10, "p10"),
                    ]
                    delta_cols = st.columns(len(quick_delta_buttons))
                    for index, (delta_value, delta_key) in enumerate(quick_delta_buttons):
                        if delta_cols[index].button(
                            f"{delta_value:+d}",
                            key=f"admin_delta_button_{delta_key}",
                            use_container_width=True,
                        ):
                            next_delta = int(st.session_state.get("admin_points_delta", 0)) + delta_value
                            st.session_state["admin_points_delta"] = max(-500, min(500, next_delta))

                    st.number_input(
                        "Points movement (+ add / - subtract)",
                        min_value=-500,
                        max_value=500,
                        step=1,
                        key="admin_points_delta",
                    )
                    current_delta = int(st.session_state.get("admin_points_delta", 0))
                    st.caption(f"Current movement: {current_delta:+d} pts")
                    preview_player_name = (player_input_value or "").strip() or "este jugador"
                    if current_delta > 0:
                        st.warning(f"Alerta: vas a agregar {current_delta} puntos a {preview_player_name}.")
                    elif current_delta < 0:
                        st.warning(f"Alerta: vas a restar {abs(current_delta)} puntos a {preview_player_name}.")
                    else:
                        st.info(f"Alerta: movimiento en 0 puntos para {preview_player_name}.")

                    if st.button("Apply", key="admin_apply_points_delta", use_container_width=True):
                        clean_player_name = (player_input_value or "").strip()
                        if clean_player_name == "":
                            st.warning("Enter a player name.")
                        elif current_delta == 0:
                            st.warning("El movimiento no puede ser 0.")
                        else:
                            normalized_target = normalize_identity(clean_player_name)
                            player_series = df["Player"].astype(str).str.strip()
                            match_indexes = df.index[player_series.map(normalize_identity) == normalized_target].tolist()

                            if match_indexes:
                                row_index = match_indexes[0]
                                canonical_player_name = str(df.at[row_index, "Player"]).strip() or clean_player_name
                                current_points = int(
                                    pd.to_numeric(
                                        pd.Series([df.at[row_index, "Points"]]),
                                        errors="coerce",
                                    ).fillna(0).iloc[0]
                                )
                                total_after = max(0, current_points + current_delta)
                                applied_delta = total_after - current_points

                                if applied_delta == 0:
                                    st.warning(f"{canonical_player_name} ya tiene 0 puntos. No se puede restar mas.")
                                else:
                                    df.at[row_index, "Points"] = total_after
                                    if save_scores(df):
                                        trend_note = log_points_update(canonical_player_name, applied_delta, total_after)
                                        update_message = f"{canonical_player_name}: {trend_note}" if trend_note else (
                                            f"{canonical_player_name}: {applied_delta:+d} pts. Total: {total_after}."
                                        )
                                        if applied_delta != current_delta:
                                            update_message = f"{update_message} (Ajustado para no bajar de 0.)"
                                        st.session_state["admin_last_update_message"] = update_message
                                        st.rerun()
                            else:
                                if current_delta < 0:
                                    st.warning("Para crear un jugador nuevo, usa puntos positivos.")
                                else:
                                    total_after = current_delta
                                    new_row = pd.DataFrame([[clean_player_name, total_after]], columns=["Player", "Points"])
                                    df = pd.concat([df, new_row], ignore_index=True)
                                    if save_scores(df):
                                        create_player_account_if_missing(clean_player_name, default_player_password)
                                        trend_note = log_points_update(clean_player_name, current_delta, total_after)
                                        st.session_state["admin_last_update_message"] = (
                                            f"{clean_player_name}: {trend_note}" if trend_note else (
                                                f"{clean_player_name}: {current_delta:+d} pts. Total: {total_after}."
                                            )
                                        )
                                        st.rerun()

                    if st.session_state.get("admin_last_update_message"):
                        st.success(st.session_state.pop("admin_last_update_message"))

                with col_right:
                    st.markdown("<p class='section-title'>Automatizaciones</p>", unsafe_allow_html=True)
                    st.caption("Only creates accounts for players without an existing account.")
                    if st.button("Assign Accounts to New Players Only", use_container_width=True):
                        created_accounts = assign_accounts_to_scoreboard_players(default_player_password)
                        if created_accounts:
                            st.success(f"New player accounts created: {', '.join(created_accounts)}")
                        else:
                            st.info("No new players found. All current players already have an account.")

                    render_scoreboard_background_uploader("admin_scoreboard_background_upload")

                    st.markdown("<p class='section-title'>Trend Updates</p>", unsafe_allow_html=True)
                    trend_tab_1, trend_tab_2 = st.tabs(["Latest by player", "Recent updates"])

                    with trend_tab_1:
                        latest_by_player = get_latest_trend_by_player(limit=6)
                        if latest_by_player.empty:
                            st.info("Aun no hay tendencias por jugador.")
                        else:
                            for _, event in latest_by_player.iterrows():
                                event_time = event["timestamp"].strftime("%b %d, %H:%M")
                                note = event["trend_note"] if str(event["trend_note"]).strip() else "Sin nota de tendencia."
                                st.markdown(
                                    f"""
                                    <div class="trend-note-card">
                                        <div class="trend-note-time">{html.escape(str(event['player']))} · {html.escape(str(event_time))}</div>
                                        <p class="trend-note-text">{html.escape(str(note))}</p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                    with trend_tab_2:
                        recent_history = get_clean_history().sort_values("timestamp", ascending=False).head(6)
                        if recent_history.empty:
                            st.info("Aun no hay actualizaciones recientes.")
                        else:
                            for _, event in recent_history.iterrows():
                                event_time = event["timestamp"].strftime("%b %d, %H:%M")
                                note = event["trend_note"] if str(event["trend_note"]).strip() else "Sin nota de tendencia."
                                st.markdown(
                                    f"""
                                    <div class="trend-note-card">
                                        <div class="trend-note-time">{html.escape(str(event_time))} · {html.escape(str(event['player']))}</div>
                                        <p class="trend-note-text">{html.escape(str(note))}</p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                st.markdown("<p class='section-title'>Vista previa del ranking</p>", unsafe_allow_html=True)
                render_dynamic_scoreboard(df)

            with admin_tab_reset:
                st.markdown("<p class='section-title'>Reset Points Table</p>", unsafe_allow_html=True)
                st.warning("Esta accion reinicia todos los puntos a 0. Los players se mantienen en la tabla.")

                if st.button("Reset table points", key="admin_reset_trigger", use_container_width=True):
                    st.session_state["admin_reset_pending"] = True

                if st.session_state.get("admin_reset_pending", False):
                    st.error("Confirmacion requerida: ¿Quieres resetear la tabla de puntos?")
                    confirm_col, cancel_col = st.columns(2)

                    with confirm_col:
                        if st.button("Yes, reset now", key="admin_reset_confirm", use_container_width=True):
                            reset_df = load_scores()
                            if not reset_df.empty:
                                reset_df["Points"] = 0
                                if not save_scores(reset_df):
                                    st.stop()
                            st.session_state["admin_reset_pending"] = False
                            st.session_state["admin_last_update_message"] = "Scoreboard reset: todos los puntos en 0."
                            st.rerun()

                    with cancel_col:
                        if st.button("Cancel", key="admin_reset_cancel", use_container_width=True):
                            st.session_state["admin_reset_pending"] = False
                            st.info("Reset cancelado.")

        elif menu == "Scoreboard General":
            render_hero("Scoreboard General", "Visualiza posiciones, tendencia y zonas calientes/frias.")
            df = load_scores()
            apply_scoreboard_background(opacity=0.24)
            render_kpi_cards(df)
            render_score_pdf_download(df, "admin_scoreboard_pdf_download")
            render_scoreboard_background_uploader("admin_scoreboard_background_upload_view")
            render_dynamic_scoreboard(df)

        elif menu == "Winners":
            df = load_scores()
            render_winners(df)

        elif menu == "Period Winners":
            render_period_winners_panel()

    elif st.session_state.role == "player":
        menu = st.sidebar.radio(
            "Navegacion",
            ["My Score", "Scoreboard General", "Period Winners"],
        )

        df = load_scores()

        if menu == "My Score":
            render_hero("My Score", "Revisa tus puntos y tu posicion actual en el torneo.")

            if st.session_state.username in df["Player"].values:
                ranking = get_ranking(df)
                projection = compute_player_week_projection(st.session_state.username, ranking)

                current_pos = projection["current_position"]
                if current_pos and current_pos <= 3:
                    zone_label = "HOT 🔥"
                elif current_pos and current_pos > len(ranking) - 5:
                    zone_label = "COLD ❄️"
                else:
                    zone_label = "RUN 🏃"

                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Your Points", projection["current_points"])
                with c2:
                    st.metric("Average Points / Week", projection["avg_points_week"])
                with c3:
                    target_label = f"#{projection['target_position']}" if projection["target_position"] else "-"
                    st.metric("Weekly Target Position", target_label)
                with c4:
                    st.metric("Weekly Forecast (pts)", projection["forecast_week_points"])
                with c5:
                    st.metric("Zone", zone_label)

                c6, c7, c8 = st.columns(3)
                with c6:
                    st.metric("Sessions / Week (est.)", projection["sessions_per_week"])
                with c7:
                    st.metric("Goal per Session (pts)", projection["points_per_session_goal"])
                with c8:
                    st.metric("Points to Next Position", projection["points_to_next_position"])

                target_pos = projection["target_position"]
                if current_pos and target_pos and target_pos < current_pos:
                    st.success(
                        f"Objetivo semanal: subir de #{current_pos} a #{target_pos}. {projection['summary']}"
                    )
                elif current_pos and target_pos:
                    st.info(
                        f"Objetivo semanal: consolidar la posicion #{current_pos} y presionar el siguiente lugar. {projection['summary']}"
                    )
                else:
                    st.info(projection["summary"])
            else:
                st.warning("No score assigned yet.")

        elif menu == "Scoreboard General":
            render_hero("Scoreboard", "Compite, sube posiciones y mantente en la zona caliente.")
            apply_scoreboard_background(opacity=0.24)
            render_kpi_cards(df)
            render_score_pdf_download(df, "player_scoreboard_pdf_download")
            render_dynamic_scoreboard(df)

        elif menu == "Period Winners":
            render_period_winners_panel()
