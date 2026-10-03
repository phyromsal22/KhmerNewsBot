import json
import urllib.request
from datetime import datetime, timedelta, timezone


# ============================================================
# CAMBODIA TIME
# ============================================================

CAMBODIA_TZ = timezone(timedelta(hours=7))


# ============================================================
# ESPN SOCCER LEAGUES
# ============================================================
#
# We collect matches from many major competitions.
# More leagues can be added here later.
#
# ============================================================

FOOTBALL_LEAGUES = [
    # England
    ("🏴 England", "Premier League", "eng.1"),
    ("🏴 England", "Championship", "eng.2"),
    ("🏴 England", "League One", "eng.3"),
    ("🏴 England", "League Two", "eng.4"),
    ("🏴 England", "FA Cup", "eng.fa"),

    # Spain
    ("🇪🇸 Spain", "La Liga", "esp.1"),
    ("🇪🇸 Spain", "La Liga 2", "esp.2"),
    ("🇪🇸 Spain", "Copa del Rey", "esp.copa_del_rey"),

    # Italy
    ("🇮🇹 Italy", "Serie A", "ita.1"),
    ("🇮🇹 Italy", "Serie B", "ita.2"),
    ("🇮🇹 Italy", "Coppa Italia", "ita.coppa_italia"),

    # Germany
    ("🇩🇪 Germany", "Bundesliga", "ger.1"),
    ("🇩🇪 Germany", "2. Bundesliga", "ger.2"),
    ("🇩🇪 Germany", "DFB Pokal", "ger.dfb_pokal"),

    # France
    ("🇫🇷 France", "Ligue 1", "fra.1"),
    ("🇫🇷 France", "Ligue 2", "fra.2"),
    ("🇫🇷 France", "Coupe de France", "fra.coupe_de_france"),

    # Netherlands
    ("🇳🇱 Netherlands", "Eredivisie", "ned.1"),

    # Portugal
    ("🇵🇹 Portugal", "Primeira Liga", "por.1"),

    # Belgium
    ("🇧🇪 Belgium", "Belgian Pro League", "bel.1"),

    # Turkey
    ("🇹🇷 Turkey", "Super Lig", "tur.1"),

    # Scotland
    ("🏴 Scotland", "Scottish Premiership", "sco.1"),

    # Greece
    ("🇬🇷 Greece", "Super League", "gre.1"),

    # Austria
    ("🇦🇹 Austria", "Bundesliga", "aut.1"),

    # Switzerland
    ("🇨🇭 Switzerland", "Super League", "sui.1"),

    # Denmark
    ("🇩🇰 Denmark", "Superliga", "den.1"),

    # Sweden
    ("🇸🇪 Sweden", "Allsvenskan", "swe.1"),

    # Norway
    ("🇳🇴 Norway", "Eliteserien", "nor.1"),

    # USA
    ("🇺🇸 USA", "MLS", "usa.1"),

    # Brazil
    ("🇧🇷 Brazil", "Brasileirao", "bra.1"),

    # Argentina
    ("🇦🇷 Argentina", "Liga Profesional", "arg.1"),

    # Mexico
    ("🇲🇽 Mexico", "Liga MX", "mex.1"),

    # Japan
    ("🇯🇵 Japan", "J League", "jpn.1"),

    # South Korea
    ("🇰🇷 South Korea", "K League 1", "kor.1"),

    # Australia
    ("🇦🇺 Australia", "A-League", "aus.1"),

    # Saudi Arabia
    ("🇸🇦 Saudi Arabia", "Saudi Pro League", "ksa.1"),

    # China
    ("🇨🇳 China", "Chinese Super League", "chn.1"),

    # India
    ("🇮🇳 India", "Indian Super League", "ind.1"),

    # Thailand
    ("🇹🇭 Thailand", "Thai League 1", "tha.1"),

    # International
    ("🌍 Europe", "Champions League", "uefa.champions"),
    ("🌍 Europe", "Europa League", "uefa.europa"),
    ("🌍 Europe", "Conference League", "uefa.europa.conf"),

    # South America
    ("🌎 South America", "Copa Libertadores", "conmebol.libertadores"),
    ("🌎 South America", "Copa Sudamericana", "conmebol.sudamericana"),
]


# ============================================================
# ESPN URL
# ============================================================

ESPN_BASE_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/"
    "soccer/{league}/scoreboard?dates={date}"
)


# ============================================================
# HTTP GET
# ============================================================

def fetch_json(url):
    """
    Download JSON from ESPN.
    """

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "KhmerNews24 Football Bot"
            )
        },
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=12
        ) as response:

            data = response.read()

            return json.loads(
                data.decode("utf-8")
            )

    except Exception as error:

        print(
            f"⚠️ ESPN request failed: {error}"
        )

        return {}


# ============================================================
# DATE
# ============================================================

