"""
Khmer News 24 - V2
AI Translator
"""

import os
import re
import time

from google import genai
from dotenv import load_dotenv

from ai.prompts import get_translation_prompt

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
    raise RuntimeError(
        "GEMINI_API_KEY not found in .env"
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3


# ==========================================
# UNWANTED SCRIPT CHECK
# ==========================================

def contains_unwanted_script(text):

    if not text:
        return False

    thai = re.search(
        r"[\u0E00-\u0E7F]",
        text
    )

    lao = re.search(
        r"[\u0E80-\u0EFF]",
        text
    )

    burmese = re.search(
        r"[\u1000-\u109F]",
        text
    )

    return bool(
        thai
        or lao
        or burmese
    )


# ==========================================
# CLEAN TRANSLATION
# ==========================================

def clean_translation(text):

    if not text:
        return ""

    text = text.strip()

    if text.startswith("```"):

        text = text.replace(
            "```text",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

    return text


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

    text = getattr(
        response,
        "text",
        ""
    )

    if not text:

        raise ValueError(
            "Gemini returned empty response"
        )

    return text


# ==========================================
# TRANSLATE WITH MODEL
# ==========================================

def translate_with_model(
    text,
    model
):

    prompt = get_translation_prompt(
        text
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"🌐 Khmer Translation | "
                f"{model} | "
                f"Attempt {attempt}/{MAX_RETRIES}"
            )

            result = call_gemini(
                model,
                prompt
            )

            result = clean_translation(
                result
            )

            if not result:

                raise ValueError(
                    "Empty translation result"
                )

            if contains_unwanted_script(
                result
            ):

                raise ValueError(
                    "Thai/Lao/Burmese "
                    "characters detected"
                )

            print(
                "✅ Khmer translation generated"
            )

            return result

        except Exception as error:

            print(
                f"⚠️ Translation AI error: "
                f"{error}"
            )

            # ==================================
            # PRIMARY QUOTA ERROR
            # ==================================

            if model == PRIMARY_MODEL:

                quota_error = handle_model_error(
                    PRIMARY_MODEL,
                    error
                )

                if quota_error:

                    print(
                        "🚨 Gemini quota/rate limit "
                        "detected."
                    )

                    print(
                        f"🔒 {PRIMARY_MODEL} locked."
                    )

                    print(
                        f"🛟 Switching immediately "
                        f"to {FALLBACK_MODEL}"
                    )

                    return ""

            # ==================================
            # NORMAL ERROR
            # ==================================

            if attempt < MAX_RETRIES:

                print(
                    f"⏳ Waiting "
                    f"{RETRY_DELAY_SECONDS}s..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

    return ""


# ==========================================
# TRANSLATE TO KHMER
# ==========================================

def translate_to_khmer(text):

    if not text:
        return ""

    # ======================================
    # CHECK GLOBAL MODEL STATE
    # ======================================

    active_model = get_active_model()

    print(
        f"🧠 Translation Active Model: "
        f"{active_model}"
    )

    # ======================================
    # PRIMARY LOCKED
    # ======================================

    if is_primary_locked():

        print(
            f"🔒 {PRIMARY_MODEL} quota locked."
        )

        print(
            f"🛟 Using {FALLBACK_MODEL} directly."
        )

        return translate_with_model(
            text,
            FALLBACK_MODEL
        )

    # ======================================
    # PRIMARY
    # ======================================

    result = translate_with_model(
        text,
        PRIMARY_MODEL
    )

    if result:

        return result

    # ======================================
    # FALLBACK
    # ======================================

    print(
        f"🛟 Fallback Translation | "
        f"{FALLBACK_MODEL}"
    )

    return translate_with_model(
        text,
        FALLBACK_MODEL
    )


# ==========================================
# TRANSLATE ARTICLE
# ==========================================

def translate_article(article):

    if not article:
        return None

    article = article.copy()

    title = article.get(
        "title",
        ""
    )

    summary = article.get(
        "summary",
        ""
    )

    if title:

        article["khmer_title"] = (
            translate_to_khmer(title)
        )

    if summary:

        article["khmer_text"] = (
            translate_to_khmer(summary)
        )

    return article