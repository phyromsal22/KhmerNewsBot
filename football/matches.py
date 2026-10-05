"""
🇰🇭 Khmer News 24
GLOBAL FOOTBALL MATCH ENGINE V5

Coverage:
- International football
- UEFA Nations League
- CONCACAF Nations League
- World Cup
- World Cup Qualifiers
- Euro
- Asian Cup
- AFCON
- Copa America
- Gold Cup
- Champions League
- Europa League
- Conference League
- Major domestic leagues
- Major domestic cups
- Other countries
- Today + Tomorrow
- Cambodia timezone GMT+7
"""

import os
import re
import requests

from datetime import datetime, timedelta
from html import escape
from dotenv import load_dotenv
from zoneinfo import ZoneInfo


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

API_URL = "https://v3.football.api-sports.io/fixtures"

TIMEZONE = "Asia/Phnom_Penh"

REQUEST_TIMEOUT = 20

# Maximum main matches per category
MAX_INTERNATIONAL = 20
MAX_CLUB = 20
MAX_SECONDARY = 10


# =========================================================
# PRIORITY COUNTRIES
# =========================================================

PRIORITY_COUNTRIES = {
    "England",
    "Spain",
    "Italy",
    "Germany",
    "France",
    "Netherlands",
    "Portugal",
    "Belgium",
    "Turkey",
    "Scotland",
    "Greece",
    "Austria",
    "Switzerland",
    "Denmark",
    "Norway",
    "Sweden",
    "Poland",
    "Croatia",
    "Serbia",
    "Brazil",
    "Argentina",
    "Mexico",
    "United States",
    "Colombia",
    "Chile",
    "Japan",
    "South Korea",
    "Saudi Arabia",
    "China",
    "Australia",
    "Thailand",
    "Vietnam",
    "Indonesia",
    "Malaysia",
    "India",
    "Cambodia",
}


# =========================================================
# INTERNATIONAL COMPETITIONS
# =========================================================

INTERNATIONAL_KEYWORDS = [
    "Nations League",
    "World Cup",
    "World Cup Qualifiers",
    "World Cup Qualification",
    "European Championship",
    "Euro Championship",
    "Euro Qualifiers",
    "Asian Cup",
    "Asian Cup Qualification",
    "Africa Cup",
    "African Cup",
    "AFCON",
    "Copa America",
    "Gold Cup",
    "CONCACAF Nations League",
    "CONMEBOL",
    "AFC Asian Cup",
    "International Friendlies",
]


# =========================================================
# IMPORTANT CLUB COMPETITIONS
# =========================================================

IMPORTANT_CLUB_KEYWORDS = [
    "Champions League",
    "Europa League",
    "Conference League",
    "Libertadores",
    "Sudamericana",

    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Eredivisie",
    "Primeira Liga",

    "FA Cup",
    "Copa del Rey",
    "Coppa Italia",
    "DFB-Pokal",
    "Coupe de France",
    "KNVB",
    "Community Shield",

    "MLS",
    "Brasileirao",
]


# =========================================================
# MAJOR LEAGUE EXACT NAMES
# =========================================================

MAJOR_LEAGUES = {
    "premier league",
    "la liga",
    "serie a",
    "bundesliga",
    "ligue 1",
    "eredivisie",
    "primeira liga",
    "championship",
    "scottish premiership",
    "super lig",
    "jupiler pro league",
    "super league",
    "mls",
    "brasileirao",
    "liga profesional argentina",
    "primera a",
    "liga mx",
    "j1 league",
    "k league 1",
    "a-league",
}


# =========================================================
# MAJOR CUP KEYWORDS
# =========================================================

MAJOR_CUP_KEYWORDS = [
    "FA Cup",
    "Copa del Rey",
    "Coppa Italia",
    "DFB-Pokal",
    "Coupe de France",
    "KNVB Cup",
    "Taça de Portugal",
    "Scottish Cup",
    "Copa Chile",
]


