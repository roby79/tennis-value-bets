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
    /* Sidebar viola */
    [data-testid="stSidebar"] {
        background-color: #7B1FA2 !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Bottoni */
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

    /* Titoli */
    h1, h2, h3, h4 {
        color: #4A148C;
        font-weight: 700;
    }

    /* Blocchi card */
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

# 🔧 Sidebar filtri
st.sidebar.header("🔧 Filtri")

# 🔹 Sidebar: pulsante per dati demo
if st.sidebar.button("Popola DB con mock data"):
    db.populate_mock_data()
    st.success("DB popolato con dati di esempio ✅")

# 🔹 Mostra tabella giocatori
st.subheader("📊 Giocatori nel database (ordinati per Elo)")

players = db.get_all_players_with_stats()
if players:
    df_players = pd.DataFrame(players)
    df_players = df_players.sort_values("elo_rating", ascending=False)

    # Mostro tabella "pulita"
    st.dataframe(df_players[["name", "country", "elo_rating", "ranking", "wins", "losses"]].head(15))

    # 🔹 Grafico Plotly: Top 10 Elo
    top10 = df_players.head(10)
    fig = px.bar(
        top10,
        x="name",
        y="elo_rating",
        color="country",
        title="🏆 Top 10 Giocatori per Elo Rating",
        text="elo_rating"
    )
    fig.update_traces(texttemplate='%{text:.0f}', textposition="outside")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ Nessun giocatore presente nel database. Popola il DB dal menu a sinistra.")

st.divider()

# 📅 Sezione partite di oggi
st.subheader("📅 Partite Oggi")

matches = db.get_today_matches()
if matches:
    df_matches = pd.DataFrame(matches)
    st.dataframe(df_matches[["tournament_name", "player1_name", "player2_name", "match_time", "round"]])
else:
    st.info("Nessuna partita trovata per oggi.")

st.divider()

# 💰 Info progetto
st.subheader("💰 Info Progetto")
st.markdown("""
🎾 **Tennis Value Bets** - Demo Dashboard con dati mock  
📊 Statistiche giocatori, quote Betfair e detection value bets  
🚀 Sviluppato con Streamlit + SQLite  
""")
