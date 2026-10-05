"""
Khmer News 24 - V2
AI News Filter

Supports:
- World / Politics / Cambodia / War
- Football-specific filtering
- Gemini 3.8 primary
- Gemini 3.5 fallback
- Global quota lock
"""

import os
import json
import time

from google import genai
from dotenv import load_dotenv

from ai.prompts import get_filter_prompt

from ai.model_state import (
    PRIMARY_MODEL,
    FALLBACK_MODEL,
    get_active_model,
    is_primary_locked,
    handle_model_error,
)


# ==========================================
# CONFIG
# ==========================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env")


client = genai.Client(
    api_key=GEMINI_API_KEY
)


# Normal errors get at most 1 retry.
# 429/quota and 503 errors switch to fallback immediately.
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3

# Normal news minimum score
DEFAULT_MIN_SCORE = 60

# Football minimum score
FOOTBALL_MIN_SCORE = 40


# ==========================================
# FOOTBALL KEYWORDS
# ==========================================

FOOTBALL_KEYWORDS = [

    # General football
    "football",
    "soccer",
    "premier league",
    "champions league",
    "europa league",
    "conference league",
    "world cup",
    "euro",
    "copa",
    "fa cup",
    "league cup",

    # Match
    "match",
    "fixture",
    "result",
    "win",
    "won",
    "lose",
    "lost",
    "draw",
    "goal",
    "goals",
    "score",
    "kick-off",
    "kickoff",

    # Players
    "player",
    "striker",
    "midfielder",
    "defender",
    "goalkeeper",
    "captain",

    # Transfer
    "transfer",
    "transfers",
    "signing",
    "signed",
    "loan",
    "contract",
    "deal",

    # Injury
    "injury",
    "injured",
    "fitness",
    "hamstring",
    "knee",

    # Coaches
    "manager",
    "coach",
    "head coach",

    # Teams
    "club",
    "national team",
    "squad",
    "team",

    # Tournaments
    "tournament",
    "qualifier",
    "qualifying",
    "semi-final",
    "semifinal",
    "final",
    "quarter-final",
    "quarterfinal",

    # Football competitions
    "premier",
    "la liga",
    "serie a",
    "bundesliga",
    "ligue 1",
    "mls",
]


# ==========================================
# FOOTBALL NEGATIVE KEYWORDS
# ==========================================

FOOTBALL_NEGATIVE_KEYWORDS = [
    "casino",
    "gambling",
    "betting tips",
    "slot",
    "poker",
]


# ==========================================
# JSON CLEANER
# ==========================================

