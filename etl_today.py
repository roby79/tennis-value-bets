import os
import time
import json
import math
import random
import datetime as dt
from typing import Dict, Any, Optional, Tuple, List

import requests

from db import DatabaseManager

SOFA_BASE = "https://api.sofascore.com/api/v1"

def _headers():
    # User-Agent per ridurre blocchi
    ua = os.environ.get("SOFA_UA", "Mozilla/5.0 (compatible; TennisValueBets/1.0)")
    return {"User-Agent": ua, "Accept": "application/json"}

def _get(url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3, backoff: float = 0.7):
    last_err = None
    for i in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=_headers(), timeout=15)
            if r.status_code == 200:
                return r.json()
            elif r.status_code in (403, 429, 500, 502, 503):
                last_err = Exception(f"HTTP {r.status_code}: {r.text[:160]}")
                time.sleep(backoff * (i + 1) + random.random())
            else:
                r.raise_for_status()
        except Exception as e:
            last_err = e
            time.sleep(backoff * (i + 1) + random.random())
    if last_err:
        raise last_err

def iso_date_utc_today() -> str:
    # Sofa vuole yyyy-mm-dd in UTC
    return dt.datetime.utcnow().strftime("%Y-%m-%d")

def fetch_scheduled_events(date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    if not date_str:
        date_str = iso_date_utc_today()
    url = f"{SOFA_BASE}/sport/tennis/scheduled-events/{date_str}"
    data = _get(url)
    return data.get("events", [])

def fetch_event_odds_featured(event_id: int) -> Dict[str, Any]:
    # Featured odds per vari bookmaker
    # In alcuni casi l’endpoint è /odds/1/featured (market 1=match-winner)
    url = f"{SOFA_BASE}/event/{event_id}/odds/1/featured"
    try:
        return _get(url)
    except Exception:
        # fallback: tutti i markets e poi filtriamo il market 1 (match winner)
        url2 = f"{SOFA_BASE}/event/{event_id}/odds/markets"
        return _get(url2)

def best_winner_odds(odds_payload: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Ritorna (best_odds_p1, best_odds_p2, bookmaker_name) se disponibili.
    Cerca market winner (id=1) o chiave 'featured'.
    """
    best_p1 = None
    best_p2 = None
    best_bk = None

    def consider(odds_list: List[Dict[str, Any]], bk_name: str):
        nonlocal best_p1, best_p2, best_bk
        # Tennis winner è binario, outcomes: { name or outcome: '1'/'2', 'home'/'away' }
        # Strutture Sofa variano. Gestiamo alcuni formati comuni.
        try:
            o1, o2 = None, None
            # Common patterns
            for o in odds_list:
                label = str(o.get("name") or o.get("choice") or o.get("outcome") or "").lower()
                price = o.get("value") or o.get("decimalOdds") or o.get("odd")
                # Alcuni payload usano "dp" o "num/den". Qui assumiamo decimali già pronti.
                if not price:
                    continue
                try:
                    price = float(price)
                except:
                    continue
                if label in ("1", "home", "player1", "p1"):
                    o1 = price
                elif label in ("2", "away", "player2", "p2"):
                    o2 = price
            if o1:
                if (best_p1 is None) or (o1 > best_p1):
                    best_p1 = o1
                    best_bk = bk_name
            if o2:
                if (best_p2 is None) or (o2 > best_p2):
                    best_p2 = o2
                    best_bk = bk_name
        except:
            pass

    # Caso 1: featuredOdds
    if "featuredOdds" in odds_payload:
        fo = odds_payload["featuredOdds"]
        if isinstance(fo, list):
            for bk in fo:
                bk_name = bk.get("bookmaker", {}).get("name") or bk.get("bookmakerName") or "book"
                outcomes = bk.get("markets") or bk.get("odds") or []
                if isinstance(outcomes, list):
                    # Alcuni hanno markets con choices
                    for m in outcomes:
                        choices = m.get("choices") or m.get("outcomes") or []
                        consider(choices, bk_name)
    # Caso 2: markets
    if "markets" in odds_payload:
        for m in odds_payload.get("markets", []):
            mid = m.get("id") or m.get("key")
            if str(mid) != "1":
                continue
            bk_odds = m.get("bookmakers") or []
            for bk in bk_odds:
                bk_name = bk.get("bookmaker", {}).get("name") or bk.get("name") or "book"
                choices = bk.get("choices") or bk.get("outcomes") or []
                consider(choices, bk_name)

    return best_p1, best_p2, best_bk

def gender_from_tournament(cat: Dict[str, Any]) -> Optional[str]:
    # Prova a dedurre M/F da nome competizione
    name = (cat.get("name") or "").lower()
    if "wta" in name or "women" in name or "ladies" in name:
        return "F"
    if "atp" in name or "men" in name:
        return "M"
    return None

def run_etl_today(verbose: bool = True) -> Dict[str, Any]:
    db = DatabaseManager()
    date_str = iso_date_utc_today()
    events = fetch_scheduled_events(date_str)

    inserted = updated = skipped = 0
    matches_with_odds = 0

    for ev in events:
        try:
            # Struttura tipica Sofa
            tournament = ev.get("tournament", {}) or {}
            category = tournament.get("category", {}) or {}
            competition = {
                "tournament_name": tournament.get("name") or "Tournament",
                "surface": (ev.get("season", {}) or {}).get("surface") or ev.get("surface") or "Hard"
            }
            # Players
            home = ev.get("homeTeam") or ev.get("homeCompetitor") or {}
            away = ev.get("awayTeam") or ev.get("awayCompetitor") or {}
            p1_name = home.get("name") or home.get("shortName")
            p2_name = away.get("name") or away.get("shortName")
            if not p1_name or not p2_name:
                skipped += 1
                continue

            # Genere (dedotto)
            gender = gender_from_tournament(category) or "M"

            # Time
            start_ts = ev.get("startTimestamp")
            match_time = None
            if start_ts:
                match_time = dt.datetime.utcfromtimestamp(int(start_ts)).isoformat()

            # Round
            round_name = (ev.get("roundInfo", {}) or {}).get("name") or ev.get("round") or "R32"

            # Upsert players
            p1_id = db.upsert_player_by_name(name=p1_name, country=home.get("country", {}).get("alpha2") or "", gender=gender)
            p2_id = db.upsert_player_by_name(name=p2_name, country=away.get("country", {}).get("alpha2") or "", gender=gender)

            # Upsert match base
            match_id = db.upsert_match(
                player1_id=p1_id,
                player2_id=p2_id,
                tournament_name=competition["tournament_name"],
                round=round_name,
                surface=competition["surface"],
                match_time=match_time,
                status=ev.get("status", {}).get("type", "not_started")
            )

            # Odds
            odds_json = fetch_event_odds_featured(ev.get("id"))
            o1, o2, bk = best_winner_odds(odds_json)
            if o1 or o2:
                matches_with_odds += 1
            db.upsert_match_odds(match_id=match_id, odds_p1=o1, odds_p2=o2, source_book=bk or "sofa")

            updated += 1
            if verbose and (updated % 20 == 0):
                print(f"Processed {updated} events...")
        except Exception as e:
            if verbose:
                print("Error on event:", e)
            skipped += 1
            continue

    return {
        "events": len(events),
        "updated": updated,
        "skipped": skipped,
        "with_odds": matches_with_odds
    }

if __name__ == "__main__":
    summary = run_etl_today(verbose=True)
    print("ETL summary:", summary)
