"""
Khmer News 24 - V2
AI News Filter

Supports:
- World / Politics / Cambodia / War
- Football-specific filtering
- Gemini 3.8 primary
- Gemini 3.5 fallback
- Gemini 3.1 second fallback
- Automatic model locking
- Automatic model fallback
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
    SECOND_FALLBACK_MODEL,
    MODEL_CHAIN,
    get_active_model,
    is_model_locked,
    all_models_locked,
    handle_model_error,
)


# ==========================================
# CONFIG
# ==========================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found in .env"
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


# Normal errors get limited retries.
# Quota / rate-limit / 503 errors switch
# to the next model immediately.
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
# MODEL ERROR CHECK
# ==========================================

def is_temporary_model_error(error):

    text = str(error).lower()

    return (
        "429" in text
        or "resource_exhausted" in text
        or "quota" in text
        or "rate limit" in text
        or "rate_limit" in text
        or "too many requests" in text
        or "503" in text
        or "unavailable" in text
        or "overloaded" in text
    )


# ==========================================
# TRY ONE MODEL
# ==========================================

def try_model(
    model,
    prompt
):
    """
    Try one Gemini model.

    Returns:
        AI result dictionary
        OR None when the model is unavailable.
    """

    # --------------------------------------
    # Check model lock
    # --------------------------------------

    if is_model_locked(model):

        print(
            f"🔒 {model} is currently locked."
        )

        return None


    # --------------------------------------
    # Attempts
    # --------------------------------------

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"🤖 AI Filter | "
                f"{model} | "
                f"Attempt "
                f"{attempt}/{MAX_RETRIES}"
            )

            response_text = call_gemini(
                model,
                prompt
            )

            result = parse_ai_result(
                response_text
            )

            print(
                f"✅ AI Result | "
                f"{model} | "
                f"score={result['score']} "
                f"important="
                f"{result['important']}"
            )

            return result


        except Exception as e:

            print(
                f"⚠️ AI Filter error | "
                f"{model} | {e}"
            )


            # ----------------------------------
            # Update global model state
            # ----------------------------------

            state_result = handle_model_error(
                model,
                e
            )


            # ----------------------------------
            # Temporary model problem
            # ----------------------------------

            if is_temporary_model_error(e):

                cooldown = state_result.get(
                    "cooldown_seconds",
                    0
                )

                next_model = state_result.get(
                    "next_model"
                )

                print(
                    f"🔒 {model} locked "
                    f"for approximately "
                    f"{cooldown}s."
                )

                if next_model:

                    print(
                        f"🛟 Next AI model → "
                        f"{next_model}"
                    )

                else:

                    print(
                        "⏳ No other Gemini "
                        "model currently available."
                    )

                return None


            # ----------------------------------
            # Normal error
            # ----------------------------------

            if attempt < MAX_RETRIES:

                print(
                    f"⏳ Waiting "
                    f"{RETRY_DELAY_SECONDS}s..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

            else:

                print(
                    f"❌ {model} failed "
                    f"after "
                    f"{MAX_RETRIES} attempts."
                )


    return None


# ==========================================
# TRY ALL GEMINI MODELS
# ==========================================

def use_ai_model_chain(
    prompt
):
    """
    Try Gemini models in priority order:

        3.8
        ↓
        3.5
        ↓
        3.1
        ↓
        wait / unavailable

    This is the main AI fallback system.
    """

    print()
    print(
        "🔄 Gemini AI Model Chain"
    )

    print(
        f"   1️⃣ {PRIMARY_MODEL}"
    )

    print(
        f"   2️⃣ {FALLBACK_MODEL}"
    )

    print(
        f"   3️⃣ {SECOND_FALLBACK_MODEL}"
    )

    print()


    # --------------------------------------
    # Check active model
    # --------------------------------------

    active_model = get_active_model()

    print(
        f"🧠 Active Gemini model: "
        f"{active_model}"
    )


    # --------------------------------------
    # Try models in configured priority
    # --------------------------------------

    for model in MODEL_CHAIN:

        if is_model_locked(model):

            print(
                f"⏭️ Skipping locked model: "
                f"{model}"
            )

            continue


        result = try_model(
            model,
            prompt
        )


        if result is not None:

            print(
                f"✅ AI Filter succeeded "
                f"with {model}"
            )

            return result


    # --------------------------------------
    # All models unavailable
    # --------------------------------------

    if all_models_locked():

        print(
            "⏳ ALL GEMINI MODELS ARE "
            "CURRENTLY LOCKED."
        )

        print(
            "⏳ Waiting for cooldown/reset."
        )


    else:

        print(
            "❌ All available Gemini "
            "models failed."
        )


    return {
        "important": False,
        "score": 0,
        "reason": (
            "AI filter temporarily "
            "unavailable"
        )
    }


# ==========================================
# BACKWARD COMPATIBILITY
# ==========================================

def try_primary_model(
    prompt
):
    """
    Backward-compatible function.

    Existing code can still call:
        try_primary_model(prompt)

    It now uses the full 3-model chain.
    """

    return use_ai_model_chain(
        prompt
    )


def use_fallback_model(
    prompt
):
    """
    Backward-compatible function.

    Existing code can still call:
        use_fallback_model(prompt)

    It now uses the complete fallback chain.
    """

    return use_ai_model_chain(
        prompt
    )


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
    # USE FULL MODEL CHAIN
    # ======================================

    result = use_ai_model_chain(
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