# =========================================================
# SECONDARY / YOUTH
# =========================================================

SECONDARY_KEYWORDS = [
    "Women",
    "U21",
    "U20",
    "U19",
    "U18",
    "U17",
    "Youth",
    "Reserve",
    "Second Division",
    "Third Division",
    "Fourth Division",
    "Second Amateur",
    "First Amateur",
    "Third Amateur",
    "National 2",
    "National 3",
    "Tercera División",
    "Primera B",
    "Primera C",
    "Primera Nacional",
    "Serie C",
    "Serie D",
    "Liga Premier Serie A",
]


# =========================================================
# COUNTRY FLAGS
# =========================================================

COUNTRY_FLAGS = {
    "Spain": "🇪🇸",
    "England": "🏴",
    "Italy": "🇮🇹",
    "Germany": "🇩🇪",
    "France": "🇫🇷",
    "Portugal": "🇵🇹",
    "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪",
    "Brazil": "🇧🇷",
    "Argentina": "🇦🇷",
    "Mexico": "🇲🇽",
    "USA": "🇺🇸",
    "United States": "🇺🇸",
    "Oman": "🇴🇲",
    "Canada": "🇨🇦",
    "Peru": "🇵🇪",
    "Tunisia": "🇹🇳",
    "Mali": "🇲🇱",
    "Cameroon": "🇨🇲",
    "Comoros": "🇰🇲",
    "Kyrgyzstan": "🇰🇬",
    "Lebanon": "🇱🇧",
    "Cyprus": "🇨🇾",
    "Congo DR": "🇨🇩",
    "Mauritius": "🇲🇺",
    "Sri Lanka": "🇱🇰",
    "Uganda": "🇺🇬",
    "Tanzania": "🇹🇿",
    "Bolivia": "🇧🇴",
    "Gambia": "🇬🇲",
    "FYR Macedonia": "🇲🇰",
    "North Macedonia": "🇲🇰",
    "Cameroon": "🇨🇲",
    "Canada": "🇨🇦",
    "Peru": "🇵🇪",
    "Tunisia": "🇹🇳",
    "Mali": "🇲🇱",
    "Comoros": "🇰🇲",
    "Kyrgyzstan": "🇰🇬",
    "Lebanon": "🇱🇧",
    "Cyprus": "🇨🇾",
    "Congo DR": "🇨🇩",
    "Mauritius": "🇲🇺",
    "Sri Lanka": "🇱🇰",
    "Uganda": "🇺🇬",
    "Tanzania": "🇹🇿",
    "Bolivia": "🇧🇴",
    "Gambia": "🇬🇲",
    "Egypt": "🇪🇬",
    "Morocco": "🇲🇦",
    "Ghana": "🇬🇭",
    "Colombia": "🇨🇴",
    "Chile": "🇨🇱",
    "Japan": "🇯🇵",
    "South Korea": "🇰🇷",
    "China": "🇨🇳",
    "Australia": "🇦🇺",
    "Thailand": "🇹🇭",
    "Vietnam": "🇻🇳",
    "Cambodia": "🇰🇭",
    "Switzerland": "🇨🇭",
    "Austria": "🇦🇹",
    "Scotland": "🏴",
    "Greece": "🇬🇷",
    "Denmark": "🇩🇰",
    "Norway": "🇳🇴",
    "Sweden": "🇸🇪",
    "Poland": "🇵🇱",
    "Croatia": "🇭🇷",
    "Serbia": "🇷🇸",
    "Czech Republic": "🇨🇿",
    "Czechia": "🇨🇿",
    "Slovenia": "🇸🇮",
    "Slovakia": "🇸🇰",
    "Lithuania": "🇱🇹",
    "Latvia": "🇱🇻",
    "Estonia": "🇪🇪",
    "Kosovo": "🇽🇰",
    "Malta": "🇲🇹",
    "Andorra": "🇦🇩",
    "Azerbaijan": "🇦🇿",
    "North Macedonia": "🇲🇰",
    "Ireland": "🇮🇪",
    "Rep. Of Ireland": "🇮🇪",
    "Israel": "🇮🇱",
    "Ghana": "🇬🇭",
    "Egypt": "🇪🇬",
    "Morocco": "🇲🇦",
    "South Africa": "🇿🇦",
    "Nigeria": "🇳🇬",
    "Senegal": "🇸🇳",
    "Ivory-Coast": "🇨🇮",
    "Ivory Coast": "🇨🇮",
    "Burkina-Faso": "🇧🇫",
    "Burkina Faso": "🇧🇫",
    "Botswana": "🇧🇼",
    "Eswatini": "🇸🇿",
    "Mongolia": "🇲🇳",
    "Costa Rica": "🇨🇷",
    "Haiti": "🇭🇹",
    "Jamaica": "🇯🇲",
    "Guyana": "🇬🇾",
    "Dominica": "🇩🇲",
    "Puerto Rico": "🇵🇷",
    "Curaçao": "🇨🇼",
    "Trinidad and Tobago": "🇹🇹",
    "Nicaragua": "🇳🇮",
    "Dominican Republic": "🇩🇴",
}


