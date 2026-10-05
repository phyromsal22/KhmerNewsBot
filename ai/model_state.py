"""
============================================================
KHMER NEWS 24
AI MODEL STATE / GLOBAL QUOTA FALLBACK
============================================================

Purpose:
    Gemini 3.8 Flash
        ↓ quota/rate limit
    Gemini 3.5 Flash Lite

Features:
    - Global quota lock
    - Persistent lock across bot restarts
    - Automatic fallback
    - Automatic unlock after reset time
    - Save state to data/ai_model_state.json
============================================================
"""

import os
import re
import json

from datetime import datetime, timedelta, timezone


# ============================================================
# MODELS
# ============================================================

PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_MODEL = "gemini-3.5-flash-lite"


# ============================================================
# STATE FILE
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

STATE_FILE = os.path.join(
    DATA_DIR,
    "ai_model_state.json"
)


# ============================================================
# GLOBAL STATE
# ============================================================

PRIMARY_QUOTA_LOCKED = False

PRIMARY_QUOTA_RESET_TIME = None


# ============================================================
# ENSURE DATA DIRECTORY
# ============================================================

def ensure_data_directory():

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )


# ============================================================
# SAVE STATE
# ============================================================

def save_state():

    ensure_data_directory()

    state = {
        "primary_model": PRIMARY_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "primary_quota_locked": PRIMARY_QUOTA_LOCKED,
        "primary_quota_reset_time": (
            PRIMARY_QUOTA_RESET_TIME.isoformat()
            if PRIMARY_QUOTA_RESET_TIME
            else None
        ),
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    temp_file = STATE_FILE + ".tmp"

    try:

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                state,
                file,
                indent=4,
                ensure_ascii=False
            )

        # Replace old state safely
        os.replace(
            temp_file,
            STATE_FILE
        )

    except Exception as error:

        print(
            f"⚠️ Could not save AI state: {error}"
        )

        try:

            if os.path.exists(
                temp_file
            ):

                os.remove(
                    temp_file
                )

        except Exception:
            pass


# ============================================================
# LOAD STATE
# ============================================================

def load_state():

    global PRIMARY_QUOTA_LOCKED
    global PRIMARY_QUOTA_RESET_TIME

    if not os.path.exists(
        STATE_FILE
    ):

        return

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            state = json.load(
                file
            )

        PRIMARY_QUOTA_LOCKED = bool(
            state.get(
                "primary_quota_locked",
                False
            )
        )

        reset_time = state.get(
            "primary_quota_reset_time"
        )

        if reset_time:

            PRIMARY_QUOTA_RESET_TIME = (
                datetime.fromisoformat(
                    reset_time
                )
            )

            # Ensure timezone-aware datetime
            if (
                PRIMARY_QUOTA_RESET_TIME.tzinfo
                is None
            ):

                PRIMARY_QUOTA_RESET_TIME = (
                    PRIMARY_QUOTA_RESET_TIME.replace(
                        tzinfo=timezone.utc
                    )
                )

        else:

            PRIMARY_QUOTA_RESET_TIME = None

        # Check whether lock already expired
        if PRIMARY_QUOTA_LOCKED:

            if PRIMARY_QUOTA_RESET_TIME:

                now = datetime.now(
                    timezone.utc
                )

                if now >= PRIMARY_QUOTA_RESET_TIME:

                    PRIMARY_QUOTA_LOCKED = False

                    PRIMARY_QUOTA_RESET_TIME = None

                    save_state()

                    print(
                        "🔓 Saved Gemini 3.8 lock "
                        "has expired."
                    )

                else:

                    print()
                    print("=" * 60)
                    print(
                        "🔒 RESTORED GEMINI 3.8 QUOTA LOCK"
                    )
                    print("=" * 60)
                    print(
                        "🛟 Using fallback: "
                        f"{FALLBACK_MODEL}"
                    )
                    print(
                        "⏰ Reset: "
                        f"{PRIMARY_QUOTA_RESET_TIME.isoformat()}"
                    )
                    print("=" * 60)

            else:

                print(
                    "🔒 Gemini 3.8 remains locked "
                    "(no reset time)."
                )

    except Exception as error:

        print(
            f"⚠️ Could not load AI state: {error}"
        )

        # Safe default
        PRIMARY_QUOTA_LOCKED = False
        PRIMARY_QUOTA_RESET_TIME = None


