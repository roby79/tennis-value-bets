"""
Utilità per il caricamento ottimizzato dei dati
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional

from db import DatabaseManager
from etl_today import run_etl_today

logger = logging.getLogger(__name__)

class TennisDataLoader:
    """Classe per il caricamento ottimizzato dei dati tennis"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self._cache = {}
        self._last_update = None
    
    def load_matches_today(self, force_refresh: bool = False) -> Tuple[pd.DataFrame, Dict]:
        """
        Carica le partite del giorno con caching intelligente
        
        Args:
            force_refresh: Forza il refresh dei dati
            
        Returns:
            Tuple[DataFrame, Dict]: Partite e summary del caricamento
        """
        cache_key = f"matches_{datetime.now().strftime('%Y-%m-%d')}"
        
        # Controlla cache se non è forzato il refresh
        if not force_refresh and cache_key in self._cache:
            cache_data = self._cache[cache_key]
            cache_time = cache_data.get('timestamp', datetime.min)
            
            # Cache valida per 5 minuti
            if datetime.now() - cache_time < timedelta(minutes=5):
                logger.info("Usando dati dalla cache")
                return cache_data['matches'], cache_data['summary']
        
        try:
            logger.info("Caricamento dati freschi...")
            
            # Esegui ETL per dati aggiornati
            summary = run_etl_today(verbose=False)
            
            # Carica dal database
            matches = self.db.get_matches_today()
            
            if matches and len(matches) > 0:
                df = pd.DataFrame(matches)
                df = self._enrich_match_data(df)
                
                # Aggiorna cache
                self._cache[cache_key] = {
                    'matches': df,
                    'summary': summary,
                    'timestamp': datetime.now()
                }
                
                self._last_update = datetime.now()
                logger.info(f"Caricati {len(df)} match dal database")
                
                return df, summary
            else:
                # Fallback a dati mock
                logger.warning("Nessun match nel database, usando dati mock")
                df_mock = self._generate_realistic_mock_data()
                
                summary_mock = {
                    "events": 0,
                    "mock": True,
                    "updated": 0,
                    "with_odds": 0,
                    "skipped": 0
                }
                
                return df_mock, summary_mock
                
        except Exception as e:
            logger.error(f"Errore caricamento dati: {e}")
            
            # Fallback a dati mock in caso di errore
            df_mock = self._generate_realistic_mock_data()
            summary_error = {
                "events": 0,
                "mock": True,
                "error": str(e),
                "updated": 0,
                "with_odds": 0,
                "skipped": 0
            }
            
            return df_mock, summary_error
    
    def _enrich_match_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Arricchisce i dati delle partite con statistiche calcolate
        
        Args:
            df: DataFrame con i dati base delle partite
            
        Returns:
            DataFrame arricchito
        """
        df = df.copy()
        
        # Calcola probabilità implicite se non presenti
        if 'odds_p1' in df.columns and 'player1_prob' not in df.columns:
            df['player1_prob'] = 1 / df['odds_p1']
            df['player2_prob'] = 1 / df['odds_p2']
            
            # Normalizza probabilità
            total_prob = df['player1_prob'] + df['player2_prob']
            df['player1_prob'] = df['player1_prob'] / total_prob
            df['player2_prob'] = df['player2_prob'] / total_prob
        
        # Calcola fair odds
        if 'player1_prob' in df.columns:
            df['fair_odds_p1'] = 1 / df['player1_prob']
            df['fair_odds_p2'] = 1 / df['player2_prob']
        
        # Calcola edge
        if 'odds_p1' in df.columns and 'fair_odds_p1' in df.columns:
            df['edge_p1'] = (df['odds_p1'] / df['fair_odds_p1'] - 1).fillna(0)
            df['edge_p2'] = (df['odds_p2'] / df['fair_odds_p2'] - 1).fillna(0)
        
        # Identifica value bets
        if 'edge_p1' in df.columns:
            df['value_p1'] = df['edge_p1'] > 0.05
            df['value_p2'] = df['edge_p2'] > 0.05
        
        # Aggiungi ELO stimati se non presenti
        if 'elo_p1' not in df.columns:
            df['elo_p1'] = self._estimate_elo_from_ranking(df.get('player1_ranking', 50))
            df['elo_p2'] = self._estimate_elo_from_ranking(df.get('player2_ranking', 50))
        
        # Formatta orari
        if 'start_time' in df.columns:
            df['match_time'] = pd.to_datetime(df['start_time']).dt.strftime('%H:%M')
        
        # Aggiungi statistiche simulate se non presenti
        df = self._add_simulated_stats(df)
        
        return df
    
    def _estimate_elo_from_ranking(self, ranking):
        """Stima ELO dal ranking ATP/WTA"""
        if pd.isna(ranking):
            return 1800
        
        # Formula approssimativa: ELO = 2200 - (ranking * 8)
        elo = 2200 - (ranking * 8)
        return max(1200, min(elo, 2400))  # Limiti realistici
    
    def _add_simulated_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge statistiche simulate realistiche"""
        df = df.copy()
        
        # Seed basato sulla data per consistenza
        np.random.seed(int(datetime.now().strftime("%Y%m%d")))
        
        n_matches = len(df)
        
        # Statistiche H2H
        if 'h2h_matches' not in df.columns:
            df['h2h_matches'] = np.random.randint(0, 8, n_matches)
            df['p1_h2h_wins'] = [
                np.random.randint(0, h2h + 1) if h2h > 0 else 0 
                for h2h in df['h2h_matches']
            ]
            df['p2_h2h_wins'] = df['h2h_matches'] - df['p1_h2h_wins']
        
        # Statistiche superficie
        if 'p1_surface_wins' not in df.columns:
            df['p1_surface_wins'] = np.random.randint(5, 30, n_matches)
            df['p1_surface_losses'] = np.random.randint(2, 20, n_matches)
            df['p2_surface_wins'] = np.random.randint(5, 30, n_matches)
            df['p2_surface_losses'] = np.random.randint(2, 20, n_matches)
        
        # Forma recente
        if 'p1_recent_wins' not in df.columns:
            df['p1_recent_wins'] = np.random.randint(3, 9, n_matches)
            df['p2_recent_wins'] = np.random.randint(3, 9, n_matches)
        
        # Statistiche servizio
        if 'p1_ace_avg' not in df.columns:
            df['p1_ace_avg'] = np.round(np.random.uniform(3, 15, n_matches), 1)
            df['p2_ace_avg'] = np.round(np.random.uniform(3, 15, n_matches), 1)
            df['p1_first_serve_pct'] = np.round(np.random.uniform(55, 75, n_matches), 1)
            df['p2_first_serve_pct'] = np.round(np.random.uniform(55, 75, n_matches), 1)
        
        return df
    
    def _generate_realistic_mock_data(self) -> pd.DataFrame:
        """Genera dati mock realistici per demo"""
        np.random.seed(int(datetime.now().strftime("%Y%m%d")))
        
        # Tornei realistici per settembre 2025
        tournaments = [
            "US Open 2025", "ATP Masters 1000 Shanghai", "WTA 1000 Beijing",
            "ATP 250 Metz", "WTA 250 Seoul", "ATP 500 Tokyo",
            "WTA 500 Ostrava", "ATP Challenger Tiburon", "WTA 125 Hua Hin"
        ]
        
        # Giocatori top con ranking realistici
        players_atp = [
            ("Jannik Sinner", "ITA", 1), ("Carlos Alcaraz", "ESP", 2),
            ("Novak Djokovic", "SRB", 3), ("Daniil Medvedev", "RUS", 4),
            ("Alexander Zverev", "GER", 5), ("Andrey Rublev", "RUS", 6),
            ("Taylor Fritz", "USA", 7), ("Casper Ruud", "NOR", 8),
            ("Grigor Dimitrov", "BUL", 9), ("Alex de Minaur", "AUS", 10),
            ("Stefanos Tsitsipas", "GRE", 11), ("Tommy Paul", "USA", 12),
            ("Lorenzo Musetti", "ITA", 15), ("Matteo Berrettini", "ITA", 35),
            ("Fabio Fognini", "ITA", 45), ("Luca Nardi", "ITA", 85)
        ]
        
        players_wta = [
            ("Iga Swiatek", "POL", 1), ("Aryna Sabalenka", "BLR", 2),
            ("Coco Gauff", "USA", 3), ("Elena Rybakina", "KAZ", 4),
            ("Jessica Pegula", "USA", 5), ("Jasmine Paolini", "ITA", 6),
            ("Qinwen Zheng", "CHN", 7), ("Emma Navarro", "USA", 8),
            ("Maria Sakkari", "GRE", 9), ("Barbora Krejcikova", "CZE", 10),
            ("Danielle Collins", "USA", 11), ("Diana Shnaider", "RUS", 12),
            ("Martina Trevisan", "ITA", 25), ("Lucia Bronzetti", "ITA", 35),
            ("Elisabetta Cocciaretto", "ITA", 45)
        ]
        
        all_players = players_atp + players_wta
        
        matches_data = []
        current_time = datetime.now()
        
        for i in range(25):  # 25 partite del giorno
            # Seleziona due giocatori diversi
            p1_idx, p2_idx = np.random.choice(len(all_players), 2, replace=False)
            player1_data = all_players[p1_idx]
            player2_data = all_players[p2_idx]
            
            # Calcola quote realistiche basate sui ranking
            rank_diff = abs(player1_data[2] - player2_data[2])
            
            if player1_data[2] < player2_data[2]:  # P1 ranking migliore
                p1_odds = np.random.uniform(1.4, 2.2)
                p2_odds = np.random.uniform(2.0, 4.5)
            else:  # P2 ranking migliore
                p1_odds = np.random.uniform(2.0, 4.5)
                p2_odds = np.random.uniform(1.4, 2.2)
            
            # Aggiungi variabilità
            p1_odds *= np.random.uniform(0.9, 1.1)
            p2_odds *= np.random.uniform(0.9, 1.1)
            
            # Limiti realistici
            p1_odds = max(1.2, min(p1_odds, 6.0))
            p2_odds = max(1.2, min(p2_odds, 6.0))
            
            # Calcola probabilità
            p1_prob = 1 / p1_odds
            p2_prob = 1 / p2_odds
            total_prob = p1_prob + p2_prob
            p1_prob = p1_prob / total_prob
            p2_prob = p2_prob / total_prob
            
            # ELO
            p1_elo = self._estimate_elo_from_ranking(player1_data[2])
            p2_elo = self._estimate_elo_from_ranking(player2_data[2])
            
            # Orario partita
            match_hour = 9 + (i * 0.6) % 15  # Dalle 9 alle 24
            match_time = current_time.replace(
                hour=int(match_hour), 
                minute=int((match_hour % 1) * 60)
            )
            
            # Torneo e superficie
            tournament = np.random.choice(tournaments)
            if "US Open" in tournament or "Shanghai" in tournament:
                surface = "Hard"
            elif "French Open" in tournament or "Rome" in tournament:
                surface = "Clay"
            elif "Wimbledon" in tournament:
                surface = "Grass"
            else:
                surface = np.random.choice(["Hard", "Clay"], p=[0.75, 0.25])
            
            # Value bet calculation
            fair_odds_p1 = 1 / p1_prob
            fair_odds_p2 = 1 / p2_prob
            
            edge_p1 = (p1_odds / fair_odds_p1 - 1)
            edge_p2 = (p2_odds / fair_odds_p2 - 1)
            
            matches_data.append({
                'match_id': f"mock_{i}",
                'tournament': tournament,
                'round': np.random.choice(["R64", "R32", "R16", "QF", "SF", "F"], 
                                        p=[0.3, 0.25, 0.2, 0.15, 0.08, 0.02]),
                'surface': surface,
                'player1': player1_data[0],
                'player2': player2_data[0],
                'player1_country': player1_data[1],
                'player2_country': player2_data[1],
                'player1_ranking': player1_data[2],
                'player2_ranking': player2_data[2],
                'odds_p1': round(p1_odds, 2),
                'odds_p2': round(p2_odds, 2),
                'player1_prob': round(p1_prob, 3),
                'player2_prob': round(p2_prob, 3),
                'fair_odds_p1': round(fair_odds_p1, 2),
                'fair_odds_p2': round(fair_odds_p2, 2),
                'edge_p1': round(edge_p1, 3),
                'edge_p2': round(edge_p2, 3),
                'elo_p1': p1_elo,
                'elo_p2': p2_elo,
                'match_time': match_time.strftime("%H:%M"),
                'start_time': match_time.isoformat(),
                'value_p1': edge_p1 > 0.05,
                'value_p2': edge_p2 > 0.05,
            })
        
        df = pd.DataFrame(matches_data)
        return self._add_simulated_stats(df)
    
    def clear_cache(self):
        """Pulisce la cache"""
        self._cache.clear()
        logger.info("Cache pulita")
    
    def get_cache_info(self) -> Dict:
        """Restituisce informazioni sulla cache"""
        return {
            'cache_size': len(self._cache),
            'last_update': self._last_update,
            'cache_keys': list(self._cache.keys())
        }
