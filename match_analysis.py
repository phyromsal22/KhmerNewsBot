# match_analysis.py
# Khmer News 24
# Match Analysis: Today / Tomorrow
# User can choose a match OR let the bot scan for >=65% candidates.

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Optional

from odds import get_all_odds, OddsSelection

try:
    from acc_engine import run_engine, MIN_PROBABILITY
except Exception:
    run_engine = None
    MIN_PROBABILITY = 72.0


# ============================================================
# SETTINGS
# ============================================================

CAMBODIA_TZ = timezone(timedelta(hours=7))

# Match Analysis display threshold
MIN_ANALYSIS_PROBABILITY = 65.0

# Only analyze today + tomorrow in Cambodia time
ANALYSIS_LEAGUES = [

    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",

    "FA Cup",
    "EFL Cup",
    "Copa del Rey",
    "Coppa Italia",
    "DFB-Pokal",
    "Coupe de France",

    "Champions League",
    "Europa League",
    "Conference League",
    "Nations League",

    "Eredivisie",
    "Primeira Liga",
    "MLS",
    "Belgian Pro League",
    "Turkish Super Lig",
    "Greek Super League",
]


# ============================================================
# TIME HELPERS
# ============================================================

def now_kh() -> datetime:
    """
    Current Cambodia time.
    """
    return datetime.now(CAMBODIA_TZ)


def parse_time(value: Optional[str]) -> Optional[datetime]:
    """
    Convert API time into Cambodia GMT+7 datetime.
    """

    if not value:
        return None

    text = str(value).strip()

    try:
        dt = datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(CAMBODIA_TZ)

    except Exception:
        return None


def day_offset(dt: datetime) -> Optional[int]:
    """
    Return:
        0 = today
        1 = tomorrow
        None = other day
    """

    today = now_kh().date()
    tomorrow = today + timedelta(days=1)

    if dt.date() == today:
        return 0

    if dt.date() == tomorrow:
        return 1

    return None


def format_kickoff(value: Optional[str]) -> str:
    """
    Format kickoff time in Cambodia timezone.
    """

    dt = parse_time(value)

    if not dt:
        return "Unknown"

    return dt.strftime("%d/%m %H:%M")


# ============================================================
# GET MATCHES
# ============================================================

def get_analysis_matches(offset: int = 0) -> list[OddsSelection]:
    """
    Get real-odds matches for Cambodia today/tomorrow only.

    offset:
        0 = today
        1 = tomorrow
    """

    selections = get_all_odds(
        leagues=ANALYSIS_LEAGUES,
        regions="eu",
    )

    result = []
    seen = set()

    for item in selections:

        dt = parse_time(item.commence_time)

        if not dt:
            continue

        if day_offset(dt) != offset:
            continue

        if not item.match_id:
            continue

        if item.match_id in seen:
            continue

        seen.add(item.match_id)

        result.append(item)

    result.sort(
        key=lambda x:
            parse_time(x.commence_time)
            or datetime.max.replace(
                tzinfo=CAMBODIA_TZ
            )
    )

    return result


def group_matches(
    selections: list[OddsSelection]
) -> list[OddsSelection]:
    """
    One OddsSelection per match.

    We use the first real selection
    only as the match identity.
    """

    matches = OrderedDict()

    for item in selections:

        if item.match_id not in matches:
            matches[item.match_id] = item

    return list(matches.values())


def find_match(
    selections: list[OddsSelection],
    match_id: str
):
    """
    Find selected match by match ID.
    """

    for item in selections:

        if str(item.match_id) == str(match_id):
            return item

    return None


# ============================================================
# ANALYZE SELECTED MATCH
# ============================================================

