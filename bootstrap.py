import os
import sqlite3
from datetime import datetime, timedelta
import random

print("🎾 Creazione progetto Tennis Value Bets...")

# Crea cartelle
os.makedirs("data", exist_ok=True)
print("✅ Cartella data/ creata")

# ==============================
# requirements.txt
# ==============================
requirements = """streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.15.0
requests>=2.31.0
python-dotenv>=1.0.0
sqlalchemy>=2.0.0
"""
with open("requirements.txt", "w") as f:
    f.write(requirements)
print("✅ requirements.txt creato")

# ==============================
# .env.example
# ==============================
env_example = """# Betfair API Configuration
BETFAIR_APP_KEY=your_betfair_app_key_here
BETFAIR_USERNAME=your_betfair_username
BETFAIR_PASSWORD=your_betfair_password

# Database Configuration
DATABASE_URL=sqlite:///data/tennis.db

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
"""
with open(".env.example", "w") as f:
    f.write(env_example)
print("✅ .env.example creato")

# ==============================
# db.py - Database Manager
# ==============================
db_code = '''import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "data/tennis.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Players table
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    country TEXT,
                    birth_date DATE,
                    hand TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Tournaments table
                CREATE TABLE IF NOT EXISTS tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    surface TEXT,
                    category TEXT,
                    start_date DATE,
                    end_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Matches table
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER,
                    player1_id INTEGER,
                    player2_id INTEGER,
                    match_time TIMESTAMP,
                    round TEXT,
                    status TEXT DEFAULT 'scheduled',
                    winner_id INTEGER,
                    score TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tournament_id) REFERENCES tournaments (id),
                    FOREIGN KEY (player1_id) REFERENCES players (id),
                    FOREIGN KEY (player2_id) REFERENCES players (id),
                    FOREIGN KEY (winner_id) REFERENCES players (id)
                );
                
                -- Player statistics
                CREATE TABLE IF NOT EXISTS player_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    elo_rating REAL DEFAULT 1500,
                    ranking INTEGER,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                );
                
                -- Markets table (Betfair)
                CREATE TABLE IF NOT EXISTS markets (
                    id TEXT PRIMARY KEY,
                    match_id INTEGER,
                    market_name TEXT,
                    market_type TEXT,
                    status TEXT,
                    total_matched REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                );
                
                -- Runners table (Betfair)
                CREATE TABLE IF NOT EXISTS runners (
                    id INTEGER PRIMARY KEY,
                    market_id TEXT,
                    runner_name TEXT,
                    selection_id INTEGER,
                    handicap REAL DEFAULT 0,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (market_id) REFERENCES markets (id)
                );
                
                -- Prices table (Betfair)
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    runner_id INTEGER,
                    back_price REAL,
                    lay_price REAL,
                    back_size REAL,
                    lay_size REAL,
                    total_matched REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (runner_id) REFERENCES runners (id)
                );
            """)
            conn.commit()
        logger.info("Database initialized successfully")
    
    def insert_tournament(self, name: str, surface: str = None, category: str = None) -> int:
        """Insert a new tournament"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO tournaments (name, surface, category, start_date, end_date)
                VALUES (?, ?, ?, ?, ?)
            """, (name, surface, category, datetime.now().date(), 
                  datetime.now().date() + timedelta(days=7)))
            conn.commit()
            return cursor.lastrowid
    
    def insert_player(self, name: str, country: str = None) -> int:
        """Insert a new player"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO players (name, country)
                VALUES (?, ?)
            """, (name, country))
            conn.commit()
            return cursor.lastrowid
    
    def insert_player_stats(self, player_id: int, elo_rating: float = 1500, 
                           ranking: int = None, wins: int = 0, losses: int = 0) -> None:
        """Insert or update player statistics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO player_stats (player_id, elo_rating, ranking, wins, losses)
                VALUES (?, ?, ?, ?, ?)
            """, (player_id, elo_rating, ranking, wins, losses))
            conn.commit()
    
    def insert_match(self, tournament_id: int, player1_id: int, player2_id: int, 
                    match_time: datetime, round_name: str = "R1") -> int:
        """Insert a new match"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO matches (tournament_id, player1_id, player2_id, match_time, round)
                VALUES (?, ?, ?, ?, ?)
            """, (tournament_id, player1_id, player2_id, match_time, round_name))
            conn.commit()
            return cursor.lastrowid
    
    def get_today_matches(self) -> List[Dict]:
        """Get today's matches with tournament and player info"""
        today = datetime.now().date()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT m.*, t.name as tournament_name,
                       p1.name as player1_name, p2.name as player2_name
                FROM matches m
                JOIN tournaments t ON m.tournament_id = t.id
                JOIN players p1 ON m.player1_id = p1.id
                JOIN players p2 ON m.player2_id = p2.id
                WHERE DATE(m.match_time) = ?
                ORDER BY m.match_time
            """, (today,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_players_with_stats(self) -> List[Dict]:
        """Get all players with their statistics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT p.name, ps.elo_rating, ps.ranking, ps.wins, ps.losses
                FROM players p
                JOIN player_stats ps ON p.id = ps.player_id
                ORDER BY ps.elo_rating DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
'''

