"""
Khmer News 24 - V2
Pipeline Test

RSS
→ Clean
→ Duplicate
→ AI Filter
→ Khmer Summary
→ Quality Check

NO TELEGRAM PUBLISH
"""

from news.sources import get_sources
from news.collector import collect_from_sources
from news.cleaner import clean_articles
from news.duplicate import remove_duplicates

from ai.filter import filter_articles
from ai.summary import summarize_articles
from ai.quality import filter_quality_articles


def test_pipeline(category="world", limit=3):

    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24 — PIPELINE TEST")
    print("=" * 60)

    # --------------------------------
    # 1. RSS SOURCES
    # --------------------------------

    print("\n[1] Loading RSS sources...")

    sources = get_sources(category)

    print(f"Category: {category}")
    print(f"Sources: {len(sources)}")

    if not sources:
        print("❌ No RSS sources found")
        return

    # --------------------------------
    # 2. COLLECT
    # --------------------------------

    print("\n[2] Collecting news...")

    articles = collect_from_sources(
        sources,
        category=category,
        limit=limit
    )

    print(f"📥 Collected: {len(articles)}")

    if not articles:
        print("❌ No articles collected")
        return

    # --------------------------------
    # 3. CLEAN
    # --------------------------------

    print("\n[3] Cleaning news...")

    articles = clean_articles(articles)

    print(f"🧹 Cleaned: {len(articles)}")

    # --------------------------------
    # 4. DUPLICATE
    # --------------------------------

    print("\n[4] Removing duplicates...")

    articles = remove_duplicates(articles)

    print(f"🧹 Unique: {len(articles)}")

    # --------------------------------
    # 5. AI FILTER
    # --------------------------------

    print("\n[5] Gemini AI Filter...")

    articles = filter_articles(
        articles,
        min_score=60
    )

    print(f"🤖 Important news: {len(articles)}")

    if not articles:
        print("ℹ️ No important news selected")
        return

    # --------------------------------
    # 6. KHMER SUMMARY
    # --------------------------------

    print("\n[6] Gemini Khmer Summary...")

    articles = summarize_articles(articles)

    print(f"🇰🇭 Khmer summaries: {len(articles)}")

    if not articles:
        print("❌ No summaries generated")
        return

    # --------------------------------
    # 7. QUALITY CHECK
    # --------------------------------

    print("\n[7] Quality Check...")

    articles = filter_quality_articles(
        articles,
        min_score=70
    )

    print(f"✅ Quality passed: {len(articles)}")

    # --------------------------------
    # RESULTS
    # --------------------------------

    print("\n")
    print("=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)

    if not articles:
        print("❌ No article passed the pipeline")
        return

    for index, article in enumerate(articles, start=1):

        print("\n" + "-" * 60)

        print(f"📰 ARTICLE {index}")

        print("\nTitle:")
        print(article.get("title", ""))

        print("\nKhmer Summary:")
        print(article.get("khmer_summary", ""))

        print("\nAI Score:")
        print(article.get("ai_score", 0))

        print("\nQuality Score:")
        print(article.get("quality_score", 0))

        print("\nSource:")
        print(article.get("source", ""))

        print("\nLink:")
        print(article.get("link", ""))

    print("\n" + "=" * 60)
    print("✅ PIPELINE TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_pipeline(
        category="world",
        limit=3
    )