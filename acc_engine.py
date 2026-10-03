# acc_engine.py
# Khmer News 24
# ACC ENGINE
# Real Odds + Probability Filter + Accumulator Generator
#
# IMPORTANT:
# - Real odds come from odds.py
# - This file does NOT invent bookmaker odds.
# - Probability is an estimate, not a guarantee.
# - ACC odds >= 2.50
# - Minimum probability >= 75%
# - 2 to 4 legs
#
# ============================================================

from __future__ import annotations

import itertools
import math
import re
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional


# ============================================================
# IMPORT REAL ODDS
# ============================================================

try:

    from odds import (
        OddsSelection,
        get_all_odds,
        calculate_combined_odds,
        calculate_implied_probability,
    )

except Exception as error:

    print()
    print("❌ Cannot import odds.py")
    print(f"Error: {error}")
    print()
    raise


# ============================================================
# SETTINGS
# ============================================================

MIN_PROBABILITY = 72.0

MIN_COMBINED_ODDS = 2.50

MIN_LEGS = 2

MAX_LEGS = 4

# Minimum historical matches required
MIN_HISTORY_MATCHES = 5

# Number of recent matches used
MAX_RECENT_MATCHES = 10

# Default regions
DEFAULT_REGIONS = "eu"

# ACC date/time rules
# - Only matches starting today or tomorrow in Cambodia time (GMT+7).
# - Legs inside one ACC must start within 6 hours of each other.
# - Today + tomorrow may be mixed when the total time span is <= 6 hours.
ACC_MAX_TIME_GAP_HOURS = 6
CAMBODIA_TZ = timezone(timedelta(hours=7))


# ============================================================
# OPTIONAL FOOTBALL DATA
# ============================================================

try:

    import football_data

    FOOTBALL_DATA_AVAILABLE = True

except Exception as error:

    FOOTBALL_DATA_AVAILABLE = False

    football_data = None

    print(
        f"⚠️ football_data.py unavailable: {error}"
    )


# ============================================================
# OPTIONAL BET MODEL
# ============================================================

try:

    import bet_model

    BET_MODEL_AVAILABLE = True

except Exception as error:

    BET_MODEL_AVAILABLE = False

    bet_model = None

    print(
        f"⚠️ bet_model.py unavailable: {error}"
    )


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Candidate:

    match_id: str

    home_team: str

    away_team: str

    league: str

    market: str

    selection: str

    odds: float

    bookmaker: str

    commence_time: Optional[str]

    probability: float

    implied_probability: float

    edge: float

    confidence: str = "NORMAL"


@dataclass
class Accumulator:

    legs: list[Candidate]

    combined_odds: float

    average_probability: float

    lowest_probability: float

    estimated_joint_probability: float

    score: float


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_team_name(
    name: str,
) -> str:

    if not name:

        return ""

    text = str(name).lower().strip()

    # Common abbreviations
    replacements = {

        "man utd":
            "manchester united",

        "man united":
            "manchester united",

        "man city":
            "manchester city",

        "spurs":
            "tottenham",

        "psg":
            "paris saint germain",

        "inter milan":
            "internazionale",

        "inter":
            "internazionale",

        "atletico madrid":
            "atletico",

        "ath madrid":
            "atletico",

        "athletic bilbao":
            "athletic club",

        "newcastle utd":
            "newcastle united",

        "west ham utd":
            "west ham",

        "wolves":
            "wolverhampton",

        "brighton & hove albion":
            "brighton",

        "nottingham forest":
            "nottingham",

    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )

    # Remove punctuation
    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    # Normalize spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# TEAM MATCHING
# ============================================================

def teams_match(
    a: str,
    b: str,
) -> bool:

    a_norm = normalize_team_name(a)

    b_norm = normalize_team_name(b)

    if not a_norm or not b_norm:

        return False

    if a_norm == b_norm:

        return True

    # Exact substring
    if (
        a_norm in b_norm
        or b_norm in a_norm
    ):

        return True

    a_words = set(
        a_norm.split()
    )

    b_words = set(
        b_norm.split()
    )

    if not a_words or not b_words:

        return False

    intersection = (
        a_words & b_words
    )

    # At least one meaningful common word
    meaningful = [
        word
        for word in intersection
        if len(word) >= 4
    ]

    return len(meaningful) >= 1


# ============================================================
# MATCH KEY
# ============================================================

def match_key(
    home: str,
    away: str,
) -> str:

    return (
        f"{normalize_team_name(home)}"
        f"__"
        f"{normalize_team_name(away)}"
    )


# ============================================================
# IMPLIED PROBABILITY
# ============================================================

def implied_probability(
    odds: float,
) -> float:

    if odds <= 1.0:

        return 0.0

    return round(
        (1.0 / odds) * 100.0,
        2
    )


# ============================================================
# ACC DATE / TIME HELPERS
# ============================================================

