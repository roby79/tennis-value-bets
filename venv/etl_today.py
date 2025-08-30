import os
import requests
from datetime import datetime, timedelta
from db import DatabaseManager
from dotenv import load_dotenv
import time
import random

# Carica variabili d'ambiente
load_dotenv()

# Inizializza il DatabaseManager
db = DatabaseManager("data/tennis.db")

# ==============================================================================
# 1. Funzione per ottenere match di tennis da Sofascore (API non ufficiale)
# ==============================================================================
def get_sofascore_matches_today():
    print("Fetching matches from Sofascore...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.sofascore.com/api/v1/sport/tennis/scheduled-events/{today_str}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Solleva un'eccezione per errori HTTP
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Sofascore data: {e}")
        return []

    matches_data = []
    for event in data.get("events", []):
        # Filtra solo ATP/WTA (o Grand Slam, Masters, etc.)
        if event.get("tournament", {}).get("category", {}).get("name") in ["ATP", "WTA", "Grand Slam", "Masters 1000", "WTA 1000"]:
            
            tournament_name = event["tournament"]["name"]
            player1_name = event["homeTeam"]["name"]
            player2_name = event["awayTeam"]["name"]
            match_time = datetime.fromtimestamp(event["startTimestamp"])
            
            matches_data.append({
                "tournament_name": tournament_name,
                "player1_name": player1_name,
                "player2_name": player2_name,
                "match_time": match_time,
                "sofascore_id": event["id"] # ID per riferimento futuro
            })
    print(f"Found {len(matches_data)} tennis matches from Sofascore.")
    return matches_data

# ==============================================================================
# 2. Funzione per ottenere quote da The Odds API
# ==============================================================================
def get_odds_from_api():
    print("Fetching odds from The Odds API...")
    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        print("ODDS_API_KEY not set in .env. Skipping odds fetching.")
        return {}

    # Sport key per tennis (può variare, controllare documentazione)
    sport_key = "tennis_atp_wta" # o "tennis_atp", "tennis_wta"
    
    # Regioni e mercati
    regions = "eu" # us, uk, au, eu
    markets = "h2h" # head to head (vincitore partita)
    odds_format = "decimal"
    
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={api_key}&regions={regions}&markets={markets}&oddsFormat={odds_format}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Odds API data: {e}")
        return {}

    odds_map = {}
    for event in data:
        event_id = event["id"]
        commence_time = datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
        
        # Cerchiamo le quote "h2h" (head to head)
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market["key"] == "h2h":
                    outcomes = market["outcomes"]
                    if len(outcomes) == 2:
                        player1_name = outcomes[0]["name"]
                        player2_name = outcomes[1]["name"]
                        odds1 = outcomes[0]["price"]
                        odds2 = outcomes[1]["price"]
                        
                        # Usiamo una tupla ordinata per la chiave per evitare problemi di ordine
                        key = tuple(sorted((player1_name, player2_name)))
                        
                        # Salviamo le quote del primo bookmaker trovato per semplicità
                        if key not in odds_map:
                            odds_map[key] = {"player1": player1_name, "odds1": odds1,
                                             "player2": player2_name, "odds2": odds2,
                                             "bookmaker": bookmaker["title"]}
                        break # Esci dal loop dei mercati
            if key in odds_map:
                break # Esci dal loop dei bookmaker
    
    print(f"Found odds for {len(odds_map)} events from The Odds API.")
    return odds_map

# ==============================================================================
# 3. Processo ETL principale
# ==============================================================================
def run_etl():
    print("\n--- Starting ETL Process ---")
    
    # 1. Ottieni match di oggi da Sofascore
    sofascore_matches = get_sofascore_matches_today()
    
    # 2. Ottieni quote da The Odds API
    odds_data = get_odds_from_api()
    
    # 3. Pulisci il database dalle partite di oggi (per evitare duplicati)
    # ATTENZIONE: Questo cancella le partite di OGGI. Se vuoi mantenere lo storico, modifica.
    # db.delete_today_matches() # Implementa questo metodo in db.py se necessario
    
    # 4. Inserisci/aggiorna dati nel database
    for match_info in sofascore_matches:
        p1_name = match_info["player1_name"]
        p2_name = match_info["player2_name"]
        tournament_name = match_info["tournament_name"]
        match_time = match_info["match_time"]

        # Inserisci/ottieni ID giocatori
        player1_id = db.insert_player(p1_name)
        player2_id = db.insert_player(p2_name)
        
        # Inserisci/aggiorna statistiche base (se non esistono)
        # Qui dovremmo avere una logica più complessa per ELO e ranking reali
        # Per ora, assicuriamoci che abbiano una entry in player_stats
        if not db.get_player_stats(player1_id):
            db.insert_player_stats(player1_id)
        if not db.get_player_stats(player2_id):
            db.insert_player_stats(player2_id)

        # Inserisci/ottieni ID torneo
        tournament_id = db.insert_tournament(tournament_name) # db.py deve gestire duplicati

        # Inserisci il match
        match_db_id = db.insert_match(tournament_id, player1_id, player2_id, match_time, "R1")
        
        # Cerca e inserisci le quote
        key = tuple(sorted((p1_name, p2_name)))
        if key in odds_data:
            odds_info = odds_data[key]
            print(f"Processing match: {p1_name} vs {p2_name} (Odds: {odds_info['odds1']} / {odds_info['odds2']})")
            
            # Inserisci mercato (Match Odds)
            market_id = f"ODDSAPI_{match_db_id}_{odds_info['bookmaker']}" # ID unico per mercato
            db.insert_market(market_id, match_db_id, "Match Odds", "H2H")
            
            # Inserisci runners
            runner1_id = db.insert_runner(market_id, odds_info['player1'], 1) # 1 è un placeholder selection_id
            runner2_id = db.insert_runner(market_id, odds_info['player2'], 2) # 2 è un placeholder selection_id
            
            # Inserisci prezzi
            db.insert_price(runner1_id, odds_info['odds1'], None, None, None, None)
            db.insert_price(runner2_id, odds_info['odds2'], None, None, None, None)
        else:
            print(f"Processing match: {p1_name} vs {p2_name} (No odds found)")
            # Se non ci sono quote, possiamo inserire un mercato con quote placeholder o lasciare vuoto
            market_id = f"ODDSAPI_{match_db_id}_NOODDS"
            db.insert_market(market_id, match_db_id, "Match Odds", "H2H", status="NO_ODDS")

    print("\n--- ETL Process Finished ---")

if __name__ == "__main__":
    run_etl()