def get_cambodia_date(offset_days=0):

    now = datetime.now(
        CAMBODIA_TZ
    )

    target = now + timedelta(
        days=offset_days
    )

    return target.strftime(
        "%Y%m%d"
    )


# ============================================================
# TIME FORMAT
# ============================================================

def format_khmer_time(date_string):

    try:

        dt = datetime.fromisoformat(
            date_string.replace(
                "Z",
                "+00:00"
            )
        )

        dt = dt.astimezone(
            CAMBODIA_TZ
        )

        return dt.strftime(
            "%I:%M %p"
        ).lstrip("0")

    except Exception:

        return "N/A"


# ============================================================
# MATCH STATUS
# ============================================================

def get_match_status(event):

    try:

        status = (
            event
            .get("competitions", [{}])[0]
            .get("status", {})
        )

        status_type = status.get(
            "type",
            {}
        )

        state = status_type.get(
            "state",
            ""
        )

        completed = status_type.get(
            "completed",
            False
        )

        detail = status_type.get(
            "shortDetail",
            ""
        )

        if completed or state == "post":

            return "FT", detail

        if state == "in":

            return "LIVE", detail

        return "UPCOMING", detail

    except Exception:

        return "UPCOMING", ""


# ============================================================
# GET SCORE
# ============================================================

def get_scores(event):

    try:

        competitors = (
            event
            .get("competitions", [{}])[0]
            .get("competitors", [])
        )

        home_score = "-"
        away_score = "-"

        for team in competitors:

            home_away = team.get(
                "homeAway"
            )

            score = team.get(
                "score",
                "-"
            )

            if home_away == "home":

                home_score = score

            elif home_away == "away":

                away_score = score

        return (
            home_score,
            away_score
        )

    except Exception:

        return "-", "-"


# ============================================================
# GET TEAM NAMES
# ============================================================

def get_teams(event):

    try:

        competitors = (
            event
            .get("competitions", [{}])[0]
            .get("competitors", [])
        )

        home_team = "Unknown"
        away_team = "Unknown"

        for team in competitors:

            team_info = team.get(
                "team",
                {}
            )

            name = (
                team_info.get("displayName")
                or team_info.get("name")
                or "Unknown"
            )

            if team.get("homeAway") == "home":

                home_team = name

            elif team.get("homeAway") == "away":

                away_team = name

        return (
            home_team,
            away_team
        )

    except Exception:

        return (
            "Unknown",
            "Unknown"
        )


# ============================================================
# GET MATCHES FROM ONE LEAGUE
# ============================================================

def get_league_matches(
    country,
    league_name,
    league_code,
    date
):

    url = ESPN_BASE_URL.format(
        league=league_code,
        date=date
    )

    data = fetch_json(
        url
    )

    events = data.get(
        "events",
        []
    )

    matches = []

    for event in events:

        try:

            event_id = str(
                event.get(
                    "id",
                    ""
                )
            )

            if not event_id:

                continue

            home_team, away_team = (
                get_teams(event)
            )

            home_score, away_score = (
                get_scores(event)
            )

            status, detail = (
                get_match_status(event)
            )

            event_date = event.get(
                "date",
                ""
            )

            time = format_khmer_time(
                event_date
            )

            matches.append(
                {
                    "id": event_id,

                    "country": country,

                    "league": league_name,

                    "league_code": league_code,

                    "home": home_team,

                    "away": away_team,

                    "home_score": home_score,

                    "away_score": away_score,

                    "time": time,

                    "datetime": event_date,

                    "status": status,

                    "detail": detail,

                    "date": date,

                    "source": "ESPN",
                }
            )

        except Exception as error:

            print(
                f"⚠️ Match parse error: {error}"
            )

    return matches


# ============================================================
# GET ALL MATCHES
# ============================================================

def get_matches(
    offset_days=0
):

    date = get_cambodia_date(
        offset_days
    )

    all_matches = []

    for (
        country,
        league_name,
        league_code
    ) in FOOTBALL_LEAGUES:

        try:

            matches = get_league_matches(
                country,
                league_name,
                league_code,
                date
            )

            all_matches.extend(
                matches
            )

        except Exception as error:

            print(
                f"⚠️ {league_name}: {error}"
            )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique = {}

    for match in all_matches:

        key = match.get(
            "id"
        )

        if key:

            unique[key] = match

    all_matches = list(
        unique.values()
    )

    # ========================================================
    # SORT BY TIME
    # ========================================================

    all_matches.sort(
        key=lambda x: (
            x.get(
                "datetime",
                ""
            ),
            x.get(
                "league",
                ""
            )
        )
    )

    return all_matches


# ============================================================
# STATUS ICON
# ============================================================

def status_icon(
    status
):

    if status == "LIVE":

        return "🔴"

    if status == "FT":

        return "✅"

    return "🕐"


# ============================================================
# FORMAT ONE MATCH
# ============================================================

