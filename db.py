import os
import sqlite3
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, date

class DatabaseManager:
    def __init__(self, db_path="data/tennis.db"):
        os.makedirs("data", exist_ok=True)  # 🔧 Crea cartella se mancante
        self.db_path = db_path
        self.init_database()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        conn = self._conn()
        cur = conn.cursor()

        # players
        cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            country TEXT,
            gender TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # player_stats
        cur.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            player_id INTEGER PRIMARY KEY,
            elo_rating REAL DEFAULT 1800,
            ranking INTEGER DEFAULT 999,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            surface_win_pct_hard REAL,
            surface_win_pct_clay REAL,
            surface_win_pct_grass REAL,
            tb_win_pct REAL,
            avg_games_won REAL,
            avg_games_lost REAL,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
        """)

        # matches
        cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id INTEGER,
            player2_id INTEGER,
            tournament_name TEXT,
            round TEXT,
            surface TEXT,
            match_time TIMESTAMP,
            odds_p1 REAL,
            odds_p2 REAL,
            status TEXT,
            source_book TEXT,
            UNIQUE(player1_id, player2_id, tournament_name, round, match_time),
            FOREIGN KEY(player1_id) REFERENCES players(id),
            FOREIGN KEY(player2_id) REFERENCES players(id)
        )
        """)

        # Indici utili
        cur.execute("CREATE INDEX IF NOT EXISTS idx_players_name ON players(name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_matches_time ON matches(match_time)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_matches_tourn ON matches(tournament_name)")
        conn.commit()
        conn.close()

    # === UPSERT HELPERS (per dati reali) ===

    def upsert_player_by_name(self, name: str, country: str = "", gender: Optional[str] = None) -> int:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM players WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            pid = row[0]
            # aggiorna country/gender se nuovi
            cur.execute("""
                UPDATE players SET country = COALESCE(NULLIF(?, ''), country),
                                   gender = COALESCE(?, gender)
                WHERE id = ?
            """, (country, gender, pid))
            conn.commit()
            conn.close()
            return pid
        else:
            cur.execute("INSERT INTO players (name, country, gender) VALUES (?, ?, ?)", (name, country, gender))
            pid = cur.lastrowid
            # crea stats base
            cur.execute("INSERT OR IGNORE INTO player_stats (player_id) VALUES (?)", (pid,))
            conn.commit()
            conn.close()
            return pid

    def upsert_match(
        self,
        player1_id: int,
        player2_id: int,
        tournament_name: str,
        round: str,
        surface: str,
        match_time: Optional[str],
        status: Optional[str] = "not_started",
    ) -> int:
        conn = self._conn()
        cur = conn.cursor()
        # 🔧 Fix: usa = ? invece di IS ? per match_time
        cur.execute("""
            SELECT id FROM matches
            WHERE player1_id=? AND player2_id=? AND tournament_name=? AND round=? AND match_time = ?
        """, (player1_id, player2_id, tournament_name, round, match_time))
        row = cur.fetchone()
        if row:
            mid = row[0]
            cur.execute("""
                UPDATE matches
                SET surface = COALESCE(?, surface),
                    status = COALESCE(?, status)
                WHERE id = ?
            """, (surface, status, mid))
            conn.commit()
            conn.close()
            return mid
        else:
            cur.execute("""
                INSERT INTO matches (player1_id, player2_id, tournament_name, round, surface, match_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (player1_id, player2_id, tournament_name, round, surface, match_time, status))
            mid = cur.lastrowid
            conn.commit()
            conn.close()
            return mid

    def upsert_match_odds(self, match_id: int, odds_p1: Optional[float], odds_p2: Optional[float], source_book: Optional[str] = None):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT odds_p1, odds_p2 FROM matches WHERE id = ?", (match_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return
        current_p1, current_p2 = row
        new_p1 = odds_p1 if odds_p1 is not None else current_p1
        new_p2 = odds_p2 if odds_p2 is not None else current_p2
        cur.execute("""
            UPDATE matches
            SET odds_p1 = ?, odds_p2 = ?, source_book = COALESCE(?, source_book)
            WHERE id = ?
        """, (new_p1, new_p2, source_book, match_id))
        conn.commit()
        conn.close()

    # === PUBLIC METHODS (usati da app.py) ===

    def get_all_players_with_stats(self) -> List[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.name, p.country, COALESCE(p.gender, '') as gender,
                   s.elo_rating, s.ranking, s.wins, s.losses
            FROM players p
            LEFT JOIN player_stats s ON s.player_id = p.id
            ORDER BY s.elo_rating DESC
        """)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        conn.close()
        return [dict(zip(cols, r)) for r in rows]

    def get_today_matches(self) -> List[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        # Prendiamo finestre +/- 24h
        cur.execute("""
            SELECT m.id, m.tournament_name, m.round, m.surface, m.match_time,
                   m.odds_p1, m.odds_p2, m.status,
                   p1.name as player1_name, p2.name as player2_name
            FROM matches m
            JOIN players p1 ON p1.id = m.player1_id
            JOIN players p2 ON p2.id = m.player2_id
            WHERE date(m.match_time) = date('now')
               OR (m.match_time IS NULL AND m.status = 'not_started')
            ORDER BY COALESCE(m.match_time, '2099-12-31T00:00:00')
        """)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        conn.close()
        return [dict(zip(cols, r)) for r in rows]

    # === MOCK DATA FUNCTIONS ===

    def populate_mock_data(self):
        conn = self._conn()
        cur = conn.cursor()

        # Mock players ATP/WTA
        mock_players = [
            ("Novak Djokovic", "RS", "M"), ("Carlos Alcaraz", "ES", "M"), ("Daniil Medvedev", "RU", "M"),
            ("Jannik Sinner", "IT", "M"), ("Stefanos Tsitsipas", "GR", "M"), ("Alexander Zverev", "DE", "M"),
            ("Rafael Nadal", "ES", "M"), ("Casper Ruud", "NO", "M"), ("Andrey Rublev", "RU", "M"),
            ("Taylor Fritz", "US", "M"), ("Grigor Dimitrov", "BG", "M"), ("Tommy Paul", "US", "M"),
            ("Iga Swiatek", "PL", "F"), ("Aryna Sabalenka", "BY", "F"), ("Coco Gauff", "US", "F"),
            ("Elena Rybakina", "KZ", "F"), ("Jessica Pegula", "US", "F"), ("Ons Jabeur", "TN", "F"),
            ("Maria Sakkari", "GR", "F"), ("Petra Kvitova", "CZ", "F"), ("Karolina Muchova", "CZ", "F"),
            ("Madison Keys", "US", "F"), ("Elina Svitolina", "UA", "F"), ("Marketa Vondrousova", "CZ", "F")
        ]

        for name, country, gender in mock_players:
            cur.execute("INSERT OR IGNORE INTO players (name, country, gender) VALUES (?, ?, ?)",
                       (name, country, gender))

        # Mock stats
        cur.execute("SELECT id, name FROM players")
        players = cur.fetchall()

        for player_id, name in players:
            base_elo = random.randint(1600, 2100)
            ranking = random.randint(1, 150)
            wins = random.randint(15, 45)
            losses = random.randint(5, 25)

            cur.execute("""
                INSERT OR REPLACE INTO player_stats 
                (player_id, elo_rating, ranking, wins, losses, surface_win_pct_hard, 
                 surface_win_pct_clay, surface_win_pct_grass, tb_win_pct, avg_games_won, avg_games_lost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_id, base_elo, ranking, wins, losses,
                round(random.uniform(0.5, 0.8), 2),  # hard
                round(random.uniform(0.4, 0.7), 2),  # clay
                round(random.uniform(0.45, 0.75), 2), # grass
                round(random.uniform(0.6, 0.85), 2),  # tiebreak
                round(random.uniform(5.5, 7.2), 1),   # avg games won
                round(random.uniform(4.8, 6.5), 1)    # avg games lost
            ))

        conn.commit()
        conn.close()

    def populate_mock_matches(self):
        conn = self._conn()
        cur = conn.cursor()

        # Prendi giocatori esistenti
        cur.execute("SELECT id, name FROM players LIMIT 20")
        players = cur.fetchall()
        if len(players) < 4:
            conn.close()
            return

        tournaments = ["US Open", "Roland Garros", "Wimbledon", "Australian Open", "Indian Wells", "Miami Open"]
        surfaces = ["Hard", "Clay", "Grass"]
        rounds = ["R128", "R64", "R32", "R16", "QF", "SF", "F"]

        # Genera 10 match mock per oggi
        for _ in range(10):
            p1, p2 = random.sample(players, 2)
            tournament = random.choice(tournaments)
            surface = random.choice(surfaces)
            round_name = random.choice(rounds)

            # Orario oggi
            hour = random.randint(10, 22)
            minute = random.choice([0, 15, 30, 45])
            match_time = f"{datetime.now().strftime('%Y-%m-%d')}T{hour:02d}:{minute:02d}:00"

            # Quote simulate
            odds_p1 = round(random.uniform(1.2, 4.5), 2)
            odds_p2 = round(random.uniform(1.2, 4.5), 2)

            cur.execute("""
                INSERT OR IGNORE INTO matches 
                (player1_id, player2_id, tournament_name, round, surface, match_time, 
                 odds_p1, odds_p2, status, source_book)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (p1[0], p2[0], tournament, round_name, surface, match_time, 
                  odds_p1, odds_p2, "not_started", "mock"))

        conn.commit()
        conn.close()
