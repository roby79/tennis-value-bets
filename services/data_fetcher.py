
"""
Servizio per raccogliere dati statistici da fonti esterne
"""
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import time
import random
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TennisDataFetcher:
    """Fetcher per dati tennis da multiple fonti"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # secondi tra richieste
    
    def _rate_limit(self):
        """Implementa rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_atp_rankings(self) -> List[Dict[str, Any]]:
        """
        Simula fetch ranking ATP (in produzione userebbe API reale)
        """
        logger.info("Fetching ATP rankings...")
        
        # Dati mock per demo - in produzione sostituire con API reale
        mock_rankings = [
            {"rank": 1, "name": "Novak Djokovic", "country": "SRB", "points": 9945},
            {"rank": 2, "name": "Carlos Alcaraz", "country": "ESP", "points": 8805},
            {"rank": 3, "name": "Daniil Medvedev", "country": "RUS", "points": 7105},
            {"rank": 4, "name": "Jannik Sinner", "country": "ITA", "points": 6490},
            {"rank": 5, "name": "Stefanos Tsitsipas", "country": "GRE", "points": 5770},
            {"rank": 6, "name": "Alexander Zverev", "country": "GER", "points": 5040},
            {"rank": 7, "name": "Rafael Nadal", "country": "ESP", "points": 4810},
            {"rank": 8, "name": "Casper Ruud", "country": "NOR", "points": 4735},
            {"rank": 9, "name": "Andrey Rublev", "country": "RUS", "points": 4200},
            {"rank": 10, "name": "Taylor Fritz", "country": "USA", "points": 3995},
        ]
        
        # Aggiungi più giocatori con ranking realistici
        for i in range(11, 101):
            points = max(1000, 4000 - (i * 30) + random.randint(-200, 200))
            mock_rankings.append({
                "rank": i,
                "name": f"Player {i}",
                "country": random.choice(["USA", "ESP", "FRA", "ITA", "GER", "RUS", "ARG"]),
                "points": points
            })
        
        return mock_rankings
    
    def fetch_wta_rankings(self) -> List[Dict[str, Any]]:
        """Simula fetch ranking WTA"""
        logger.info("Fetching WTA rankings...")
        
        mock_rankings = [
            {"rank": 1, "name": "Iga Swiatek", "country": "POL", "points": 9340},
            {"rank": 2, "name": "Aryna Sabalenka", "country": "BLR", "points": 7881},
            {"rank": 3, "name": "Coco Gauff", "country": "USA", "points": 6743},
            {"rank": 4, "name": "Elena Rybakina", "country": "KAZ", "points": 5871},
            {"rank": 5, "name": "Jessica Pegula", "country": "USA", "points": 5205},
            {"rank": 6, "name": "Ons Jabeur", "country": "TUN", "points": 4748},
            {"rank": 7, "name": "Maria Sakkari", "country": "GRE", "points": 4190},
            {"rank": 8, "name": "Petra Kvitova", "country": "CZE", "points": 3971},
            {"rank": 9, "name": "Karolina Muchova", "country": "CZE", "points": 3685},
            {"rank": 10, "name": "Madison Keys", "country": "USA", "points": 3450},
        ]
        
        for i in range(11, 101):
            points = max(800, 3500 - (i * 25) + random.randint(-150, 150))
            mock_rankings.append({
                "rank": i,
                "name": f"WTA Player {i}",
                "country": random.choice(["USA", "ESP", "FRA", "ITA", "GER", "RUS", "POL", "CZE"]),
                "points": points
            })
        
        return mock_rankings
    
    def fetch_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Simula fetch statistiche dettagliate giocatore
        In produzione userebbe API come Ultimate Tennis Statistics
        """
        logger.info(f"Fetching stats for {player_name}")
        
        # Statistiche mock realistiche
        stats = {
            # Servizio
            "avg_first_serve_pct": round(random.uniform(55, 75), 1),
            "avg_first_serve_won_pct": round(random.uniform(65, 85), 1),
            "avg_second_serve_won_pct": round(random.uniform(45, 65), 1),
            "avg_aces_per_match": round(random.uniform(3, 15), 1),
            "avg_double_faults_per_match": round(random.uniform(1, 5), 1),
            "avg_service_games_won_pct": round(random.uniform(75, 95), 1),
            "avg_break_points_saved_pct": round(random.uniform(55, 75), 1),
            
            # Risposta
            "avg_first_return_won_pct": round(random.uniform(25, 45), 1),
            "avg_second_return_won_pct": round(random.uniform(45, 65), 1),
            "avg_break_points_converted_pct": round(random.uniform(35, 55), 1),
            "avg_return_games_won_pct": round(random.uniform(15, 35), 1),
            
            # Gioco generale
            "avg_winners_per_match": round(random.uniform(20, 50), 1),
            "avg_unforced_errors_per_match": round(random.uniform(15, 40), 1),
            "avg_net_points_won_pct": round(random.uniform(60, 80), 1),
            "avg_total_points_won_pct": round(random.uniform(48, 55), 1),
            
            # Superfici
            "hard_wins": random.randint(15, 45),
            "hard_losses": random.randint(5, 25),
            "clay_wins": random.randint(10, 35),
            "clay_losses": random.randint(8, 30),
            "grass_wins": random.randint(3, 15),
            "grass_losses": random.randint(2, 12),
            
            # Carriera
            "career_wins": random.randint(100, 800),
            "career_losses": random.randint(80, 400),
            "career_titles": random.randint(0, 25),
            "career_prize_money": random.randint(500000, 50000000),
        }
        
        # Calcola metriche derivate
        total_service_points_won = (stats["avg_first_serve_pct"] * stats["avg_first_serve_won_pct"] + 
                                   (100 - stats["avg_first_serve_pct"]) * stats["avg_second_serve_won_pct"]) / 100
        service_points_lost_pct = 100 - total_service_points_won
        return_points_won_pct = (stats["avg_first_return_won_pct"] + stats["avg_second_return_won_pct"]) / 2
        
        stats["dominance_ratio"] = round(return_points_won_pct / service_points_lost_pct if service_points_lost_pct > 0 else 1.0, 3)
        stats["pressure_points_won_pct"] = round(random.uniform(45, 65), 1)
        stats["momentum_score"] = round(random.uniform(0.3, 0.7), 3)
        
        return stats
    
    def fetch_match_stats(self, match_id: str) -> Dict[str, Any]:
        """
        Simula fetch statistiche dettagliate partita
        """
        logger.info(f"Fetching match stats for {match_id}")
        
        # Genera statistiche realistiche per entrambi i giocatori
        p1_stats = self._generate_match_player_stats()
        p2_stats = self._generate_match_player_stats()
        
        # Assicura coerenza (totali devono combaciare)
        total_games = p1_stats["service_games_total"] + p2_stats["service_games_total"]
        match_duration = random.randint(90, 240)  # minuti
        
        return {
            **{f"p1_{k}": v for k, v in p1_stats.items()},
            **{f"p2_{k}": v for k, v in p2_stats.items()},
            "match_duration_minutes": match_duration,
            "sets_played": random.choice([2, 3, 4, 5]),
            "total_games": total_games,
            "match_quality_score": round(random.uniform(6.5, 9.5), 1)
        }
    
    def _generate_match_player_stats(self) -> Dict[str, Any]:
        """Genera statistiche realistiche per un giocatore in una partita"""
        service_games = random.randint(8, 15)
        return_games = random.randint(8, 15)
        
        return {
            "first_serve_pct": round(random.uniform(55, 75), 1),
            "first_serve_won_pct": round(random.uniform(65, 85), 1),
            "second_serve_won_pct": round(random.uniform(45, 65), 1),
            "aces": random.randint(0, 20),
            "double_faults": random.randint(0, 8),
            "service_games_won": random.randint(int(service_games * 0.6), service_games),
            "service_games_total": service_games,
            "break_points_saved": random.randint(0, 10),
            "break_points_faced": random.randint(0, 15),
            
            "first_return_won_pct": round(random.uniform(25, 45), 1),
            "second_return_won_pct": round(random.uniform(45, 65), 1),
            "break_points_converted": random.randint(0, 8),
            "break_points_opportunities": random.randint(0, 12),
            "return_games_won": random.randint(0, int(return_games * 0.4)),
            "return_games_total": return_games,
            
            "winners": random.randint(10, 60),
            "unforced_errors": random.randint(8, 50),
            "net_points_won": random.randint(5, 25),
            "net_points_total": random.randint(8, 35),
            "total_points_won": random.randint(60, 120),
            "total_points_total": random.randint(120, 200),
        }
    
    def fetch_head_to_head(self, player1: str, player2: str) -> Dict[str, Any]:
        """Simula fetch head-to-head tra due giocatori"""
        logger.info(f"Fetching H2H: {player1} vs {player2}")
        
        total_matches = random.randint(0, 15)
        p1_wins = random.randint(0, total_matches)
        p2_wins = total_matches - p1_wins
        
        return {
            "total_matches": total_matches,
            "player1_wins": p1_wins,
            "player2_wins": p2_wins,
            "hard_matches": random.randint(0, total_matches),
            "clay_matches": random.randint(0, total_matches - random.randint(0, total_matches)),
            "grass_matches": random.randint(0, max(0, total_matches - random.randint(0, total_matches))),
            "last_match_date": (datetime.now() - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d') if total_matches > 0 else None
        }
    
    def fetch_tournament_history(self, player_name: str, tournament: str, years: int = 5) -> List[Dict[str, Any]]:
        """Simula fetch storico performance in un torneo"""
        logger.info(f"Fetching tournament history: {player_name} at {tournament}")
        
        history = []
        current_year = datetime.now().year
        
        for year in range(current_year - years, current_year + 1):
            if random.random() < 0.7:  # 70% probabilità di partecipazione
                result = random.choice(["R128", "R64", "R32", "R16", "QF", "SF", "F", "W"])
                matches_played = {"R128": 1, "R64": 2, "R32": 3, "R16": 4, "QF": 5, "SF": 6, "F": 7, "W": 7}[result]
                wins = matches_played if result == "W" else matches_played - 1
                
                history.append({
                    "year": year,
                    "matches_played": matches_played,
                    "wins": wins,
                    "losses": 1 if result != "W" else 0,
                    "best_result": result,
                    "prize_money": random.randint(10000, 2000000),
                    "avg_first_serve_pct": round(random.uniform(55, 75), 1),
                    "avg_aces_per_match": round(random.uniform(3, 15), 1),
                    "avg_winners_per_match": round(random.uniform(20, 50), 1),
                    "avg_unforced_errors_per_match": round(random.uniform(15, 40), 1)
                })
        
        return history
    
    def get_live_matches(self) -> List[Dict[str, Any]]:
        """Simula fetch partite live con statistiche in tempo reale"""
        logger.info("Fetching live matches...")
        
        # In produzione userebbe API come Sofascore o simili
        live_matches = []
        
        for i in range(random.randint(3, 8)):
            match = {
                "match_id": f"live_{i}",
                "player1": f"Player {random.randint(1, 50)}",
                "player2": f"Player {random.randint(51, 100)}",
                "tournament": random.choice(["US Open", "Roland Garros", "Wimbledon", "Australian Open"]),
                "surface": random.choice(["Hard", "Clay", "Grass"]),
                "status": "live",
                "current_set": random.randint(1, 3),
                "score": f"{random.randint(0, 6)}-{random.randint(0, 6)}",
                
                # Statistiche live
                "p1_aces": random.randint(0, 15),
                "p2_aces": random.randint(0, 15),
                "p1_double_faults": random.randint(0, 5),
                "p2_double_faults": random.randint(0, 5),
                "p1_first_serve_pct": round(random.uniform(55, 75), 1),
                "p2_first_serve_pct": round(random.uniform(55, 75), 1),
                "p1_winners": random.randint(5, 30),
                "p2_winners": random.randint(5, 30),
                "p1_unforced_errors": random.randint(3, 25),
                "p2_unforced_errors": random.randint(3, 25),
            }
            
            live_matches.append(match)
        
        return live_matches
