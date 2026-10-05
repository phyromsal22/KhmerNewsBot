"""
🇰🇭 Khmer News 24 - V2
News Pipeline + Database

FLOW:

RSS
↓
Clean
↓
Duplicate
↓
Freshness Filter
↓
Database Check
↓
AI Quota Protection
↓
Collected
↓
AI Filter
↓
Filtered
↓
Khmer Summary
↓
Summarized
↓
Quality Check
↓
Quality Passed
↓
Telegram
↓
Published
↓
Database Update
"""

import asyncio
from datetime import datetime, timezone, timedelta

from news.sources import get_sources
from news.collector import collect_from_sources
from news.cleaner import clean_articles
from news.duplicate import remove_duplicates

from ai.filter import filter_articles
from ai.summary import summarize_articles
from ai.quality import filter_quality_articles

from database.news import (
    init_news_table,
    news_exists,
    save_news,
    update_news_status,
    update_ai_score,
    update_quality_score,
    update_image_url,
    get_connection,
)

from publisher.telegram import publish_news_batch


# ============================================================
# SETTINGS
# ============================================================

MAX_AI_ARTICLES = 3

AI_MIN_SCORE = 60

QUALITY_MIN_SCORE = 70

TELEGRAM_DELAY_SECONDS = 2

FRESHNESS_HOURS = 6


# ============================================================
# FRESHNESS FUNCTIONS
# ============================================================

