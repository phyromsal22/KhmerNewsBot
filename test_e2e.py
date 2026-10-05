"""
Khmer News 24 - V2
V2.6.4 Controlled E2E Test

Purpose:
Test AI Filter -> Khmer Summary -> Quality Check
without publishing to Telegram and without changing production DB.
"""

import json

from ai.filter import filter_articles
from ai.summary import summarize_articles
from ai.quality import filter_quality_articles


TEST_ARTICLE = {
    "title": "G7 leaders announce emergency energy measures after major oil market disruption",
    "summary": (
        "G7 leaders have announced emergency measures to stabilize energy markets "
        "after a major disruption affected global oil and fuel supplies. "
        "Officials said the measures are intended to reduce market pressure "
        "and protect energy security."
    ),
    "link": "https://example.com/e2e-test-khmer-news-24",
    "source": "E2E TEST",
    "category": "world",
    "published": "2026-10-04T09:55:00+00:00",
}


def print_article(article, label):
    print("\n" + "=" * 60)
    print(label)
    print("=" * 60)

    print(
        json.dumps(
            article,
            indent=2,
            ensure_ascii=False
        )
    )


def main():

    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24")
    print("V2.6.4 CONTROLLED E2E TEST")
    print("=" * 60)

    articles = [TEST_ARTICLE.copy()]

    # ========================================================
    # 1. AI FILTER
    # ========================================================

    print("\n[1/3] 🤖 Testing AI Filter...")

    filtered = filter_articles(
        articles,
        min_score=60
    )

    if not filtered:
        print("❌ AI Filter rejected the test article.")
        print("❌ E2E TEST FAILED")
        return

    article = filtered[0]

    print("✅ AI Filter passed")

    print(
        f"🤖 AI Important: "
        f"{article.get('ai_important')}"
    )

    print(
        f"🤖 AI Score: "
        f"{article.get('ai_score')}"
    )

    print_article(
        article,
        "AI FILTER RESULT"
    )

    # ========================================================
    # 2. KHMER SUMMARY
    # ========================================================

    print("\n[2/3] 🇰🇭 Testing Khmer Summary...")

    summarized = summarize_articles(
        filtered
    )

    if not summarized:
        print("❌ Khmer Summary failed.")
        print("❌ E2E TEST FAILED")
        return

    article = summarized[0]

    print("✅ Khmer Summary passed")

    print(
        "\n📰 Khmer Title:"
    )

    print(
        article.get(
            "khmer_title",
            ""
        )
    )

    print(
        "\n📝 Khmer Summary:"
    )

    print(
        article.get(
            "khmer_summary",
            ""
        )
    )

    # ========================================================
    # 3. QUALITY CHECK
    # ========================================================

    print("\n[3/3] 🔍 Testing Quality Check...")

    quality_articles = filter_quality_articles(
        summarized,
        min_score=70
    )

    if not quality_articles:
        print("❌ Quality Check rejected the test article.")
        print("❌ E2E TEST FAILED")
        return

    article = quality_articles[0]

    print("✅ Quality Check passed")

    print(
        f"🔍 Quality Valid: "
        f"{article.get('quality_valid')}"
    )

    print(
        f"🔍 Quality Score: "
        f"{article.get('quality_score')}"
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print("\n" + "=" * 60)
    print("🎉 V2.6.4 E2E TEST PASSED")
    print("=" * 60)

    print(
        f"🤖 AI Score      : "
        f"{article.get('ai_score')}"
    )

    print(
        f"🔍 Quality Score : "
        f"{article.get('quality_score')}"
    )

    print(
        f"🇰🇭 Khmer Title  : "
        f"{article.get('khmer_title', '')}"
    )

    print(
        "\n✅ AI Filter"
    )

    print(
        "✅ Khmer Summary"
    )

    print(
        "✅ Quality Check"
    )

    print(
        "\nℹ️ Telegram publishing was intentionally skipped."
    )

    print(
        "ℹ️ Production database was intentionally not modified."
    )


if __name__ == "__main__":
    main()