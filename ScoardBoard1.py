import base64
import html
import io
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
        f"No se pudo guardar `{file_path}` porque esta en uso o bloqueado. "
        "Cierra el archivo si esta abierto (por ejemplo, en Excel) e intenta de nuevo."
    )
    if last_error:
        st.caption(f"Detalle tecnico: {last_error}")
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
        return "Sin historial suficiente para tendencia."

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

    trend_label = "estable"
    if len(player_history) >= 6:
        previous_block = int(player_history.iloc[-6:-3]["points_added"].sum())
        recent_block = int(player_history.iloc[-3:]["points_added"].sum())
        if recent_block > previous_block:
            trend_label = "al alza"
        elif recent_block < previous_block:
            trend_label = "a la baja"
    elif len(player_history) >= 2:
        prev_gain = int(player_history.iloc[-2]["points_added"])
        if last_gain > prev_gain:
            trend_label = "al alza"
        elif last_gain < prev_gain:
            trend_label = "a la baja"

    return (
        f"+{last_gain} pts. Total: {total_after}. "
        f"Semana: {week_points} pts. Mes: {month_points} pts. "
        f"Tendencia: {trend_label}."
    )


def log_points_update(player_name, points_added, total_after):
    if points_added <= 0:
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


def create_player_account_if_missing(player_name, default_password):
    users = load_users()
    if player_name in users["username"].values:
        return False

    new_user = pd.DataFrame(
        [[player_name, default_password, "player"]],
        columns=["username", "password", "role"]
    )
    users = pd.concat([users, new_user], ignore_index=True)
    return save_users(users)


def assign_accounts_to_scoreboard_players(default_password):
    scores = load_scores()
    users = load_users()

    players = scores["Player"].dropna().astype(str).str.strip().tolist()
    players = list(dict.fromkeys([player for player in players if player]))

    existing_users = set(users["username"].astype(str).tolist())
    missing_players = [player for player in players if player not in existing_users]

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
    history = history[(history["player"] != "") & (history["points_added"] > 0)]
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
            --ink: #1f2937;
            --muted: #6b7280;
            --navy: #0f172a;
            --blue: #1d4ed8;
            --red: #be123c;
            --card: #ffffff;
            --soft: #f8fafc;
        }

        .stApp {
            background: radial-gradient(circle at 0% 0%, #eef2ff 0%, #f8fafc 45%, #f3f4f6 100%);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(165deg, #0b132b 0%, #12284c 52%, #1f3d64 100%);
        }

        [data-testid="stSidebar"] * {
            color: #e5e7eb !important;
        }

        .hero {
            background: linear-gradient(125deg, rgba(15,23,42,0.96), rgba(29,78,216,0.88));
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 14px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.25);
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
        }

        .kpi-card {
            background: var(--card);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 8px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
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

        .podium-card {
            border-radius: 14px;
            border: 1px solid rgba(15, 23, 42, 0.08);
            background: #ffffff;
            padding: 16px;
            min-height: 130px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.10);
        }

        .podium-title {
            margin: 0;
            font-size: 1rem;
            color: #0f172a;
            font-weight: 700;
        }

        .podium-player {
            margin: 8px 0 2px 0;
            color: #111827;
            font-weight: 700;
            font-size: 1.15rem;
        }

        .podium-points {
            color: #475569;
            font-size: 0.95rem;
        }

        .section-title {
            color: #111827;
            margin: 8px 0 10px 0;
            font-size: 1.2rem;
            font-weight: 700;
        }

        .winner-card {
            border-radius: 14px;
            border: 1px solid rgba(15, 23, 42, 0.08);
            background: rgba(255, 255, 255, 0.95);
            padding: 14px;
            margin-bottom: 10px;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
        }

        .winner-card .period {
            font-size: 0.9rem;
            color: #475569;
            margin-bottom: 8px;
        }

        .winner-card .winner {
            font-size: 1.1rem;
            color: #0f172a;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .winner-card .points {
            font-size: 0.95rem;
            color: #be123c;
            font-weight: 700;
        }

        .trend-note-card {
            border-radius: 12px;
            border: 1px solid rgba(15, 23, 42, 0.08);
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
            color: #0f172a;
            font-size: 0.94rem;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title, subtitle):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
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


def render_dynamic_scoreboard(df):
    ranking = get_ranking(df)

    if ranking.empty:
        st.info("No hay players en el scoreboard todavia.")
        return

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

    tab1, tab2 = st.tabs(["Leaderboard", "Tendencia"])

    with tab1:
        height = 460 if total_players > 10 else None
        st.dataframe(styled, use_container_width=True, height=height)

    with tab2:
        st.markdown("<p class='section-title'>Top 10 por puntos</p>", unsafe_allow_html=True)
        chart_data = ranking.head(10).set_index("Player")[["Points"]]
        st.bar_chart(chart_data, use_container_width=True)


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


# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None


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
                    admin_ranking = get_ranking(df)
                    existing_players = admin_ranking["Player"].tolist()

                    target_type = st.radio(
                        "Target",
                        ["Existing player", "New player"],
                        horizontal=True,
                        key="admin_target_type",
                    )

                    with st.form("fast_update_points_form"):
                        if target_type == "Existing player" and existing_players:
                            selected_player = st.selectbox("Select player", existing_players, key="admin_existing_player")
                            player_input_value = selected_player
                        else:
                            if target_type == "Existing player":
                                st.info("No hay players existentes. Crea uno nuevo.")
                            player_input_value = st.text_input("New player name", key="admin_new_player_name")

                        quick_col, custom_col = st.columns(2)
                        with quick_col:
                            quick_points = st.select_slider(
                                "Quick points",
                                options=[1, 2, 3, 5, 8, 10, 15, 20, 30, 50],
                                value=5,
                                key="admin_quick_points",
                            )
                        with custom_col:
                            custom_points = st.number_input(
                                "Custom points (optional)",
                                min_value=0,
                                step=1,
                                value=0,
                                key="admin_custom_points",
                            )

                        points_to_add = int(custom_points) if int(custom_points) > 0 else int(quick_points)
                        submitted = st.form_submit_button(f"Apply +{points_to_add} points", use_container_width=True)

                    if submitted:
                        clean_player_name = (player_input_value or "").strip()
                        if clean_player_name == "":
                            st.warning("Enter a player name.")
                        else:
                            if clean_player_name in df["Player"].values:
                                df.loc[df["Player"] == clean_player_name, "Points"] += points_to_add
                            else:
                                new_row = pd.DataFrame([[clean_player_name, points_to_add]], columns=["Player", "Points"])
                                df = pd.concat([df, new_row], ignore_index=True)
                                create_player_account_if_missing(clean_player_name, default_player_password)

                            total_after = int(
                                pd.to_numeric(
                                    df.loc[df["Player"] == clean_player_name, "Points"],
                                    errors="coerce",
                                ).fillna(0).iloc[0]
                            )
                            trend_note = log_points_update(clean_player_name, points_to_add, total_after)
                            if save_scores(df):
                                st.session_state["admin_last_update_message"] = f"{clean_player_name}: {trend_note}"
                                st.rerun()

                    if st.session_state.get("admin_last_update_message"):
                        st.success(st.session_state.pop("admin_last_update_message"))

                with col_right:
                    st.markdown("<p class='section-title'>Automatizaciones</p>", unsafe_allow_html=True)
                    if st.button("Assign Accounts to Scoreboard Players", use_container_width=True):
                        created_accounts = assign_accounts_to_scoreboard_players(default_player_password)
                        if created_accounts:
                            st.success(f"Accounts created: {', '.join(created_accounts)}")
                        else:
                            st.info("All scoreboard players already have an account.")

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
                player_data = ranking[ranking["Player"] == st.session_state.username]
                points = int(player_data["Points"].values[0])
                position = int(ranking[ranking["Player"] == st.session_state.username].index[0] + 1)

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Your Points", points)
                with c2:
                    st.metric("Your Position", f"#{position}")
                with c3:
                    status = "HOT 🔥" if position <= 3 else "COLD ❄️" if position > len(ranking) - 5 else "RUN 🏃"
                    st.metric("Zone", status)

                st.markdown("<p class='section-title'>Trend updates (tu jugador)</p>", unsafe_allow_html=True)
                trend_feed = get_player_trend_feed(st.session_state.username, limit=6)
                if trend_feed.empty:
                    st.info("Todavia no hay actualizaciones de tendencia para este player.")
                else:
                    latest_note = trend_feed.iloc[0]["trend_note"] if str(trend_feed.iloc[0]["trend_note"]).strip() else "Sin nota disponible."
                    st.success(f"Ultima tendencia: {latest_note}")
                    for _, event in trend_feed.iterrows():
                        event_time = event["timestamp"].strftime("%b %d, %H:%M")
                        note = event["trend_note"] if str(event["trend_note"]).strip() else "Sin nota de tendencia."
                        st.markdown(
                            f"""
                            <div class="trend-note-card">
                                <div class="trend-note-time">{html.escape(str(event_time))}</div>
                                <p class="trend-note-text">{html.escape(str(note))}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                st.markdown("<p class='section-title'>Ranking general</p>", unsafe_allow_html=True)
                render_dynamic_scoreboard(df)
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