with open("db.py", "w") as f:
    f.write(db_code)
print("✅ db.py creato")

# ==============================
# INIZIALIZZA IL DATABASE PRIMA DI POPOLARE
# ==============================
print("🔧 Inizializzazione database...")
exec(db_code)  # Esegue il codice per avere la classe DatabaseManager
db_manager = DatabaseManager("data/tennis.db")
print("✅ Database inizializzato con tabelle")

# ==============================
# POPOLA IL DATABASE CON DATI MOCK
# ==============================
print("📊 Popolamento database con dati mock...")

# Inserisci tornei
tournaments_data = [
    {"name": "ATP Australian Open", "surface": "Hard", "category": "Grand Slam"},
    {"name": "WTA Australian Open", "surface": "Hard", "category": "Grand Slam"},
    {"name": "ATP Miami Open", "surface": "Hard", "category": "Masters 1000"},
    {"name": "WTA Miami Open", "surface": "Hard", "category": "WTA 1000"}
]

tournament_ids = []
for t_data in tournaments_data:
    tournament_id = db_manager.insert_tournament(t_data["name"], t_data["surface"], t_data["category"])
    tournament_ids.append(tournament_id)
    print(f"  ✅ Torneo: {t_data['name']}")

# Inserisci giocatori
atp_players = [
    {"name": "Novak Djokovic", "country": "SRB", "elo": 2100, "ranking": 1, "wins": 45, "losses": 8},
    {"name": "Carlos Alcaraz", "country": "ESP", "elo": 2080, "ranking": 2, "wins": 42, "losses": 10},
    {"name": "Jannik Sinner", "country": "ITA", "elo": 2050, "ranking": 3, "wins": 38, "losses": 12},
    {"name": "Daniil Medvedev", "country": "RUS", "elo": 2020, "ranking": 4, "wins": 35, "losses": 15}
]

wta_players = [
    {"name": "Iga Swiatek", "country": "POL", "elo": 2080, "ranking": 1, "wins": 48, "losses": 7},
    {"name": "Aryna Sabalenka", "country": "BLR", "elo": 2040, "ranking": 2, "wins": 40, "losses": 12},
    {"name": "Coco Gauff", "country": "USA", "elo": 2000, "ranking": 3, "wins": 35, "losses": 15},
    {"name": "Elena Rybakina", "country": "KAZ", "elo": 1980, "ranking": 4, "wins": 33, "losses": 17}
]

all_players = atp_players + wta_players
player_ids = {}

for p_data in all_players:
    player_id = db_manager.insert_player(p_data["name"], p_data["country"])
    player_ids[p_data["name"]] = player_id
    db_manager.insert_player_stats(
        player_id, p_data["elo"], p_data["ranking"], p_data["wins"], p_data["losses"]
    )
    print(f"  ✅ Giocatore: {p_data['name']} (ELO: {p_data['elo']})")

# Inserisci partite per oggi
today = datetime.now()
match_counter = 0

for i, tournament_id in enumerate(tournament_ids):
    is_wta = "WTA" in tournaments_data[i]["name"]
    
    for j in range(2):  # 2 partite per torneo
        match_counter += 1
        
        if is_wta:
            p1_name = random.choice([p["name"] for p in wta_players])
            p2_name = random.choice([p["name"] for p in wta_players if p["name"] != p1_name])
        else:
            p1_name = random.choice([p["name"] for p in atp_players])
            p2_name = random.choice([p["name"] for p in atp_players if p["name"] != p1_name])
        
        player1_id = player_ids[p1_name]
        player2_id = player_ids[p2_name]
        
        match_time = today + timedelta(hours=j*4 + random.randint(0, 2))
        match_id = db_manager.insert_match(tournament_id, player1_id, player2_id, match_time, f"R{j+1}")
        
        print(f"  ✅ Match: {p1_name} vs {p2_name}")

print(f"✅ Database popolato con {len(all_players)} giocatori e {match_counter} partite")

# ==============================
# app.py - Streamlit App
# ==============================
app_code = '''import streamlit as st
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
        fig_top.update_xaxis(tickangle=45)
        st.plotly_chart(fig_top, use_container_width=True)
        
        # Players table
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
'''

with open("app.py", "w") as f:
    f.write(app_code)
print("✅ app.py creato")

print("\n🎉 PROGETTO COMPLETATO!")
print("=" * 50)
print("Prossimi passi:")
print("1) python3 -m venv venv")
print("2) source venv/bin/activate")
print("3) pip3 install -r requirements.txt")
print("4) streamlit run app.py")
print("\n🌐 L'app sarà disponibile su: http://localhost:8501")
