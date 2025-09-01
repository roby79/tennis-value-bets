import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

from db import DatabaseManager

# ⚙️ Configurazione pagina
st.set_page_config(
    page_title="Tennis Value Bets",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Tema custom con CSS (bianco+viola)
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #7B1FA2 !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    .stButton>button {
        background-color: #7B1FA2;
        color: white;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #9C27B0;
        color: #fff;
    }
    h1, h2, h3, h4 {
        color: #4A148C;
        font-weight: 700;
    }
    .match-card {
        background:#f6f6f6;
        padding:10px;
        border-radius:8px;
        text-align:center;
    }
    .stDataFrame, .stPlotlyChart, .element-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 1em;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 1.5em;
    }
    .badge {
        display:inline-block;
        padding:2px 8px;
        border-radius:12px;
        font-size:12px;
        font-weight:700;
        color:#fff;
        background:#2e7d32;
        margin-left:6px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Inizializza DB
db = DatabaseManager()

# 🎾 Titolo principale
st.title("🎾 Tennis Value Bets Dashboard")
st.markdown("**Analisi ATP/WTA con quote Betfair e detection value bets**")

# 🔧 Sidebar azioni
st.sidebar.header("🔧 Azioni")

if st.sidebar.button("Popola DB giocatori 👥"):
    db.populate_mock_data()
    st.success("DB popolato con giocatori demo ✅")

if st.sidebar.button("Genera partite mock 🎲"):
    try:
        db.populate_mock_matches()
        st.success("Partite mock generate ✅")
    except Exception as e:
        st.error(f"Errore nel generare partite mock: {e}")

# -------------------------
# 👥 Filtri Giocatori
# -------------------------
st.sidebar.header("Filtri giocatori")

players = db.get_all_players_with_stats()
if players:
    df_players = pd.DataFrame(players)
    df_players = df_players.sort_values("elo_rating", ascending=False)

    nations = sorted(df_players["country"].dropna().unique())
    selected_nations = st.sidebar.multiselect("🌍 Seleziona Paesi", nations, default=nations)

    min_elo = int(df_players["elo_rating"].min())
    max_elo = int(df_players["elo_rating"].max())
    elo_min = st.sidebar.slider("📈 Elo minimo", min_elo, max_elo, min_elo)

    min_rank = int(df_players["ranking"].min())
    max_rank = int(df_players["ranking"].max())
    rank_max = st.sidebar.slider("🏅 Ranking massimo", min_rank, max_rank, max_rank)

    df_filtered = df_players[
        (df_players["country"].isin(selected_nations)) &
        (df_players["elo_rating"] >= elo_min) &
        (df_players["ranking"] <= rank_max)
    ]

    st.subheader(f"📊 Giocatori trovati: {len(df_filtered)}")

    if not df_filtered.empty:
        st.dataframe(df_filtered[["name", "country", "elo_rating", "ranking", "wins", "losses"]].head(15))

        top10 = df_filtered.head(10)
        fig = px.bar(
            top10,
            x="name",
            y="elo_rating",
            color="country",
            title="🏆 Top 10 Giocatori per Elo Rating (filtrati)",
            text="elo_rating"
        )
        fig.update_traces(texttemplate='%{text:.0f}', textposition="outside")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # 👤 Scheda giocatore
        player_names = df_filtered["name"].tolist()
        selected_player = st.selectbox("👤 Vedi scheda giocatore", ["—"] + player_names)

        if selected_player != "—":
            player_data = df_filtered[df_filtered["name"] == selected_player].iloc[0]
            st.markdown(f"### 👤 {player_data['name']} ({player_data['country']})")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Elo Rating", f"{player_data['elo_rating']}")
                st.metric("Ranking", f"{player_data['ranking']}")
            with col2:
                st.metric("Vittorie", f"{player_data['wins']}")
                st.metric("Sconfitte", f"{player_data['losses']}")

            fig_trend = px.line(
                x=list(range(10)),
                y=np.random.randint(1600, 2000, 10),
                title=f"Andamento Elo di {player_data['name']}"
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    else:
        st.warning("⚠️ Nessun giocatore trovato con i filtri attuali.")
else:
    st.info("ℹ️ Nessun giocatore presente nel database. Popola il DB dal menu a sinistra.")

st.divider()

# -------------------------
# 🎾 Partite di Oggi (card layout + filtri + grafico quote)
# -------------------------
st.subheader("📅 Partite Oggi")

matches = db.get_today_matches()
if matches:
    df_matches = pd.DataFrame(matches)

    # Probabilità stimate da Elo
    def win_prob(elo1, elo2):
        return 1 / (1 + 10 ** ((elo2 - elo1) / 400))

    elo_map = {p["name"]: p["elo_rating"] for p in players}
    df_matches["elo_p1"] = df_matches["player1_name"].map(elo_map)
    df_matches["elo_p2"] = df_matches["player2_name"].map(elo_map)

    # Gestione possibili NaN Elo
    df_matches["elo_p1"] = df_matches["elo_p1"].fillna(df_players["elo_rating"].median() if players else 1800)
    df_matches["elo_p2"] = df_matches["elo_p2"].fillna(df_players["elo_rating"].median() if players else 1800)

    df_matches["prob_p1"] = df_matches.apply(lambda r: win_prob(r["elo_p1"], r["elo_p2"]), axis=1)
    df_matches["prob_p2"] = 1 - df_matches["prob_p1"]

    df_matches["fair_odds_p1"] = (1 / df_matches["prob_p1"]).round(2)
    df_matches["fair_odds_p2"] = (1 / df_matches["prob_p2"]).round(2)

    df_matches["value_p1"] = df_matches["odds_p1"] > df_matches["fair_odds_p1"]
    df_matches["value_p2"] = df_matches["odds_p2"] > df_matches["fair_odds_p2"]

    # Edge come scostamento percentuale vs fair odds
    df_matches["edge_p1"] = (df_matches["odds_p1"] / df_matches["fair_odds_p1"] - 1).round(3)
    df_matches["edge_p2"] = (df_matches["odds_p2"] / df_matches["fair_odds_p2"] - 1).round(3)

    # ---- Filtri partite (sidebar)
    st.sidebar.header("Filtri partite")

    tournaments = sorted(df_matches["tournament_name"].dropna().unique().tolist())
    selected_tournaments = st.sidebar.multiselect("🏟️ Tornei", tournaments, default=tournaments)

    surfaces = sorted(df_matches["surface"].dropna().unique().tolist())
    selected_surfaces = st.sidebar.multiselect("🟦 Superfici", surfaces, default=surfaces)

    only_value = st.sidebar.checkbox("🔥 Solo Value Bets", value=False)
    min_edge = st.sidebar.slider("📊 Edge minimo (%)", 0, 50, 5)  # percento
    min_edge_dec = min_edge / 100.0

    # Applica filtri
    dfm = df_matches[
        (df_matches["tournament_name"].isin(selected_tournaments)) &
        (df_matches["surface"].isin(selected_surfaces))
    ].copy()

    if only_value:
        dfm = dfm[(dfm["value_p1"]) | (dfm["value_p2"])]

    # Edge soglia su almeno uno dei due lati
    dfm = dfm[(dfm["edge_p1"] >= min_edge_dec) | (dfm["edge_p2"] >= min_edge_dec)]

    st.caption(f"Partite dopo filtri: {len(dfm)}")

    # Download CSV value bets
    vb = dfm[
        (dfm["edge_p1"] >= min_edge_dec) | (dfm["edge_p2"] >= min_edge_dec)
    ][[
        "tournament_name","round","surface",
        "player1_name","odds_p1","fair_odds_p1","edge_p1",
        "player2_name","odds_p2","fair_odds_p2","edge_p2",
        "match_time"
    ]].copy()
    if not vb.empty:
        vb_sorted = vb.sort_values(by=["edge_p1","edge_p2"], ascending=False)
        csv = vb_sorted.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Scarica Value Bets (CSV)", data=csv, file_name="value_bets.csv", mime="text/csv")

    # Render card + grafico per ciascun match
    if dfm.empty:
        st.info("Nessuna partita soddisfa i filtri attuali.")
    else:
        for _, row in dfm.iterrows():
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                badge_html = '<span class="badge">VALUE</span>' if row["value_p1"] and row["edge_p1"] >= min_edge_dec else ""
                st.markdown(f"""
                <div class="match-card">
                    <b>{row['player1_name']}</b> {badge_html}<br>
                    Elo: {int(row['elo_p1'])}<br>
                    Odds: <span style="color:{'green' if row['value_p1'] and row['edge_p1'] >= min_edge_dec else 'black'}">{row['odds_p1']}</span><br>
                    Fair: {row['fair_odds_p1']}<br>
                    Edge: {(row['edge_p1']*100):.1f}%
                </div>
                """, unsafe_allow_html=True)

            with col2:
                when = ""
                try:
                    when = pd.to_datetime(row["match_time"]).strftime("%H:%M")
                except Exception:
                    when = str(row["match_time"])
                st.markdown(f"""
                <div style="text-align:center; font-size:22px;">
                    <b>VS</b><br>
                    <span style="font-size:14px;">{row['tournament_name']} - {row['round']} ({row['surface']})</span><br>
                    <span style="font-size:12px;">{when}</span>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                badge_html2 = '<span class="badge">VALUE</span>' if row["value_p2"] and row["edge_p2"] >= min_edge_dec else ""
                st.markdown(f"""
                <div class="match-card">
                    <b>{row['player2_name']}</b> {badge_html2}<br>
                    Elo: {int(row['elo_p2'])}<br>
                    Odds: <span style="color:{'green' if row['value_p2'] and row['edge_p2'] >= min_edge_dec else 'black'}">{row['odds_p2']}</span><br>
                    Fair: {row['fair_odds_p2']}<br>
                    Edge: {(row['edge_p2']*100):.1f}%
                </div>
                """, unsafe_allow_html=True)

            # 🔹 Grafico quote vs fair
            fig_match = px.bar(
                x=["Odds P1", "Fair P1", "Odds P2", "Fair P2"],
                y=[row['odds_p1'], row['fair_odds_p1'], row['odds_p2'], row['fair_odds_p2']],
                color=["Real", "Fair", "Real", "Fair"],
                title=f"Confronto Quote - {row['player1_name']} vs {row['player2_name']}",
                text=[row['odds_p1'], row['fair_odds_p1'], row['odds_p2'], row['fair_odds_p2']]
            )
            fig_match.update_traces(texttemplate='%{text:.2f}', textposition="outside")
            fig_match.update_layout(yaxis_title="Quota", xaxis_title="", showlegend=False, height=380)
            st.plotly_chart(fig_match, use_container_width=True)

            st.markdown("---")

else:
    st.info("Nessuna partita trovata per oggi. Usa 'Genera partite mock 🎲'.")

st.divider()

# -------------------------
# ℹ️ Info progetto
# -------------------------
st.subheader("💰 Info Progetto")
st.markdown("""
🎾 **Tennis Value Bets** - Demo Dashboard con dati mock  
📊 Statistiche giocatori, quote Betfair e detection value bets  
🚀 Sviluppato con Streamlit + SQLite  
""")