def clean_json_response(text):

    if not text:
        raise ValueError(
            "Empty Gemini response"
        )

    text = text.strip()

    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```JSON",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:

        text = text[
            start:end + 1
        ]

    return text


# ==========================================
# PARSE AI RESULT
# ==========================================

def parse_ai_result(text):

    cleaned = clean_json_response(
        text
    )

    result = json.loads(
        cleaned
    )

    important = bool(
        result.get(
            "important",
            False
        )
    )

    try:

        score = int(
            result.get(
                "score",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        score = 0

    score = max(
        0,
        min(
            100,
            score
        )
    )

    reason = str(
        result.get(
            "reason",
            ""
        )
    ).strip()

    return {
        "important": important,
        "score": score,
        "reason": reason
    }


# ==========================================
# GEMINI CALL
# ==========================================

def call_gemini(
    model,
    prompt
):

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    if not response.text:

        raise ValueError(
            "Gemini returned an empty response"
        )

    return response.text


# ==========================================
# PRIMARY MODEL
# ==========================================

def try_primary_model(
    prompt
):

    # --------------------------------------
    # Check global quota lock
    # --------------------------------------

    if is_primary_locked():

        print(
            f"🔒 {PRIMARY_MODEL} "
            f"is currently locked."
        )

        print(
            f"🛟 Using {FALLBACK_MODEL} "
            f"directly."
        )

        return None

    # --------------------------------------
    # Primary attempts
    # --------------------------------------

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"🤖 AI Filter | "
                f"{PRIMARY_MODEL} | "
                f"Attempt "
                f"{attempt}/{MAX_RETRIES}"
            )

            response_text = call_gemini(
                PRIMARY_MODEL,
                prompt
            )

            result = parse_ai_result(
                response_text
            )

            print(
                f"✅ AI Result: "
                f"score={result['score']} "
                f"important="
                f"{result['important']}"
            )

            return result

        except Exception as e:

            error_text = str(e)

            print(
                f"⚠️ Primary AI error: "
                f"{e}"
            )

            # ----------------------------------
            # Tell global model state
            # ----------------------------------

            quota_error = handle_model_error(
                PRIMARY_MODEL,
                e
            )

            # ----------------------------------
            # 429 QUOTA / RATE LIMIT
            # ----------------------------------

            if quota_error:

                print(
                    "🚨 Gemini quota/rate "
                    "limit detected."
                )

                print(
                    f"🔒 Locking "
                    f"{PRIMARY_MODEL}"
                )

                print(
                    f"🛟 Switching immediately "
                    f"to {FALLBACK_MODEL}"
                )

                return None

            # ----------------------------------
            # 503 MODEL UNAVAILABLE
            # ----------------------------------
            # 503 usually means the model is
            # temporarily overloaded/unavailable.
            # Do NOT waste 3 requests on 3.8.
            # Switch to fallback immediately.

            if (
                "503" in error_text
                or "unavailable" in error_text.lower()
            ):

                print(
                    f"⚠️ {PRIMARY_MODEL} is "
                    f"temporarily unavailable (503)."
                )

                print(
                    f"🛟 Switching immediately "
                    f"to {FALLBACK_MODEL}"
                )

                return None

            # ----------------------------------
            # OTHER NORMAL ERROR
            # ----------------------------------

            if attempt < MAX_RETRIES:

                print(
                    f"⏳ Waiting "
                    f"{RETRY_DELAY_SECONDS}s..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

    return None


# ==========================================
# FALLBACK MODEL
# ==========================================

def use_fallback_model(
    prompt
):

    try:

        print(
            f"🤖 Fallback AI | "
            f"{FALLBACK_MODEL}"
        )

        response_text = call_gemini(
            FALLBACK_MODEL,
            prompt
        )

        result = parse_ai_result(
            response_text
        )

        print(
            f"✅ Fallback AI Result: "
            f"score={result['score']} "
            f"important="
            f"{result['important']}"
        )

        return result

    except Exception as e:

        error_text = str(e)

        print(
            f"❌ Fallback AI error: "
            f"{e}"
        )

        # IMPORTANT:
        # 3.5 is the fallback for 3.8. If 3.5 itself is
        # rate-limited/unavailable, do not retry immediately.
        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
            or "quota" in error_text.lower()
            or "rate limit" in error_text.lower()
            or "503" in error_text
            or "UNAVAILABLE" in error_text.upper()
        ):
            print(
                "🛑 Fallback model is temporarily "
                "rate-limited/unavailable. "
                "Skipping this article safely."
            )

        return {
            "important": False,
            "score": 0,
            "reason": (
                "AI filter unavailable"
            )
        }


# ==========================================
# FOOTBALL LOCAL RULES
# ==========================================

def apply_football_rules(
    article,
    result
):
    """
    Football-specific filtering.

    Score:
        0-29  -> reject
        30-39 -> boost to 40
        40+   -> keep original score

    Useful football content includes:
    - Player stories
    - Club news
    - National team
    - World Cup
    - Transfers
    - Injuries
    - Managers
    - Matches
    - Tournaments
    """

    title = str(
        article.get(
            "title",
            ""
        )
    ).strip()

    summary = str(
        article.get(
            "summary",
            ""
        )
    ).strip()

    text = (
        title
        + " "
        + summary
    ).lower()

    # --------------------------------------
    # 1. Reject obvious gambling content
    # --------------------------------------

    for keyword in FOOTBALL_NEGATIVE_KEYWORDS:

        if keyword in text:

            result["important"] = False

            result["reason"] = (
                "Football article contains "
                "restricted gambling or "
                "promotional content."
            )

            return result

    # --------------------------------------
    # 2. Original AI score
    # --------------------------------------

    try:

        original_score = int(
            result.get(
                "score",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        original_score = 0

    original_score = max(
        0,
        min(
            100,
            original_score
        )
    )

    # --------------------------------------
    # 3. Very low-quality article
    # --------------------------------------

    if original_score < 30:

        result["important"] = False

        result["score"] = (
            original_score
        )

        result["reason"] = (
            "Football article received "
            "a very low relevance score "
            "from AI."
        )

        return result

    # --------------------------------------
    # 4. Useful football article
    # --------------------------------------
    #
    # Example:
    # Bellingham = 35
    # Final = 40
    #
    # Scotland = 30
    # Final = 40
    #
    # This allows player/team stories
    # even when they are not breaking news.

    if (
        original_score >= 30
        and
        original_score < FOOTBALL_MIN_SCORE
    ):

        result["score"] = (
            FOOTBALL_MIN_SCORE
        )

        result["important"] = True

        result["reason"] = (
            "Relevant football article "
            "covering a player, team, club, "
            "national team, match, tournament, "
            "or football-related story."
        )

        return result

    # --------------------------------------
    # 5. Good football score
    # --------------------------------------

    result["score"] = (
        original_score
    )

    result["important"] = True

    if not result.get("reason"):

        result["reason"] = (
            "Relevant football news."
        )

    return result


# ==========================================
# FILTER ONE ARTICLE
# ==========================================

def filter_article(
    article
):

    category = str(
        article.get(
            "category",
            ""
        )
    ).lower().strip()

    prompt = get_filter_prompt(
        title=article.get(
            "title",
            ""
        ),
        summary=article.get(
            "summary",
            ""
        ),
        category=category,
        source=article.get(
            "source",
            ""
        )
    )

    # ======================================
    # CHECK ACTIVE MODEL
    # ======================================

    active_model = get_active_model()

    print(
        f"🧠 AI Filter Active Model: "
        f"{active_model}"
    )

    # ======================================
    # IF PRIMARY IS LOCKED
    # USE FALLBACK DIRECTLY
    # ======================================

    if is_primary_locked():

        print(
            f"🔒 {PRIMARY_MODEL} "
            f"quota locked."
        )

        result = use_fallback_model(
            prompt
        )

    else:

        # ==================================
        # TRY PRIMARY
        # ==================================

        result = try_primary_model(
            prompt
        )

        # ==================================
        # FALLBACK
        # ==================================

        if result is None:

            print(
                f"🛟 Primary unavailable → "
                f"using {FALLBACK_MODEL}"
            )

            result = use_fallback_model(
                prompt
            )

    # ======================================
    # FOOTBALL SPECIAL RULE
    # ======================================

    if category == "football":

        result = apply_football_rules(
            article,
            result
        )

        print(
            f"⚽ Football Filter Result: "
            f"score={result['score']} "
            f"important={result['important']}"
        )

    return result


# ==========================================
# FILTER ARTICLES
# ==========================================

def filter_articles(
    articles,
    min_score=DEFAULT_MIN_SCORE
):

    selected = []

    for article in articles:

        result = filter_article(
            article
        )

        item = article.copy()

        item["ai_important"] = (
            result["important"]
        )

        item["ai_score"] = (
            result["score"]
        )

        item["ai_reason"] = (
            result["reason"]
        )

        # ----------------------------------
        # Category-specific threshold
        # ----------------------------------

        category = str(
            item.get(
                "category",
                ""
            )
        ).lower().strip()

        if category == "football":

            required_score = (
                FOOTBALL_MIN_SCORE
            )

        else:

            required_score = (
                min_score
            )

        # ----------------------------------
        # Final selection
        # ----------------------------------

        if (
            result["important"]
            and
            result["score"] >= required_score
        ):

            selected.append(
                item
            )

    return selected