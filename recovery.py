"""
Khmer News 24 - V2.7.6
Collected News Recovery System

Purpose:
- Recover news stuck in "collected"
- Retry AI processing
- Continue Khmer summary
- Continue quality check
- Publish successfully processed news to Telegram
- Update database status correctly
- Do NOT process already published news
- Limit AI usage per run
"""

import asyncio


# ============================================================
# PROJECT MODULES
# ============================================================

from database.news import (
    init_news_table,
    get_news_by_status,
    update_news_status,
    update_ai_score,
    update_quality_score,
)

from ai.filter import filter_articles
from ai.summary import summarize_articles
from ai.quality import filter_quality_articles

from publisher.telegram import publish_news_batch


# ============================================================
# SETTINGS
# ============================================================

MAX_RECOVERY_ARTICLES = 2

AI_MIN_SCORE = 60

QUALITY_MIN_SCORE = 70

TELEGRAM_DELAY_SECONDS = 2


# ============================================================
# DATABASE HELPERS
# ============================================================

def set_status(article, status):
    """
    Update database status using article link.
    """

    link = (
        article.get("link", "")
        or ""
    ).strip()

    if not link:
        return False

    return update_news_status(
        link,
        status
    )


def set_ai_score(article, score):
    """
    Update AI score in database.
    """

    link = (
        article.get("link", "")
        or ""
    ).strip()

    if not link:
        return False

    return update_ai_score(
        link,
        score
    )


def set_quality_score(article, score):
    """
    Update quality score in database.
    """

    link = (
        article.get("link", "")
        or ""
    ).strip()

    if not link:
        return False

    return update_quality_score(
        link,
        score
    )


# ============================================================
# CHECK TEST ARTICLE
# ============================================================

def is_test_article(article):
    """
    Prevent accidental publishing of known test records.
    """

    title = (
        article.get("title", "")
        or ""
    ).lower()

    link = (
        article.get("link", "")
        or ""
    ).lower()

    test_keywords = [
        "test news khmer news 24",
        "test_news",
        "test-news",
        "example.com",
    ]

    for keyword in test_keywords:

        if keyword in title:
            return True

        if keyword in link:
            return True

    return False


# ============================================================
# LOAD RECOVERY ARTICLES
# ============================================================

def load_recovery_articles():
    """
    Load articles currently stuck in collected status.
    """

    articles = get_news_by_status(
        "collected",
        limit=50
    )

    if not articles:

        print(
            "ℹ️ No collected articles "
            "need recovery."
        )

        return []

    print(
        f"📦 Collected records found: "
        f"{len(articles)}"
    )

    valid_articles = []

    skipped_tests = 0

    for article in articles:

        if is_test_article(article):

            skipped_tests += 1

            print(
                f"🧪 Skipping test article: "
                f"{article.get('title', '')[:60]}"
            )

            continue

        valid_articles.append(
            article
        )

    print(
        f"🧹 Valid recovery articles: "
        f"{len(valid_articles)}"
    )

    print(
        f"🧪 Test articles skipped: "
        f"{skipped_tests}"
    )

    if len(valid_articles) > MAX_RECOVERY_ARTICLES:

        print(
            f"🛡️ Limiting recovery to "
            f"{MAX_RECOVERY_ARTICLES} articles."
        )

        valid_articles = (
            valid_articles[
                :MAX_RECOVERY_ARTICLES
            ]
        )

    return valid_articles


# ============================================================
# RECOVERY PIPELINE
# ============================================================

