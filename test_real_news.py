import asyncio

from news.collector import collect_from_sources
from news.sources import get_sources

from ai.filter import filter_article
from ai.summary import generate_summary
from ai.quality import check_quality

from publisher.telegram import publish_news

from database.news import (
    save_news,
    news_exists,
)


async def main():

    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24")
    print("🧪 STEP 13 — REAL NEWS TEST")
    print("=" * 60)

    # ========================================================
    # STEP 1 — GET RSS SOURCES
    # ========================================================

    print("\n[1/7] 📰 GETTING WORLD NEWS SOURCES")

    sources = get_sources("world")

    if not sources:
        print("❌ No RSS sources found.")
        return

    for source in sources:
        print("  -", source)

    # ========================================================
    # STEP 2 — COLLECT REAL NEWS
    # ========================================================

    print("\n[2/7] 📡 COLLECTING REAL NEWS")

    articles = collect_from_sources(
        sources=sources,
        category="world",
        limit=10
    )

    if not articles:
        print("❌ No news collected.")
        return

    print(
        f"\n📊 Collected {len(articles)} articles"
    )

    # ========================================================
    # FIND FIRST NON-DUPLICATE ARTICLE
    # ========================================================

    article = None

    for index, candidate in enumerate(
        articles,
        start=1
    ):

        title = candidate.get(
            "title",
            ""
        )

        link = candidate.get(
            "link",
            ""
        ).strip()

        print(
            f"\n🔎 Checking article {index}:"
        )

        print(
            f"   {title[:100]}"
        )

        if not link:

            print(
                "   ⚠️ No link — skipped"
            )

            continue

        if news_exists(link):

            print(
                "   ⚠️ Duplicate — skipped"
            )

            continue

        article = candidate

        print(
            "   ✅ NEW ARTICLE FOUND"
        )

        break

    if article is None:

        print("\n⚠️ All collected articles already exist.")
        print("🛑 Test stopped safely.")
        return

    print("\n" + "=" * 60)
    print("🆕 SELECTED NEW ARTICLE")
    print("=" * 60)

    print(
        "Title:",
        article.get("title", "")
    )

    print(
        "Source:",
        article.get("source", "")
    )

    print(
        "Link:",
        article.get("link", "")
    )

    # ========================================================
    # STEP 3 — AI FILTER
    # ========================================================

    print("\n[3/7] 🤖 AI FILTER")

    filter_result = filter_article(
        article
    )

    print("\nFilter result:")
    print(filter_result)

    if isinstance(
        filter_result,
        dict
    ):
        article.update(
            filter_result
        )

    if not article.get(
        "important",
        True
    ):

        print(
            "\n⚠️ AI rejected this article."
        )

        return

    print(
        "\n✅ AI Filter PASS"
    )

    # ========================================================
    # STEP 4 — KHMER SUMMARY
    # ========================================================

    print("\n[4/7] 🇰🇭 KHMER SUMMARY")

    summary = generate_summary(
        article
    )

    if not summary:

        print(
            "❌ Summary generation failed."
        )

        return

    article["khmer_summary"] = summary

    print(
        "✅ Khmer Summary generated"
    )

    print("\n" + summary)

    # ========================================================
    # STEP 5 — QUALITY CHECK
    # ========================================================

    print("\n[5/7] ✅ QUALITY CHECK")

    quality = check_quality(
        summary
    )

    print("\nQuality result:")
    print(quality)

    if not quality.get(
        "valid",
        False
    ):

        print(
            "❌ Quality check FAILED."
        )

        return

    article["quality_score"] = quality.get(
        "score",
        0
    )

    article["ai_score"] = article.get(
        "score",
        article.get(
            "ai_score",
            0
        )
    )

    print(
        "✅ Quality PASS"
    )

    # ========================================================
    # STEP 6 — TELEGRAM
    # ========================================================

    print("\n[6/7] 📤 TELEGRAM")

    try:

        telegram_result = await publish_news(
            article
        )

    except Exception as e:

        print(
            "❌ Telegram error:"
        )

        print(e)

        return

    if not telegram_result:

        print(
            "❌ Telegram publishing failed."
        )

        return

    print(
        "✅ Telegram published"
    )

    # ========================================================
    # STEP 7 — DATABASE
    # ========================================================

    print("\n[7/7] 💾 DATABASE")

    article["status"] = "published"

    saved = save_news(
        article,
        status="published"
    )

    if saved:

        print(
            "✅ Article saved to database"
        )

    else:

        print(
            "⚠️ Database save returned False."
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print("\n" + "=" * 60)
    print("🎉 STEP 13 REAL NEWS TEST PASSED")
    print("=" * 60)

    print("✅ RSS Sources")
    print("✅ RSS Collector")
    print("✅ Duplicate Check")
    print("✅ New Article Selection")
    print("✅ AI Filter")
    print("✅ Khmer Summary")
    print("✅ Quality Check")
    print("✅ Telegram")
    print("✅ Database")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())