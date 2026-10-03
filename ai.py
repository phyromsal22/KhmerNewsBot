import os
import json
import time

from dotenv import load_dotenv
from google import genai


# =========================================================
# ENV
# =========================================================

load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


if not GEMINI_API_KEY:

    raise ValueError(
        "❌ GEMINI_API_KEY not found in .env"
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# GEMINI MODELS
# =========================================================

# Main model
PRIMARY_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)


# Backup model
FALLBACK_MODEL = os.getenv(
    "GEMINI_FALLBACK_MODEL",
    "gemini-3.5-flash-lite"
)


# =========================================================
# SETTINGS
# =========================================================

# Retry only temporary errors such as 503
MAX_RETRIES = 2

# Seconds between retry
RETRY_DELAY = 5


# =========================================================
# PRINT MODEL CONFIG
# =========================================================

print(
    f"🤖 Primary Gemini Model: {PRIMARY_MODEL}"
)

print(
    f"🔄 Fallback Gemini Model: {FALLBACK_MODEL}"
)


# =========================================================
# CLEAN AI JSON
# =========================================================

def clean_json_response(text):

    if not text:

        return ""


    text = text.strip()


    # Remove ```json

    if text.startswith(
        "```json"
    ):

        text = text[7:]


    # Remove ```

    if text.startswith(
        "```"
    ):

        text = text[3:]


    # Remove ending ```

    if text.endswith(
        "```"
    ):

        text = text[:-3]


    return text.strip()


# =========================================================
# ERROR TYPE CHECK
# =========================================================

def is_quota_error(error):

    error_text = str(
        error
    ).lower()


    quota_words = [

        "429",

        "resource_exhausted",

        "quota exceeded",

        "quota",

        "rate limit",

    ]


    for word in quota_words:

        if word in error_text:

            return True


    return False


# =========================================================
# TEMPORARY ERROR CHECK
# =========================================================

def is_temporary_error(error):

    error_text = str(
        error
    ).lower()


    temporary_words = [

        "503",

        "unavailable",

        "temporarily",

        "high demand",

        "service unavailable",

        "internal server error",

    ]


    for word in temporary_words:

        if word in error_text:

            return True


    return False


# =========================================================
# BUILD NEWS PROMPT
# =========================================================

def build_news_prompt(
    articles
):

    prompt = f"""
You are the AI editor for Khmer News 24.

Translate and summarize the news into natural,
clear Khmer.

RULES:

1. Do not invent facts.
2. Do not add information that is not in the source.
3. Keep names accurate.
4. Keep locations accurate.
5. Keep numbers accurate.
6. Keep dates accurate.
7. Keep organizations accurate.
8. Do not give personal opinions.
9. Do not exaggerate.
10. If something is an allegation or claim,
    clearly indicate that it is reported or alleged.
11. Do not present an unverified claim as confirmed.
12. Create a short Khmer headline.
13. Summary should normally be 3-5 clear Khmer sentences: explain what happened, who/what was involved, where/when if stated, and the impact if the source states it.
14. IMPORTANT LANGUAGE RULE: Write the headline and summary in Khmer only. English/Latin text is allowed only for necessary proper names, club names, organization names, brand names, model names, or technical terms.
15. NEVER output Thai, Lao, Burmese, Chinese, Vietnamese, or other non-Khmer scripts. If a word is uncertain, use a clear Khmer word or necessary English name instead.
16. Preserve the meaning of the original.
17. Do not use markdown.
18. Return ONLY valid JSON.
19. Return one JSON object for each news article.
20. Keep the same article ID.

JSON FORMAT:

[
  {{
    "id": 1,
    "title_kh": "ចំណងជើងជាភាសាខ្មែរ",
    "summary_kh": "សេចក្តីសង្ខេបជាភាសាខ្មែរ"
  }}
]

NEWS:

{json.dumps(
    articles,
    ensure_ascii=False,
    indent=2
)}
"""

    return prompt


