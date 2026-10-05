"""
Gemini AI Model State Manager
3-Level Automatic Fallback

Priority:
1. gemini-3.8-flash
2. gemini-3.5-flash-lite
3. gemini-3.1-flash-lite

If all models are temporarily unavailable, the system waits
until the appropriate cooldown/reset time.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# ============================================================
# MODEL CONFIGURATION
# ============================================================

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"
SECOND_FALLBACK_MODEL = "gemini-3.1-flash-lite"

MODEL_CHAIN = (
    PRIMARY_MODEL,
    FALLBACK_MODEL,
    SECOND_FALLBACK_MODEL,
)

STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "ai_model_state.json",
)


# ============================================================
# DEFAULT COOLDOWNS
# ============================================================

DEFAULT_RPM_COOLDOWN_SECONDS = 60
DEFAULT_503_COOLDOWN_SECONDS = 15 * 60
DEFAULT_QUOTA_COOLDOWN_SECONDS = 15 * 60 * 60


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

PRIMARY_QUOTA_LOCKED = False
PRIMARY_QUOTA_RESET_TIME: Optional[float] = None


# ============================================================
# MODEL STATE
# ============================================================

MODEL_LOCKED: Dict[str, bool] = {
    PRIMARY_MODEL: False,
    FALLBACK_MODEL: False,
    SECOND_FALLBACK_MODEL: False,
}

MODEL_RESET_TIME: Dict[str, Optional[float]] = {
    PRIMARY_MODEL: None,
    FALLBACK_MODEL: None,
    SECOND_FALLBACK_MODEL: None,
}

MODEL_LAST_ERROR: Dict[str, str] = {
    PRIMARY_MODEL: "",
    FALLBACK_MODEL: "",
    SECOND_FALLBACK_MODEL: "",
}


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _ensure_data_directory() -> None:
    """Create data directory if it does not exist."""
    data_dir = os.path.dirname(STATE_FILE)

    if data_dir:
        os.makedirs(data_dir, exist_ok=True)


def _now() -> float:
    """Return current Unix timestamp."""
    return time.time()


def _iso_from_timestamp(
    timestamp: Optional[float],
) -> Optional[str]:
    """Convert timestamp to readable UTC ISO format."""
    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        ).isoformat()
    except Exception:
        return None


def _timestamp_from_iso(
    value: Any,
) -> Optional[float]:
    """Convert ISO timestamp to Unix timestamp."""
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            str(value)
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.timestamp()

    except Exception:
        return None


def _safe_int(
    value: Any,
    default: int,
) -> int:
    """Convert value to int safely."""
    try:
        return int(value)
    except Exception:
        return default


def _normalize_model_name(
    model_name: str,
) -> str:
    """Normalize Gemini model name."""
    if not model_name:
        return ""

    return str(model_name).strip()


# ============================================================
# STATE SAVE / LOAD
# ============================================================

def _save_state() -> None:
    """Save model state to JSON."""
    global PRIMARY_QUOTA_LOCKED
    global PRIMARY_QUOTA_RESET_TIME

    try:
        _ensure_data_directory()

        data = {
            "version": 3,
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),

            "models": {
                model: {
                    "locked": MODEL_LOCKED.get(
                        model,
                        False,
                    ),
                    "reset_time": _iso_from_timestamp(
                        MODEL_RESET_TIME.get(model)
                    ),
                    "last_error": MODEL_LAST_ERROR.get(
                        model,
                        "",
                    ),
                }
                for model in MODEL_CHAIN
            },

            # Backward-compatible fields
            "primary_quota_locked": (
                PRIMARY_QUOTA_LOCKED
            ),
            "primary_quota_reset_time": (
                _iso_from_timestamp(
                    PRIMARY_QUOTA_RESET_TIME
                )
            ),
        }

        temp_file = STATE_FILE + ".tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        os.replace(
            temp_file,
            STATE_FILE,
        )

    except Exception:
        # State persistence must never crash the bot.
        pass


def _load_state() -> None:
    """Load saved model state."""
    global PRIMARY_QUOTA_LOCKED
    global PRIMARY_QUOTA_RESET_TIME

    if not os.path.exists(STATE_FILE):
        return

    try:
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        models_data = data.get(
            "models",
            {},
        )

        if isinstance(
            models_data,
            dict,
        ):
            for model in MODEL_CHAIN:
                model_data = models_data.get(
                    model,
                    {},
                )

                if not isinstance(
                    model_data,
                    dict,
                ):
                    continue

                MODEL_LOCKED[model] = bool(
                    model_data.get(
                        "locked",
                        False,
                    )
                )

                MODEL_RESET_TIME[model] = (
                    _timestamp_from_iso(
                        model_data.get(
                            "reset_time"
                        )
                    )
                )

                MODEL_LAST_ERROR[model] = str(
                    model_data.get(
                        "last_error",
                        "",
                    )
                )

        # Backward compatibility with old state files
        old_locked = data.get(
            "primary_quota_locked"
        )

        if old_locked is not None:
            PRIMARY_QUOTA_LOCKED = bool(
                old_locked
            )

        old_reset = data.get(
            "primary_quota_reset_time"
        )

        if old_reset:
            PRIMARY_QUOTA_RESET_TIME = (
                _timestamp_from_iso(
                    old_reset
                )
            )

        # Migrate old primary lock.
        if PRIMARY_QUOTA_LOCKED:
            MODEL_LOCKED[
                PRIMARY_MODEL
            ] = True

            if (
                MODEL_RESET_TIME[
                    PRIMARY_MODEL
                ]
                is None
            ):
                MODEL_RESET_TIME[
                    PRIMARY_MODEL
                ] = PRIMARY_QUOTA_RESET_TIME

    except Exception:
        # Corrupt state should not stop the bot.
        pass


# ============================================================
# RESET EXPIRED LOCKS
# ============================================================

def _refresh_expired_locks() -> None:
    """Unlock models whose cooldown has expired."""
    global PRIMARY_QUOTA_LOCKED
    global PRIMARY_QUOTA_RESET_TIME

    current_time = _now()
    changed = False

    for model in MODEL_CHAIN:
        if not MODEL_LOCKED.get(
            model,
            False,
        ):
            continue

        reset_time = MODEL_RESET_TIME.get(
            model
        )

        if reset_time is None:
            continue

        if current_time >= reset_time:
            MODEL_LOCKED[model] = False
            MODEL_RESET_TIME[model] = None
            MODEL_LAST_ERROR[model] = ""
            changed = True

    # Keep backward compatibility variables synchronized.
    PRIMARY_QUOTA_LOCKED = MODEL_LOCKED.get(
        PRIMARY_MODEL,
        False,
    )

    PRIMARY_QUOTA_RESET_TIME = (
        MODEL_RESET_TIME.get(
            PRIMARY_MODEL
        )
    )

    if changed:
        _save_state()


# ============================================================
# INITIAL LOAD
# ============================================================

_load_state()
_refresh_expired_locks()


# ============================================================
# ERROR DETECTION
# ============================================================

def _error_text(
    error: Any,
) -> str:
    """Convert exception/error to lowercase text."""
    try:
        return str(error).lower()
    except Exception:
        return ""


def is_quota_error(
    error: Any,
) -> bool:
    """Detect Gemini daily quota/resource exhaustion."""
    text = _error_text(error)

    quota_keywords = (
        "resource_exhausted",
        "quota",
        "daily limit",
        "daily quota",
        "quota exceeded",
        "limit exceeded",
        "resource exhausted",
    )

    return any(
        keyword in text
        for keyword in quota_keywords
    )


def is_rate_limit_error(
    error: Any,
) -> bool:
    """Detect RPM/rate-limit/429 errors."""
    text = _error_text(error)

    rate_keywords = (
        "429",
        "rate limit",
        "rate_limit",
        "too many requests",
        "requests per minute",
        "rpm",
        "ratelimit",
    )

    return any(
        keyword in text
        for keyword in rate_keywords
    )


def is_server_error(
    error: Any,
) -> bool:
    """Detect temporary Gemini server errors."""
    text = _error_text(error)

    server_keywords = (
        "503",
        "service unavailable",
        "unavailable",
        "overloaded",
        "temporarily unavailable",
        "internal server error",
        "server error",
    )

    return any(
        keyword in text
        for keyword in server_keywords
    )


def is_model_error(
    error: Any,
) -> bool:
    """Detect errors that should cause model fallback."""
    return (
        is_quota_error(error)
        or is_rate_limit_error(error)
        or is_server_error(error)
    )


# ============================================================
# RETRY TIME DETECTION
# ============================================================

def _extract_retry_seconds(
    error: Any,
) -> Optional[int]:
    """
    Try to extract retry delay from Gemini error text.

    Supports examples such as:
        retry in 37s
        retry in 1m 20s
        retryDelay: 45s
    """

    text = _error_text(error)

    # retry in Xs
    match = re.search(
        r"retry(?:\s+after|\s+in)?\s*[:=]?\s*"
        r"(\d+(?:\.\d+)?)\s*s",
        text,
        re.IGNORECASE,
    )

    if match:
        try:
            return max(
                1,
                int(
                    float(
                        match.group(1)
                    )
                ),
            )
        except Exception:
            pass

    # retry in Xm Ys
    match = re.search(
        r"retry(?:\s+after|\s+in)?\s*[:=]?\s*"
        r"(\d+)\s*m(?:\s*(\d+)\s*s)?",
        text,
        re.IGNORECASE,
    )

    if match:
        try:
            minutes = int(
                match.group(1)
            )

            seconds = int(
                match.group(2) or 0
            )

            return max(
                1,
                minutes * 60 + seconds,
            )
        except Exception:
            pass

    # retryDelay: 45s
    match = re.search(
        r"retrydelay[^0-9]*"
        r"(\d+(?:\.\d+)?)\s*s",
        text,
        re.IGNORECASE,
    )

    if match:
        try:
            return max(
                1,
                int(
                    float(
                        match.group(1)
                    )
                ),
            )
        except Exception:
            pass

    # retryDelay: 45
    match = re.search(
        r"retrydelay[^0-9]*(\d+)",
        text,
        re.IGNORECASE,
    )

    if match:
        try:
            return max(
                1,
                int(
                    match.group(1)
                ),
            )
        except Exception:
            pass

    return None


# ============================================================
# COOLDOWN CALCULATION
# ============================================================

def _calculate_cooldown(
    error: Any,
) -> int:
    """
    Determine model cooldown.

    Priority:
        1. Gemini retry delay
        2. Daily quota
        3. RPM/rate limit
        4. 503/server error
        5. Generic cooldown
    """

    retry_seconds = _extract_retry_seconds(
        error
    )

    if retry_seconds is not None:
        return max(
            retry_seconds,
            5,
        )

    if is_quota_error(error):
        return DEFAULT_QUOTA_COOLDOWN_SECONDS

    if is_rate_limit_error(error):
        return DEFAULT_RPM_COOLDOWN_SECONDS

    if is_server_error(error):
        return DEFAULT_503_COOLDOWN_SECONDS

    return DEFAULT_RPM_COOLDOWN_SECONDS


# ============================================================
# MODEL LOCKING
# ============================================================

def lock_model(
    model_name: str,
    error: Any = None,
    cooldown_seconds: Optional[int] = None,
) -> float:
    """
    Temporarily lock a Gemini model.

    Returns:
        Unix timestamp when model can be retried.
    """

    global PRIMARY_QUOTA_LOCKED
    global PRIMARY_QUOTA_RESET_TIME

    model_name = _normalize_model_name(
        model_name
    )

    if model_name not in MODEL_CHAIN:
        return _now()

    if cooldown_seconds is None:
        cooldown_seconds = _calculate_cooldown(
            error
        )

    cooldown_seconds = max(
        1,
        _safe_int(
            cooldown_seconds,
            DEFAULT_RPM_COOLDOWN_SECONDS,
        ),
    )

    reset_time = (
        _now()
        + cooldown_seconds
    )

    MODEL_LOCKED[
        model_name
    ] = True

    MODEL_RESET_TIME[
        model_name
    ] = reset_time

    if error is not None:
        MODEL_LAST_ERROR[
            model_name
        ] = str(error)

    # Backward compatibility
    if model_name == PRIMARY_MODEL:
        PRIMARY_QUOTA_LOCKED = True
        PRIMARY_QUOTA_RESET_TIME = (
            reset_time
        )

    _save_state()

    return reset_time


def unlock_model(
    model_name: str,
) -> bool:
    """Manually unlock a model."""

    global PRIMARY_QUOTA_LOCKED
    global PRIMARY_QUOTA_RESET_TIME

    model_name = _normalize_model_name(
        model_name
    )

    if model_name not in MODEL_CHAIN:
        return False

    MODEL_LOCKED[
        model_name
    ] = False

    MODEL_RESET_TIME[
        model_name
    ] = None

    MODEL_LAST_ERROR[
        model_name
    ] = ""

    if model_name == PRIMARY_MODEL:
        PRIMARY_QUOTA_LOCKED = False
        PRIMARY_QUOTA_RESET_TIME = None

    _save_state()

    return True


def is_model_locked(
    model_name: str,
) -> bool:
    """Check whether a model is currently locked."""

    _refresh_expired_locks()

    model_name = _normalize_model_name(
        model_name
    )

    if model_name not in MODEL_CHAIN:
        return False

    return bool(
        MODEL_LOCKED.get(
            model_name,
            False,
        )
    )


def is_primary_locked() -> bool:
    """Backward-compatible primary lock check."""
    return is_model_locked(
        PRIMARY_MODEL
    )


# ============================================================
# ACTIVE MODEL
# ============================================================

def get_active_model() -> str:
    """
    Return first available model.

    Priority:
        3.8 → 3.5 → 3.1
    """

    _refresh_expired_locks()

    for model in MODEL_CHAIN:
        if not MODEL_LOCKED.get(
            model,
            False,
        ):
            return model

    # All models locked.
    return MODEL_CHAIN[0]


def get_next_model(
    current_model: str,
) -> Optional[str]:
    """Return model immediately after current model."""

    current_model = _normalize_model_name(
        current_model
    )

    try:
        index = MODEL_CHAIN.index(
            current_model
        )
    except ValueError:
        return MODEL_CHAIN[0]

    next_index = index + 1

    if next_index >= len(
        MODEL_CHAIN
    ):
        return None

    return MODEL_CHAIN[
        next_index
    ]


def get_available_models() -> list[str]:
    """Return all currently available models."""

    _refresh_expired_locks()

    return [
        model
        for model in MODEL_CHAIN
        if not MODEL_LOCKED.get(
            model,
            False,
        )
    ]


def all_models_locked() -> bool:
    """Return True if every model is locked."""

    _refresh_expired_locks()

    return all(
        MODEL_LOCKED.get(
            model,
            False,
        )
        for model in MODEL_CHAIN
    )


# ============================================================
# WAIT TIME
# ============================================================

def get_model_reset_time(
    model_name: str,
) -> Optional[float]:
    """Return reset timestamp for model."""

    _refresh_expired_locks()

    model_name = _normalize_model_name(
        model_name
    )

    return MODEL_RESET_TIME.get(
        model_name
    )


def get_model_wait_seconds(
    model_name: str,
) -> int:
    """Return remaining cooldown seconds."""

    reset_time = get_model_reset_time(
        model_name
    )

    if reset_time is None:
        return 0

    remaining = (
        reset_time
        - _now()
    )

    return max(
        0,
        int(remaining),
    )


def get_short_wait_message(
    model_name: str,
) -> str:
    """Return human-readable wait message."""

    seconds = get_model_wait_seconds(
        model_name
    )

    if seconds <= 0:
        return "Ready"

    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60

    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = (
        minutes % 60
    )

    if remaining_minutes:
        return (
            f"{hours}h "
            f"{remaining_minutes}m"
        )

    return f"{hours}h"


# ============================================================
# ERROR HANDLING
# ============================================================

def handle_model_error(
    model_name: str,
    error: Any,
) -> Dict[str, Any]:
    """
    Handle Gemini model error.

    The failed model is temporarily locked.
    """

    model_name = _normalize_model_name(
        model_name
    )

    if model_name not in MODEL_CHAIN:
        return {
            "model": model_name,
            "handled": False,
            "locked": False,
            "quota_error": False,
            "rate_limit_error": False,
            "server_error": False,
            "cooldown_seconds": 0,
            "reset_time": None,
            "next_model": get_next_model(
                model_name
            ),
        }

    quota_error = is_quota_error(
        error
    )

    rate_limit_error = (
        is_rate_limit_error(
            error
        )
    )

    server_error = is_server_error(
        error
    )

    should_lock = (
        quota_error
        or rate_limit_error
        or server_error
    )

    if should_lock:
        cooldown_seconds = (
            _calculate_cooldown(
                error
            )
        )

    else:
        # Generic error.
        cooldown_seconds = 15

    reset_time = lock_model(
        model_name=model_name,
        error=error,
        cooldown_seconds=cooldown_seconds,
    )

    next_model = None

    # Find next available model strictly AFTER the failed model.
    # Never move backward in MODEL_CHAIN.
    try:
        failed_index = MODEL_CHAIN.index(model_name)
    except ValueError:
        failed_index = -1

    for candidate in MODEL_CHAIN[failed_index + 1:]:
        if not is_model_locked(candidate):
            next_model = candidate
            break

    return {
        "model": model_name,
        "handled": True,
        "locked": True,
        "quota_error": quota_error,
        "rate_limit_error": rate_limit_error,
        "server_error": server_error,
        "cooldown_seconds": cooldown_seconds,
        "reset_time": reset_time,
        "reset_time_iso": (
            _iso_from_timestamp(
                reset_time
            )
        ),
        "next_model": next_model,
        "all_models_locked": (
            all_models_locked()
        ),
    }


def fallback_after_model_error(
    model_name: str,
    error: Any,
) -> Optional[str]:
    """Lock failed model and return next available model."""

    handle_model_error(
        model_name,
        error,
    )

    return get_available_fallback(
        failed_model=model_name
    )


def fallback_after_primary_error(
    error: Any,
) -> Optional[str]:
    """
    Backward-compatible helper for primary model.
    """

    return fallback_after_model_error(
        PRIMARY_MODEL,
        error,
    )


def get_available_fallback(
    failed_model: Optional[str] = None,
) -> Optional[str]:
    """
    Return the next available model strictly after failed_model.

    Fallback is one-way only:
        3.8 -> 3.5 -> 3.1 -> STOP

    A fallback can never move backward to an earlier model.
    """

    _refresh_expired_locks()

    failed_model = _normalize_model_name(
        failed_model or ""
    )

    # No failed model supplied: return the first available model.
    if not failed_model:
        for model in MODEL_CHAIN:
            if not MODEL_LOCKED.get(model, False):
                return model
        return None

    try:
        failed_index = MODEL_CHAIN.index(failed_model)
    except ValueError:
        return None

    # IMPORTANT: only inspect models AFTER failed_model.
    for model in MODEL_CHAIN[failed_index + 1:]:
        if not MODEL_LOCKED.get(model, False):
            return model

    return None


# ============================================================
# FORCE RESET
# ============================================================

def reset_all_models() -> None:
    """Unlock all Gemini models."""

    global PRIMARY_QUOTA_LOCKED
    global PRIMARY_QUOTA_RESET_TIME

    for model in MODEL_CHAIN:
        MODEL_LOCKED[
            model
        ] = False

        MODEL_RESET_TIME[
            model
        ] = None

        MODEL_LAST_ERROR[
            model
        ] = ""

    PRIMARY_QUOTA_LOCKED = False
    PRIMARY_QUOTA_RESET_TIME = None

    _save_state()


# ============================================================
# STATUS
# ============================================================

def get_model_status(
    model_name: str,
) -> Dict[str, Any]:
    """Return detailed status for one model."""

    _refresh_expired_locks()

    model_name = _normalize_model_name(
        model_name
    )

    if model_name not in MODEL_CHAIN:
        return {
            "model": model_name,
            "known": False,
            "locked": False,
            "available": False,
            "wait_seconds": 0,
            "wait": "Unknown",
            "reset_time": None,
            "last_error": "",
        }

    locked = MODEL_LOCKED.get(
        model_name,
        False,
    )

    return {
        "model": model_name,
        "known": True,
        "locked": locked,
        "available": not locked,
        "wait_seconds": (
            get_model_wait_seconds(
                model_name
            )
        ),
        "wait": (
            get_short_wait_message(
                model_name
            )
        ),
        "reset_time": (
            _iso_from_timestamp(
                MODEL_RESET_TIME.get(
                    model_name
                )
            )
        ),
        "last_error": (
            MODEL_LAST_ERROR.get(
                model_name,
                "",
            )
        ),
    }


def get_status() -> Dict[str, Any]:
    """Return complete Gemini model status."""

    _refresh_expired_locks()

    statuses = {
        model: get_model_status(
            model
        )
        for model in MODEL_CHAIN
    }

    active_model = get_active_model()

    return {
        "version": 3,
        "primary_model": PRIMARY_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "second_fallback_model": (
            SECOND_FALLBACK_MODEL
        ),
        "model_chain": list(
            MODEL_CHAIN
        ),
        "active_model": active_model,
        "all_models_locked": (
            all_models_locked()
        ),
        "models": statuses,
    }


def print_status() -> None:
    """Print model status."""

    status = get_status()

    print()
    print("=" * 60)
    print("GEMINI AI MODEL STATUS")
    print("=" * 60)

    print(
        f"Active Model: "
        f"{status['active_model']}"
    )

    print()

    for model in MODEL_CHAIN:
        model_status = status[
            "models"
        ][model]

        if model_status[
            "available"
        ]:
            state = "AVAILABLE"
        else:
            state = (
                "LOCKED "
                f"({model_status['wait']})"
            )

        print(
            f"{model:<30} "
            f"{state}"
        )

    print("=" * 60)
    print()


# ============================================================
# COMPATIBILITY HELPERS
# ============================================================

def get_primary_model() -> str:
    """Return primary Gemini model."""
    return PRIMARY_MODEL


def get_fallback_model() -> str:
    """Return first fallback Gemini model."""
    return FALLBACK_MODEL


def get_second_fallback_model() -> str:
    """Return second fallback Gemini model."""
    return SECOND_FALLBACK_MODEL


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print_status()

    print("Model Chain:")

    for index, model in enumerate(
        MODEL_CHAIN,
        start=1,
    ):
        print(
            f"{index}. {model}"
        )

    print()

    print(
        f"Active model: "
        f"{get_active_model()}"
    )

    print(
        f"All models locked: "
        f"{all_models_locked()}"
    )

    print()