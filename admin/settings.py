# ============================================================
# KHMER NEWS 24 — ADMIN SETTINGS
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# ADMIN USER IDS
# ============================================================

def get_admin_user_ids():
    """
    Read Telegram admin user IDs from .env

    Example:
    ADMIN_USER_IDS=123456789,987654321
    """

    raw = os.getenv(
        "ADMIN_USER_IDS",
        ""
    ).strip()

    if not raw:
        return set()

    admin_ids = set()

    for value in raw.split(","):

        value = value.strip()

        if not value:
            continue

        try:
            admin_ids.add(
                int(value)
            )

        except ValueError:
            print(
                f"⚠️ Invalid ADMIN_USER_ID: {value}"
            )

    return admin_ids


ADMIN_USER_IDS = get_admin_user_ids()


# ============================================================
# CHECK ADMIN
# ============================================================

def is_admin(user_id):
    """
    Return True when the Telegram user is an admin.
    """

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return False

    return user_id in ADMIN_USER_IDS


# ============================================================
# ADMIN SETTINGS
# ============================================================

ADMIN_TITLE = "👨‍💻 Khmer News 24 Admin"

ADMIN_REFRESH_SECONDS = 30