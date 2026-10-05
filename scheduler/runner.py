"""
Khmer News 24 - V2
Automatic News Scheduler

Cambodia Time: GMT+7

Runs:
World
Football
Politics

Every 10 minutes.
"""

import time
from datetime import datetime, timezone, timedelta

import sys
import os

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )

from pipeline import run_pipeline


# ==========================================
# SETTINGS
# ==========================================

INTERVAL_MINUTES = 10

CAMBODIA_TZ = timezone(
    timedelta(hours=7)
)

CATEGORIES = [
    "world",
    "football",
    "politics",
]

ARTICLES_PER_CATEGORY = 3

CATEGORY_DELAY_SECONDS = 5


# ==========================================
# CAMBODIA TIME
# ==========================================

def now_kh():

    return datetime.now(
        timezone.utc
    ).astimezone(
        CAMBODIA_TZ
    )


# ==========================================
# RUN ONE CATEGORY
# ==========================================

def run_category(category):

    current_time = now_kh()

    print("\n" + "=" * 60)

    print(
        f"⏰ Category: {category}"
    )

    print(
        "🇰🇭 Cambodia Time: "
        f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print("=" * 60)

    try:

        result = run_pipeline(
            category=category,
            limit=ARTICLES_PER_CATEGORY
        )

        if result:

            print(
                f"✅ {category}: "
                f"{len(result)} article(s) processed"
            )

        else:

            print(
                f"ℹ️ {category}: "
                "No new articles"
            )

        return True

    except Exception as e:

        print(
            f"❌ {category} error: {e}"
        )

        print(
            "➡️ Scheduler will continue "
            "with the next category."
        )

        return False


# ==========================================
# RUN ALL CATEGORIES
# ==========================================

def run_all_categories():

    current_time = now_kh()

    print("\n" + "#" * 60)

    print(
        "🇰🇭 KHMER NEWS 24 — V2 SCHEDULER"
    )

    print(
        "🇰🇭 Cambodia Time: "
        f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        f"⏰ Interval: "
        f"{INTERVAL_MINUTES} minutes"
    )

    print("#" * 60)

    success_count = 0
    error_count = 0

    for category in CATEGORIES:

        success = run_category(
            category
        )

        if success:

            success_count += 1

        else:

            error_count += 1

        time.sleep(
            CATEGORY_DELAY_SECONDS
        )

    print("\n" + "-" * 60)

    print(
        f"📊 Categories completed: "
        f"{success_count}/{len(CATEGORIES)}"
    )

    print(
        f"❌ Categories with errors: "
        f"{error_count}"
    )

    print("-" * 60)


# ==========================================
# MAIN LOOP
# ==========================================

def main():

    print("=" * 60)

    print(
        "🇰🇭 KHMER NEWS 24"
    )

    print(
        "V2 AUTOMATIC NEWS SCHEDULER"
    )

    print("=" * 60)

    print(
        "🇰🇭 Timezone: Cambodia GMT+7"
    )

    print(
        f"⏰ Scan every "
        f"{INTERVAL_MINUTES} minutes"
    )

    print(
        "📰 Categories: "
        + ", ".join(CATEGORIES)
    )

    print(
        "🛑 Press CTRL+C to stop."
    )

    print("=" * 60)

    while True:

        try:

            run_all_categories()

            next_run = now_kh()

            print(
                "\n😴 Scheduler sleeping..."
            )

            print(
                f"🕐 Current Cambodia Time: "
                f"{next_run.strftime('%H:%M:%S')}"
            )

            print(
                f"⏳ Next scan in "
                f"{INTERVAL_MINUTES} minutes"
            )

            time.sleep(
                INTERVAL_MINUTES * 60
            )

        except KeyboardInterrupt:

            print(
                "\n🛑 Scheduler stopped by user."
            )

            break

        except Exception as e:

            print(
                f"\n❌ Scheduler main error: {e}"
            )

            print(
                "⏳ Restarting after 30 seconds..."
            )

            time.sleep(30)


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    main()