# odds.py
# Khmer News 24
# Real Football Odds - The Odds API v4

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv


# ============================================================
# LOAD .ENV SAFELY
# ============================================================

# Folder where this odds.py file is located
BASE_DIR = Path(__file__).resolve().parent

# Exact .env path
ENV_FILE = BASE_DIR / ".env"

# Load .env from the same folder as odds.py
load_dotenv(
    dotenv_path=ENV_FILE,
    override=True,
)


# ============================================================
# SETTINGS
# ============================================================

ODDS_API_KEY = os.getenv(
    "ODDS_API_KEY",
    "",
).strip()

BASE_URL = (
    "https://api.the-odds-api.com/v4"
)

MIN_ACC_ODDS = 2.50
MAX_ACC_LEGS = 4

REQUEST_TIMEOUT = 15


# ============================================================
# LEAGUES
# ============================================================

SPORT_KEYS = {

    "Premier League":
        "soccer_epl",

    "FA Cup":
        "soccer_fa_cup",

    "EFL Cup":
        "soccer_england_efl_cup",

    "La Liga":
        "soccer_spain_la_liga",

    "Copa del Rey":
        "soccer_spain_copa_del_rey",

    "Serie A":
        "soccer_italy_serie_a",

    "Coppa Italia":
        "soccer_italy_coppa_italia",

    "Bundesliga":
        "soccer_germany_bundesliga",

    "DFB-Pokal":
        "soccer_germany_dfb_pokal",

    "Ligue 1":
        "soccer_france_ligue_one",

    "Coupe de France":
        "soccer_france_coupe_de_france",

    "Champions League":
        "soccer_uefa_champs_league",

    "Europa League":
        "soccer_uefa_europa_league",

    "Conference League":
        "soccer_uefa_europa_conference_league",

    "Nations League":
        "soccer_uefa_nations_league",

    "MLS":
        "soccer_usa_mls",

    "Eredivisie":
        "soccer_netherlands_eredivisie",

    "Primeira Liga":
        "soccer_portugal_primeira_liga",

    "Belgian Pro League":
        "soccer_belgium_first_div",

    "Turkish Super Lig":
        "soccer_turkey_super_league",

    "Greek Super League":
        "soccer_greece_super_league",
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class OddsSelection:

    match_id: str

    home_team: str
    away_team: str

    market: str
    selection: str

    odds: float

    bookmaker: Optional[str] = None

    model_probability: Optional[float] = None

    league: Optional[str] = None

    commence_time: Optional[str] = None


@dataclass
class MatchOdds:

    match_id: str

    league: str

    home_team: str
    away_team: str

    commence_time: Optional[str]

    selections: list[OddsSelection]


# ============================================================
# API KEY CHECK
# ============================================================

def check_api_key() -> bool:
    """
    Check whether ODDS_API_KEY was loaded.

    The actual API key is NEVER printed.
    """

    print()
    print("=" * 60)
    print("🔐 ODDS API CONFIGURATION")
    print("=" * 60)

    print(
        f"📁 odds.py folder:"
    )

    print(
        f"   {BASE_DIR}"
    )

    print()

    print(
        f"📄 .env path:"
    )

    print(
        f"   {ENV_FILE}"
    )

    print()

    if ENV_FILE.exists():

        print(
            "✅ .env file found."
        )

    else:

        print(
            "❌ .env file NOT found."
        )

        print()
        print(
            "Make sure .env is here:"
        )

        print(
            str(ENV_FILE)
        )

        return False

    print()

    if ODDS_API_KEY:

        print(
            "✅ ODDS_API_KEY loaded."
        )

        # Show only safe information
        print(
            f"🔑 Key length: "
            f"{len(ODDS_API_KEY)} characters"
        )

        return True

    print(
        "❌ ODDS_API_KEY is empty."
    )

    print()
    print(
        "Your .env should contain:"
    )

    print(
        "ODDS_API_KEY=YOUR_REAL_KEY"
    )

    return False


# ============================================================
# API REQUEST
# ============================================================

def api_get(
    sport_key: str,
    markets: str = "h2h,totals",
    regions: str = "eu",
) -> Optional[list]:

    if not ODDS_API_KEY:

        print(
            "❌ ODDS_API_KEY is missing."
        )

        return None

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": regions,
        "markets": markets,
        "oddsFormat": "decimal",
    }

    url = (
        f"{BASE_URL}/sports/"
        f"{sport_key}/odds?"
        f"{urlencode(params)}"
    )

    request = Request(
        url,
        headers={
            "User-Agent":
                "KhmerNews24/1.0"
        },
    )

    try:

        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:

            raw = response.read()

            remaining = response.headers.get(
                "x-requests-remaining"
            )

            used = response.headers.get(
                "x-requests-used"
            )

            if remaining:

                print(
                    f"[Odds API] "
                    f"Credits remaining: "
                    f"{remaining}"
                )

            if used:

                print(
                    f"[Odds API] "
                    f"Credits used: "
                    f"{used}"
                )

        return json.loads(
            raw.decode("utf-8")
        )

    except HTTPError as error:

        print(
            f"[Odds API] HTTP {error.code}"
        )

        try:

            body = error.read().decode(
                "utf-8",
                errors="ignore",
            )

            print(
                body[:500]
            )

        except Exception:
            pass

        return None

    except URLError as error:

        print(
            "[Odds API] "
            f"Connection error: {error}"
        )

        return None

    except TimeoutError:

        print(
            "[Odds API] "
            "Request timeout."
        )

        return None

    except json.JSONDecodeError:

        print(
            "[Odds API] "
            "Invalid JSON."
        )

        return None

    except Exception as error:

        print(
            "[Odds API] "
            f"Unexpected error: {error}"
        )

        return None