def parse_published_time(value):
    """
    Convert published time into UTC datetime.
    """

    if not value:
        return None

    if isinstance(value, datetime):

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )

    value = str(value).strip()

    if not value:
        return None

    try:

        normalized = value.replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(
            normalized
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception:
        return None


def is_fresh_article(
    article,
    max_age_hours=FRESHNESS_HOURS
):
    """
    Check whether article is fresh enough.
    """

    published = article.get(
        "published",
        ""
    )

    published_dt = parse_published_time(
        published
    )

    if published_dt is None:

        print(
            "⚠️ Published time unavailable. "
            "Allowing article."
        )

        return True

    now = datetime.now(
        timezone.utc
    )

    age = now - published_dt

    if age.total_seconds() < 0:

        print(
            "ℹ️ Article has future timestamp. "
            "Allowing article."
        )

        return True

    max_age = timedelta(
        hours=max_age_hours
    )

    if age <= max_age:

        minutes = int(
            age.total_seconds() / 60
        )

        print(
            f"🟢 Fresh: "
            f"{minutes} minute(s) old"
        )

        return True

    hours = age.total_seconds() / 3600

    print(
        f"⏭️ Old article: "
        f"{hours:.1f} hour(s) old"
    )

    return False


def filter_fresh_articles(
    articles,
    max_age_hours=FRESHNESS_HOURS
):
    """
    Keep only fresh articles.
    """

    fresh_articles = []

    old_count = 0

    for article in articles:

        if is_fresh_article(
            article,
            max_age_hours
        ):

            fresh_articles.append(
                article
            )

        else:

            old_count += 1

    print(
        f"🕐 Fresh articles: "
        f"{len(fresh_articles)}"
    )

    print(
        f"⏭️ Old articles skipped: "
        f"{old_count}"
    )

    return fresh_articles


# ============================================================
# DATABASE ID RESOLUTION
# ============================================================

def get_news_id(article):
    """
    Resolve database numeric ID safely.

    Priority:
    1. Existing article["id"]
    2. Search database using article link
    """

    article_id = article.get("id")

    if article_id:

        try:
            return int(article_id)

        except (TypeError, ValueError):
            pass

    link = str(
        article.get("link", "")
    ).strip()

    if not link:
        return None

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM news
            WHERE link = ?
            LIMIT 1
            """,
            (link,)
        )

        row = cursor.fetchone()

        if row:

            article_id = int(
                row["id"]
            )

            article["id"] = article_id

            return article_id

        return None

    except Exception as error:

        print(
            f"❌ Could not resolve database ID: {error}"
        )

        return None

    finally:

        connection.close()


# ============================================================
# UPDATE STATUS SAFELY
# ============================================================

def set_status(article, status):
    """
    Update article status using numeric database ID.
    """

    article_id = get_news_id(
        article
    )

    if not article_id:

        print(
            f"⚠️ Cannot update status '{status}': "
            f"database ID not found for "
            f"{article.get('title', '')[:60]}"
        )

        return False

    return update_news_status(
        article_id,
        status
    )


def set_ai_score(article, score):
    """
    Update AI score using numeric database ID.
    """

    article_id = get_news_id(
        article
    )

    if not article_id:

        print(
            "⚠️ Cannot update AI score: "
            "database ID not found."
        )

        return False

    return update_ai_score(
        article_id,
        score
    )


def set_quality_score(article, score):
    """
    Update quality score using numeric database ID.
    """

    article_id = get_news_id(
        article
    )

    if not article_id:

        print(
            "⚠️ Cannot update quality score: "
            "database ID not found."
        )

        return False

    return update_quality_score(
        article_id,
        score
    )


# ============================================================
# IMAGE DATABASE UPDATE
# ============================================================

def set_image_url(article):
    """
    Save/update image URL in database.

    This works for both:
    - New articles
    - Existing articles
    """

    article_id = get_news_id(
        article
    )

    if not article_id:

        print(
            "⚠️ Cannot update image: "
            "database ID not found."
        )

        return False

    image_url = str(
        article.get("image_url", "")
    ).strip()

    if not image_url:

        print(
            f"⚠️ No image URL: "
            f"{article.get('title', '')[:60]}"
        )

        return False

    success = update_image_url(
        article_id,
        image_url
    )

    if success:

        print(
            f"🖼️ Image saved/updated: "
            f"{image_url[:100]}"
        )

    else:

        print(
            "⚠️ Failed to update image URL."
        )

    return success


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline(
    category="world",
    limit=5
):

    print("=" * 60)

    print(
        "🇰🇭 KHMER NEWS 24 — V2 NEWS PIPELINE"
    )

    print("=" * 60)

    # ========================================================
    # DATABASE
    # ========================================================

    print(
        "\n🗄️ Initializing database..."
    )

    init_news_table()

    # ========================================================
    # 1. SOURCES
    # ========================================================

    print(
        "\n[1/10] Loading RSS sources..."
    )

    sources = get_sources(
        category
    )

    print(
        f"Category: {category}"
    )

    print(
        f"Sources: {len(sources)}"
    )

    if not sources:

        print(
            "❌ No RSS sources configured"
        )

        return []

    # ========================================================
    # 2. COLLECT
    # ========================================================

    print(
        "\n[2/10] Collecting news..."
    )

    articles = collect_from_sources(
        sources,
        category=category,
        limit=limit
    )

    print(
        f"📥 Collected: {len(articles)}"
    )

    if not articles:

        print(
            "❌ No articles collected"
        )

        return []

    # ========================================================
    # 3. CLEAN
    # ========================================================

    print(
        "\n[3/10] Cleaning news..."
    )

    articles = clean_articles(
        articles
    )

    print(
        f"🧹 Cleaned: {len(articles)}"
    )

    if not articles:

        print(
            "❌ No clean articles"
        )

        return []

    # ========================================================
    # 4. DUPLICATE
    # ========================================================

    print(
        "\n[4/10] Removing duplicates..."
    )

    articles = remove_duplicates(
        articles
    )

    print(
        f"🧹 Unique: {len(articles)}"
    )

    if not articles:

        print(
            "❌ No unique articles"
        )

        return []

    # ========================================================
    # 5. FRESHNESS
    # ========================================================

    print(
        "\n[5/10] Checking news freshness..."
    )

    print(
        f"🕐 Freshness window: "
        f"{FRESHNESS_HOURS} hour(s)"
    )

    articles = filter_fresh_articles(
        articles,
        max_age_hours=FRESHNESS_HOURS
    )

    if not articles:

        print(
            "\nℹ️ No fresh news to process."
        )

        return []

    # ========================================================
    # 6. DATABASE CHECK
    # ========================================================

    print(
        "\n[6/10] Checking database..."
    )

    new_articles = []

    skipped = 0

    for article in articles:

        link = article.get(
            "link",
            ""
        ).strip()

        if not link:
            continue

        if news_exists(link):

            skipped += 1

            print(
                f"⏭️ Already exists: "
                f"{article.get('title', '')[:60]}"
            )

            # ------------------------------------------------
            # IMPORTANT:
            # Existing article may have a new image.
            # Update image even when article already exists.
            # ------------------------------------------------

            get_news_id(
                article
            )

            set_image_url(
                article
            )

            continue

        new_articles.append(
            article
        )

    print(
        f"🆕 New articles: "
        f"{len(new_articles)}"
    )

    print(
        f"⏭️ Skipped existing: "
        f"{skipped}"
    )

    if not new_articles:

        print(
            "\nℹ️ No new news to process."
        )

        return []

    articles = new_articles

    # ========================================================
    # AI QUOTA PROTECTION
    # ========================================================

    print(
        "\n🛡️ AI QUOTA PROTECTION"
    )

    print(
        f"📰 New articles available: "
        f"{len(articles)}"
    )

    print(
        f"🤖 Maximum AI articles per cycle: "
        f"{MAX_AI_ARTICLES}"
    )

    if len(articles) > MAX_AI_ARTICLES:

        print(
            f"⚠️ {len(articles)} new articles found."
        )

        print(
            f"🛡️ Limiting AI processing to "
            f"{MAX_AI_ARTICLES} articles."
        )

        articles = articles[
            :MAX_AI_ARTICLES
        ]

    print(
        f"🤖 AI processing: "
        f"{len(articles)} article(s)"
    )

    # ========================================================
    # SAVE COLLECTED
    # ========================================================

    print(
        "\n💾 Saving collected news..."
    )

    saved_count = 0

    image_updated_count = 0

    for article in articles:

        # ----------------------------------------------------
        # Save new article
        # ----------------------------------------------------

        saved = save_news(
            article,
            status="collected"
        )

        # ----------------------------------------------------
        # Always resolve database ID
        # ----------------------------------------------------

        article_id = get_news_id(
            article
        )

        if article_id:

            article["id"] = article_id

        # ----------------------------------------------------
        # Always save/update image
        # ----------------------------------------------------

        image_url = str(
            article.get("image_url", "")
        ).strip()

        if article_id and image_url:

            if update_image_url(
                article_id,
                image_url
            ):

                image_updated_count += 1

                print(
                    f"🖼️ Image saved/updated: "
                    f"{image_url[:100]}"
                )

            else:

                print(
                    "⚠️ Failed to save image URL."
                )

        else:

            if not image_url:

                print(
                    f"⚠️ No image URL: "
                    f"{article.get('title', '')[:60]}"
                )

        if saved:

            saved_count += 1

    print(
        f"💾 New articles saved: "
        f"{saved_count}/{len(articles)}"
    )

    print(
        f"🖼️ Images saved/updated: "
        f"{image_updated_count}"
    )

    # ========================================================
    # 7. AI FILTER
    # ========================================================

    print(
        "\n[7/10] Gemini AI Filter..."
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
            "ℹ️ No important news selected."
        )

        return []

    # ========================================================
    # SAVE AI SCORES + FILTERED STATUS
    # ========================================================

    print(
        "\n💾 Updating AI filter status..."
    )

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
    # 8. KHMER SUMMARY
    # ========================================================

    print(
        "\n[8/10] Generating Khmer summaries..."
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

    # ========================================================
    # SAVE SUMMARIZED STATUS
    # ========================================================

    print(
        "\n💾 Updating summary status..."
    )

    for article in summarized_articles:

        set_status(
            article,
            "summarized"
        )

    articles = summarized_articles

    # ========================================================
    # 9. QUALITY CHECK
    # ========================================================

    print(
        "\n[9/10] Checking quality..."
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
            "❌ No articles passed quality check."
        )

        return []

    # ========================================================
    # SAVE QUALITY STATUS
    # ========================================================

    print(
        "\n💾 Updating quality status..."
    )

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
    # 10. TELEGRAM
    # ========================================================

    print(
        "\n[10/10] Publishing to Telegram..."
    )

    try:

        publish_result = asyncio.run(
            publish_news_batch(
                articles,
                delay_seconds=TELEGRAM_DELAY_SECONDS
            )
        )

        # V2.7.5 publisher returns detailed results.

        published_count = publish_result.get(
            "published_count",
            0
        )

        published_articles = publish_result.get(
            "published_articles",
            []
        )

    except Exception as error:

        print(
            f"❌ Telegram publishing error: "
            f"{error}"
        )

        published_count = 0

        published_articles = []

    print(
        f"📤 Published: "
        f"{published_count}/{len(articles)}"
    )

    # ========================================================
    # PUBLISHED STATUS
    # ========================================================

    if published_count > 0:

        updated_count = 0

        # Only mark articles that Telegram
        # actually published.

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

    else:

        print(
            "⚠️ No articles were published."
        )

        print(
            "ℹ️ Database status remains "
            "quality_passed."
        )

    # ========================================================
    # COMPLETE
    # ========================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "✅ PIPELINE COMPLETE"
    )

    print(
        "=" * 60
    )

    return articles


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    run_pipeline(
        category="world",
        limit=10
    )