def analyze_selected_match(match_id: str) -> dict:
    """
    Analyze one selected match.

    IMPORTANT:
    Match Analysis shows TOP 5 model candidates,
    even if they are below 65%.

    ACC filtering remains controlled separately
    by acc_engine.py.
    """

    if run_engine is None:

        return {
            "ok": False,
            "error": "acc_engine.py is unavailable.",
            "match": None,
            "candidates": [],
        }

    try:

        # ----------------------------------------------------
        # Get current real odds
        # ----------------------------------------------------

        selections = get_all_odds(
            leagues=ANALYSIS_LEAGUES,
            regions="eu",
        )

        # ----------------------------------------------------
        # Find selected match
        # ----------------------------------------------------

        selected = find_match(
            selections,
            match_id
        )

        if not selected:

            return {
                "ok": False,
                "error": "Match not found in current real odds.",
                "match": None,
                "candidates": [],
            }

        # ----------------------------------------------------
        # Check Cambodia date
        # ----------------------------------------------------

        dt = parse_time(
            selected.commence_time
        )

        if not dt or day_offset(dt) not in (0, 1):

            return {
                "ok": False,
                "error":
                    "This match is not today or tomorrow "
                    "in Cambodia time.",
                "match": selected,
                "candidates": [],
            }

        # ----------------------------------------------------
        # Run model engine
        # ----------------------------------------------------

        result = run_engine(
            ANALYSIS_LEAGUES
        )

        # IMPORTANT:
        # Use ALL candidates, not ACC-qualified candidates.
        #
        # acc_engine.py must return:
        #
        # "all_candidates": candidates
        #
        # Otherwise Match Analysis will only see
        # candidates that passed the ACC threshold.

        candidates = (
            result.get(
                "all_candidates",
                []
            )
            or []
        )

        # ----------------------------------------------------
        # Filter candidates belonging to this match
        # ----------------------------------------------------

        all_match_candidates = []

        for candidate in candidates:

            if str(candidate.match_id) != str(match_id):
                continue

            candidate_dt = parse_time(
                candidate.commence_time
            )

            if not candidate_dt:
                continue

            if day_offset(candidate_dt) not in (0, 1):
                continue

            all_match_candidates.append(
                candidate
            )

        # ----------------------------------------------------
        # Sort by model probability
        # ----------------------------------------------------

        all_match_candidates.sort(
            key=lambda x: (
                float(x.probability),
                float(x.edge),
                float(x.odds)
            ),
            reverse=True,
        )

        # ----------------------------------------------------
        # Return TOP 5
        # ----------------------------------------------------

        return {
            "ok": True,
            "match": selected,
            "candidates": all_match_candidates[:5],
        }

    except Exception as exc:

        return {
            "ok": False,
            "error": str(exc),
            "match": None,
            "candidates": [],
        }


# ============================================================
# BOT SCAN
# ============================================================

def bot_scan_today_tomorrow() -> dict:
    """
    Scan today's and tomorrow's model candidates.

    Bot Scan keeps only candidates >=65%.

    This is separate from ACC threshold.
    """

    if run_engine is None:

        return {
            "ok": False,
            "error": "acc_engine.py is unavailable.",
            "candidates": [],
        }

    try:

        result = run_engine(
            ANALYSIS_LEAGUES
        )

        # Bot Scan can use all candidates
        # and then apply its own 65% filter.

        candidates = (
            result.get(
                "all_candidates",
                []
            )
            or []
        )

        filtered = []

        for candidate in candidates:

            dt = parse_time(
                candidate.commence_time
            )

            if not dt:
                continue

            # Today + tomorrow only
            if day_offset(dt) not in (0, 1):
                continue

            # Match Analysis threshold
            if float(candidate.probability) < MIN_ANALYSIS_PROBABILITY:
                continue

            filtered.append(candidate)

        # Highest probability first
        filtered.sort(
            key=lambda x: (
                float(x.probability),
                float(x.edge),
            ),
            reverse=True,
        )

        return {
            "ok": True,
            "candidates": filtered,
        }

    except Exception as exc:

        return {
            "ok": False,
            "error": str(exc),
            "candidates": [],
        }


# ============================================================
# FORMAT SELECTED MATCH ANALYSIS
# ============================================================