# ============================================================
# CONVERT 1X2
# ============================================================

def parse_h2h_market(
    event: dict,
    bookmaker: dict,
    market: dict,
    league: str,
) -> list[OddsSelection]:

    selections = []

    outcomes = (
        market.get("outcomes")
        or []
    )

    for outcome in outcomes:

        name = (
            outcome.get("name")
            or ""
        ).strip()

        price = outcome.get(
            "price"
        )

        if not name:
            continue

        try:

            odds = float(price)

        except (
            ValueError,
            TypeError,
        ):

            continue

        if odds <= 1.0:
            continue

        selections.append(
            OddsSelection(

                match_id=str(
                    event.get("id")
                    or ""
                ),

                home_team=(
                    event.get(
                        "home_team"
                    )
                    or ""
                ),

                away_team=(
                    event.get(
                        "away_team"
                    )
                    or ""
                ),

                market="1X2",

                selection=name,

                odds=odds,

                bookmaker=(
                    bookmaker.get(
                        "title"
                    )
                ),

                league=league,

                commence_time=(
                    event.get(
                        "commence_time"
                    )
                ),
            )
        )

    return selections


# ============================================================
# CONVERT TOTALS
# ============================================================

def parse_totals_market(
    event: dict,
    bookmaker: dict,
    market: dict,
    league: str,
) -> list[OddsSelection]:

    selections = []

    outcomes = (
        market.get("outcomes")
        or []
    )

    for outcome in outcomes:

        name = (
            outcome.get("name")
            or ""
        ).strip()

        point = outcome.get(
            "point"
        )

        price = outcome.get(
            "price"
        )

        if not name:
            continue

        if point is None:
            continue

        try:

            odds = float(price)
            point = float(point)

        except (
            ValueError,
            TypeError,
        ):

            continue

        if odds <= 1.0:
            continue

        if name.lower() not in (
            "over",
            "under",
        ):
            continue

        selection_name = (
            f"{name} {point:g}"
        )

        selections.append(
            OddsSelection(

                match_id=str(
                    event.get("id")
                    or ""
                ),

                home_team=(
                    event.get(
                        "home_team"
                    )
                    or ""
                ),

                away_team=(
                    event.get(
                        "away_team"
                    )
                    or ""
                ),

                market="Over/Under",

                selection=selection_name,

                odds=odds,

                bookmaker=(
                    bookmaker.get(
                        "title"
                    )
                ),

                league=league,

                commence_time=(
                    event.get(
                        "commence_time"
                    )
                ),
            )
        )

    return selections


# ============================================================
# GET LEAGUE ODDS
# ============================================================

def get_league_odds(
    league: str,
    regions: str = "eu",
) -> list[OddsSelection]:

    sport_key = SPORT_KEYS.get(
        league
    )

    if not sport_key:

        print(
            f"❌ Unknown league: "
            f"{league}"
        )

        return []

    print()
    print(
        f"📡 Loading odds: "
        f"{league}"
    )

    events = api_get(
        sport_key=sport_key,
        markets="h2h,totals",
        regions=regions,
    )

    if not events:

        print(
            f"⚠️ No odds returned: "
            f"{league}"
        )

        return []

    selections = []

    for event in events:

        bookmakers = (
            event.get(
                "bookmakers"
            )
            or []
        )

        if not bookmakers:
            continue

        # Use first bookmaker with data
        event_selections = []

        for bookmaker in bookmakers:

            markets = (
                bookmaker.get(
                    "markets"
                )
                or []
            )

            bookmaker_selections = []

            for market in markets:

                market_key = (
                    market.get(
                        "key"
                    )
                )

                if market_key == "h2h":

                    bookmaker_selections.extend(
                        parse_h2h_market(
                            event,
                            bookmaker,
                            market,
                            league,
                        )
                    )

                elif market_key == "totals":

                    bookmaker_selections.extend(
                        parse_totals_market(
                            event,
                            bookmaker,
                            market,
                            league,
                        )
                    )

            if bookmaker_selections:

                event_selections = (
                    bookmaker_selections
                )

                break

        selections.extend(
            event_selections
        )

    print(
        f"✅ {league}: "
        f"{len(selections)} selections"
    )

    return selections