# ============================================================
# QUOTA ERROR DETECTION
# ============================================================

def is_quota_error(error):

    if error is None:
        return False

    text = str(error).lower()

    quota_words = [
        "429",
        "resource_exhausted",
        "quota exceeded",
        "quota",
        "rate limit",
        "ratelimit",
        "generate_content_free_tier_requests",
    ]

    return any(
        word in text
        for word in quota_words
    )


def is_temporary_service_error(error):
    """Return True for Gemini temporary service overload/unavailable errors."""
    if error is None:
        return False

    text = str(error).lower()
    return (
        "503" in text
        or "unavailable" in text
        or "service unavailable" in text
    )


# ============================================================
# EXTRACT RETRY SECONDS
# ============================================================

def extract_retry_seconds(error):

    if error is None:
        return None

    text = str(error)

    # --------------------------------------------------------
    # retry in 14h32m1.6s
    # --------------------------------------------------------

    match = re.search(
        r"retry in\s+"
        r"(?:(\d+)h)?"
        r"(?:(\d+)m)?"
        r"(?:(\d+(?:\.\d+)?)s)?",
        text,
        re.IGNORECASE,
    )

    if match:

        hours = int(
            match.group(1) or 0
        )

        minutes = int(
            match.group(2) or 0
        )

        seconds = float(
            match.group(3) or 0
        )

        total = (
            hours * 3600
            + minutes * 60
            + seconds
        )

        if total > 0:

            return int(
                total
            )

    # --------------------------------------------------------
    # retryDelay: 52323s
    # --------------------------------------------------------

    match = re.search(
        r"retryDelay['\"]?\s*:\s*['\"]?"
        r"(\d+(?:\.\d+)?)s",
        text,
        re.IGNORECASE,
    )

    if match:

        seconds = float(
            match.group(1)
        )

        if seconds > 0:

            return int(
                seconds
            )

    # --------------------------------------------------------
    # retryDelay = 52323s
    # --------------------------------------------------------

    match = re.search(
        r"retryDelay\s*=\s*"
        r"(\d+(?:\.\d+)?)s",
        text,
        re.IGNORECASE,
    )

    if match:

        seconds = float(
            match.group(1)
        )

        if seconds > 0:

            return int(
                seconds
            )

    return None


# ============================================================
# LOCK PRIMARY MODEL
# ============================================================

def lock_primary_model(
    error=None,
    default_hours=15,
):

    global PRIMARY_QUOTA_LOCKED
    global PRIMARY_QUOTA_RESET_TIME

    # If 3.8 is already locked, keep the existing reset time.
    # This prevents repeated errors from extending the lock.
    if PRIMARY_QUOTA_LOCKED and PRIMARY_QUOTA_RESET_TIME is not None:
        if datetime.now(timezone.utc) < PRIMARY_QUOTA_RESET_TIME:
            print(
                "🔒 Gemini 3.8 is already locked. "
                "Keeping existing reset time."
            )
            return

    PRIMARY_QUOTA_LOCKED = True

    retry_seconds = extract_retry_seconds(
        error
    )

    if retry_seconds is None:
        retry_seconds = (
            default_hours * 60 * 60
        )

    PRIMARY_QUOTA_RESET_TIME = (
        datetime.now(
            timezone.utc
        )
        + timedelta(
            seconds=retry_seconds
        )
    )

    # SAVE BEFORE USING FALLBACK
    save_state()

    print()
    print("=" * 60)
    print("🔒 GEMINI 3.8 QUOTA LOCKED")
    print("=" * 60)

    print(
        "🚨 Primary model quota/rate limit detected."
    )

    print(
        f"🛟 Using fallback: "
        f"{FALLBACK_MODEL}"
    )

    print(
        f"⏳ 3.8 unlock time: "
        f"{PRIMARY_QUOTA_RESET_TIME.isoformat()}"
    )

    print(
        f"💾 State saved: "
        f"{STATE_FILE}"
    )

    print("=" * 60)


# ============================================================
# CHECK LOCK
# ============================================================

