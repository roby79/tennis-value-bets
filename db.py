import sqlite3
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
