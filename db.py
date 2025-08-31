import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict

class DatabaseManager:
    def __init__(self, db_path="data/tennis.db"):
        os.makedirs("data", exist_ok=True)   # crea la cartella se non esiste
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Tabella giocatori
        cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT,
            gender TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tabella statistiche giocatori
        cur.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            elo_rating REAL,
            ranking INTEGER,
            wins INTEGER,
            losses INTEGER,
            surface_win_pct_hard REAL,
            surface_win_pct_clay REAL,
            surface_win_pct_grass REAL,
            tb_win_pct REAL,
            avg_games_won REAL,
            avg_games_lost REAL,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
        """)

        # Tabella partite
        cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_name TEXT,
            player1_id INTEGER,
            player2_id INTEGER,
            match_time TIMESTAMP,
            round TEXT,
            surface TEXT,
            odds_p1 REAL,
            odds_p2 REAL,
            status TEXT,
            FOREIGN KEY (player1_id) REFERENCES players (id),
            FOREIGN KEY (player2_id) REFERENCES players (id)
        )
        """)

        conn.commit()
        conn.close()

    # -------------------
    # Mock data giocatori
    # -------------------
    def populate_mock_data(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Cancello giocatori e stats
        cur.execute("DELETE FROM player_stats")
        cur.execute("DELETE FROM players")
        conn.commit()

        players = [
            ("Novak Djokovic", "SRB", "M"),
            ("Rafael Nadal", "ESP", "M"),
            ("Roger Federer", "SUI", "M"),
            ("Carlos Alcaraz", "ESP", "M"),
            ("Jannik Sinner", "ITA", "M"),
            ("Matteo Berrettini", "ITA", "M"),
            ("Iga Swiatek", "POL", "F"),
            ("Cori Gauff", "USA", "F"),
            ("Aryna Sabalenka", "BLR", "F"),
            ("Naomi Osaka", "JPN", "F"),
        ]

        import random
        for name, country, gender in players:
            cur.execute("INSERT INTO players (name, country, gender) VALUES (?, ?, ?)",
                        (name, country, gender))
            player_id = cur.lastrowid
            cur.execute("""
                INSERT INTO player_stats (
                    player_id, elo_rating, ranking, wins, losses, 
                    surface_win_pct_hard, surface_win_pct_clay, surface_win_pct_grass,
                    tb_win_pct, avg_games_won, avg_games_lost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_id,
                random.randint(1600, 2300),
                random.randint(1, 100),
                random.randint(50, 300),
                random.randint(50, 200),
                round(random.uniform(50, 90), 1),
                round(random.uniform(40, 85), 1),
                round(random.uniform(30, 80), 1),
                round(random.uniform(40, 80), 1),
                round(random.uniform(5, 12), 1),
                round(random.uniform(3, 10), 1),
            ))

        conn.commit()
        conn.close()

    # -------------------
    # Giocatori
    # -------------------
    def get_all_players_with_stats(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT p.name, p.country,
                   ps.elo_rating, ps.ranking, ps.wins, ps.losses,
                   ps.surface_win_pct_hard, ps.surface_win_pct_clay, ps.surface_win_pct_grass,
                   ps.tb_win_pct, ps.avg_games_won, ps.avg_games_lost
            FROM players p
            LEFT JOIN player_stats ps ON p.id = ps.player_id
            ORDER BY COALESCE(ps.elo_rating, 0) DESC, p.name ASC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # -------------------
    # Partite
    # -------------------
    def get_today_matches(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        today = datetime.now().strftime("%Y-%m-%d")
        rows = conn.execute("""
            SELECT m.tournament_name, m.match_time, m.round, m.surface,
                   m.odds_p1, m.odds_p2,
                   p1.name as player1_name, p2.name as player2_name
            FROM matches m
            JOIN players p1 ON m.player1_id = p1.id
            JOIN players p2 ON m.player2_id = p2.id
            WHERE date(m.match_time) = ?
            ORDER BY m.match_time ASC
        """, (today,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # -------------------
    # POPOLAZIONE PARTITE MOCK
    # -------------------
    def populate_mock_matches(self):
        """Genera partite mock con quote simulate per testing"""
        import random
        from datetime import timedelta

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Cancella matches vecchi
        cur.execute("DELETE FROM matches")
        conn.commit()

        # Prendi giocatori
        players = cur.execute("SELECT id, name FROM players").fetchall()
        if len(players) < 4:
            conn.close()
            return

        tournaments = [
            "US Open", "Roland Garros", "Wimbledon",
            "Australian Open", "Indian Wells", "Miami Open",
            "Monte Carlo", "Madrid", "Rome Masters"
        ]
        rounds = ["R1", "R2", "Ottavi", "Quarti", "Semifinale", "Finale"]

        num_matches = random.randint(6, 10)

        for _ in range(num_matches):
            p1, p2 = random.sample(players, 2)
            match_time = datetime.now() + timedelta(hours=random.randint(1, 18))

            odds_p1 = round(random.uniform(1.2, 4.5), 2)
            odds_p2 = round(random.uniform(1.2, 4.5), 2)
            surface = random.choice(["Hard", "Clay", "Grass"])

            cur.execute("""
                INSERT INTO matches (
                    tournament_name, player1_id, player2_id, match_time,
                    round, surface, odds_p1, odds_p2, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                random.choice(tournaments),
                p1[0], p2[0],
                match_time.strftime("%Y-%m-%d %H:%M:%S"),
                random.choice(rounds),
                surface, odds_p1, odds_p2,
                "scheduled"
            ))

        conn.commit()
        conn.close()
        print(f"✅ Generate {num_matches} partite mock con quote simulate")
