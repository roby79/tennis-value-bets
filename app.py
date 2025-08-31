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

# 🎨 Tema custom con CSS (bianco+viola stile mobile UI)
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
    .stDataFrame, .stPlotlyChart, .element-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 1em;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 1.5em;
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

# Pulsante popola giocatori
if st.sidebar.button("Popola DB giocatori 👥"):
    db.populate_mock_data()
    st.success("DB popolato con giocatori demo ✅")

# Pulsante genera match mock
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

    # Applica filtri
    df_filtered = df_players[
        (df_players["country"].isin(selected_nations)) &
        (df_players["elo_rating"] >= elo_min) &
        (df_players["ranking"] <= rank_max)
    ]

    st.subheader(f"📊 Giocatori trovati: {len(df_filtered)}")

    if not df_filtered.empty:
        # Tabella
        st.dataframe(df_filtered[["name", "country", "elo_rating", "ranking", "wins", "losses"]].head(15))

        # Grafico
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

        # 👤 Scheda Giocatore
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

            # Trend Elo mock
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
# 🎾 Partite di Oggi + Value Bets
# -------------------------
st.subheader("📅 Partite Oggi")

matches = db.get_today_matches()
if matches:
    df_matches = pd.DataFrame(matches)

    # Calcolo probabilità stimata da Elo (semplice modello)
    def win_prob(elo1, elo2):
        return 1 / (1 + 10 ** ((elo2 - elo1) / 400))

    # Join con elo
    elo_map = {p["name"]: p["elo_rating"] for p in players}
    df_matches["elo_p1"] = df_matches["player1_name"].map(elo_map)
    df_matches["elo_p2"] = df_matches["player2_name"].map(elo_map)

    df_matches["prob_p1"] = df_matches.apply(lambda r: win_prob(r["elo_p1"], r["elo_p2"]), axis=1)
    df_matches["prob_p2"] = 1 - df_matches["prob_p1"]

    df_matches["fair_odds_p1"] = (1 / df_matches["prob_p1"]).round(2)
    df_matches["fair_odds_p2"] = (1 / df_matches["prob_p2"]).round(2)

    # Value Bet check
    df_matches["value_p1"] = df_matches["odds_p1"] > df_matches["fair_odds_p1"]
    df_matches["value_p2"] = df_matches["odds_p2"] > df_matches["fair_odds_p2"]

    st.dataframe(df_matches[[
        "tournament_name", "player1_name", "player2_name", "round", "surface",
        "odds_p1", "fair_odds_p1", "value_p1",
        "odds_p2", "fair_odds_p2", "value_p2"
    ]])

else:
    st.info("Nessuna partita trovata per oggi. Usa 'Genera partite mock 🎲' nella sidebar.")

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
