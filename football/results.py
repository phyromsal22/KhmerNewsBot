# =========================================================
# 🇰🇭 KHMER NEWS 24
# FOOTBALL RESULTS ENGINE
# =========================================================

import os
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

API_URL = "https://v3.football.api-sports.io/fixtures"

TIMEZONE = "Asia/Phnom_Penh"

REQUEST_TIMEOUT = 20


# =========================================================
# HEADERS
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
# FETCH RESULTS
# =========================================================

def fetch_results(day_offset=0):

    date_string = get_date_string(
        day_offset
    )

    params = {
        "date": date_string,
        "timezone": TIMEZONE
    }

    try:

        response = requests.get(
            API_URL,
            headers=get_headers(),
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        fixtures = data.get(
            "response",
            []
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
# CHECK FINISHED
# =========================================================

def is_finished(fixture):

    status = (
        fixture
        .get("fixture", {})
        .get("status", {})
        .get("short", "")
    )

    finished_statuses = {
        "FT",
        "AET",
        "PEN"
    }

    return status in finished_statuses


# =========================================================
# NORMALIZE RESULT
# =========================================================

def normalize_result(fixture):

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

    goals = fixture.get(
        "goals",
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

    return {

        "id": fixture_info.get(
            "id"
        ),

        "home": home.get(
            "name",
            "Unknown"
        ),

        "away": away.get(
            "name",
            "Unknown"
        ),

        "home_goals": goals.get(
            "home"
        ),

        "away_goals": goals.get(
            "away"
        ),

        "league": league.get(
            "name",
            "Unknown"
        ),

        "country": league.get(
            "country",
            "World"
        ),

        "status": fixture_info.get(
            "status",
            {}
        ).get(
            "short",
            ""
        ),

        "elapsed": fixture_info.get(
            "status",
            {}
        ).get(
            "elapsed"
        ),

        "timestamp": fixture_info.get(
            "timestamp"
        )
    }


# =========================================================
# GET FINISHED RESULTS
# =========================================================

def get_results_for_day(day_offset=0):

    fixtures = fetch_results(
        day_offset
    )

    results = []

    for fixture in fixtures:

        if not is_finished(
            fixture
        ):
            continue

        result = normalize_result(
            fixture
        )

        results.append(
            result
        )

    results.sort(
        key=lambda x: (
            x["timestamp"]
            if x["timestamp"]
            else 9999999999
        )
    )

    return {
        "date": get_date_string(
            day_offset
        ),
        "results": results
    }


# =========================================================
# FORMAT RESULTS
# =========================================================

def format_results(data):

    date = data["date"]

    results = data["results"]

    lines = [

        "⚽ <b>KHMER NEWS 24</b>",

        "📊 <b>FOOTBALL RESULTS</b>",

        "🇰🇭 ម៉ោងកម្ពុជា — GMT+7",

        ""
    ]

    if not results:

        lines.append(
            "ℹ️ មិនទាន់មានលទ្ធផលការប្រកួតដែលបញ្ចប់ទេ។"
        )

    else:

        current_country = None
        current_league = None

        for match in results:

            country = match["country"]
            league = match["league"]

            if country != current_country:

                lines.append("")

                lines.append(
                    f"🌍 <b>{country}</b>"
                )

                current_country = country
                current_league = None

            if league != current_league:

                lines.append("")

                lines.append(
                    f"🏆 <b>{league}</b>"
                )

                current_league = league

            home_goals = (
                "-"
                if match["home_goals"] is None
                else str(match["home_goals"])
            )

            away_goals = (
                "-"
                if match["away_goals"] is None
                else str(match["away_goals"])
            )

            status = match["status"]

            lines.append("")

            lines.append(
                f"⚽ <b>{match['home']}</b> "
                f"<b>{home_goals}</b> - "
                f"<b>{away_goals}</b> "
                f"<b>{match['away']}</b>"
            )

            lines.append(
                f"✅ {status}"
            )

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
# MAIN TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "🇰🇭 KHMER NEWS 24"
    )

    print(
        "⚽ FOOTBALL RESULTS TEST"
    )

    print("=" * 60)

    data = get_results_for_day(
        0
    )

    print(
        f"\n📆 Date: {data['date']}"
    )

    print(
        f"📊 Finished matches: "
        f"{len(data['results'])}"
    )

    print("\n" + "=" * 60)

    print(
        format_results(data)
    )

    print("=" * 60)