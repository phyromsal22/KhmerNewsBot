"""
🇰🇭 Khmer News 24
News Sources V2

Reliable RSS sources
"""

NEWS_SOURCES = {

    # ========================================================
    # 🌍 WORLD
    # ========================================================

    "world": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
    ],

    # ========================================================
    # ⚽ FOOTBALL
    # ========================================================

    "football": [
        "https://feeds.bbci.co.uk/sport/football/rss.xml",
    ],

    # ========================================================
    # 🏛️ POLITICS
    # ========================================================

    "politics": [
        "https://feeds.bbci.co.uk/news/politics/rss.xml",
    ],

    # ========================================================
    # ⚔️ WAR / CONFLICT
    # ========================================================

    "war": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
    ],

    # ========================================================
    # 🇰🇭 CAMBODIA
    # ========================================================

    "cambodia": [
        # Add Cambodia RSS sources here
        # after verifying their RSS availability.
    ],
}


# ============================================================
# GET SOURCES
# ============================================================

def get_sources(category=None):

    if category:

        return NEWS_SOURCES.get(
            category,
            []
        )

    all_sources = []

    for sources in NEWS_SOURCES.values():

        all_sources.extend(
            sources
        )

    # Remove duplicates
    return list(
        dict.fromkeys(
            all_sources
        )
    )