import asyncio

from ai.filter import filter_article
from ai.summary import generate_summary
from ai.quality import check_quality
from publisher.telegram import publish_news


# ============================================================
# TEST ARTICLE
# ============================================================

TEST_ARTICLE = {
    "title": "G7 leaders announce emergency energy measures",
    "link": "https://example.com/khmer-news-24-test",
    "source": "BBC News",
    "category": "world",
    "summary": (
        "G7 leaders announced emergency energy measures after major "
        "disruptions affected global oil markets and energy supplies."
    ),
    "published": "2026-10-04T12:00:00Z",
    "collected_at": "2026-10-04T12:05:00Z",
    "image_url": "",
}


# ============================================================
# MAIN TEST
# ============================================================

async def main():

    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24")
    print("🧪 FULL PIPELINE TEST — 1 ARTICLE")
    print("=" * 60)

    article = TEST_ARTICLE.copy()

    # ========================================================
    # STEP 1 — AI FILTER
    # ========================================================

    print("\n[1/4] 🤖 AI FILTER")

    # filter_article() is synchronous
    filter_result = filter_article(article)

    print("\nFilter result:")
    print(filter_result)

    if isinstance(filter_result, dict):
        article.update(filter_result)

    if not article.get("important", True):

        print(
            "\n⚠️ Article rejected by AI Filter."
        )

        return

    print("\n✅ AI Filter PASS")

    # ========================================================
    # STEP 2 — KHMER SUMMARY
    # ========================================================

    print("\n[2/4] 🇰🇭 KHMER SUMMARY")

    # generate_summary() is synchronous
    summary = generate_summary(article)

    if not summary:

        print(
            "❌ Summary generation failed."
        )

        return

    article["khmer_summary"] = summary

    print(
        "✅ Summary generated"
    )

    print("\n" + summary)

    # ========================================================
    # STEP 3 — QUALITY CHECK
    # ========================================================

    print("\n[3/4] ✅ QUALITY CHECK")

    quality = check_quality(summary)

    print("\nQuality result:")
    print(quality)

    if not quality.get("valid"):

        print(
            "❌ Quality check FAILED"
        )

        return

    article["quality_score"] = quality.get(
        "score",
        0
    )

    print(
        "✅ Quality PASS"
    )

    # ========================================================
    # STEP 4 — TELEGRAM
    # ========================================================

    print("\n[4/4] 📤 TELEGRAM")

    article["ai_score"] = article.get(
        "score",
        article.get(
            "ai_score",
            0
        )
    )

    try:

        result = await publish_news(
            article
        )

    except Exception as e:

        print(
            "\n❌ Telegram publishing error:"
        )

        print(e)

        return

    if result:

        print("\n" + "=" * 60)
        print("🎉 FULL PIPELINE TEST PASSED")
        print("=" * 60)

        print("✅ AI Filter")
        print("✅ Khmer Summary")
        print("✅ Quality Check")
        print("✅ Telegram Publisher")

        print("=" * 60)

    else:

        print("\n❌ Telegram publishing failed.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())