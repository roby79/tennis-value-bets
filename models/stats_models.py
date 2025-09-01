
"""
Modelli estesi per statistiche dettagliate delle partite di tennis
"""
import sqlite3
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np

class TennisStatsDatabase:
    """Database manager esteso per statistiche complete"""
    
    def __init__(self, db_path="data/tennis_stats.db"):
        self.db_path = db_path
        self.init_extended_database()
    
    def _conn(self):
        return sqlite3.connect(self.db_path)
    
    def init_extended_database(self):
        """Inizializza database con tabelle per statistiche complete"""
        conn = self._conn()
        cur = conn.cursor()
        
        # Tabella statistiche dettagliate giocatori
        cur.execute("""
        CREATE TABLE IF NOT EXISTS player_detailed_stats (
            player_id INTEGER PRIMARY KEY,
            -- Ranking e rating
            atp_ranking INTEGER,
            wta_ranking INTEGER,
            elo_rating REAL DEFAULT 1800,
            peak_ranking INTEGER,
            weeks_at_no1 INTEGER DEFAULT 0,
            
            -- Statistiche generali
            career_wins INTEGER DEFAULT 0,
            career_losses INTEGER DEFAULT 0,
            career_titles INTEGER DEFAULT 0,
            career_prize_money REAL DEFAULT 0,
            
            -- Forma recente (ultimi 10 match)
            recent_wins INTEGER DEFAULT 0,
            recent_losses INTEGER DEFAULT 0,
            recent_form_rating REAL DEFAULT 0,
            
            -- Statistiche per superficie
            hard_wins INTEGER DEFAULT 0,
            hard_losses INTEGER DEFAULT 0,
            clay_wins INTEGER DEFAULT 0,
            clay_losses INTEGER DEFAULT 0,
            grass_wins INTEGER DEFAULT 0,
            grass_losses INTEGER DEFAULT 0,
            
            -- Statistiche di servizio
            avg_first_serve_pct REAL,
            avg_first_serve_won_pct REAL,
            avg_second_serve_won_pct REAL,
            avg_aces_per_match REAL,
            avg_double_faults_per_match REAL,
            avg_service_games_won_pct REAL,
            avg_break_points_saved_pct REAL,
            
            -- Statistiche di risposta
            avg_first_return_won_pct REAL,
            avg_second_return_won_pct REAL,
            avg_break_points_converted_pct REAL,
            avg_return_games_won_pct REAL,
            
            -- Statistiche di gioco
            avg_winners_per_match REAL,
            avg_unforced_errors_per_match REAL,
            avg_net_points_won_pct REAL,
            avg_total_points_won_pct REAL,
            
            -- Metriche avanzate
            dominance_ratio REAL,
            pressure_points_won_pct REAL,
            momentum_score REAL,
            
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
        """)
        
        # Tabella statistiche dettagliate partite
        cur.execute("""
        CREATE TABLE IF NOT EXISTS match_detailed_stats (
            match_id INTEGER PRIMARY KEY,
            
            -- Statistiche Player 1
            p1_first_serve_pct REAL,
            p1_first_serve_won_pct REAL,
            p1_second_serve_won_pct REAL,
            p1_aces INTEGER,
            p1_double_faults INTEGER,
            p1_service_games_won INTEGER,
            p1_service_games_total INTEGER,
            p1_break_points_saved INTEGER,
            p1_break_points_faced INTEGER,
            
            p1_first_return_won_pct REAL,
            p1_second_return_won_pct REAL,
            p1_break_points_converted INTEGER,
            p1_break_points_opportunities INTEGER,
            p1_return_games_won INTEGER,
            p1_return_games_total INTEGER,
            
            p1_winners INTEGER,
            p1_unforced_errors INTEGER,
            p1_net_points_won INTEGER,
            p1_net_points_total INTEGER,
            p1_total_points_won INTEGER,
            p1_total_points_total INTEGER,
            
            -- Statistiche Player 2 (stesso schema)
            p2_first_serve_pct REAL,
            p2_first_serve_won_pct REAL,
            p2_second_serve_won_pct REAL,
            p2_aces INTEGER,
            p2_double_faults INTEGER,
            p2_service_games_won INTEGER,
            p2_service_games_total INTEGER,
            p2_break_points_saved INTEGER,
            p2_break_points_faced INTEGER,
            
            p2_first_return_won_pct REAL,
            p2_second_return_won_pct REAL,
            p2_break_points_converted INTEGER,
            p2_break_points_opportunities INTEGER,
            p2_return_games_won INTEGER,
            p2_return_games_total INTEGER,
            
            p2_winners INTEGER,
            p2_unforced_errors INTEGER,
            p2_net_points_won INTEGER,
            p2_net_points_total INTEGER,
            p2_total_points_won INTEGER,
            p2_total_points_total INTEGER,
            
            -- Metriche avanzate partita
            p1_dominance_ratio REAL,
            p2_dominance_ratio REAL,
            p1_momentum_score REAL,
            p2_momentum_score REAL,
            match_quality_score REAL,
            
            -- Durata e info partita
            match_duration_minutes INTEGER,
            sets_played INTEGER,
            total_games INTEGER,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(match_id) REFERENCES matches(id)
        )
        """)
        
        # Tabella head-to-head
        cur.execute("""
        CREATE TABLE IF NOT EXISTS head_to_head (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id INTEGER,
            player2_id INTEGER,
            total_matches INTEGER DEFAULT 0,
            player1_wins INTEGER DEFAULT 0,
            player2_wins INTEGER DEFAULT 0,
            
            -- Per superficie
            hard_matches INTEGER DEFAULT 0,
            hard_p1_wins INTEGER DEFAULT 0,
            clay_matches INTEGER DEFAULT 0,
            clay_p1_wins INTEGER DEFAULT 0,
            grass_matches INTEGER DEFAULT 0,
            grass_p1_wins INTEGER DEFAULT 0,
            
            last_match_date DATE,
            last_winner_id INTEGER,
            
            UNIQUE(player1_id, player2_id),
            FOREIGN KEY(player1_id) REFERENCES players(id),
            FOREIGN KEY(player2_id) REFERENCES players(id),
            FOREIGN KEY(last_winner_id) REFERENCES players(id)
        )
        """)
        
        # Tabella trend storici
        cur.execute("""
        CREATE TABLE IF NOT EXISTS historical_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            date DATE,
            ranking INTEGER,
            elo_rating REAL,
            form_rating REAL,
            surface TEXT,
            tournament_level TEXT,
            
            -- Performance metrics del periodo
            matches_played INTEGER,
            wins INTEGER,
            losses INTEGER,
            win_percentage REAL,
            
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
        """)
        
        # Tabella performance per torneo
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tournament_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            tournament_name TEXT,
            year INTEGER,
            surface TEXT,
            level TEXT,
            
            matches_played INTEGER,
            wins INTEGER,
            losses INTEGER,
            best_result TEXT,
            prize_money REAL,
            
            -- Statistiche aggregate del torneo
            avg_first_serve_pct REAL,
            avg_aces_per_match REAL,
            avg_winners_per_match REAL,
            avg_unforced_errors_per_match REAL,
            
            UNIQUE(player_id, tournament_name, year),
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
        """)
        
        # Indici per performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_player_stats_ranking ON player_detailed_stats(atp_ranking, wta_ranking)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_match_stats_match ON match_detailed_stats(match_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_h2h_players ON head_to_head(player1_id, player2_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_trends_player_date ON historical_trends(player_id, date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tournament_perf ON tournament_performance(player_id, tournament_name, year)")
        
        conn.commit()
        conn.close()
    
    def calculate_dominance_ratio(self, return_points_won_pct: float, service_points_lost_pct: float) -> float:
        """
        Calcola Dominance Ratio: (% punti vinti in risposta) / (% punti persi al servizio)
        DR > 1.0 indica dominanza
        """
        if service_points_lost_pct == 0:
            return float('inf') if return_points_won_pct > 0 else 1.0
        return return_points_won_pct / service_points_lost_pct
    
    def calculate_momentum_score(self, recent_points: List[bool], leverage_weights: List[float] = None) -> float:
        """
        Calcola Momentum Score basato su punti recenti vinti/persi
        Usa exponentially weighted moving average con leverage
        """
        if not recent_points:
            return 0.5
        
        if leverage_weights is None:
            # Pesi decrescenti esponenziali (più recente = più importante)
            leverage_weights = [0.5 ** i for i in range(len(recent_points))]
        
        weighted_sum = sum(point * weight for point, weight in zip(recent_points, leverage_weights))
        total_weight = sum(leverage_weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def update_player_detailed_stats(self, player_id: int, stats: Dict[str, Any]):
        """Aggiorna statistiche dettagliate giocatore"""
        conn = self._conn()
        cur = conn.cursor()
        
        # Costruisce query dinamica basata sui campi forniti
        fields = list(stats.keys())
        placeholders = ', '.join([f"{field} = ?" for field in fields])
        values = list(stats.values()) + [player_id]
        
        cur.execute(f"""
            INSERT OR REPLACE INTO player_detailed_stats (player_id, {', '.join(fields)})
            VALUES (?, {', '.join(['?' for _ in fields])})
            ON CONFLICT(player_id) DO UPDATE SET {placeholders}, last_updated = CURRENT_TIMESTAMP
        """, [player_id] + list(stats.values()) + list(stats.values()))
        
        conn.commit()
        conn.close()
    
    def get_player_detailed_stats(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Recupera statistiche dettagliate giocatore"""
        conn = self._conn()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM player_detailed_stats WHERE player_id = ?", (player_id,))
        row = cur.fetchone()
        
        if row:
            columns = [desc[0] for desc in cur.description]
            conn.close()
            return dict(zip(columns, row))
        
        conn.close()
        return None
    
    def get_head_to_head(self, player1_id: int, player2_id: int) -> Dict[str, Any]:
        """Recupera statistiche head-to-head tra due giocatori"""
        conn = self._conn()
        cur = conn.cursor()
        
        # Cerca in entrambe le direzioni
        cur.execute("""
            SELECT * FROM head_to_head 
            WHERE (player1_id = ? AND player2_id = ?) OR (player1_id = ? AND player2_id = ?)
        """, (player1_id, player2_id, player2_id, player1_id))
        
        row = cur.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, row))
        
        # Nessun head-to-head trovato
        return {
            'total_matches': 0,
            'player1_wins': 0,
            'player2_wins': 0,
            'hard_matches': 0,
            'clay_matches': 0,
            'grass_matches': 0
        }
    
    def get_player_form(self, player_id: int, days: int = 90) -> Dict[str, Any]:
        """Calcola forma recente del giocatore negli ultimi N giorni"""
        conn = self._conn()
        cur = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cur.execute("""
            SELECT COUNT(*) as matches,
                   SUM(CASE WHEN (player1_id = ? AND winner_id = ?) OR (player2_id = ? AND winner_id = ?) THEN 1 ELSE 0 END) as wins
            FROM matches 
            WHERE (player1_id = ? OR player2_id = ?) 
            AND date(match_time) >= ?
            AND status = 'completed'
        """, (player_id, player_id, player_id, player_id, player_id, player_id, cutoff_date))
        
        row = cur.fetchone()
        conn.close()
        
        matches = row[0] if row[0] else 0
        wins = row[1] if row[1] else 0
        losses = matches - wins
        
        win_pct = wins / matches if matches > 0 else 0
        
        return {
            'matches': matches,
            'wins': wins,
            'losses': losses,
            'win_percentage': win_pct,
            'form_rating': win_pct * 100  # Rating 0-100
        }