# =========================================================
# API HEADERS
# =========================================================

def get_headers():

    if not API_KEY:
        raise RuntimeError(
            "❌ API_FOOTBALL_KEY មិនមានក្នុង .env"
        )

    return {
        "x-apisports-key": API_KEY
    }


# =========================================================
# DATE
# =========================================================

def get_date_string(day_offset=0):

    today = datetime.now(
        ZoneInfo(TIMEZONE)
    ).date()

    target = today + timedelta(
        days=day_offset
    )

    return target.strftime("%Y-%m-%d")


# =========================================================
# FETCH FIXTURES
# =========================================================

def fetch_fixtures(date_string):

    params = {
        "date": date_string,
        "timezone": TIMEZONE,
    }

    try:

        response = requests.get(
            API_URL,
            headers=get_headers(),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        errors = data.get("errors")

        if errors:
            print(
                "⚠️ API errors:",
                errors
            )

        fixtures = data.get(
            "response",
            []
        )

        print(
            f"📡 {date_string} → "
            f"{len(fixtures)} fixtures received"
        )

        return fixtures

    except requests.RequestException as e:

        print(
            "❌ API request error:",
            e
        )

        return []

    except Exception as e:

        print(
            "❌ Unexpected error:",
            e
        )

        return []


# =========================================================
# TEXT HELPERS
# =========================================================

def contains_keyword(text, keywords):

    text_lower = text.lower()

    for keyword in keywords:

        if keyword.lower() in text_lower:
            return True

    return False


# =========================================================
# SECONDARY DETECTION
# =========================================================

def is_youth_fixture(
    league,
    home,
    away
):
    """Return True for youth/U23 fixtures so they can be displayed separately."""
    league_name = league.get("name", "")
    text = f"{league_name} {home} {away}"

    return bool(re.search(
        r"\b(?:u17|u18|u19|u20|u21|u23|youth)\b",
        text,
        flags=re.IGNORECASE
    ))


def is_secondary_fixture(
    league,
    home,
    away
):

    league_name = league.get(
        "name",
        ""
    )

    text = (
        f"{league_name} "
        f"{home} "
        f"{away}"
    )

    # -----------------------------------------------------
    # Normal keywords
    # -----------------------------------------------------

    if contains_keyword(
        text,
        SECONDARY_KEYWORDS
    ):
        return True

    # -----------------------------------------------------
    # "II" only when it is a separate word
    # -----------------------------------------------------

    if re.search(
        r"\bII\b",
        text,
        flags=re.IGNORECASE
    ):
        return True

    return False


# =========================================================
# INTERNATIONAL DETECTION
# =========================================================

def is_international(league, home="", away=""):

    league_name = league.get("name", "")
    league_type = league.get("type", "")

    name_lower = league_name.lower().strip()
    home_lower = home.lower()
    away_lower = away.lower()

    # Club friendlies are club football, even if API labels them
    # under an international-style competition type.
    if "friendlies clubs" in name_lower or "club friendlies" in name_lower:
        return False

    # Clear international competitions.
    international_keywords = [
        "nations league",
        "world cup",
        "world cup qualifiers",
        "world cup qualification",
        "european championship",
        "euro championship",
        "euro qualifiers",
        "asian cup",
        "asian cup qualification",
        "africa cup",
        "african cup",
        "afcon",
        "copa america",
        "gold cup",
        "concacaf nations league",
        "international friendlies",
    ]

    for keyword in international_keywords:
        if keyword in name_lower:
            return True

    # Generic national-team Friendlies.
    if name_lower == "friendlies":
        return True

    # API says International. Do not override the explicit club-friendly
    # rule above.
    if league_type.lower() == "international":
        return True

    return False


# =========================================================
# CLUB DETECTION
# =========================================================

def is_major_club_competition(league):

    name = league.get(
        "name",
        ""
    )

    name_lower = name.lower()

    # Exact major league
    if name_lower in MAJOR_LEAGUES:
        return True

    # Major club competitions
    if contains_keyword(
        name,
        IMPORTANT_CLUB_KEYWORDS
    ):
        return True

    # Domestic cups
    if contains_keyword(
        name,
        MAJOR_CUP_KEYWORDS
    ):
        return True

    return False


# =========================================================
# PRIORITY
# =========================================================

def get_priority(
    league,
    home="",
    away=""
):

    name = league.get(
        "name",
        ""
    )

    country = league.get(
        "country",
        ""
    )

    name_lower = name.lower()

    score = 0

    # =====================================================
    # INTERNATIONAL
    # =====================================================

    if "nations league" in name_lower:
        score = 120

    elif "world cup" in name_lower:
        score = 120

    elif "european championship" in name_lower:
        score = 115

    elif "euro championship" in name_lower:
        score = 115

    elif "asian cup" in name_lower:
        score = 110

    elif "afcon" in name_lower:
        score = 110

    elif "africa cup" in name_lower:
        score = 110

    elif "copa america" in name_lower:
        score = 110

    elif "gold cup" in name_lower:
        score = 105

    elif "friendlies" in name_lower:
        score = 40

    # =====================================================
    # EUROPEAN CLUB COMPETITIONS
    # =====================================================

    elif "champions league" in name_lower:
        score = 100

    elif "europa league" in name_lower:
        score = 95

    elif "conference league" in name_lower:
        score = 90

    elif "libertadores" in name_lower:
        score = 90

    elif "sudamericana" in name_lower:
        score = 85

    # =====================================================
    # MAJOR DOMESTIC LEAGUES
    # =====================================================

    elif name_lower == "premier league":
        score = 90

    elif name_lower == "la liga":
        score = 90

    elif name_lower == "serie a":
        score = 90

    elif name_lower == "bundesliga":
        score = 90

    elif name_lower == "ligue 1":
        score = 90

    elif name_lower == "eredivisie":
        score = 85

    elif name_lower == "primeira liga":
        score = 85

    elif name_lower == "mls":
        score = 80

    elif name_lower == "brasileirao":
        score = 80

    elif name_lower == "liga profesional argentina":
        score = 80

    elif name_lower == "primera a":
        score = 80

    elif name_lower == "liga mx":
        score = 80

    elif name_lower == "j1 league":
        score = 75

    elif name_lower == "k league 1":
        score = 75

    elif name_lower == "a-league":
        score = 75

    # =====================================================
    # DOMESTIC CUPS
    # =====================================================

    elif "fa cup" in name_lower:
        score = 80

    elif "copa del rey" in name_lower:
        score = 80

    elif "coppa italia" in name_lower:
        score = 80

    elif "dfb-pokal" in name_lower:
        score = 80

    elif "coupe de france" in name_lower:
        score = 80

    elif "knvb" in name_lower:
        score = 75

    elif "copa chile" in name_lower:
        score = 70

    # =====================================================
    # OTHER COUNTRIES
    # =====================================================

    else:

        if country in PRIORITY_COUNTRIES:

            score = 55

        else:

            score = 30

    # =====================================================
    # INTERNATIONAL BONUS
    # =====================================================

    if is_international(league):

        score += 30

    # =====================================================
    # SECONDARY PENALTY
    # =====================================================

    if is_secondary_fixture(
        league,
        home,
        away
    ):

        score -= 60

    return score


# =========================================================
# NORMALIZE FIXTURE
# =========================================================

def normalize_fixture(fixture):

    fixture_info = fixture.get(
        "fixture",
        {}
    )

    league = fixture.get(
        "league",
        {}
    )

    teams = fixture.get(
        "teams",
        {}
    )

    home = teams.get(
        "home",
        {}
    )

    away = teams.get(
        "away",
        {}
    )

    kickoff = fixture_info.get(
        "date"
    )

    timestamp = fixture_info.get(
        "timestamp"
    )

    # -----------------------------------------------------
    # Convert UTC → Cambodia
    # -----------------------------------------------------

    try:

        if kickoff:

            dt = datetime.fromisoformat(
                kickoff.replace(
                    "Z",
                    "+00:00"
                )
            )

            local_dt = dt.astimezone(
                ZoneInfo(TIMEZONE)
            )

            time_string = local_dt.strftime(
                "%H:%M"
            )

        else:

            time_string = "--:--"

    except Exception:

        time_string = "--:--"

    home_name = home.get(
        "name",
        "Unknown"
    )

    away_name = away.get(
        "name",
        "Unknown"
    )

    youth = is_youth_fixture(
        league,
        home_name,
        away_name
    )

    secondary = is_secondary_fixture(
        league,
        home_name,
        away_name
    )

    international = is_international(
        league,
        home_name,
        away_name
    )

    priority = get_priority(
        league,
        home_name,
        away_name
    )

    return {
        "id": fixture_info.get(
            "id"
        ),

        "timestamp": timestamp,

        "time": time_string,

        "home": home_name,

        "away": away_name,

        "home_logo": home.get(
            "logo"
        ),

        "away_logo": away.get(
            "logo"
        ),

        "league": league.get(
            "name",
            "Unknown"
        ),

        "country": league.get(
            "country",
            "World"
        ),

        "type": league.get(
            "type",
            "Unknown"
        ),

        "priority": priority,

        "international": international,

        "secondary": secondary,

        "youth": youth,

        "status": fixture_info.get(
            "status",
            {}
        ).get(
            "short",
            ""
        ),
    }


# =========================================================
# CLASSIFY MATCHES
# =========================================================

def classify_matches(fixtures):

    international = []

    club = []

    secondary = []

    for fixture in fixtures:

        match = normalize_fixture(
            fixture
        )

        # Ignore useless / invalid matches
        if match["priority"] < 20:
            continue

        # -------------------------------------------------
        # Youth / U23 first
        # -------------------------------------------------

        if match["youth"]:

            secondary.append(
                match
            )

        # -------------------------------------------------
        # Secondary
        # -------------------------------------------------

        elif match["secondary"]:

            secondary.append(
                match
            )

        # -------------------------------------------------
        # International
        # -------------------------------------------------

        elif match["international"]:

            international.append(
                match
            )

        # -------------------------------------------------
        # Club
        # -------------------------------------------------

        else:

            club.append(
                match
            )

    return (
        international,
        club,
        secondary
    )


# =========================================================
# SORT
# =========================================================

def sort_matches(matches):

    return sorted(
        matches,
        key=lambda x: (
            -x["priority"],
            x["league"].lower(),
            x["timestamp"]
            if x["timestamp"]
            else 9999999999
        )
    )


# =========================================================
# GET MATCHES FOR ONE DAY
# =========================================================

def get_matches_for_day(
    day_offset=0
):

    date_string = get_date_string(
        day_offset
    )

    fixtures = fetch_fixtures(
        date_string
    )

    if not fixtures:

        return {
            "date": date_string,
            "international": [],
            "club": [],
            "secondary": [],
        }

    (
        international,
        club,
        secondary
    ) = classify_matches(
        fixtures
    )

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    international = sort_matches(
        international
    )

    club = sort_matches(
        club
    )

    secondary = sort_matches(
        secondary
    )

    # -----------------------------------------------------
    # Smart limits
    # -----------------------------------------------------

    international = international[
        :MAX_INTERNATIONAL
    ]

    club = club[
        :MAX_CLUB
    ]

    secondary = secondary[
        :MAX_SECONDARY
    ]

    return {
        "date": date_string,

        "international":
            international,

        "club":
            club,

        "secondary":
            secondary,
    }


# =========================================================
# FLAG
# =========================================================

def get_flag(value):

    return COUNTRY_FLAGS.get(
        value,
        "🌍"
    )


# =========================================================
# TELEGRAM HTML HELPER
# =========================================================

def html_text(value):
    """Escape Telegram HTML safely without encoding apostrophes."""
    value = str(value or "")
    return (
        value.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
    )

# =========================================================
# INTERNATIONAL MATCH FORMAT
# =========================================================

def format_international_match(match):
    home_flag = get_flag(match["home"])
    away_flag = get_flag(match["away"])

    return (
        f"{home_flag} <b>{html_text(match['home'])}</b> 🆚 "
        f"{away_flag} <b>{html_text(match['away'])}</b>\n"
        f"⏰ {html_text(match['time'])}"
    )


# =========================================================
# CLUB MATCH FORMAT
# =========================================================

def format_club_match(match):
    return (
        f"⚽ <b>{html_text(match['home'])}</b> 🆚 "
        f"<b>{html_text(match['away'])}</b>\n"
        f"⏰ {html_text(match['time'])}"
    )


# =========================================================
# INTERNATIONAL FORMAT
# =========================================================

def format_international(matches):
    if not matches:
        return ""

    lines = [
        "🌍 <b>INTERNATIONAL FOOTBALL</b>",
        "━━━━━━━━━━━━━━━━━━",
    ]

    current_league = None

    for match in matches:
        league = match["league"]

        if league != current_league:
            lines.append("")
            lines.append(f"🏆 <b>{html_text(league)}</b>")
            current_league = league

        lines.append("")
        lines.append(format_international_match(match))

    return "\n".join(lines).strip()


# =========================================================
# CLUB FORMAT
# =========================================================

def format_club(matches):
    if not matches:
        return ""

    lines = [
        "🏆 <b>CLUB FOOTBALL</b>",
        "━━━━━━━━━━━━━━━━━━",
    ]

    current_country = None
    current_league = None

    for match in matches:
        country = match["country"]
        league = match["league"]

        if country != current_country:
            lines.append("")
            lines.append(
                f"{get_flag(country)} <b>{html_text(country)}</b>"
            )
            current_country = country
            current_league = None

        if league != current_league:
            lines.append(f"🏆 {html_text(league)}")
            current_league = league

        lines.append("")
        lines.append(format_club_match(match))

    return "\n".join(lines).strip()


# =========================================================
# SECONDARY FORMAT
# =========================================================

def format_secondary(matches):
    if not matches:
        return ""

    lines = [
        "👶 <b>YOUTH / U23</b>",
        "━━━━━━━━━━━━━━━━━━",
    ]

    for match in matches:
        lines.append("")
        lines.append(
            f"⚽ <b>{html_text(match['home'])}</b> 🆚 "
            f"<b>{html_text(match['away'])}</b>"
        )
        lines.append(
            f"⏰ {html_text(match['time'])} | "
            f"🏆 {html_text(match['league'])}"
        )

    return "\n".join(lines).strip()


# =========================================================
# FORMAT ONE DAY

# =========================================================

def format_day(
    data,
    label
):

    date = data["date"]

    lines = [
        "⚽ <b>KHMER NEWS 24</b>",
        f"📅 <b>{label}</b>",
        "🇰🇭 ម៉ោងកម្ពុជា — GMT+7",
    ]

    # =====================================================
    # INTERNATIONAL
    # =====================================================

    international_text = format_international(
        data["international"]
    )

    if international_text:

        lines.append("")

        lines.append(
            international_text
        )

    # =====================================================
    # CLUB
    # =====================================================

    club_text = format_club(
        data["club"]
    )

    if club_text:

        lines.append("")

        lines.append(
            club_text
        )

    # =====================================================
    # SECONDARY
    # =====================================================

    secondary_text = format_secondary(
        data["secondary"]
    )

    if secondary_text:

        lines.append("")

        lines.append(
            secondary_text
        )

    # =====================================================
    # FOOTER
    # =====================================================

    lines.append("")

    lines.append(
        "━━━━━━━━━━━━━━━━━━"
    )

    lines.append(
        f"📆 {date}"
    )

    lines.append(
        "🇰🇭 Khmer News 24"
    )

    return "\n".join(
        lines
    )


# =========================================================
# SCAN TODAY + TOMORROW
# =========================================================

def scan_today_tomorrow():

    print()
    print("=" * 70)

    print(
        "🇰🇭 KHMER NEWS 24"
    )

    print(
        "⚽ GLOBAL FOOTBALL MATCH ENGINE V5"
    )

    print("=" * 70)

    # =====================================================
    # TODAY
    # =====================================================

    today = get_matches_for_day(
        0
    )

    # =====================================================
    # TOMORROW
    # =====================================================

    tomorrow = get_matches_for_day(
        1
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    print()

    print(
        f"📅 TODAY: "
        f"{len(today['international'])} "
        f"international | "
        f"{len(today['club'])} "
        f"club | "
        f"{len(today['secondary'])} "
        f"secondary"
    )

    print(
        f"📅 TOMORROW: "
        f"{len(tomorrow['international'])} "
        f"international | "
        f"{len(tomorrow['club'])} "
        f"club | "
        f"{len(tomorrow['secondary'])} "
        f"secondary"
    )

    # =====================================================
    # TELEGRAM PREVIEW
    # =====================================================

    today_text = format_day(
        today,
        "TODAY"
    )

    tomorrow_text = format_day(
        tomorrow,
        "TOMORROW"
    )

    # =====================================================
    # TODAY PREVIEW
    # =====================================================

    print()
    print("=" * 70)

    print(
        "📱 TELEGRAM PREVIEW — TODAY"
    )

    print("=" * 70)

    print()

    print(
        today_text
    )

    # =====================================================
    # TOMORROW PREVIEW
    # =====================================================

    print()
    print("=" * 70)

    print(
        "📱 TELEGRAM PREVIEW — TOMORROW"
    )

    print("=" * 70)

    print()

    print(
        tomorrow_text
    )

    return {
        "today": today,

        "tomorrow": tomorrow,

        "today_text":
            today_text,

        "tomorrow_text":
            tomorrow_text,
    }


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    if not API_KEY:

        print()
        print(
            "❌ API_FOOTBALL_KEY "
            "មិនមានក្នុង .env"
        )

        print()
        print(
            "👉 បន្ថែម:"
        )

        print(
            "API_FOOTBALL_KEY=YOUR_API_KEY"
        )

    else:

        try:

            scan_today_tomorrow()

        except KeyboardInterrupt:

            print()
            print(
                "🛑 Stopped by user."
            )

        except Exception as e:

            print()
            print(
                "❌ Fatal error:"
            )

            print(e)