def format_selected_analysis(data: dict) -> str:

    if not data.get("ok"):

        return (
            "❌ <b>Match Analysis Error</b>\n\n"
            f"<code>"
            f"{str(data.get('error', 'Unknown error'))[:1800]}"
            f"</code>"
        )

    match = data.get("match")

    candidates = data.get(
        "candidates",
        []
    )

    if not match:

        return "❌ មិនអាចរក Match នេះបានទេ។"

    lines = [

        "📊 <b>MATCH ANALYSIS</b>",
        "",

        f"⚽ <b>{match.home_team}</b> "
        f"vs "
        f"<b>{match.away_team}</b>",

        f"🏆 League: "
        f"{match.league or 'Unknown'}",

        f"🕐 Kickoff 🇰🇭: "
        f"{format_kickoff(match.commence_time)}",

        "",

        "🎯 <b>TOP 5 MODEL PICKS</b>",

        "ℹ️ Match Analysis បង្ហាញ Top 5 "
        "ទោះបី Probability &lt;65% ក៏ដោយ។",

        "",
    ]

    # --------------------------------------------------------
    # No candidates
    # --------------------------------------------------------

    if not candidates:

        lines.extend([

            "❌ មិនមាន Model Pick សម្រាប់គូនេះទេ។",

            "",

            "ℹ️ អាចបណ្តាលមកពី៖",
            "• មិនមាន Model data",
            "• មិនមាន historical data គ្រប់គ្រាន់",
            "• Real odds មិនគ្រប់គ្រាន់",
            "• Match មិនមាន selection ដែល Model អាចវិភាគបាន",

        ])

    # --------------------------------------------------------
    # Candidates
    # --------------------------------------------------------

    else:

        for i, candidate in enumerate(
            candidates[:5],
            1
        ):

            probability = float(
                candidate.probability
            )

            # Status
            if probability >= MIN_ANALYSIS_PROBABILITY:
                status = "✅ ≥65%"
            else:
                status = "⚪ <65%"

            lines.extend([

                f"<b>{i}. {candidate.market}</b> "
                f"{status}",

                f"📌 Pick: "
                f"<b>{candidate.selection}</b>",

                f"💰 Odds: "
                f"{candidate.odds:.2f}",

                f"🤖 Model Probability: "
                f"<b>{probability:.1f}%</b>",

                f"📈 Edge: "
                f"{candidate.edge:+.1f}%",

                f"🏦 Bookmaker: "
                f"{candidate.bookmaker}",

                "",
            ])

    lines.extend([

        "────────────────────",

        "📌 <b>Threshold</b>",
        f"• Match Analysis: ≥{MIN_ANALYSIS_PROBABILITY:.0f}%",
        "• Top 5 អាចបង្ហាញក្រោម Threshold",

        "",

        "⚠️ Probability គឺជា "
        "ការប៉ាន់ស្មានពី Model "
        "មិនមែនការធានាឈ្នះទេ។",

        "📅 Match Analysis ប្រើតែ "
        "ថ្ងៃនេះ និងថ្ងៃស្អែក 🇰🇭។",

    ])

    return "\n".join(lines)


# ============================================================
# FORMAT BOT SCAN
# ============================================================

def format_bot_scan(data: dict) -> str:

    if not data.get("ok"):

        return (
            "❌ <b>Bot Scan Error</b>\n\n"
            f"<code>"
            f"{str(data.get('error', 'Unknown error'))[:1800]}"
            f"</code>"
        )

    candidates = data.get(
        "candidates",
        []
    )

    lines = [

        "🤖 <b>BOT MATCH SCAN</b>",
        "",

        "📅 Scope: "
        "ថ្ងៃនេះ + ថ្ងៃស្អែក 🇰🇭",

        f"🎯 Filter: "
        f"Model Probability ≥ "
        f"{MIN_ANALYSIS_PROBABILITY:.0f}%",

        "",
    ]

    if not candidates:

        lines.append(
            "❌ មិនទាន់មាន Match/Pick "
            "ដែលឆ្លង ≥65% ទេ។"
        )

    else:

        for i, candidate in enumerate(
            candidates[:15],
            1
        ):

            lines.extend([

                f"<b>{i}. "
                f"{candidate.home_team} "
                f"vs "
                f"{candidate.away_team}</b>",

                f"🕐 "
                f"{format_kickoff(candidate.commence_time)} "
                f"🇰🇭",

                f"🏆 "
                f"{candidate.league}",

                f"📌 "
                f"{candidate.market}: "
                f"<b>{candidate.selection}</b>",

                f"💰 Odds: "
                f"{candidate.odds:.2f}",

                f"🤖 Probability: "
                f"<b>{candidate.probability:.1f}%</b>",

                f"📈 Edge: "
                f"{candidate.edge:+.1f}%",

                "",
            ])

    lines.extend([

        "────────────────────",

        "⚠️ Probability គឺជា "
        "Model estimate មិនមែន guarantee។",

        "🎯 ACC បន្ទាប់ពីនេះត្រូវគោរព៖",
        "• 2–4 legs",
        "• Kickoff gap ≤ 6h",
        "• ACC threshold ≥72%",

        "📅 ACC ប្រើថ្ងៃនេះ + ថ្ងៃស្អែក 🇰🇭",

    ])

    return "\n".join(lines)