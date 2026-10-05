# =========================================================
# KHMER NEWS 24
# STEP 17 — FOOTBALL DATABASE TEST
# =========================================================

from football.matches import get_matches_for_day
from database.news import init_news_table, save_news, get_news_count


def main():
    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24")
    print("⚽ STEP 17 — FOOTBALL DATABASE TEST")
    print("=" * 60)

    # -----------------------------------------------------
    # 1. Initialize database
    # -----------------------------------------------------

    print("\n[1/4] Initializing database...")

    init_news_table()

    print("✅ Database initialized")

    # -----------------------------------------------------
    # 2. Get today's football
    # -----------------------------------------------------

    print("\n[2/4] Loading today's football...")

    data = get_matches_for_day(0)

    international = data.get("international", [])
    club = data.get("club", [])
    secondary = data.get("secondary", [])

    print(f"🌍 International: {len(international)}")
    print(f"🏆 Club: {len(club)}")
    print(f"👶 Youth/U23: {len(secondary)}")

    all_matches = international + club + secondary

    if not all_matches:
        print("❌ No football matches found.")
        return

    # -----------------------------------------------------
    # 3. Save first match
    # -----------------------------------------------------

    print("\n[3/4] Saving first football match...")

    match = all_matches[0]

    article = {
        "title": f"{match['home']} vs {match['away']}",
        "link": f"football://fixture/{match['id']}",
        "source": "API-Football",
        "category": "football",
        "published": data["date"],
        "collected_at": data["date"],
        "ai_score": 0,
        "quality_score": 0,
        "image_url": "",
    }

    saved = save_news(
        article,
        status="collected"
    )

    print(f"💾 Save result: {saved}")

    if saved:
        print("✅ Football match saved to database")
    else:
        print("⚠️ Match may already exist in database")

    # -----------------------------------------------------
    # 4. Database count
    # -----------------------------------------------------

    print("\n[4/4] Checking database...")

    total = get_news_count()

    print(f"📊 Total news records: {total}")

    print("\n" + "=" * 60)
    print("🎉 STEP 17 TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()