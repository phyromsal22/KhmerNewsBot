"""
Khmer News 24 - V2
AI Khmer News Summary

Primary:
    gemini-3.8-flash

Fallback:
    gemini-3.5-flash-lite

Features:
- Global Gemini quota lock
- Automatic fallback
- Khmer language validation
- Retry invalid Khmer output
- No Thai / Lao / Burmese
- Khmer title extraction
"""

import os
import re
import time

from dotenv import load_dotenv
from google import genai

from ai.prompts import get_summary_prompt

from ai.model_state import (
    PRIMARY_MODEL,
    FALLBACK_MODEL,
    get_active_model,
    is_primary_locked,
    handle_model_error,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found in .env"
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# CONFIG
# ============================================================

# One retry is enough for invalid/empty output.
# 429/quota and 503 errors switch away from the primary immediately.
MAX_RETRIES = 2
RETRY_DELAY = 3
# 503 means the model is temporarily unavailable; switch to fallback immediately.
FALLBACK_ON_503 = True


# ============================================================
# LANGUAGE CHECK
# ============================================================

THAI_PATTERN = re.compile(
    r"[\u0E00-\u0E7F]"
)

LAO_PATTERN = re.compile(
    r"[\u0E80-\u0EFF]"
)

BURMESE_PATTERN = re.compile(
    r"[\u1000-\u109F]"
)

KHMER_PATTERN = re.compile(
    r"[\u1780-\u17FF]"
)


def contains_unwanted_scripts(text):
    """
    Check for Thai, Lao or Burmese characters.
    """

    if not text:
        return False

    if THAI_PATTERN.search(text):
        return True

    if LAO_PATTERN.search(text):
        return True

    if BURMESE_PATTERN.search(text):
        return True

    return False


def has_khmer(text):
    """
    Check whether text contains Khmer characters.
    """

    if not text:
        return False

    return bool(
        KHMER_PATTERN.search(text)
    )


def validate_khmer_summary(text):
    """
    Validate generated Khmer summary.
    """

    if not text:
        return False

    text = text.strip()

    # Too short
    if len(text) < 50:

        print(
            "⚠️ Summary too short"
        )

        return False

    # Must contain Khmer
    if not has_khmer(text):

        print(
            "⚠️ No Khmer characters detected"
        )

        return False

    # No Thai/Lao/Burmese
    if contains_unwanted_scripts(text):

        print(
            "⚠️ Thai/Lao/Burmese characters detected"
        )

        return False

    # Reject other unexpected writing systems that can appear in
    # malformed model output. English names/technical terms remain allowed.
    unexpected_patterns = {
        "Georgian": r"[\u10A0-\u10FF]",
        "Greek": r"[\u0370-\u03FF]",
        "Cyrillic": r"[\u0400-\u04FF]",
        "Arabic": r"[\u0600-\u06FF]",
    }

    for script_name, pattern in unexpected_patterns.items():
        if re.search(pattern, text):
            print(
                f"⚠️ {script_name} characters detected"
            )
            return False

    # Require a strong Khmer presence so a mostly-English response
    # cannot pass merely because it contains one Khmer character.
    khmer_chars = len(re.findall(r"[\u1780-\u17FF]", text))
    latin_chars = len(re.findall(r"[A-Za-z]", text))
    comparable = khmer_chars + latin_chars

    if khmer_chars < 20:
        print("⚠️ Not enough Khmer characters")
        return False

    if comparable > 0:
        ratio = (khmer_chars / comparable) * 100
        if ratio < 55:
            print(
                f"⚠️ Khmer ratio too low: {ratio:.1f}%"
            )
            return False

    return True


# ============================================================
# KHMER TITLE EXTRACTION
# ============================================================

def extract_khmer_title(text):
    """
    Extract Khmer title from generated summary.

    Expected format:

    ចំណងជើង៖
    [Khmer title]

    Returns:
        Khmer title string
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace(
        "\r\n",
        "\n"
    ).replace(
        "\r",
        "\n"
    )

    # Find title section
    patterns = [
        r"ចំណងជើង\s*៖\s*\n?\s*(.+)",
        r"ចំណងជើង\s*:\s*\n?\s*(.+)",
        r"Title\s*:\s*\n?\s*(.+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            title = match.group(
                1
            ).strip()

            # Stop if another section accidentally
            # appears on the same line
            stop_words = [
                "សេចក្តីសង្ខេប",
                "សេចក្តីសង្ខេប:",
                "ព័ត៌មានសំខាន់",
                "ព័ត៌មានសំខាន់:",
                "ប្រភព",
                "ប្រភព:",
            ]

            for stop_word in stop_words:

                if stop_word in title:

                    title = title.split(
                        stop_word
                    )[0].strip()

            # Remove markdown formatting
            title = re.sub(
                r"^[#*\-\s]+",
                "",
                title
            ).strip()

            if title and has_khmer(title):

                if not contains_unwanted_scripts(title):

                    return title

    return ""


# ============================================================
# CLEAN OUTPUT
# ============================================================

def clean_summary(text):
    """
    Basic cleanup without changing the meaning.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"^```(?:text|markdown)?",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```$",
        "",
        text
    )

    return text.strip()


# ============================================================
# CALL GEMINI
# ============================================================

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
            "Gemini returned an empty response"
        )

    return text


# ============================================================
# GENERATE SUMMARY WITH ONE MODEL
# ============================================================

def generate_summary_with_model(
    article,
    model
):

    title = article.get(
        "title",
        ""
    )

    summary = article.get(
        "summary",
        ""
    )

    category = article.get(
        "category",
        ""
    )

    source = article.get(
        "source",
        ""
    )

    prompt = get_summary_prompt(
        title=title,
        summary=summary,
        category=category,
        source=source
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        print(
            f"📝 Khmer Summary | "
            f"{model} | "
            f"Attempt {attempt}/{MAX_RETRIES}"
        )

        try:

            text = call_gemini(
                model,
                prompt
            )

            text = clean_summary(
                text
            )

            if not text:

                print(
                    "⚠️ Empty summary response"
                )

                if attempt < MAX_RETRIES:
                    time.sleep(
                        RETRY_DELAY
                    )

                continue

            if validate_khmer_summary(
                text
            ):

                print(
                    "✅ Khmer summary generated"
                )

                return text

            print(
                "⚠️ Invalid Khmer summary"
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_DELAY
                )

        except Exception as error:

            print(
                f"⚠️ Summary AI error: {error}"
            )

            error_text = str(error).upper()
            is_503 = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "SERVICE UNAVAILABLE" in error_text
            )

            # ------------------------------------------
            # Primary model: 429 quota OR 503 unavailable
            # ------------------------------------------

            if model == PRIMARY_MODEL:

                quota_error = handle_model_error(
                    PRIMARY_MODEL,
                    error
                )

                if quota_error:

                    print(
                        "🚨 Gemini primary quota/rate limit detected."
                    )

                    print(
                        f"🔒 {PRIMARY_MODEL} locked."
                    )

                    print(
                        f"🛟 Switching immediately to "
                        f"{FALLBACK_MODEL}"
                    )

                    return ""

                # 503 is not necessarily a quota error, but the
                # primary model is temporarily unavailable. Do not
                # waste more primary requests; let summarize_article()
                # switch to the fallback model.
                if is_503 and FALLBACK_ON_503:

                    print(
                        f"⚠️ {PRIMARY_MODEL} returned 503 UNAVAILABLE."
                    )

                    print(
                        f"🛟 Switching immediately to {FALLBACK_MODEL}"
                    )

                    return ""

            # ------------------------------------------
            # Fallback model: do not hammer 3.5 on 429/503
            # ------------------------------------------

            if model == FALLBACK_MODEL and (
                "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
                or "QUOTA" in error_text
                or "RATE LIMIT" in error_text
                or "503" in error_text
                or "UNAVAILABLE" in error_text
            ):
                print(
                    f"🛑 {FALLBACK_MODEL} is temporarily "
                    "rate-limited/unavailable."
                )
                print(
                    "⏭️ Skipping this article instead of "
                    "retrying immediately."
                )
                return ""

            # ------------------------------------------
            # Normal error
            # ------------------------------------------

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_DELAY
                )

    return ""


# ============================================================
# GENERATE SUMMARY
# ============================================================

def generate_summary(
    article,
    model=None
):

    # ========================================================
    # GLOBAL MODEL STATE
    # ========================================================

    active_model = get_active_model()

    print(
        f"🧠 Summary Active Model: "
        f"{active_model}"
    )

    # ========================================================
    # PRIMARY LOCKED
    # ========================================================

    if is_primary_locked():

        print(
            f"🔒 {PRIMARY_MODEL} quota locked."
        )

        print(
            f"🛟 Using {FALLBACK_MODEL} directly."
        )

        return generate_summary_with_model(
            article,
            FALLBACK_MODEL
        )

    # ========================================================
    # EXPLICIT FALLBACK REQUEST
    # ========================================================

    if model == FALLBACK_MODEL:

        return generate_summary_with_model(
            article,
            FALLBACK_MODEL
        )

    # ========================================================
    # PRIMARY
    # ========================================================

    return generate_summary_with_model(
        article,
        PRIMARY_MODEL
    )


# ============================================================
# FALLBACK SUMMARY
# ============================================================

def generate_fallback_summary(
    article
):

    print(
        f"🛟 Fallback Summary | "
        f"{FALLBACK_MODEL}"
    )

    # One call chain is enough because
    # generate_summary() already handles
    # fallback model execution.

    result = generate_summary(
        article,
        model=FALLBACK_MODEL
    )

    if result:

        print(
            "✅ Fallback Khmer summary generated"
        )

        return result

    print(
        "❌ Fallback could not generate "
        "valid Khmer summary"
    )

    return ""


# ============================================================
# PROCESS ONE ARTICLE
# ============================================================

def summarize_article(
    article
):

    if not article:
        return None

    # ========================================================
    # GENERATE SUMMARY
    # ========================================================

    result = generate_summary(
        article
    )

    # ========================================================
    # IF PRIMARY FAILED
    # TRY FALLBACK
    # ========================================================

    if not result:
        # generate_summary() already uses 3.5 directly when 3.8
        # is globally locked. Only one fallback attempt is needed.
        result = generate_fallback_summary(
            article
        )

    # ========================================================
    # SAVE RESULT
    # ========================================================

    if result:

        article = article.copy()

        # Full Khmer summary
        article["khmer_summary"] = result

        # Extract Khmer title
        khmer_title = extract_khmer_title(
            result
        )

        if khmer_title:

            article["khmer_title"] = (
                khmer_title
            )

            print(
                f"📰 Khmer Title: "
                f"{khmer_title}"
            )

        else:

            # Keep empty rather than invent title
            article["khmer_title"] = ""

            print(
                "⚠️ Khmer title could not be extracted"
            )

        return article

    return None


# ============================================================
# PROCESS MULTIPLE ARTICLES
# ============================================================

def summarize_articles(
    articles
):

    if not articles:
        return []

    results = []

    for article in articles:

        try:

            processed = summarize_article(
                article
            )

            if processed:

                results.append(
                    processed
                )

        except Exception as error:

            print(
                f"❌ Summary processing error: {error}"
            )

    return results


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    test_article = {

        "title": (
            "International leaders meet "
            "to discuss major global issues"
        ),

        "summary": (
            "World leaders held talks on "
            "major international developments "
            "and discussed possible responses."
        ),

        "category": "world",

        "source": "BBC News",
    }

    result = summarize_article(
        test_article
    )

    print(
        "\n" + "=" * 60
    )

    if result:

        print(
            "🇰🇭 Khmer Title:"
        )

        print(
            result.get(
                "khmer_title",
                ""
            )
        )

        print(
            "\n📝 Khmer Summary:"
        )

        print(
            result.get(
                "khmer_summary",
                ""
            )
        )

    else:

        print(
            "❌ Summary test failed"
        )