# ============================================================
# GET ALL ODDS
# ============================================================

def get_all_odds(
    leagues: Optional[list[str]] = None,
    regions: str = "eu",
) -> list[OddsSelection]:

    if leagues is None:

        leagues = [
            "Premier League",
            "La Liga",
            "Serie A",
            "Bundesliga",
            "Ligue 1",
            "Eredivisie",
            "Primeira Liga",
            "Belgian Pro League",
            "Turkish Super Lig",
            "Greek Super League",
            "Champions League",
            "Europa League",
            "Conference League",
            "MLS",
        ]

    all_selections = []

    for league in leagues:

        selections = get_league_odds(
            league,
            regions=regions,
        )

        all_selections.extend(
            selections
        )

    return all_selections


# ============================================================
# COMBINED ODDS
# ============================================================

def calculate_combined_odds(
    selections: list[OddsSelection],
) -> float:

    if not selections:
        return 0.0

    combined = 1.0

    for selection in selections:

        if selection.odds <= 1.0:
            return 0.0

        combined *= selection.odds

    return round(
        combined,
        2,
    )


# ============================================================
# IMPLIED PROBABILITY
# ============================================================

def calculate_implied_probability(
    odds: float,
) -> float:

    if odds <= 1.0:
        return 0.0

    return round(
        (1 / odds) * 100,
        2,
    )


# ============================================================
# FILTER
# ============================================================

def filter_high_probability_selections(
    selections: list[OddsSelection],
    minimum_probability: float = 75.0,
) -> list[OddsSelection]:

    result = []

    for selection in selections:

        if (
            selection.model_probability
            is None
        ):
            continue

        if (
            selection.model_probability
            >= minimum_probability
        ):

            result.append(
                selection
            )

    return result


# ============================================================
# FORMAT SELECTION
# ============================================================

def format_selection(
    selection: OddsSelection,
) -> str:

    probability = ""

    if (
        selection.model_probability
        is not None
    ):

        probability = (
            f"\n🤖 Model: "
            f"{selection.model_probability:.1f}%"
        )

    return (
        f"⚽ {selection.home_team} "
        f"vs {selection.away_team}\n"
        f"📌 {selection.market}: "
        f"{selection.selection}\n"
        f"💰 Odds: "
        f"{selection.odds:.2f}\n"
        f"🏦 "
        f"{selection.bookmaker or 'Unknown'}"
        f"{probability}"
    )


# ============================================================
# TEST REAL ODDS
# ============================================================

def test_real_odds():

    print()
    print("=" * 60)
    print(
        "🇰🇭 KHMER NEWS 24"
    )
    print(
        "💰 REAL ODDS API TEST"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Check .env
    # --------------------------------------------------------

    if not check_api_key():

        print()
        print(
            "❌ Configuration failed."
        )

        print(
            "Fix the .env file first."
        )

        return

    print()
    print(
        "🚀 API key detected."
    )

    print(
        "🔒 API key value hidden."
    )

    print()

    # --------------------------------------------------------
    # Test Premier League only
    # This saves API credits.
    # --------------------------------------------------------

    selections = get_league_odds(
        "Premier League",
        regions="eu",
    )

    print()

    if not selections:

        print(
            "❌ No odds received."
        )

        print()
        print(
            "Possible reasons:"
        )

        print(
            "1. No upcoming Premier League matches"
        )

        print(
            "2. API quota exhausted"
        )

        print(
            "3. Invalid API key"
        )

        print(
            "4. Temporary API problem"
        )

        return

    print(
        f"🎯 Total selections: "
        f"{len(selections)}"
    )

    print()

    print(
        "FIRST 15 REAL ODDS:"
    )

    print("-" * 60)

    for selection in selections[:15]:

        print(
            format_selection(
                selection
            )
        )

        print(
            "-" * 60
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    test_real_odds()