import os
import time
import random
import datetime as dt
from typing import Dict, Any, Optional, Tuple, List

import requests

from db import DatabaseManager

SOFA_BASE = "https://api.sofascore.com/api/v1"

def _headers():
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
    return dt.datetime.utcnow().strftime("%Y-%m-%d")

def fetch_scheduled_events(date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    if not date_str:
        date_str = iso_date_utc_today()
    url = f"{SOFA_BASE}/sport/tennis/scheduled-events/{date_str}"
    data = _get(url)
    return data.get("events", [])

def extract_players(ev: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Ritorna (p1_name, p2_name, p1_country, p2_country) cercando in vari layout:
    - homeTeam/awayTeam
    - homeCompetitor/awayCompetitor
    - participants (con isHome True/False)
    """
    p1_name = p2_name = p1_country = p2_country = None

    # 1) homeTeam / awayTeam
    home = ev.get("homeTeam") or {}
    away = ev.get("awayTeam") or {}
    if not home and ev.get("homeCompetitor"):  # fallback
        home = ev.get("homeCompetitor") or {}
    if not away and ev.get("awayCompetitor"):
        away = ev.get("awayCompetitor") or {}

    def get_nm_cty(obj):
        if not obj:
            return None, None
        name = obj.get("name") or obj.get("shortName")
        cty = (obj.get("country") or {}).get("alpha2")
        return name, cty

    p1_name, p1_country = get_nm_cty(home)
    p2_name, p2_country = get_nm_cty(away)

    # 2) participants array (se non trovato sopra)
    if (not p1_name or not p2_name) and isinstance(ev.get("participants"), list):
        parts = ev["participants"]
        home_part = next((x for x in parts if x.get("isHome")), None)
        away_part = next((x for x in parts if x.get("isAway")), None)
        if home_part:
            p1_name = p1_name or home_part.get("name") or (home_part.get("team") or {}).get("name")
            p1_country = p1_country or ((home_part.get("team") or {}).get("country") or {}).get("alpha2")
        if away_part:
            p2_name = p2_name or away_part.get("name") or (away_part.get("team") or {}).get("name")
            p2_country = p2_country or ((away_part.get("team") or {}).get("country") or {}).get("alpha2")

    return p1_name, p2_name, p1_country, p2_country

def gender_from_tournament(cat: Dict[str, Any], tournament_name: str) -> Optional[str]:
    name = (cat.get("name") or tournament_name or "").lower()
    if "wta" in name or "women" in name or "ladies" in name:
        return "F"
    if "atp" in name or "men" in name:
        return "M"
    return None

def fetch_event_odds_featured(event_id: int) -> Dict[str, Any]:
    # Proviamo featured, poi markets, poi all
    for path in [f"/event/{event_id}/odds/1/featured",
                 f"/event/{event_id}/odds/markets",
                 f"/event/{event_id}/odds/1/all"]:
        url = f"{SOFA_BASE}{path}"
        try:
            return _get(url)
        except Exception:
            continue
    return {}

def best_winner_odds(odds_payload: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    best_p1 = None
    best_p2 = None
    best_bk = None

    def consider(odds_list: List[Dict[str, Any]], bk_name: str):
        nonlocal best_p1, best_p2, best_bk
        o1, o2 = None, None
        for o in odds_list or []:
            label = str(o.get("name") or o.get("choice") or o.get("outcome") or o.get("handicap") or "").lower()
            price = o.get("value") or o.get("decimalOdds") or o.get("odd") or o.get("price")
            if price is None:
                continue
            try:
                price = float(price)
            except:
                continue
            if label in ("1", "home", "player1", "p1"):
                o1 = price
            elif label in ("2", "away", "player2", "p2"):
                o2 = price
        if o1 is not None and (best_p1 is None or o1 > best_p1):
            best_p1 = o1
            best_bk = bk_name
        if o2 is not None and (best_p2 is None or o2 > best_p2):
            best_p2 = o2
            best_bk = bk_name

    # featuredOdds
    fo = odds_payload.get("featuredOdds")
    if isinstance(fo, list):
        for bk in fo:
            bk_name = bk.get("bookmaker", {}).get("name") or bk.get("bookmakerName") or "book"
            markets = bk.get("markets") or bk.get("odds") or []
            for m in markets or []:
                choices = m.get("choices") or m.get("outcomes") or []
                consider(choices, bk_name)

    # markets (id=1 winner)
    for m in odds_payload.get("markets", []) or []:
        mid = str(m.get("id") or m.get("key"))
        if mid != "1":
            continue
        for bk in m.get("bookmakers") or []:
            bk_name = bk.get("bookmaker", {}).get("name") or bk.get("name") or "book"
            choices = bk.get("choices") or bk.get("outcomes") or []
            consider(choices, bk_name)

    return best_p1, best_p2, best_bk

def run_etl_today(verbose: bool = True) -> Dict[str, Any]:
    db = DatabaseManager()
    date_str = iso_date_utc_today()
    events = fetch_scheduled_events(date_str)

    inserted = updated = skipped = 0
    matches_with_odds = 0

    for idx, ev in enumerate(events):
        try:
            tournament = ev.get("tournament", {}) or {}
            category = tournament.get("category", {}) or {}
            tournament_name = tournament.get("name") or "Tournament"

            surface = (ev.get("season", {}) or {}).get("surface") or ev.get("surface") or "Hard"

            p1_name, p2_name, p1_cty, p2_cty = extract_players(ev)
            if not p1_name or not p2_name:
                skipped += 1
                if verbose and idx < 3:
                    print("Skip missing players:", {"id": ev.get("id"), "keys": list(ev.keys())[:12]})
                continue

            gender = gender_from_tournament(category, tournament_name) or "M"

            start_ts = ev.get("startTimestamp")
            match_time = None
            if start_ts:
                match_time = dt.datetime.utcfromtimestamp(int(start_ts)).isoformat()

            round_name = (ev.get("roundInfo", {}) or {}).get("name") or ev.get("round") or "R32"

            # Upsert players
            p1_id = db.upsert_player_by_name(name=p1_name, country=p1_cty or "", gender=gender)
            p2_id = db.upsert_player_by_name(name=p2_name, country=p2_cty or "", gender=gender)

            # Upsert match base
            mid_before = None
            match_id = db.upsert_match(
                player1_id=p1_id,
                player2_id=p2_id,
                tournament_name=tournament_name,
                round=round_name,
                surface=surface,
                match_time=match_time,
                status=(ev.get("status") or {}).get("type") or "not_started",
            )

            # Odds (non blocca ETL se fallisce)
            try:
                odds_json = fetch_event_odds_featured(ev.get("id"))
                o1, o2, bk = best_winner_odds(odds_json)
                if o1 is not None or o2 is not None:
                    matches_with_odds += 1
                db.upsert_match_odds(match_id=match_id, odds_p1=o1, odds_p2=o2, source_book=bk or "sofa")
            except Exception:
                pass

            updated += 1
            if verbose and (updated % 50 == 0):
                print(f"Processed {updated} events...")

        except Exception as e:
            skipped += 1
            if verbose and idx < 5:
                print("Error on event:", ev.get("id"), str(e)[:160])
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
