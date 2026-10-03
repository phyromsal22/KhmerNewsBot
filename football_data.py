# football_data.py
# Khmer News 24
# Football Results Data Source
# TheSportsDB Free API
#
# This file provides completed football results
# for bet_model.py
#
# IMPORTANT:
# The data returned by this file is for statistical analysis.
# It does NOT guarantee betting results.

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ============================================================
# SETTINGS
# ============================================================

API_KEY = os.getenv(
    "THESPORTSDB_API_KEY",
    "123",
).strip()

BASE_URL = (
    "https://www.thesportsdb.com/api/v1/json"
)

REQUEST_TIMEOUT = 10

# TheSportsDB free API = 30 requests/minute.
# We use a much smaller request rate.
MIN_REQUEST_INTERVAL = 2.1

_last_request_time = 0.0


# ============================================================
# LEAGUES
# ============================================================

# TheSportsDB league IDs.
#
# IMPORTANT:
# These IDs are kept separate from ESPN league codes.
#
# We will expand/verify more leagues after the first test.

LEAGUES = {
    "Premier League": {
        "id": 4328,
        "country": "England",
    },

    "La Liga": {
        "id": 4335,
        "country": "Spain",
    },

    "Serie A": {
        "id": 4332,
        "country": "Italy",
    },

    "Bundesliga": {
        "id": 4331,
        "country": "Germany",
    },

    "Ligue 1": {
        "id": 4334,
        "country": "France",
    },
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class FootballMatch:
    """
    Completed football match.
    """

    event_id: str

    league: str

    home_team: str
    away_team: str

    home_score: int
    away_score: int

    date: Optional[str] = None
    time: Optional[str] = None

    status: str = "finished"

    season: Optional[str] = None


# ============================================================
# REQUEST HELPER
# ============================================================

def wait_for_rate_limit() -> None:
    """
    Keep requests slow enough for the free API.
    """

    global _last_request_time

    now = time.time()

    elapsed = (
        now -
        _last_request_time
    )

    if elapsed < MIN_REQUEST_INTERVAL:

        sleep_time = (
            MIN_REQUEST_INTERVAL -
            elapsed
        )

        time.sleep(sleep_time)

    _last_request_time = time.time()


def api_get(
    endpoint: str,
    params: Optional[dict] = None,
) -> Optional[dict]:
    """
    Send GET request to TheSportsDB.
    """

    wait_for_rate_limit()

    if params is None:
        params = {}

    query = urlencode(params)

    url = (
        f"{BASE_URL}/"
        f"{API_KEY}/"
        f"{endpoint}"
    )

    if query:
        url += "?" + query

    request = Request(
        url,
        headers={
            "User-Agent": (
                "KhmerNews24/1.0 "
                "(Football Statistics Bot)"
            )
        },
    )

    try:

        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:

            raw_data = response.read()

        return json.loads(
            raw_data.decode(
                "utf-8"
            )
        )

    except HTTPError as error:

        print(
            f"[TheSportsDB] HTTP error: "
            f"{error.code}"
        )

        if error.code == 429:
            print(
                "[TheSportsDB] "
                "Rate limit reached. "
                "Please wait."
            )

        return None

    except URLError as error:

        print(
            f"[TheSportsDB] "
            f"Connection error: {error}"
        )

        return None

    except TimeoutError:

        print(
            "[TheSportsDB] "
            "Request timeout."
        )

        return None

    except json.JSONDecodeError:

        print(
            "[TheSportsDB] "
            "Invalid JSON response."
        )

        return None

    except Exception as error:

        print(
            f"[TheSportsDB] "
            f"Unexpected error: {error}"
        )

        return None


# ============================================================
# SCORE PARSER
# ============================================================

def parse_score(
    value,
) -> Optional[int]:
    """
    Convert API score into integer.
    """

    if value is None:
        return None

    try:
        return int(value)

    except (
        ValueError,
        TypeError,
    ):
        return None


# ============================================================
# EVENT PARSER
# ============================================================

def parse_event(
    event: dict,
    league_name: str,
) -> Optional[FootballMatch]:
    """
    Convert TheSportsDB event into FootballMatch.
    """

    home_team = (
        event.get("strHomeTeam")
        or ""
    ).strip()

    away_team = (
        event.get("strAwayTeam")
        or ""
    ).strip()

    home_score = parse_score(
        event.get("intHomeScore")
    )

    away_score = parse_score(
        event.get("intAwayScore")
    )

    event_id = str(
        event.get("idEvent")
        or ""
    )

    if not event_id:
        return None

    if not home_team:
        return None

    if not away_team:
        return None

    # Only completed matches
    if home_score is None:
        return None

    if away_score is None:
        return None

    return FootballMatch(

        event_id=event_id,

        league=league_name,

        home_team=home_team,

        away_team=away_team,

        home_score=home_score,

        away_score=away_score,

        date=event.get(
            "dateEvent"
        ),

        time=event.get(
            "strTime"
        ),

        status=(
            event.get(
                "strStatus"
            )
            or "finished"
        ),

        season=event.get(
            "strSeason"
        ),
    )


# ============================================================
# FETCH PAST LEAGUE EVENTS
# ============================================================

def fetch_past_league(
    league_id: int,
    league_name: str,
) -> list[FootballMatch]:
    """
    Fetch recent completed matches
    from a league.

    TheSportsDB free endpoint:
        eventspastleague.php?id=...

    Free tier returns a limited number
    of recent events.
    """

    data = api_get(
        "eventspastleague.php",
        {
            "id": league_id,
        },
    )

    if not data:
        return []

    events = (
        data.get("events")
        or []
    )

    results = []

    for event in events:

        match = parse_event(
            event,
            league_name,
        )

        if match is not None:
            results.append(match)

    return results


# ============================================================
# FETCH ONE LEAGUE
# ============================================================

def get_league_results(
    league_name: str,
) -> list[FootballMatch]:
    """
    Get recent results for one league.
    """

    league = LEAGUES.get(
        league_name
    )

    if league is None:

        print(
            f"[FootballData] "
            f"Unknown league: "
            f"{league_name}"
        )

        return []

    print(
        f"[FootballData] "
        f"Loading {league_name}..."
    )

    matches = fetch_past_league(
        league_id=league["id"],
        league_name=league_name,
    )

    print(
        f"[FootballData] "
        f"{league_name}: "
        f"{len(matches)} matches"
    )

    return matches


# ============================================================
# FETCH ALL SUPPORTED LEAGUES
# ============================================================

def get_all_results() -> list[FootballMatch]:
    """
    Fetch recent results from all configured leagues.
    """

    all_matches = []

    for league_name in LEAGUES:

        matches = get_league_results(
            league_name
        )

        all_matches.extend(
            matches
        )

    return all_matches


# ============================================================
# FILTER TEAM MATCHES
# ============================================================

def get_team_results(
    team_name: str,
    matches: list[FootballMatch],
) -> list[FootballMatch]:
    """
    Get matches involving one team.
    """

    target = team_name.lower().strip()

    results = []

    for match in matches:

        if (
            match.home_team.lower()
            == target
        ):

            results.append(match)

        elif (
            match.away_team.lower()
            == target
        ):

            results.append(match)

    return results


# ============================================================
# CONVERT TO bet_model.py FORMAT
# ============================================================

def convert_to_model_data(
    matches: list[FootballMatch],
):
    """
    Convert FootballMatch objects into
    MatchResult objects expected by bet_model.py.
    """

    # Import here to avoid circular import problems.
    from bet_model import MatchResult

    result = []

    for match in matches:

        result.append(
            MatchResult(

                home_team=(
                    match.home_team
                ),

                away_team=(
                    match.away_team
                ),

                home_goals=(
                    match.home_score
                ),

                away_goals=(
                    match.away_score
                ),
            )
        )

    return result


# ============================================================
# FIND TEAM NAMES
# ============================================================

def get_team_names(
    matches: list[FootballMatch],
) -> list[str]:
    """
    Return unique team names.
    """

    teams = set()

    for match in matches:

        teams.add(
            match.home_team
        )

        teams.add(
            match.away_team
        )

    return sorted(
        teams
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    matches: list[FootballMatch],
) -> None:

    print()
    print("=" * 60)
    print(
        "FOOTBALL DATA SUMMARY"
    )
    print("=" * 60)

    if not matches:

        print(
            "❌ No completed matches found."
        )

        return

    leagues = {}

    for match in matches:

        leagues.setdefault(
            match.league,
            0,
        )

        leagues[
            match.league
        ] += 1

    print(
        f"Total matches: "
        f"{len(matches)}"
    )

    print()

    for league, count in leagues.items():

        print(
            f"⚽ {league}: "
            f"{count}"
        )

    print()

    teams = get_team_names(
        matches
    )

    print(
        f"Unique teams: "
        f"{len(teams)}"
    )

    print("=" * 60)


# ============================================================
# PRINT MATCHES
# ============================================================

def print_matches(
    matches: list[FootballMatch],
    limit: int = 20,
) -> None:

    print()

    if not matches:

        print(
            "❌ No matches."
        )

        return

    print(
        f"Showing {min(limit, len(matches))} "
        f"matches:"
    )

    print()

    for index, match in enumerate(
        matches[:limit],
        start=1,
    ):

        date = (
            match.date
            or "Unknown date"
        )

        print(
            f"{index}. "
            f"[{match.league}] "
            f"{date}"
        )

        print(
            f"   {match.home_team} "
            f"{match.home_score} - "
            f"{match.away_score} "
            f"{match.away_team}"
        )


# ============================================================
# TEST ONE LEAGUE
# ============================================================

def test_one_league():

    print()
    print("=" * 60)
    print(
        "TEST: TheSportsDB"
    )
    print("=" * 60)

    league_name = (
        "Premier League"
    )

    matches = get_league_results(
        league_name
    )

    print_matches(
        matches,
        limit=10,
    )

    print_summary(
        matches
    )


# ============================================================
# TEST MODEL CONNECTION
# ============================================================

def test_model_connection():

    print()
    print("=" * 60)
    print(
        "TEST: DATA → BET MODEL"
    )
    print("=" * 60)

    matches = get_league_results(
        "Premier League"
    )

    if not matches:

        print(
            "❌ No data to send "
            "to bet_model.py"
        )

        return

    model_data = (
        convert_to_model_data(
            matches
        )
    )

    print(
        f"Converted "
        f"{len(model_data)} "
        f"matches."
    )

    print()

    for match in model_data[:5]:

        print(
            f"{match.home_team} "
            f"{match.home_goals} - "
            f"{match.away_goals} "
            f"{match.away_team}"
        )

    print()
    print(
        "✅ football_data.py "
        "can communicate with "
        "bet_model.py"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "Khmer News 24"
    )

    print(
        "Football Data Module"
    )

    print(
        "Source: TheSportsDB"
    )

    print()

    # --------------------------------------------------------
    # FIRST TEST ONLY:
    # Use one league to save API requests.
    # --------------------------------------------------------

    test_one_league()

    # --------------------------------------------------------
    # After the first test works,
    # uncomment the next line to test
    # connection with bet_model.py.
    # --------------------------------------------------------

    # test_model_connection()