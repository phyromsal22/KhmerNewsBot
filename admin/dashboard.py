# ============================================================
# KHMER NEWS 24 — ADMIN DASHBOARD
# V2.8
# ============================================================

from admin.settings import (
    is_admin,
    ADMIN_TITLE,
)

from database import (
    get_sent_news_count,
    get_category_count,
)


# ============================================================
# ADMIN DASHBOARD TEXT
# ============================================================

def build_dashboard():
    """
    Build the admin dashboard text.
    """

    try:
        total = get_sent_news_count()

    except Exception:
        total = 0

    try:
        football = get_category_count(
            "football"
        )

    except Exception:
        football = 0

    try:
        world = get_category_count(
            "war"
        )

    except Exception:
        world = 0

    try:
        politics = get_category_count(
            "politics"
        )

    except Exception:
        politics = 0

    try:
        cambodia = get_category_count(
            "cambodia"
        )

    except Exception:
        cambodia = 0

    text = (
        f"<b>{ADMIN_TITLE}</b>\n\n"

        "🟢 <b>BOT STATUS</b>\n"
        "Status: Running\n\n"

        "🤖 <b>AI SYSTEM</b>\n"
        "Gemini AI: Enabled\n"
        "Primary: Gemini 3.8 Flash\n"
        "Fallback: Gemini 3.5 Flash Lite\n\n"

        "💾 <b>DATABASE</b>\n"
        f"📰 Total Sent: {total}\n\n"

        "📊 <b>NEWS STATISTICS</b>\n"
        f"🇰🇭 Cambodia: {cambodia}\n"
        f"🌍 World: {world}\n"
        f"🏛️ Politics: {politics}\n"
        f"⚽ Football: {football}\n\n"

        "🔥 <b>AUTO SYSTEM</b>\n"
        "Breaking News: 🟢 ON\n"
        "Cambodia News: 🟢 ON\n"
        "Football Matches: 🟢 ON\n\n"

        "🕐 Cambodia Time: GMT+7"
    )

    return text


# ============================================================
# ADMIN ACCESS
# ============================================================

def check_admin(user_id):
    """
    Check whether Telegram user is an admin.
    """

    return is_admin(
        user_id
    )


# ============================================================
# ADMIN HELP
# ============================================================

def admin_help():
    """
    Admin command information.
    """

    return (
        "<b>👨‍💻 ADMIN COMMANDS</b>\n\n"

        "/admin - Dashboard\n"
        "/adminhelp - Admin Help\n\n"

        "📊 Dashboard shows:\n"
        "• Bot status\n"
        "• AI status\n"
        "• Database statistics\n"
        "• News statistics\n"
        "• Auto system status"
    )