def run_recovery():

    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24")
    print("V2.7.6 COLLECTED NEWS RECOVERY")
    print("=" * 60)

    # ========================================================
    # DATABASE
    # ========================================================

    print(
        "\n🗄️ Initializing database..."
    )

    init_news_table()

    # ========================================================
    # LOAD ARTICLES
    # ========================================================

    print(
        "\n[1/6] Loading collected articles..."
    )

    articles = load_recovery_articles()

    if not articles:

        print(
            "\n✅ Nothing to recover."
        )

        return []

    print(
        f"🔄 Recovery articles: "
        f"{len(articles)}"
    )

    for article in articles:

        print(
            f"   • {article.get('title', '')[:80]}"
        )

    # ========================================================
    # BUILD ARTICLE DATA
    # ========================================================

    print(
        "\n[2/6] Preparing articles..."
    )

    prepared_articles = []

    for article in articles:

        # Convert SQLite record to a normal
        # article structure expected by AI modules.

        item = dict(article)

        # Database uses published_at.
        # AI modules expect published.
        item["published"] = (
            item.get("published_at", "")
            or ""
        )

        # Database has no image_url column.
        # Recovery therefore does not invent one.
        # Image will be available only if another
        # source provides it later.

        prepared_articles.append(
            item
        )

    articles = prepared_articles

    print(
        f"✅ Prepared: {len(articles)}"
    )

    # ========================================================
    # AI FILTER
    # ========================================================

    print(
        "\n[3/6] Running Gemini AI Filter..."
    )

    filtered_articles = filter_articles(
        articles,
        min_score=AI_MIN_SCORE
    )

    print(
        f"🤖 Important news: "
        f"{len(filtered_articles)}"
    )

    if not filtered_articles:

        print(
            "ℹ️ No collected articles passed "
            "the AI filter."
        )

        return []

    # ========================================================
    # SAVE AI STATUS
    # ========================================================

    for article in filtered_articles:

        score = article.get(
            "ai_score",
            0
        )

        set_ai_score(
            article,
            score
        )

        set_status(
            article,
            "filtered"
        )

    articles = filtered_articles

    # ========================================================
    # KHMER SUMMARY
    # ========================================================

    print(
        "\n[4/6] Generating Khmer summaries..."
    )

    summarized_articles = summarize_articles(
        articles
    )

    print(
        f"📝 Summaries: "
        f"{len(summarized_articles)}"
    )

    if not summarized_articles:

        print(
            "❌ No summaries generated."
        )

        return []

    for article in summarized_articles:

        set_status(
            article,
            "summarized"
        )

    articles = summarized_articles

    # ========================================================
    # QUALITY CHECK
    # ========================================================

    print(
        "\n[5/6] Checking quality..."
    )

    quality_articles = filter_quality_articles(
        articles,
        min_score=QUALITY_MIN_SCORE
    )

    print(
        f"✅ Quality passed: "
        f"{len(quality_articles)}"
    )

    if not quality_articles:

        print(
            "❌ No articles passed quality."
        )

        return []

    for article in quality_articles:

        score = article.get(
            "quality_score",
            0
        )

        set_quality_score(
            article,
            score
        )

        set_status(
            article,
            "quality_passed"
        )

    articles = quality_articles

    # ========================================================
    # TELEGRAM
    # ========================================================

    print(
        "\n[6/6] Publishing to Telegram..."
    )

    try:

        result = asyncio.run(
            publish_news_batch(
                articles,
                delay_seconds=TELEGRAM_DELAY_SECONDS
            )
        )

        published_count = result.get(
            "published_count",
            0
        )

        published_articles = result.get(
            "published_articles",
            []
        )

    except Exception as error:

        print(
            f"❌ Telegram error: {error}"
        )

        published_count = 0

        published_articles = []

    print(
        f"📤 Published: "
        f"{published_count}/{len(articles)}"
    )

    # ========================================================
    # UPDATE PUBLISHED STATUS
    # ========================================================

    updated_count = 0

    for article in published_articles:

        if set_status(
            article,
            "published"
        ):

            updated_count += 1

    print(
        f"💾 Published status updated: "
        f"{updated_count}"
    )

    # ========================================================
    # COMPLETE
    # ========================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "✅ RECOVERY COMPLETE"
    )

    print(
        "=" * 60
    )

    return articles


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    run_recovery()