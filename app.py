import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime
import plotly.express as px
from db import DatabaseManager

# Page config
st.set_page_config(
    page_title="Tennis Value Bets",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_db():
    return DatabaseManager()

db = init_db()

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .value-bet {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎾 Tennis Value Bets Dashboard")
st.markdown("**Analisi ATP/WTA con quote Betfair e detection value bets**")

# Sidebar
st.sidebar.header("🔧 Filtri")
show_value_only = st.sidebar.checkbox("Mostra solo Value Bets", False)

# Refresh data
if st.sidebar.button("🔄 Aggiorna Dati"):
    st.cache_resource.clear()
    st.rerun()

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📅 Partite Oggi", "📊 Statistiche Giocatori", "💰 Info Progetto"])

with tab1:
    st.header("Partite di Oggi")
    
    # Get today's matches
    matches = db.get_today_matches()
    
    if not matches:
        st.warning("Nessuna partita trovata per oggi.")
        st.info("💡 Esegui `python etl_today.py` per importare nuovi dati.")
    else:
        st.success(f"Trovate {len(matches)} partite per oggi!")
        
        for match in matches:
            player1 = match['player1_name']
            player2 = match['player2_name']
            tournament = match['tournament_name']
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.subheader(f"{player1} vs {player2}")
                st.caption(f"🏆 {tournament} • {match['match_time']}")
            
            with col2:
                # Mock odds per demo
                odds1 = round(np.random.uniform(1.5, 3.0), 2)
                odds2 = round(np.random.uniform(1.5, 3.0), 2)
                st.metric("Quote Mock", f"{odds1} / {odds2}")
            
            with col3:
                # Mock EV per demo
                ev1 = round(np.random.uniform(-0.1, 0.2), 3)
                ev2 = round(np.random.uniform(-0.1, 0.2), 3)
                st.metric("EV Mock", f"{ev1:+.3f} / {ev2:+.3f}")
                
                if ev1 > 0.05 or ev2 > 0.05:
                    st.success("🎯 VALUE BET!")
                else:
                    st.info("📊 Normale")
            
            st.divider()

with tab2:
    st.header("Statistiche Giocatori")
    
    # Get all players with stats
    players = db.get_all_players_with_stats()
    
    if players:
        # Create DataFrame
        df_players = pd.DataFrame(players)
        
        # ELO distribution
        st.subheader("Distribuzione ELO")
        fig_elo = px.histogram(df_players, x='elo_rating', nbins=15, 
                              title="Distribuzione Rating ELO")
        st.plotly_chart(fig_elo, use_container_width=True)
        
       # Top players by ELO
st.subheader("Top Giocatori per ELO")
top_players = df_players.nlargest(8, 'elo_rating')

fig_top = px.bar(top_players, x='name', y='elo_rating',
                 title="Top Giocatori per Rating ELO")
fig_top.update_layout(xaxis_tickangle=45)
st.plotly_chart(fig_top, use_container_width=True)

# Tabella Giocatori
st.subheader("Tabella Giocatori")
st.dataframe(
    df_players[['name', 'elo_rating', 'ranking', 'wins', 'losses']].round(0),
    use_container_width=True
)
    else:
        st.warning("Nessun giocatore trovato nel database.")

with tab3:
    st.header("💰 Info Progetto")
    
    st.markdown("""
    ### 🎾 Tennis Value Bets Dashboard
    
    Questa è una **demo funzionante** del progetto completo per l'analisi di value bets nel tennis.
    
    #### ✅ Cosa funziona già:
    - **Database SQLite** popolato con giocatori ATP/WTA reali
    - **Sistema ELO** per rating giocatori
    - **Partite mock** generate per oggi
    - **Dashboard interattiva** con filtri e grafici
    - **Struttura completa** pronta per integrazioni API
    
    #### 🚀 Prossimi passi per la versione completa:
    1. **Integrazione Betfair API** (credenziali in `.env`)
    2. **ETL automatico** per import partite reali
    3. **Modelli ML** avanzati per predizioni
    4. **Deploy su Streamlit Cloud** o Heroku
    
    #### 📁 File del progetto:
    - `app.py` - Questa dashboard Streamlit
    - `db.py` - Gestione database SQLite
    - `bootstrap.py` - Script di setup iniziale
    - `data/tennis.db` - Database con dati mock
    
    #### 🔧 Comandi utili:
    ```bash
    # Avvia l'app
    streamlit run app.py
    
    # Rigenera dati mock
    python3 bootstrap.py
    ```
    """)
    
    # Database stats
    st.subheader("📊 Statistiche Database")
    
    with sqlite3.connect("data/tennis.db") as conn:
        players_count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        matches_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        tournaments_count = conn.execute("SELECT COUNT(*) FROM tournaments").fetchone()[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Giocatori", players_count)
    with col2:
        st.metric("Partite", matches_count)
    with col3:
        st.metric("Tornei", tournaments_count)

# Footer
st.markdown("---")
st.markdown("🎾 **Tennis Value Bets** - Demo Dashboard con dati mock")