def parse_commence_time(value) -> Optional[datetime]:
    """Parse Odds API commence_time into Cambodia local time."""
    if not value:
        return None

    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip()
        if not raw:
            return None

        try:
            # ISO-8601, including the Odds API's trailing Z.
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            # Fallback for common timestamp formats.
            formats = (
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S",
            )
            dt = None
            for fmt in formats:
                try:
                    dt = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue

            if dt is None:
                return None

    if dt.tzinfo is None:
        # Odds API normally supplies UTC timestamps. If a timestamp has
        # no timezone, treat it as UTC rather than guessing local time.
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(CAMBODIA_TZ)


def is_today_or_tomorrow(commence_time) -> bool:
    """Return True only for matches starting today or tomorrow in Cambodia."""
    local_dt = parse_commence_time(commence_time)
    if local_dt is None:
        return False

    today = datetime.now(CAMBODIA_TZ).date()
    tomorrow = today + timedelta(days=1)

    return local_dt.date() in (today, tomorrow)


def filter_today_tomorrow_selections(
    selections: list[OddsSelection],
) -> list[OddsSelection]:
    """Keep only real-odds selections for today/tomorrow (Cambodia time)."""
    filtered = []

    for selection in selections:
        if is_today_or_tomorrow(
            getattr(selection, "commence_time", None)
        ):
            filtered.append(selection)

    return filtered


def candidate_datetime(candidate: Candidate) -> Optional[datetime]:
    """Get a Candidate kickoff time in Cambodia local time."""
    return parse_commence_time(candidate.commence_time)


def within_six_hour_window(
    legs: list[Candidate],
) -> bool:
    """
    Check the ACC 6-hour rule.

    The earliest and latest kickoff in the ACC must be no more than
    6 hours apart. This naturally allows today + tomorrow when they
    cross midnight but stay within the 6-hour window.
    """
    if not legs:
        return False

    times = [candidate_datetime(leg) for leg in legs]

    # We require real kickoff times. This prevents an unknown date from
    # accidentally bypassing the 6-hour rule.
    if any(value is None for value in times):
        return False

    earliest = min(times)
    latest = max(times)

    gap = latest - earliest
    return gap <= timedelta(hours=ACC_MAX_TIME_GAP_HOURS)


def format_kickoff(commence_time) -> str:
    """Format kickoff as Cambodia local date/time for Telegram."""
    local_dt = parse_commence_time(commence_time)
    if local_dt is None:
        return "Time unavailable"

    return local_dt.strftime("%d %b %Y, %H:%M")


# ============================================================
# BASIC FORM MODEL
# ============================================================

