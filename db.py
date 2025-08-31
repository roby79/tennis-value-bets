import sqlite3
from typing import Optional, List, Dict

class DatabaseManager:
    def __init__(self, db_path="data/tennis.db"):
        self.db_path = db_path
        self.init_database()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    def init_database(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    country TEXT,
                    birth_date DATE,
                    hand TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS player_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER UNIQUE,
                    elo_rating REAL DEFAULT 1500,
                    ranking INTEGER,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    surface_win_pct_hard REAL,
                    surface_win_pct_clay REAL,
                    surface_win_pct_grass REAL,
                    tb_win_pct REAL,
                    avg_games_won REAL,
                    avg_games_lost REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    surface TEXT,
                    category TEXT,
                    start_date DATE,
                    end_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, start_date, end_date)
                );

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
                    FOREIGN KEY (tournament_id) REFERENCES tournaments (id) ON DELETE CASCADE,
                    FOREIGN KEY (player1_id) REFERENCES players (id) ON DELETE CASCADE,
                    FOREIGN KEY (player2_id) REFERENCES players (id) ON DELETE CASCADE,
                    FOREIGN KEY (winner_id) REFERENCES players (id)
                );

                CREATE TABLE IF NOT EXISTS markets (
                    id TEXT PRIMARY KEY,
                    match_id INTEGER,
                    market_name TEXT,
                    market_type TEXT,
                    status TEXT,
                    total_matched REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS runners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT,
                    runner_name TEXT,
                    selection_id INTEGER,
                    handicap REAL DEFAULT 0,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(market_id, selection_id),
                    FOREIGN KEY (market_id) REFERENCES markets (id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    runner_id INTEGER,
                    back_price REAL,
                    lay_price REAL,
                    back_size REAL,
                    lay_size REAL,
                    total_matched REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (runner_id) REFERENCES runners (id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_matches_time ON matches(match_time);
                CREATE INDEX IF NOT EXISTS idx_matches_players ON matches(player1_id, player2_id);
                CREATE INDEX IF NOT EXISTS idx_markets_match ON markets(match_id);
                CREATE INDEX IF NOT EXISTS idx_runners_market ON runners(market_id);
                CREATE INDEX IF NOT EXISTS idx_prices_runner ON prices(runner_id);
            """)
            conn.commit()

    def get_player_by_name(self, name: str) -> Optional[int]:
        with self._connect() as conn:
            row = conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()
            return row[0] if row else None

    def insert_player(self, name: str, country: Optional[str] = None) -> int:
        existing = self.get_player_by_name(name)
        if existing:
            return existing
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO players (name, country) VALUES (?, ?)",
                (name, country)
            )
            conn.commit()
            return cur.lastrowid

    def get_player_stats(self, player_id: int) -> Optional[Dict]:
        if not player_id:
            return None
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM player_stats WHERE player_id = ?",
                (player_id,)
            ).fetchone()
            return dict(row) if row else None

    def insert_player_stats(self, player_id: int, elo_rating: float = 1500,
                            ranking: Optional[int] = None, wins: int = 0, losses: int = 0,
                            surface_win_pct_hard: Optional[float] = None,
                            surface_win_pct_clay: Optional[float] = None,
                            surface_win_pct_grass: Optional[float] = None,
                            tb_win_pct: Optional[float] = None,
                            avg_games_won: Optional[float] = None,
                            avg_games_lost: Optional[float] = None) -> None:
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO player_stats (
                    player_id, elo_rating, ranking, wins, losses,
                    surface_win_pct_hard, surface_win_pct_clay, surface_win_pct_grass,
                    tb_win_pct, avg_games_won, avg_games_lost, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(player_id) DO UPDATE SET
                    elo_rating=excluded.elo_rating,
                    ranking=excluded.ranking,
                    wins=excluded.wins,
                    losses=excluded.losses,
                    surface_win_pct_hard=COALESCE(excluded.surface_win_pct_hard, player_stats.surface_win_pct_hard),
                    surface_win_pct_clay=COALESCE(excluded.surface_win_pct_clay, player_stats.surface_win_pct_clay),
                    surface_win_pct_grass=COALESCE(excluded.surface_win_pct_grass, player_stats.surface_win_pct_grass),
                    tb_win_pct=COALESCE(excluded.tb_win_pct, player_stats.tb_win_pct),
                    avg_games_won=COALESCE(excluded.avg_games_won, player_stats.avg_games_won),
                    avg_games_lost=COALESCE(excluded.avg_games_lost, player_stats.avg_games_lost),
                    last_updated=CURRENT_TIMESTAMP
            """, (
                player_id, elo_rating, ranking, wins, losses,
                surface_win_pct_hard, surface_win_pct_clay, surface_win_pct_grass,
                tb_win_pct, avg_games_won, avg_games_lost
            ))
            conn.commit()

    def get_tournament(self, name: str, start_date: Optional[datetime.date] = None,
                       end_date: Optional[datetime.date] = None) -> Optional[int]:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT id FROM tournaments
                WHERE name = ? AND (start_date IS ? OR start_date = ?)
                                  AND (end_date IS ? OR end_date = ?)
            """, (name, start_date, start_date, end_date, end_date)).fetchone()
            return row[0] if row else None

    def insert_tournament(self, name: str, surface: Optional[str] = None,
                          category: Optional[str] = None,
                          start_date: Optional[datetime.date] = None,
                          end_date: Optional[datetime.date] = None) -> int:
        start_date = start_date or datetime.now().date()
        end_date = end_date or (start_date + timedelta(days=7))
        existing = self.get_tournament(name, start_date, end_date)
        if existing:
            return existing
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT INTO tournaments (name, surface, category, start_date, end_date)
                VALUES (?, ?, ?, ?, ?)
            """, (name, surface, category, start_date, end_date))
            conn.commit()
            return cur.lastrowid

    def insert_match(self, tournament_id: int, player1_id: int, player2_id: int,
                     match_time: datetime, round_name: str = "R1",
                     status: str = "scheduled") -> int:
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT INTO matches (tournament_id, player1_id, player2_id, match_time, round, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tournament_id, player1_id, player2_id, match_time, round_name, status))
            conn.commit()
            return cur.lastrowid

    def delete_today_matches(self):
        today = datetime.now().date()
        with self._connect() as conn:
            conn.execute("DELETE FROM matches WHERE DATE(match_time) = ?", (today,))
            conn.commit()

    def get_today_matches(self) -> List[Dict]:
        today = datetime.now().date()
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT m.id, m.tournament_id, m.player1_id, m.player2_id, 
                       m.match_time, m.round, m.status,
                       t.name AS tournament_name,
                       p1.name AS player1_name, p2.name AS player2_name
                FROM matches m
                JOIN tournaments t ON m.tournament_id = t.id
                JOIN players p1 ON m.player1_id = p1.id
                JOIN players p2 ON m.player2_id = p2.id
                WHERE DATE(m.match_time) = ?
                ORDER BY m.match_time
            """, (today,)).fetchall()
            return [dict(r) for r in rows]

    def insert_market(self, market_id: str, match_id: int, market_name: str,
                      market_type: str, status: str = "OPEN",
                      total_matched: Optional[float] = 0.0) -> str:
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO markets (id, match_id, market_name, market_type, status, total_matched)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    match_id=excluded.match_id,
                    market_name=excluded.market_name,
                    market_type=excluded.market_type,
                    status=excluded.status,
                    total_matched=COALESCE(excluded.total_matched, markets.total_matched)
            """, (market_id, match_id, market_name, market_type, status, total_matched))
            conn.commit()
            return market_id

    def insert_runner(self, market_id: str, runner_name: str, selection_id: int,
                      handicap: float = 0.0, status: str = "ACTIVE") -> int:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT id FROM runners WHERE market_id = ? AND selection_id = ?
            """, (market_id, selection_id)).fetchone()
            if row:
                return row[0]
            cur = conn.execute("""
                INSERT INTO runners (market_id, runner_name, selection_id, handicap, status)
                VALUES (?, ?, ?, ?, ?)
            """, (market_id, runner_name, selection_id, handicap, status))
            conn.commit()
            return cur.lastrowid

    def insert_price(self, runner_id: int,
                     back_price: Optional[float],
                     lay_price: Optional[float],
                     back_size: Optional[float],
                     lay_size: Optional[float],
                     total_matched: Optional[float]) -> int:
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT INTO prices (runner_id, back_price, lay_price, back_size, lay_size, total_matched, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (runner_id, back_price, lay_price, back_size, lay_size, total_matched))
            conn.commit()
            return cur.lastrowid

    def get_all_players_with_stats(self) -> List[Dict]:
        with self._connect() as conn:
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
            return [dict(r) for r in rows]

    def populate_mock_data(self):
        """Popola il database con dati di esempio per testing"""
        import random
        
        # Mock players
        mock_players = [
            ("Novak Djokovic", "SRB"), ("Rafael Nadal", "ESP"), ("Roger Federer", "SUI"),
            ("Daniil Medvedev", "RUS"), ("Alexander Zverev", "GER"), ("Stefanos Tsitsipas", "GRE"),
            ("Andrey Rublev", "RUS"), ("Matteo Berrettini", "ITA"), ("Hubert Hurkacz", "POL"),
            ("Jannik Sinner", "ITA"), ("Iga Swiatek", "POL"), ("Aryna Sabalenka", "BLR"),
            ("Jessica Pegula", "USA"), ("Elena Rybakina", "KAZ"), ("Caroline Garcia", "FRA"),
            ("Coco Gauff", "USA"), ("Maria Sakkari", "GRE"), ("Petra Kvitova", "CZE"),
            ("Belinda Bencic", "SUI"), ("Karolina Pliskova", "CZE")
        ]
        
        for name, country in mock_players:
            player_id = self.insert_player(name, country)
            
            # Mock stats
            elo = random.randint(1400, 2200)
            ranking = random.randint(1, 100)
            wins = random.randint(15, 45)
            losses = random.randint(5, 25)
            
            self.insert_player_stats(
                player_id, elo, ranking, wins, losses,
                surface_win_pct_hard=random.uniform(0.5, 0.8),
                surface_win_pct_clay=random.uniform(0.4, 0.75),
                surface_win_pct_grass=random.uniform(0.45, 0.7),
                tb_win_pct=random.uniform(0.4, 0.7),
                avg_games_won=random.uniform(5.5, 7.2),
                avg_games_lost=random.uniform(4.8, 6.5)
            )
        
        print("✅ Mock data populated successfully!")