# =========================================================
# KHMER LANGUAGE CLEANER
# =========================================================

def clean_foreign_scripts(text):
    """Keep Khmer + Latin/English + numbers/punctuation.
    Remove accidental Thai/Lao/other-script characters from Gemini output.
    """
    if not isinstance(text, str):
        return text

    cleaned = []
    for ch in text:
        cp = ord(ch)

        # Khmer Unicode block
        is_khmer = 0x1780 <= cp <= 0x17FF

        # Latin letters, digits and common Latin extensions
        is_latin = (
            0x0041 <= cp <= 0x005A or
            0x0061 <= cp <= 0x007A or
            0x00C0 <= cp <= 0x024F
        )

        # Keep numbers, whitespace and normal punctuation/symbols.
        is_number = 0x0030 <= cp <= 0x0039
        is_space = ch.isspace()
        is_punctuation = ch in ".,!?;:'\"-–—()[]{}%+/&@#$*_+=<>|…៖៕។,៘៙"

        if is_khmer or is_latin or is_number or is_space or is_punctuation:
            cleaned.append(ch)

    result = "".join(cleaned)

    # Remove accidental leftover repeated spaces.
    while "  " in result:
        result = result.replace("  ", " ")

    return result.strip()


def clean_ai_output(data):
    """Clean title/summary text returned by Gemini."""
    if not isinstance(data, list):
        return data

    cleaned_data = []

    for item in data:
        if not isinstance(item, dict):
            continue

        item = dict(item)
        item["title_kh"] = clean_foreign_scripts(item.get("title_kh", ""))
        item["summary_kh"] = clean_foreign_scripts(item.get("summary_kh", ""))
        cleaned_data.append(item)

    return cleaned_data


# =========================================================
# CALL GEMINI
# =========================================================

def call_gemini(
    model,
    prompt
):

    response = (
        client.models.generate_content(
            model=model,
            contents=prompt
        )
    )


    result = response.text


    if not result:

        raise ValueError(
            "Gemini returned empty response."
        )


    return result


# =========================================================
# PROCESS WITH ONE MODEL
# =========================================================

def process_with_model(
    model,
    prompt
):

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"🤖 Using {model} "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )


            # -------------------------------------------------
            # Call Gemini
            # -------------------------------------------------

            result = call_gemini(
                model,
                prompt
            )


            # -------------------------------------------------
            # Clean response
            # -------------------------------------------------

            result = clean_json_response(
                result
            )


            # -------------------------------------------------
            # Parse JSON
            # -------------------------------------------------

            data = json.loads(
                result
            )


            # -------------------------------------------------
            # Validate JSON
            # -------------------------------------------------

            if not isinstance(
                data,
                list
            ):

                raise ValueError(
                    "Gemini returned JSON "
                    "but it is not a list."
                )


            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            print(
                f"✅ {model} success: "
                f"{len(data)} articles processed."
            )


            return {
                "success": True,
                "data": clean_ai_output(data),
                "error": None,
                "error_type": None
            }


        except Exception as error:

            print(
                f"❌ {model} error "
                f"(attempt {attempt}/{MAX_RETRIES}): "
                f"{error}"
            )


            # -------------------------------------------------
            # QUOTA ERROR
            # -------------------------------------------------

            if is_quota_error(
                error
            ):

                print(
                    f"⚠️ {model} quota/rate limit reached."
                )


                return {
                    "success": False,
                    "data": [],
                    "error": error,
                    "error_type": "quota"
                }


            # -------------------------------------------------
            # TEMPORARY ERROR
            # -------------------------------------------------

            if is_temporary_error(
                error
            ):

                if attempt < MAX_RETRIES:

                    print(
                        f"⏳ Temporary error."
                        f" Retrying in "
                        f"{RETRY_DELAY} seconds..."
                    )


                    time.sleep(
                        RETRY_DELAY
                    )


                    continue


                print(
                    f"⚠️ {model} temporary "
                    f"error after retries."
                )


                return {
                    "success": False,
                    "data": [],
                    "error": error,
                    "error_type": "temporary"
                }


            # -------------------------------------------------
            # JSON ERROR
            # -------------------------------------------------

            if isinstance(
                error,
                json.JSONDecodeError
            ):

                if attempt < MAX_RETRIES:

                    print(
                        "⚠️ Invalid JSON."
                        " Retrying..."
                    )


                    time.sleep(
                        RETRY_DELAY
                    )


                    continue


                return {
                    "success": False,
                    "data": [],
                    "error": error,
                    "error_type": "json"
                }


            # -------------------------------------------------
            # OTHER ERROR
            # -------------------------------------------------

            return {
                "success": False,
                "data": [],
                "error": error,
                "error_type": "other"
            }


    # ---------------------------------------------------------
    # FINAL FAILURE
    # ---------------------------------------------------------

    return {
        "success": False,
        "data": [],
        "error": None,
        "error_type": "unknown"
    }