def format_one_match(
    match,
    number
):

    status = match.get(
        "status",
        "UPCOMING"
    )

    icon = status_icon(
        status
    )

    home = match.get(
        "home",
        "Unknown"
    )

    away = match.get(
        "away",
        "Unknown"
    )

    time = match.get(
        "time",
        "N/A"
    )

    country = match.get(
        "country",
        ""
    )

    league = match.get(
        "league",
        ""
    )

    home_score = match.get(
        "home_score",
        "-"
    )

    away_score = match.get(
        "away_score",
        "-"
    )

    detail = match.get(
        "detail",
        ""
    )

    # --------------------------------------------------------
    # UPCOMING
    # --------------------------------------------------------

    if status == "UPCOMING":

        return (
            f"<b>{number}️⃣ "
            f"{home}</b>\n"
            f"   🆚 <b>{away}</b>\n"
            f"   🕐 <b>{time}</b> 🇰🇭\n"
        )

    # --------------------------------------------------------
    # LIVE
    # --------------------------------------------------------

    if status == "LIVE":

        extra = ""

        if detail:

            extra = (
                f" • {detail}"
            )

        return (
            f"<b>{number}️⃣ {icon} LIVE"
            f"{extra}</b>\n"
            f"   {home} "
            f"<b>{home_score}</b> - "
            f"<b>{away_score}</b> "
            f"{away}\n"
        )

    # --------------------------------------------------------
    # FINISHED
    # --------------------------------------------------------

    return (
        f"<b>{number}️⃣ {icon} FT</b>\n"
        f"   {home} "
        f"<b>{home_score}</b> - "
        f"<b>{away_score}</b> "
        f"{away}\n"
    )


# ============================================================
# FORMAT MATCH LIST
# ============================================================

def format_matches(
    matches,
    offset_days=0
):

    if offset_days == 0:

        title = (
            "📅 <b>ការប្រកួតបាល់ទាត់ថ្ងៃនេះ</b>"
        )

    else:

        title = (
            "📆 <b>ការប្រកួតបាល់ទាត់ថ្ងៃស្អែក</b>"
        )

    if not matches:

        return [
            (
                f"{title}\n\n"
                "ℹ️ មិនទាន់រកឃើញការប្រកួត "
                "សម្រាប់ថ្ងៃនេះទេ។\n\n"
                "📡 ប្រភព៖ ESPN"
            )
        ]

    messages = []

    current_message = (
        f"{title}\n\n"
    )

    current_league = None

    number = 0

    for match in matches:

        league_key = (
            match.get("country", ""),
            match.get("league", "")
        )

        # ----------------------------------------------------
        # NEW LEAGUE HEADER
        # ----------------------------------------------------

        if league_key != current_league:

            country = match.get(
                "country",
                ""
            )

            league = match.get(
                "league",
                ""
            )

            header = (
                f"\n<b>{country}</b>\n"
                f"🏆 <b>{league}</b>\n\n"
            )

            # If message gets too large
            if (
                len(current_message)
                + len(header)
                > 3500
            ):

                messages.append(
                    current_message
                )

                current_message = (
                    f"{title}\n\n"
                )

            current_message += header

            current_league = league_key

        number += 1

        match_text = format_one_match(
            match,
            number
        )

        # ----------------------------------------------------
        # MESSAGE LIMIT
        # ----------------------------------------------------

        if (
            len(current_message)
            + len(match_text)
            > 3500
        ):

            messages.append(
                current_message
            )

            current_message = (
                f"{title}\n\n"
            )

            current_message += (
                f"<b>{match.get('country', '')}"
                f" — {match.get('league', '')}</b>\n\n"
            )

            current_message += match_text

        else:

            current_message += (
                match_text
                + "\n"
            )

    # --------------------------------------------------------
    # LAST MESSAGE
    # --------------------------------------------------------

    if current_message.strip():

        current_message += (
            "\n━━━━━━━━━━━━━━━━━━\n"
            "📡 <b>Source:</b> ESPN\n"
            "🇰🇭 ម៉ោង = Cambodia GMT+7"
        )

        messages.append(
            current_message
        )

    return messages


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def get_today_matches():

    return get_matches(
        offset_days=0
    )


def get_tomorrow_matches():

    return get_matches(
        offset_days=1
    )


def get_today_messages():

    matches = get_today_matches()

    return format_matches(
        matches,
        offset_days=0
    )


def get_tomorrow_messages():

    matches = get_tomorrow_matches()

    return format_matches(
        matches,
        offset_days=1
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "⚽ Testing Football Matches..."
    )

    matches = get_today_matches()

    print(
        f"\nFound {len(matches)} matches.\n"
    )

    for match in matches[:20]:

        print(
            f"{match['league']} | "
            f"{match['home']} vs "
            f"{match['away']} | "
            f"{match['time']} | "
            f"{match['status']}"
        )