def calculate_team_form(
    results,
    team_name: str,
    limit: int = MAX_RECENT_MATCHES,
):

    if not results:

        return {

            "matches": 0,

            "wins": 0,

            "draws": 0,

            "losses": 0,

            "goals_for": 0,

            "goals_against": 0,

            "points": 0,

        }

    target = normalize_team_name(
        team_name
    )

    team_results = []

    for match in results:

        home = normalize_team_name(
            match.get(
                "home_team",
                match.get(
                    "home",
                    ""
                )
            )
        )

        away = normalize_team_name(
            match.get(
                "away_team",
                match.get(
                    "away",
                    ""
                )
            )
        )

        if (
            target != home
            and target != away
        ):

            continue

        try:

            home_score = int(
                match.get(
                    "home_score",
                    match.get(
                        "home_goals",
                        0
                    )
                )
            )

            away_score = int(
                match.get(
                    "away_score",
                    match.get(
                        "away_goals",
                        0
                    )
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            continue

        team_results.append(
            (
                home,
                away,
                home_score,
                away_score,
            )
        )

    team_results = team_results[
        -limit:
    ]

    stats = {

        "matches": 0,

        "wins": 0,

        "draws": 0,

        "losses": 0,

        "goals_for": 0,

        "goals_against": 0,

        "points": 0,

    }

    for (
        home,
        away,
        home_score,
        away_score,
    ) in team_results:

        stats["matches"] += 1

        if target == home:

            gf = home_score

            ga = away_score

        else:

            gf = away_score

            ga = home_score

        stats["goals_for"] += gf

        stats["goals_against"] += ga

        if gf > ga:

            stats["wins"] += 1

            stats["points"] += 3

        elif gf == ga:

            stats["draws"] += 1

            stats["points"] += 1

        else:

            stats["losses"] += 1

    return stats


# ============================================================
# FORM STRENGTH
# ============================================================

def form_strength(
    stats: dict,
) -> float:

    matches = stats.get(
        "matches",
        0
    )

    if matches <= 0:

        return 0.5

    points = stats.get(
        "points",
        0
    )

    max_points = matches * 3

    if max_points <= 0:

        return 0.5

    return (
        points
        / max_points
    )


# ============================================================
# POISSON
# ============================================================

def poisson_probability(
    goals: int,
    expected_goals: float,
) -> float:

    if expected_goals <= 0:

        expected_goals = 0.01

    try:

        return (
            math.exp(
                -expected_goals
            )
            * (
                expected_goals
                ** goals
            )
            / math.factorial(
                goals
            )
        )

    except Exception:

        return 0.0


# ============================================================
# POISSON SCORE MATRIX
# ============================================================

def score_matrix(
    expected_home: float,
    expected_away: float,
    max_goals: int = 7,
):

    matrix = []

    for home_goals in range(
        max_goals + 1
    ):

        row = []

        for away_goals in range(
            max_goals + 1
        ):

            probability = (
                poisson_probability(
                    home_goals,
                    expected_home
                )
                *
                poisson_probability(
                    away_goals,
                    expected_away
                )
            )

            row.append(
                probability
            )

        matrix.append(row)

    return matrix


# ============================================================
# MARKET PROBABILITIES
# ============================================================

def calculate_market_probabilities(
    expected_home: float,
    expected_away: float,
):

    matrix = score_matrix(
        expected_home,
        expected_away
    )

    home_win = 0.0

    draw = 0.0

    away_win = 0.0

    over_15 = 0.0

    under_15 = 0.0

    over_25 = 0.0

    under_25 = 0.0

    btts_yes = 0.0

    btts_no = 0.0

    for home_goals, row in enumerate(
        matrix
    ):

        for away_goals, probability in enumerate(
            row
        ):

            total = (
                home_goals
                + away_goals
            )

            if home_goals > away_goals:

                home_win += probability

            elif home_goals == away_goals:

                draw += probability

            else:

                away_win += probability

            if total >= 2:

                over_15 += probability

            else:

                under_15 += probability

            if total >= 3:

                over_25 += probability

            else:

                under_25 += probability

            if (
                home_goals >= 1
                and away_goals >= 1
            ):

                btts_yes += probability

            else:

                btts_no += probability

    return {

        "home_win":
            home_win * 100,

        "draw":
            draw * 100,

        "away_win":
            away_win * 100,

        "over_1_5":
            over_15 * 100,

        "under_1_5":
            under_15 * 100,

        "over_2_5":
            over_25 * 100,

        "under_2_5":
            under_25 * 100,

        "btts_yes":
            btts_yes * 100,

        "btts_no":
            btts_no * 100,

    }


# ============================================================
# EXPECTED GOALS FROM FORM
# ============================================================

def expected_goals_from_form(
    home_stats: dict,
    away_stats: dict,
):

    home_matches = max(
        home_stats.get(
            "matches",
            0
        ),
        1
    )

    away_matches = max(
        away_stats.get(
            "matches",
            0
        ),
        1
    )

    home_attack = (
        home_stats.get(
            "goals_for",
            0
        )
        / home_matches
    )

    home_defense = (
        home_stats.get(
            "goals_against",
            0
        )
        / home_matches
    )

    away_attack = (
        away_stats.get(
            "goals_for",
            0
        )
        / away_matches
    )

    away_defense = (
        away_stats.get(
            "goals_against",
            0
        )
        / away_matches
    )

    # Simple blend
    expected_home = (
        home_attack * 0.65
        + away_defense * 0.35
    )

    expected_away = (
        away_attack * 0.65
        + home_defense * 0.35
    )

    # Home advantage
    expected_home *= 1.08

    # Prevent unrealistic zero
    expected_home = max(
        0.20,
        min(
            expected_home,
            4.0
        )
    )

    expected_away = max(
        0.20,
        min(
            expected_away,
            4.0
        )
    )

    return (
        expected_home,
        expected_away
    )


# ============================================================
# FORM ADJUSTMENT
# ============================================================

def apply_form_adjustment(
    probabilities: dict,
    home_stats: dict,
    away_stats: dict,
):

    home_form = form_strength(
        home_stats
    )

    away_form = form_strength(
        away_stats
    )

    difference = (
        home_form
        - away_form
    )

    # Small adjustment only
    adjustment = (
        difference
        * 8.0
    )

    result = dict(
        probabilities
    )

    result["home_win"] += (
        adjustment
    )

    result["away_win"] -= (
        adjustment
    )

    # Keep all probabilities sane
    for key in result:

        result[key] = max(
            0.0,
            min(
                100.0,
                result[key]
            )
        )

    return result


# ============================================================
# GET HISTORICAL RESULTS
# ============================================================

def get_historical_results():

    if not FOOTBALL_DATA_AVAILABLE:

        return []

    try:

        if hasattr(
            football_data,
            "get_all_results"
        ):

            results = (
                football_data
                .get_all_results()
            )

            if results:

                return results

    except Exception as error:

        print(
            "⚠️ get_all_results error:",
            error
        )

    return []


# ============================================================
# CONVERT RESULT OBJECT
# ============================================================

def result_to_dict(
    result,
):

    if isinstance(
        result,
        dict
    ):

        return result

    data = {}

    attributes = [

        "home_team",

        "away_team",

        "home_score",

        "away_score",

        "date",

        "league",

        "match_date",

    ]

    for attribute in attributes:

        try:

            data[attribute] = getattr(
                result,
                attribute
            )

        except Exception:

            pass

    # Alternative names
    if "home_team" not in data:

        try:

            data["home_team"] = getattr(
                result,
                "home"
            )

        except Exception:

            pass

    if "away_team" not in data:

        try:

            data["away_team"] = getattr(
                result,
                "away"
            )

        except Exception:

            pass

    return data


# ============================================================
# NORMALIZE RESULTS
# ============================================================

def normalize_results(
    results,
):

    normalized = []

    for result in results:

        data = result_to_dict(
            result
        )

        if not data:

            continue

        home = (
            data.get(
                "home_team"
            )
            or data.get(
                "home"
            )
            or ""
        )

        away = (
            data.get(
                "away_team"
            )
            or data.get(
                "away"
            )
            or ""
        )

        if not home or not away:

            continue

        try:

            home_score = int(
                data.get(
                    "home_score",
                    data.get(
                        "home_goals",
                        0
                    )
                )
            )

            away_score = int(
                data.get(
                    "away_score",
                    data.get(
                        "away_goals",
                        0
                    )
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            continue

        normalized.append({

            "home_team":
                str(home),

            "away_team":
                str(away),

            "home_score":
                home_score,

            "away_score":
                away_score,

            "date":
                data.get(
                    "date",
                    data.get(
                        "match_date",
                        ""
                    )
                ),

            "league":
                data.get(
                    "league",
                    ""
                ),

        })

    return normalized


# ============================================================
# PREDICT MATCH
# ============================================================

def predict_match_probability(
    home_team: str,
    away_team: str,
    historical_results,
):

    results = normalize_results(
        historical_results
    )

    if not results:

        return {}

    home_stats = calculate_team_form(
        results,
        home_team
    )

    away_stats = calculate_team_form(
        results,
        away_team
    )

    if (
        home_stats["matches"]
        < MIN_HISTORY_MATCHES
        or
        away_stats["matches"]
        < MIN_HISTORY_MATCHES
    ):

        return {}

    (
        expected_home,
        expected_away
    ) = expected_goals_from_form(
        home_stats,
        away_stats
    )

    probabilities = (
        calculate_market_probabilities(
            expected_home,
            expected_away
        )
    )

    probabilities = (
        apply_form_adjustment(
            probabilities,
            home_stats,
            away_stats
        )
    )

    return probabilities


# ============================================================
# MARKET SELECTION PROBABILITY
# ============================================================

def selection_probability(
    selection: OddsSelection,
    probabilities: dict,
) -> Optional[float]:

    market = (
        selection.market
        or ""
    ).lower().strip()

    name = (
        selection.selection
        or ""
    ).lower().strip()

    # --------------------------------------------------------
    # 1X2
    # --------------------------------------------------------

    if market == "1x2":

        home = normalize_team_name(
            selection.home_team
        )

        away = normalize_team_name(
            selection.away_team
        )

        selected = normalize_team_name(
            selection.selection
        )

        if selected == home:

            return probabilities.get(
                "home_win"
            )

        if selected == away:

            return probabilities.get(
                "away_win"
            )

        if selected == "draw":

            return probabilities.get(
                "draw"
            )

        return None

    # --------------------------------------------------------
    # OVER / UNDER
    # --------------------------------------------------------

    if (
        market == "over/under"
        or
        "over" in market
        or
        "under" in market
    ):

        if name == "over 1.5":

            return probabilities.get(
                "over_1_5"
            )

        if name == "under 1.5":

            return probabilities.get(
                "under_1_5"
            )

        if name == "over 2.5":

            return probabilities.get(
                "over_2_5"
            )

        if name == "under 2.5":

            return probabilities.get(
                "under_2_5"
            )

        # Generic parser
        if "over 1.5" in name:

            return probabilities.get(
                "over_1_5"
            )

        if "under 1.5" in name:

            return probabilities.get(
                "under_1_5"
            )

        if "over 2.5" in name:

            return probabilities.get(
                "over_2_5"
            )

        if "under 2.5" in name:

            return probabilities.get(
                "under_2_5"
            )

    # --------------------------------------------------------
    # BTTS
    # --------------------------------------------------------

    if (
        "btts" in market
        or
        "both teams" in market
    ):

        if (
            name == "yes"
            or "yes" in name
        ):

            return probabilities.get(
                "btts_yes"
            )

        if (
            name == "no"
            or "no" in name
        ):

            return probabilities.get(
                "btts_no"
            )

    return None


# ============================================================
# BUILD CANDIDATES
# ============================================================

def build_candidates(
    selections: list[OddsSelection],
    historical_results,
) -> list[Candidate]:

    candidates = []

    probability_cache = {}

    for selection in selections:

        key = match_key(
            selection.home_team,
            selection.away_team
        )

        if key not in probability_cache:

            probability_cache[key] = (
                predict_match_probability(
                    selection.home_team,
                    selection.away_team,
                    historical_results
                )
            )

        probabilities = (
            probability_cache[key]
        )

        probability = (
            selection_probability(
                selection,
                probabilities
            )
        )

        # ----------------------------------------------------
        # If historical model cannot calculate:
        # use implied probability ONLY as baseline.
        # It is NOT called model probability.
        # ----------------------------------------------------

        if probability is None:

            probability = (
                calculate_implied_probability(
                    selection.odds
                )
            )

        implied = (
            calculate_implied_probability(
                selection.odds
            )
        )

        edge = (
            probability
            - implied
        )

        confidence = "LOW"

        if probability >= 80:

            confidence = "HIGH"

        elif probability >= 75:

            confidence = "MEDIUM"

        candidates.append(

            Candidate(

                match_id=(
                    selection.match_id
                ),

                home_team=(
                    selection.home_team
                ),

                away_team=(
                    selection.away_team
                ),

                league=(
                    selection.league
                    or ""
                ),

                market=(
                    selection.market
                ),

                selection=(
                    selection.selection
                ),

                odds=float(
                    selection.odds
                ),

                bookmaker=(
                    selection.bookmaker
                    or "Unknown"
                ),

                commence_time=(
                    selection.commence_time
                ),

                probability=float(
                    probability
                ),

                implied_probability=float(
                    implied
                ),

                edge=float(
                    edge
                ),

                confidence=confidence,

            )

        )

    return candidates


# ============================================================
# FILTER QUALIFIED CANDIDATES
# ============================================================

def filter_candidates(
    candidates: list[Candidate],
) -> list[Candidate]:

    qualified = []

    for candidate in candidates:

        if candidate.odds <= 1.0:

            continue

        if (
            candidate.probability
            < MIN_PROBABILITY
        ):

            continue

        qualified.append(
            candidate
        )

    # Highest probability first
    qualified.sort(

        key=lambda x: (
            x.probability,
            x.edge,
            x.odds
        ),

        reverse=True

    )

    return qualified


# ============================================================
# REMOVE DUPLICATE MARKET
# ============================================================

def remove_duplicate_candidates(
    candidates,
):

    unique = {}

    for candidate in candidates:

        key = (

            candidate.match_id,

            candidate.market,

            candidate.selection,

        )

        if key not in unique:

            unique[key] = candidate

    return list(
        unique.values()
    )


# ============================================================
# CHECK SAME MATCH
# ============================================================

def same_match(
    a: Candidate,
    b: Candidate,
) -> bool:

    if (
        a.match_id
        and b.match_id
        and a.match_id == b.match_id
    ):

        return True

    return (
        teams_match(
            a.home_team,
            b.home_team
        )
        and
        teams_match(
            a.away_team,
            b.away_team
        )
    )


# ============================================================
# COMBINED ODDS
# ============================================================

def combined_odds(
    legs: list[Candidate],
) -> float:

    result = 1.0

    for leg in legs:

        result *= leg.odds

    return round(
        result,
        2
    )


# ============================================================
# ESTIMATED JOINT PROBABILITY
# ============================================================

def joint_probability(
    legs: list[Candidate],
) -> float:

    result = 1.0

    for leg in legs:

        result *= (
            leg.probability
            / 100.0
        )

    return round(
        result * 100.0,
        4
    )


# ============================================================
# ACC SCORE
# ============================================================

def accumulator_score(
    legs: list[Candidate],
) -> float:

    if not legs:

        return 0.0

    odds = combined_odds(
        legs
    )

    avg_probability = (
        sum(
            leg.probability
            for leg in legs
        )
        / len(legs)
    )

    lowest_probability = min(
        leg.probability
        for leg in legs
    )

    # Prefer probability and reasonable odds
    score = (
        lowest_probability
        * 0.55
        +
        avg_probability
        * 0.25
        +
        min(
            odds,
            10.0
        )
        * 2.0
    )

    return round(
        score,
        4
    )


# ============================================================
# GENERATE ACCUMULATORS
# ============================================================

def generate_accumulators(
    candidates: list[Candidate],
) -> list[Accumulator]:

    candidates = (
        remove_duplicate_candidates(
            candidates
        )
    )

    accumulators = []

    max_legs = min(
        MAX_LEGS,
        len(candidates)
    )

    for number_of_legs in range(
        MIN_LEGS,
        max_legs + 1
    ):

        for combination in itertools.combinations(
            candidates,
            number_of_legs
        ):

            valid = True

            # ----------------------------------------------
            # No two selections from same match
            # ----------------------------------------------

            for i in range(
                len(combination)
            ):

                for j in range(
                    i + 1,
                    len(combination)
                ):

                    if same_match(
                        combination[i],
                        combination[j]
                    ):

                        valid = False

                        break

                if not valid:

                    break

            if not valid:

                continue

            legs = list(
                combination
            )

            # --------------------------------------------------
            # 6-HOUR KICKOFF WINDOW
            # --------------------------------------------------
            # All legs must start within 6 hours of the earliest
            # kickoff. Today + tomorrow is allowed across midnight.
            if not within_six_hour_window(legs):
                continue

            odds = combined_odds(
                legs
            )

            if odds < MIN_COMBINED_ODDS:

                continue

            probabilities = [
                leg.probability
                for leg in legs
            ]

            average_probability = (
                sum(probabilities)
                / len(probabilities)
            )

            lowest_probability = min(
                probabilities
            )

            estimated_joint = (
                joint_probability(
                    legs
                )
            )

            score = accumulator_score(
                legs
            )

            accumulators.append(

                Accumulator(

                    legs=legs,

                    combined_odds=odds,

                    average_probability=round(
                        average_probability,
                        2
                    ),

                    lowest_probability=round(
                        lowest_probability,
                        2
                    ),

                    estimated_joint_probability=(
                        estimated_joint
                    ),

                    score=score,

                )

            )

    # Best score first
    accumulators.sort(

        key=lambda x: (
            x.score,
            x.lowest_probability,
            x.combined_odds
        ),

        reverse=True

    )

    return accumulators


# ============================================================
# GET BEST ACC
# ============================================================

def get_best_accumulator(
    candidates: list[Candidate],
) -> Optional[Accumulator]:

    accumulators = (
        generate_accumulators(
            candidates
        )
    )

    if not accumulators:

        return None

    return accumulators[0]


# ============================================================
# FORMAT CANDIDATE
# ============================================================

def format_candidate(
    candidate: Candidate,
) -> str:

    return (

        f"⚽ <b>"
        f"{candidate.home_team}"
        f" vs "
        f"{candidate.away_team}"
        f"</b>\n"

        f"📌 {candidate.market}: "
        f"<b>{candidate.selection}</b>\n"

        f"💰 Odds: "
        f"<b>{candidate.odds:.2f}</b>\n"

        f"🤖 Probability: "
        f"<b>{candidate.probability:.1f}%</b>\n"

        f"📊 Implied: "
        f"{candidate.implied_probability:.1f}%\n"

        f"📈 Edge: "
        f"{candidate.edge:+.1f}%\n"

        f"🏦 {candidate.bookmaker}\n"

        f"🟢 Confidence: "
        f"{candidate.confidence}"

    )


# ============================================================
# FORMAT ACCUMULATOR
# ============================================================

def format_accumulator(
    accumulator: Accumulator,
) -> str:

    lines = []

    lines.append(
        "🎯 <b>KHMER NEWS 24 — ACC</b>"
    )

    lines.append("")

    lines.append(
        f"📌 Legs: "
        f"<b>{len(accumulator.legs)}</b>"
    )

    lines.append(
        f"💰 Combined Odds: "
        f"<b>{accumulator.combined_odds:.2f}</b>"
    )

    lines.append(
        f"📊 Average Probability: "
        f"<b>{accumulator.average_probability:.1f}%</b>"
    )

    lines.append(
        f"📉 Lowest Probability: "
        f"<b>{accumulator.lowest_probability:.1f}%</b>"
    )

    if accumulator.legs:
        kickoff_times = [
            candidate_datetime(leg)
            for leg in accumulator.legs
        ]
        kickoff_times = [
            value for value in kickoff_times
            if value is not None
        ]

        if kickoff_times:
            earliest = min(kickoff_times)
            latest = max(kickoff_times)
            gap_hours = (
                latest - earliest
            ).total_seconds() / 3600.0

            lines.append(
                f"⏱️ Kickoff window: "
                f"<b>{gap_hours:.1f}h</b> / "
                f"{ACC_MAX_TIME_GAP_HOURS}h max"
            )

    lines.append("")

    for index, leg in enumerate(
        accumulator.legs,
        start=1
    ):

        lines.append(
            f"<b>{index}.</b> "
            f"{leg.home_team} "
            f"vs "
            f"{leg.away_team}"
        )

        lines.append(
            f"   🕐 {format_kickoff(leg.commence_time)} GMT+7"
        )

        lines.append(
            f"   📌 {leg.market}: "
            f"<b>{leg.selection}</b>"
        )

        lines.append(
            f"   💰 {leg.odds:.2f}"
            f" | 🤖 {leg.probability:.1f}%"
        )

        lines.append("")

    lines.append(
        "━━━━━━━━━━━━━━━━━━"
    )

    lines.append(
        "⚠️ Probability is an estimate, "
        "not a guarantee."
    )

    lines.append(
        "📊 Odds are from real bookmaker data."
    )

    return "\n".join(
        lines
    )


# ============================================================
# FORMAT CANDIDATES
# ============================================================

def format_candidates(
    candidates: list[Candidate],
    limit: int = 20,
) -> str:

    if not candidates:

        return (
            "❌ No qualified candidates.\n\n"
            f"Requirement:\n"
            f"• Probability ≥ {MIN_PROBABILITY}%\n"
        )

    lines = []

    lines.append(
        "🎯 <b>QUALIFIED BETTING CANDIDATES</b>"
    )

    lines.append("")

    for index, candidate in enumerate(
        candidates[:limit],
        start=1
    ):

        lines.append(
            f"<b>{index}.</b> "
            f"{candidate.home_team} "
            f"vs "
            f"{candidate.away_team}"
        )

        lines.append(
            f"   📌 {candidate.selection}"
        )

        lines.append(
            f"   💰 Odds: "
            f"{candidate.odds:.2f}"
        )

        lines.append(
            f"   🤖 Probability: "
            f"{candidate.probability:.1f}%"
        )

        lines.append(
            f"   📈 Edge: "
            f"{candidate.edge:+.1f}%"
        )

        lines.append("")

    return "\n".join(
        lines
    )


# ============================================================
# LOAD REAL ODDS
# ============================================================

def load_real_odds(
    leagues=None,
):

    print()
    print("=" * 70)
    print(
        "KHMER NEWS 24 — REAL ODDS"
    )
    print("=" * 70)

    selections = get_all_odds(
        leagues=leagues,
        regions=DEFAULT_REGIONS,
    )

    print()

    print(
        f"📊 Total real selections: "
        f"{len(selections)}"
    )

    return selections


# ============================================================
# RUN ENGINE
# ============================================================

def run_engine(
    leagues=None,
):

    print()
    print("=" * 70)
    print(
        "🎯 KHMER NEWS 24 — ACC ENGINE"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # STEP 1 — REAL ODDS
    # --------------------------------------------------------

    selections = load_real_odds(
        leagues=leagues
    )

    # --------------------------------------------------------
    # STEP 1B — TODAY + TOMORROW ONLY (CAMBODIA GMT+7)
    # --------------------------------------------------------
    all_selections_count = len(selections)

    selections = filter_today_tomorrow_selections(
        selections
    )

    today = datetime.now(CAMBODIA_TZ).date()
    tomorrow = today + timedelta(days=1)

    print()
    print(
        f"📅 ACC dates: {today.isoformat()} + {tomorrow.isoformat()}"
    )
    print(
        f"⏱️ Max kickoff gap: "
        f"{ACC_MAX_TIME_GAP_HOURS} hours"
    )
    print(
        f"🧹 Date-filtered selections: "
        f"{len(selections)}/{all_selections_count}"
    )

    if not selections:

        print()
        print(
            "❌ No real odds received."
        )

        return {
            "selections": [],
            "all_candidates": [],
            "candidates": [],
            "accumulators": [],
            "best": None,
        }

    # --------------------------------------------------------
    # STEP 2 — HISTORICAL DATA
    # --------------------------------------------------------

    historical_results = (
        get_historical_results()
    )

    print()

    print(
        f"📚 Historical results: "
        f"{len(historical_results)}"
    )

    if not historical_results:

        print(
            "⚠️ Historical data unavailable."
        )

        print(
            "Using market-implied "
            "probability as baseline."
        )

    # --------------------------------------------------------
    # STEP 3 — CANDIDATES
    # --------------------------------------------------------

    candidates = build_candidates(

        selections,

        historical_results

    )

    print()

    print(
        f"🔎 Candidates created: "
        f"{len(candidates)}"
    )

    # --------------------------------------------------------
    # STEP 4 — FILTER
    # --------------------------------------------------------

    qualified = (
        filter_candidates(
            candidates
        )
    )

    print(
        f"✅ Qualified selections: "
        f"{len(qualified)}"
    )

    # --------------------------------------------------------
    # STEP 5 — ACC
    # --------------------------------------------------------

    accumulators = (
        generate_accumulators(
            qualified
        )
    )

    print(
        f"🎯 ACC combinations: "
        f"{len(accumulators)}"
    )

    # --------------------------------------------------------
    # STEP 6 — BEST
    # --------------------------------------------------------

    best = None

    if accumulators:

        best = accumulators[0]

    return {

        "selections":
            selections,

        "candidates":
            qualified,

        "accumulators":
            accumulators,

        "best":
            best,

    }


# ============================================================
# PRINT RESULTS
# ============================================================

def print_results(
    result,
):

    print()

    print("=" * 70)

    print(
        "🎯 QUALIFIED SELECTIONS"
    )

    print("=" * 70)

    candidates = result.get(
        "candidates",
        []
    )

    if not candidates:

        print(
            "❌ No qualified selections."
        )

    else:

        for index, candidate in enumerate(
            candidates[:20],
            start=1
        ):

            print()

            print(
                f"{index}. "
                f"{candidate.home_team}"
                f" vs "
                f"{candidate.away_team}"
            )

            print(
                f"   Market: "
                f"{candidate.market}"
            )

            print(
                f"   Selection: "
                f"{candidate.selection}"
            )

            print(
                f"   Odds: "
                f"{candidate.odds:.2f}"
            )

            print(
                f"   Probability: "
                f"{candidate.probability:.1f}%"
            )

            print(
                f"   Implied: "
                f"{candidate.implied_probability:.1f}%"
            )

            print(
                f"   Edge: "
                f"{candidate.edge:+.1f}%"
            )

    print()

    print("=" * 70)

    print(
        "🎯 ACC RESULTS"
    )

    print("=" * 70)

    accumulators = result.get(
        "accumulators",
        []
    )

    if not accumulators:

        print()

        print(
            "❌ No ACC meets "
            f"combined odds ≥ {MIN_COMBINED_ODDS:.2f}"
        )

    else:

        for index, accumulator in enumerate(
            accumulators[:10],
            start=1
        ):

            print()

            print(
                f"ACC #{index}"
            )

            print(
                f"   Legs: "
                f"{len(accumulator.legs)}"
            )

            print(
                f"   Combined Odds: "
                f"{accumulator.combined_odds:.2f}"
            )

            print(
                f"   Average Probability: "
                f"{accumulator.average_probability:.1f}%"
            )

            print(
                f"   Lowest Probability: "
                f"{accumulator.lowest_probability:.1f}%"
            )

            print(
                f"   Estimated Joint Probability: "
                f"{accumulator.estimated_joint_probability:.2f}%"
            )

            for leg in accumulator.legs:

                print(
                    f"      - "
                    f"{leg.home_team} "
                    f"vs "
                    f"{leg.away_team}"
                )

                print(
                    f"        "
                    f"{leg.market}: "
                    f"{leg.selection}"
                )

                print(
                    f"        "
                    f"Odds {leg.odds:.2f}"
                    f" | "
                    f"Prob {leg.probability:.1f}%"
                )

    print()

    print("=" * 70)

    print(
        "⚠️ END OF ANALYSIS"
    )

    print("=" * 70)


# ============================================================
# TELEGRAM TEXT
# ============================================================

def telegram_accumulator_text(
    result,
) -> str:

    candidates = result.get(
        "candidates",
        []
    )

    best = result.get(
        "best"
    )

    # --------------------------------------------------------
    # INDIVIDUAL MATCH ANALYSIS
    # --------------------------------------------------------
    # Show every qualified single-match selection at >= 80%.
    lines = [
        "📊 <b>INDIVIDUAL MATCH ANALYSIS</b>",
        "",
        f"📌 Each pick: Probability ≥ {MIN_PROBABILITY:.0f}%",
        "📅 Today + Tomorrow (GMT+7)",
        f"⏱️ ACC window: ≤ {ACC_MAX_TIME_GAP_HOURS} hours",
        "",
    ]

    if candidates:
        for index, candidate in enumerate(
            candidates[:20],
            start=1
        ):
            lines.append(
                f"<b>{index}.</b> "
                f"{candidate.home_team} vs "
                f"{candidate.away_team}"
            )
            lines.append(
                f"   🕐 {format_kickoff(candidate.commence_time)} GMT+7"
            )
            lines.append(
                f"   📌 {candidate.market}: "
                f"<b>{candidate.selection}</b>"
            )
            lines.append(
                f"   💰 Odds: <b>{candidate.odds:.2f}</b>"
            )
            lines.append(
                f"   🤖 Probability: "
                f"<b>{candidate.probability:.1f}%</b>"
            )
            lines.append(
                f"   📈 Edge: {candidate.edge:+.1f}%"
            )
            lines.append("")
    else:
        lines.append(
            "❌ មិនមាន Match ដែល Model Probability "
            f"≥ {MIN_PROBABILITY:.0f}% ទេ។"
        )
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("🎯 <b>ACC RESULT</b>")
    lines.append("")

    if not best:
        lines.extend([
            "❌ មិនទាន់រកឃើញ ACC ដែលបំពេញលក្ខខណ្ឌទេ។",
            "",
            f"📌 Each leg Probability ≥ {MIN_PROBABILITY:.0f}%",
            f"📌 Combined Odds ≥ {MIN_COMBINED_ODDS:.2f}",
            f"📌 Legs: {MIN_LEGS}-{MAX_LEGS}",
            "📌 Match dates: Today + Tomorrow (GMT+7)",
            f"📌 Kickoff gap: ≤ {ACC_MAX_TIME_GAP_HOURS} hours",
            "",
            "⚠️ Probability គឺជាការប៉ាន់ស្មាន "
            "មិនមែនការធានាឈ្នះទេ។",
        ])
        return "\n".join(lines)

    lines.append(
        format_accumulator(best)
    )

    return "\n".join(lines)


# ============================================================
# MAIN TEST
# ============================================================

def main():

    print()

    print(
        "🚀 Starting ACC Engine..."
    )

    print()

    result = run_engine(

        leagues=[

            "Premier League",

            "La Liga",

            "Serie A",

            "Bundesliga",

            "Ligue 1",

            "Champions League",

            "Europa League",

            "Conference League",

            "Eredivisie",

            "Primeira Liga",

            "MLS",

        ]

    )

    print_results(
        result
    )

    print()

    print("=" * 70)

    print(
        "📱 TELEGRAM PREVIEW"
    )

    print("=" * 70)

    print()

    print(
        telegram_accumulator_text(
            result
        )
    )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()