"""
Khmer News 24 - V2
AI Khmer News Summary

Gemini Model Priority:
    1. gemini-3.8-flash
    2. gemini-3.5-flash-lite
    3. gemini-3.1-flash-lite

Features:
- Automatic 3-level Gemini fallback
- Daily quota detection
- RPM/rate-limit detection
- Temporary server error detection
- Persistent model lock state
- Khmer language validation
- No Thai / Lao / Burmese
- Khmer title extraction
- Retry invalid Khmer output
- Compatible with ai.processor.py
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
    SECOND_FALLBACK_MODEL,
    MODEL_CHAIN,
    get_active_model,
    get_available_fallback,
    is_model_locked,
    handle_model_error,
    all_models_locked,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

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
# CONFIGURATION
# ============================================================

MAX_RETRIES = 3
RETRY_DELAY = 3

MIN_KHMER_CHARACTERS = 20
MIN_KHMER_RATIO = 0.55


# ============================================================
# LANGUAGE PATTERNS
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

# Cyrillic
CYRILLIC_PATTERN = re.compile(
    r"[\u0400-\u04FF]"
)

# Greek
GREEK_PATTERN = re.compile(
    r"[\u0370-\u03FF]"
)

# Arabic
ARABIC_PATTERN = re.compile(
    r"[\u0600-\u06FF]"
)


# ============================================================
# LANGUAGE CHECK
# ============================================================

def contains_unwanted_scripts(text):
    """
    Check for Thai, Lao, Burmese, Cyrillic,
    Greek or Arabic characters.
    """

    if not text:
        return False

    if THAI_PATTERN.search(text):
        return True

    if LAO_PATTERN.search(text):
        return True

    if BURMESE_PATTERN.search(text):
        return True

    if CYRILLIC_PATTERN.search(text):
        return True

    if GREEK_PATTERN.search(text):
        return True

    if ARABIC_PATTERN.search(text):
        return True

    return False


def count_khmer_characters(text):
    """
    Count Khmer Unicode characters.
    """

    if not text:
        return 0

    return len(
        KHMER_PATTERN.findall(text)
    )


def has_khmer(text):
    """
    Check whether text contains Khmer.
    """

    return (
        count_khmer_characters(text) > 0
    )


def calculate_khmer_ratio(text):
    """
    Calculate approximate Khmer character ratio.

    Spaces, punctuation and numbers are ignored.
    """

    if not text:
        return 0.0

    khmer_count = count_khmer_characters(
        text
    )

    meaningful_chars = []

    for char in text:

        if char.isspace():
            continue

        if char.isdigit():
            continue

        if char.isascii() and not char.isalpha():
            continue

        meaningful_chars.append(char)

    if not meaningful_chars:
        return 0.0

    return (
        khmer_count
        / len(meaningful_chars)
    )


def validate_khmer_summary(text):
    """
    Strong validation for Khmer summary.

    Requirements:
    - Not empty
    - At least 20 Khmer characters
    - Khmer ratio >= 55%
    - No Thai
    - No Lao
    - No Burmese
    - No Cyrillic
    - No Greek
    - No Arabic
    """

    if not text:
        print(
            "⚠️ Summary is empty"
        )
        return False

    text = text.strip()

    khmer_count = (
        count_khmer_characters(text)
    )

    if khmer_count < MIN_KHMER_CHARACTERS:
        print(
            "⚠️ Not enough Khmer characters: "
            f"{khmer_count}"
        )
        return False

    if contains_unwanted_scripts(text):
        print(
            "⚠️ Unwanted language/script detected"
        )
        return False

    ratio = calculate_khmer_ratio(
        text
    )

    if ratio < MIN_KHMER_RATIO:
        print(
            "⚠️ Khmer ratio too low: "
            f"{ratio:.1%}"
        )
        return False

    return True


# ============================================================
# KHMER TITLE EXTRACTION
# ============================================================

def extract_khmer_title(text):
    """
    Extract a Khmer title from the generated output.

    Supports common formats:

        ចំណងជើង:
        <title>

        ចំណងជើង
        <title>

        Title:
        <title>

    If no explicit title is found, the function
    searches for the first suitable Khmer line.
    """

    if not text:
        return ""

    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    # --------------------------------------------------------
    # Explicit title markers
    # --------------------------------------------------------

    title_markers = [
        "ចំណងជើង:",
        "ចំណងជើង៖",
        "ចំណងជើង",
        "ប្រធានបទ:",
        "ប្រធានបទ៖",
        "Title:",
        "TITLE:",
        "title:",
        "Headline:",
        "ចំណងជើងព័ត៌មាន:",
        "ចំណងជើងព័ត៌មាន៖",
    ]

    for index, line in enumerate(lines):

        clean_line = line.strip()

        # Remove markdown formatting
        clean_line = re.sub(
            r"^[#*\-•\s]+",
            "",
            clean_line,
        ).strip()

        for marker in title_markers:

            if clean_line.startswith(marker):

                title = clean_line[
                    len(marker):
                ].strip()

                title = re.sub(
                    r"^[#*\-•\s]+",
                    "",
                    title,
                ).strip()

                # If marker has no title on same line,
                # use next line.
                if not title:

                    if index + 1 < len(lines):

                        title = lines[
                            index + 1
                        ].strip()

                        title = re.sub(
                            r"^[#*\-•\s]+",
                            "",
                            title,
                        ).strip()

                if (
                    title
                    and has_khmer(title)
                    and not contains_unwanted_scripts(
                        title
                    )
                ):
                    return title

    # --------------------------------------------------------
    # Look for first Khmer line
    # --------------------------------------------------------

    for line in lines:

        line = re.sub(
            r"^[#*\-•\s]+",
            "",
            line,
        ).strip()

        if not line:
            continue

        # Skip obvious section labels
        lower_line = line.lower()

        if lower_line in (
            "summary",
            "title",
            "headline",
        ):
            continue

        if (
            has_khmer(line)
            and not contains_unwanted_scripts(
                line
            )
        ):

            # Keep title reasonably short.
            if len(line) <= 180:
                return line

    return ""


# ============================================================
# ERROR CHECKING
# ============================================================

def is_quota_error(error):
    """
    Backward-compatible quota check.
    """

    message = str(error).lower()

    keywords = [
        "429",
        "resource_exhausted",
        "quota",
        "quota exceeded",
        "daily quota",
        "daily limit",
        "generate_content_free_tier_requests",
        "rate limit",
        "rate_limit",
        "too many requests",
        "requests per minute",
    ]

    return any(
        keyword in message
        for keyword in keywords
    )


def is_temporary_model_error(error):
    """
    Detect temporary Gemini errors that should
    trigger model fallback.
    """

    message = str(error).lower()

    keywords = [
        "429",
        "resource_exhausted",
        "quota",
        "rate limit",
        "rate_limit",
        "too many requests",
        "503",
        "service unavailable",
        "unavailable",
        "overloaded",
        "temporarily unavailable",
    ]

    return any(
        keyword in message
        for keyword in keywords
    )


# ============================================================
# CLEAN OUTPUT
# ============================================================

def clean_summary(text):
    """
    Basic cleanup without changing meaning.
    """

    if not text:
        return ""

    text = str(text).strip()

    # Remove code fences
    text = re.sub(
        r"^```(?:text|markdown)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()


# ============================================================
# BUILD PROMPT
# ============================================================

def build_summary_prompt(article):
    """
    Build the summary prompt using the existing
    prompt system.
    """

    title = article.get(
        "title",
        "",
    )

    summary = article.get(
        "summary",
        "",
    )

    category = article.get(
        "category",
        "",
    )

    source = article.get(
        "source",
        "",
    )

    return get_summary_prompt(
        title=title,
        summary=summary,
        category=category,
        source=source,
    )


# ============================================================
# CALL GEMINI
# ============================================================

def call_gemini(
    model,
    prompt,
):
    """
    Send request to Gemini.
    """

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    text = getattr(
        response,
        "text",
        "",
    )

    if not text:
        raise ValueError(
            "Gemini returned an empty response"
        )

    return text


# ============================================================
# GENERATE WITH ONE MODEL
# ============================================================

def generate_with_model(
    article,
    model,
):
    """
    Generate Khmer summary using one model.

    Returns:
        Valid Khmer summary string
        or empty string
    """

    prompt = build_summary_prompt(
        article
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        print(
            f"🤖 Khmer Summary | "
            f"{model} | "
            f"Attempt "
            f"{attempt}/{MAX_RETRIES}"
        )

        try:

            response_text = call_gemini(
                model,
                prompt,
            )

            text = clean_summary(
                response_text
            )

            if not text:

                print(
                    "⚠️ Empty summary response"
                )

            elif validate_khmer_summary(
                text
            ):

                print(
                    f"✅ Khmer summary generated "
                    f"with {model}"
                )

                return text

            else:

                print(
                    f"⚠️ Invalid Khmer output "
                    f"from {model}"
                )

                # Invalid language output is not
                # necessarily a model quota error.
                # Give the same model another chance.
                if attempt < MAX_RETRIES:

                    time.sleep(
                        RETRY_DELAY
                    )

                    continue

                return ""

        except Exception as error:

            print(
                f"⚠️ {model} error: "
                f"{error}"
            )

            # Tell global model state about
            # quota/rate/server errors.
            state_result = handle_model_error(
                model,
                error,
            )

            # Temporary model error:
            # immediately leave this model.
            if is_temporary_model_error(
                error
            ):

                print(
                    f"🔒 {model} temporarily "
                    f"unavailable."
                )

                print(
                    "🛟 Moving to next model."
                )

                return ""

            # Other normal error:
            # retry this model.
            if attempt < MAX_RETRIES:

                print(
                    f"⏳ Waiting "
                    f"{RETRY_DELAY}s "
                    f"before retry..."
                )

                time.sleep(
                    RETRY_DELAY
                )

            else:

                return ""

    return ""


# ============================================================
# GENERATE SUMMARY
# ============================================================

def generate_summary(
    article,
    model=None,
):
    """
    Generate Khmer summary using STRICT sequential model fallback.

    Priority is always: 3.8 -> 3.5 -> 3.1.

    Once a model has failed, this function never goes backward
    to an earlier model during the same request.
    """

    if not article:
        return ""

    # --------------------------------------------------------
    # Build a strict forward-only model sequence.
    # --------------------------------------------------------
    if model:
        requested_model = str(model).strip()

        if requested_model in MODEL_CHAIN:
            start_index = MODEL_CHAIN.index(requested_model)
        else:
            print(
                f"⚠️ Unknown requested model: {requested_model}"
            )
            start_index = 0
    else:
        # Start with the highest-priority currently available model.
        start_index = None

        for index, candidate in enumerate(MODEL_CHAIN):
            if not is_model_locked(candidate):
                start_index = index
                break

        if start_index is None:
            print(
                "⏳ All Gemini models are temporarily unavailable."
            )
            return ""

    # --------------------------------------------------------
    # STRICT FALLBACK: only move forward in MODEL_CHAIN.
    # Never restart from 3.8 after moving to 3.5 or 3.1.
    # --------------------------------------------------------
    for index in range(start_index, len(MODEL_CHAIN)):
        active_model = MODEL_CHAIN[index]

        if is_model_locked(active_model):
            print(
                f"🔒 {active_model} is locked. Skipping to next model."
            )
            continue

        print(
            f"🧠 Summary Active Model: {active_model}"
        )

        result = generate_with_model(
            article,
            active_model,
        )

        if result:
            return result

        # Move ONLY to the next model in MODEL_CHAIN.
        if index + 1 < len(MODEL_CHAIN):
            next_model = MODEL_CHAIN[index + 1]

            print(
                f"🛟 Summary fallback: "
                f"{active_model} → {next_model}"
            )
        else:
            print(
                f"🛑 {active_model} failed. "
                "No more fallback models available."
            )

    print(
        "❌ All models in the allowed fallback chain failed."
    )
    return ""


# ============================================================
# FALLBACK SUMMARY
# ============================================================

def generate_fallback_summary(
    article,
):
    """
    Backward-compatible function.

    Uses the next available model instead of
    hard-coding only Gemini 3.5.
    """

    fallback_model = get_available_fallback()

    if not fallback_model:

        print(
            "⏳ No fallback Gemini model available."
        )

        return ""

    print(
        f"🛟 Fallback Summary | "
        f"{fallback_model}"
    )

    result = generate_with_model(
        article,
        fallback_model,
    )

    if result:

        print(
            f"✅ Fallback summary generated "
            f"with {fallback_model}"
        )

    else:

        print(
            "❌ Fallback could not generate "
            "valid Khmer summary."
        )

    return result


# ============================================================
# PROCESS ONE ARTICLE
# ============================================================

def summarize_article(
    article,
):
    """
    Process one article.

    Adds:
        khmer_summary
        khmer_title
    """

    if not article:
        return None

    result = generate_summary(
        article
    )

    if not result:

        print(
            "❌ Could not generate Khmer summary."
        )

        return None

    processed_article = article.copy()

    # --------------------------------------------------------
    # Khmer summary
    # --------------------------------------------------------

    processed_article[
        "khmer_summary"
    ] = result

    # --------------------------------------------------------
    # Khmer title
    # --------------------------------------------------------

    khmer_title = extract_khmer_title(
        result
    )

    if khmer_title:

        processed_article[
            "khmer_title"
        ] = khmer_title

        print(
            f"📰 Khmer Title: "
            f"{khmer_title}"
        )

    else:

        processed_article[
            "khmer_title"
        ] = ""

        print(
            "⚠️ Khmer title could not "
            "be extracted."
        )

    return processed_article


# ============================================================
# PROCESS MULTIPLE ARTICLES
# ============================================================

def summarize_articles(
    articles,
):
    """
    Process multiple articles.
    """

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
                f"❌ Summary processing error: "
                f"{error}"
            )

    return results


# ============================================================
# MODEL STATUS
# ============================================================

def get_summary_model_status():
    """
    Return current model information.

    Useful for admin/debugging.
    """

    return {
        "primary": PRIMARY_MODEL,
        "fallback": FALLBACK_MODEL,
        "second_fallback": (
            SECOND_FALLBACK_MODEL
        ),
        "model_chain": list(
            MODEL_CHAIN
        ),
        "active_model": (
            get_active_model()
        ),
        "all_locked": (
            all_models_locked()
        ),
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("KHMER NEWS 24")
    print("AI SUMMARY TEST")
    print("=" * 60)

    print()
    print("Gemini Model Chain:")

    for index, model_name in enumerate(
        MODEL_CHAIN,
        start=1,
    ):

        print(
            f"{index}. {model_name}"
        )

    print()

    print(
        f"Active Model: "
        f"{get_active_model()}"
    )

    print(
        f"All Models Locked: "
        f"{all_models_locked()}"
    )

    print()
    print("=" * 60)

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

    print()

    if result:

        print(
            "✅ SUMMARY TEST PASSED"
        )

        print()
        print(
            "Khmer Title:"
        )

        print(
            result.get(
                "khmer_title",
                "",
            )
        )

        print()
        print(
            "Khmer Summary:"
        )

        print(
            result.get(
                "khmer_summary",
                "",
            )
        )

    else:

        print(
            "❌ SUMMARY TEST FAILED"
        )

    print()
    print("=" * 60)