# =========================================================
# BATCH PROCESS
# =========================================================

def process_news_batch(
    news_list
):

    if not news_list:

        return []


    # ---------------------------------------------------------
    # Prepare articles
    # ---------------------------------------------------------

    articles = []


    for index, news in enumerate(
        news_list,
        start=1
    ):

        articles.append({

            "id": index,

            "title": news.get(
                "title",
                ""
            ),

            "summary": news.get(
                "summary",
                ""
            ),

            "source": news.get(
                "source",
                ""
            ),

            "category": news.get(
                "category",
                ""
            ),

        })


    # ---------------------------------------------------------
    # Build prompt
    # ---------------------------------------------------------

    prompt = build_news_prompt(
        articles
    )


    # =========================================================
    # TRY PRIMARY MODEL
    # =========================================================

    print(
        ""
    )

    print(
        "=========================================="
    )

    print(
        f"🤖 Trying primary model: "
        f"{PRIMARY_MODEL}"
    )

    print(
        "=========================================="
    )


    primary_result = process_with_model(
        PRIMARY_MODEL,
        prompt
    )


    # ---------------------------------------------------------
    # Primary SUCCESS
    # ---------------------------------------------------------

    if primary_result[
        "success"
    ]:

        return primary_result[
            "data"
        ]


    # =========================================================
    # PRIMARY FAILED
    # =========================================================

    print(
        ""
    )

    print(
        f"⚠️ Primary model failed: "
        f"{PRIMARY_MODEL}"
    )


    # =========================================================
    # TRY FALLBACK MODEL
    # =========================================================

    # Prevent using the same model twice

    if (
        FALLBACK_MODEL
        and
        FALLBACK_MODEL != PRIMARY_MODEL
    ):

        print(
            ""
        )

        print(
            "=========================================="
        )

        print(
            f"🔄 Switching to fallback model: "
            f"{FALLBACK_MODEL}"
        )

        print(
            "=========================================="
        )


        fallback_result = process_with_model(
            FALLBACK_MODEL,
            prompt
        )


        # -----------------------------------------------------
        # Fallback SUCCESS
        # -----------------------------------------------------

        if fallback_result[
            "success"
        ]:

            print(
                f"✅ Fallback model "
                f"{FALLBACK_MODEL} worked!"
            )


            return fallback_result[
                "data"
            ]


        # -----------------------------------------------------
        # Fallback FAILED
        # -----------------------------------------------------

        print(
            ""
        )

        print(
            f"❌ Fallback model also failed: "
            f"{FALLBACK_MODEL}"
        )


    # =========================================================
    # ALL MODELS FAILED
    # =========================================================

    print(
        ""
    )

    print(
        "❌ All Gemini models failed."
    )

    print(
        "⚠️ News will continue without "
        "AI processing."
    )


    return []


# =========================================================
# SINGLE ARTICLE
# =========================================================

def process_single_news(
    news
):

    result = process_news_batch(
        [news]
    )


    if not result:

        return None


    return result[0]