def is_primary_locked():

    global PRIMARY_QUOTA_LOCKED
    global PRIMARY_QUOTA_RESET_TIME

    if not PRIMARY_QUOTA_LOCKED:

        return False

    # No reset time = stay locked
    if PRIMARY_QUOTA_RESET_TIME is None:

        return True

    now = datetime.now(
        timezone.utc
    )

    # Still locked
    if now < PRIMARY_QUOTA_RESET_TIME:

        return True

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    PRIMARY_QUOTA_LOCKED = False

    PRIMARY_QUOTA_RESET_TIME = None

    save_state()

    print()
    print("=" * 60)
    print("🔓 GEMINI 3.8 QUOTA LOCK RELEASED")
    print("=" * 60)
    print(
        "🚀 Primary model is available again."
    )
    print("=" * 60)

    return False


# ============================================================
# GET ACTIVE MODEL
# ============================================================

def get_active_model():

    if is_primary_locked():

        return FALLBACK_MODEL

    return PRIMARY_MODEL


# ============================================================
# SHOULD USE PRIMARY?
# ============================================================

def should_use_primary():

    return not is_primary_locked()


# ============================================================
# HANDLE MODEL ERROR
# ============================================================

def handle_model_error(
    model_name,
    error,
):

    if model_name != PRIMARY_MODEL:

        return False

    # IMPORTANT:
    # If Gemini 3.8 returns 429/quota/rate-limit OR 503,
    # immediately lock 3.8 and force the system to use 3.5.
    if is_quota_error(error) or is_temporary_service_error(error):

        # Quota errors normally contain an exact retry/reset time.
        # If 503 has no retry time, use a short 15-minute cooldown.
        lock_primary_model(
            error=error,
            default_hours=0.25
            if is_temporary_service_error(error)
            and not is_quota_error(error)
            else 15,
        )

        return True

    return False


# ============================================================
# PRIMARY FAILURE → FALLBACK
# ============================================================

def fallback_after_primary_error(error):
    """
    Handle a Gemini 3.8 failure and return the model to use next.

    Returns:
        gemini-3.5-flash-lite when 3.8 quota/rate-limit/503 is detected.
    """
    handled = handle_model_error(
        PRIMARY_MODEL,
        error,
    )

    if handled:
        return FALLBACK_MODEL

    return get_active_model()


# ============================================================
# STATUS
# ============================================================

def get_model_status():

    locked = is_primary_locked()

    if locked:

        active_model = FALLBACK_MODEL

    else:

        active_model = PRIMARY_MODEL

    reset_time = None

    if PRIMARY_QUOTA_RESET_TIME:

        reset_time = (
            PRIMARY_QUOTA_RESET_TIME.isoformat()
        )

    return {
        "primary_model": PRIMARY_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "primary_locked": locked,
        "active_model": active_model,
        "reset_time": reset_time,
        "state_file": STATE_FILE,
    }


# ============================================================
# PRINT STATUS
# ============================================================

def print_model_status():

    status = get_model_status()

    print()
    print("=" * 60)
    print("🤖 KHMER NEWS 24 — AI MODEL STATUS")
    print("=" * 60)

    print(
        f"🚀 Primary: "
        f"{status['primary_model']}"
    )

    print(
        f"🛟 Fallback: "
        f"{status['fallback_model']}"
    )

    print(
        f"🤖 Active: "
        f"{status['active_model']}"
    )

    print(
        f"🔒 Primary locked: "
        f"{status['primary_locked']}"
    )

    if status["reset_time"]:

        print(
            f"⏳ Reset: "
            f"{status['reset_time']}"
        )

    print(
        f"💾 State file: "
        f"{status['state_file']}"
    )

    print("=" * 60)


# ============================================================
# LOAD SAVED STATE WHEN MODULE STARTS
# ============================================================

load_state()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print_model_status()

    fake_error = """
    429 RESOURCE_EXHAUSTED
    Quota exceeded
    Please retry in 2h30m10s.
    """

    print()
    print("🧪 Testing quota lock...")

    handle_model_error(
        PRIMARY_MODEL,
        fake_error
    )

    print_model_status()

    print()
    print(
        f"🤖 Active model: "
        f"{get_active_model()}"
    )