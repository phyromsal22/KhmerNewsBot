"""
Khmer News 24 - V2
News Collector

Collects news articles from RSS feeds
and extracts available images.
"""

import os
import sys
import feedparser

from datetime import datetime, timezone


# ============================================================
# PROJECT ROOT
# ============================================================

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


# ============================================================
# IMAGE SYSTEM
# ============================================================

from publisher.images import (
    extract_image_from_entry
)


# ============================================================
# COLLECT FROM ONE RSS
# ============================================================

def collect_from_rss(
    url,
    category="unknown",
    limit=20
):
    """
    Collect news articles from one RSS feed.
    """

    articles = []

    try:

        print(
            f"📰 Collecting: {url}"
        )

        feed = feedparser.parse(
            url
        )

        # ----------------------------------------------------
        # CHECK FEED
        # ----------------------------------------------------

        if getattr(
            feed,
            "bozo",
            False
        ):

            print(
                "⚠️ RSS feed returned a parsing warning."
            )

        entries = getattr(
            feed,
            "entries",
            []
        )

        print(
            f"   📥 RSS entries: "
            f"{len(entries)}"
        )

        # ----------------------------------------------------
        # PROCESS ARTICLES
        # ----------------------------------------------------

        for entry in entries[:limit]:

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            title = entry.get(
                "title",
                ""
            ).strip()

            # ------------------------------------------------
            # LINK
            # ------------------------------------------------

            link = entry.get(
                "link",
                ""
            ).strip()

            # ------------------------------------------------
            # SUMMARY
            # ------------------------------------------------

            summary = entry.get(
                "summary",
                ""
            ).strip()

            # ------------------------------------------------
            # REQUIRED FIELDS
            # ------------------------------------------------

            if not title or not link:

                continue

            # ------------------------------------------------
            # PUBLISHED TIME
            # ------------------------------------------------

            published = entry.get(
                "published",
                ""
            )

            published_parsed = entry.get(
                "published_parsed"
            )

            if published_parsed:

                try:

                    published_dt = datetime(
                        *published_parsed[:6],
                        tzinfo=timezone.utc
                    ).isoformat()

                except Exception:

                    published_dt = published

            else:

                published_dt = published

            # ------------------------------------------------
            # IMAGE
            # ------------------------------------------------

            image_url = ""

            try:

                image_url = (
                    extract_image_from_entry(
                        entry
                    )
                )

            except Exception as image_error:

                print(
                    f"⚠️ Image extraction error: "
                    f"{image_error}"
                )

                image_url = ""

            # ------------------------------------------------
            # SOURCE
            # ------------------------------------------------

            source = feed.feed.get(
                "title",
                "Unknown"
            )

            # ------------------------------------------------
            # COLLECTED TIME
            # ------------------------------------------------

            collected_at = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            # ------------------------------------------------
            # ARTICLE OBJECT
            # ------------------------------------------------

            article = {

                "title": title,

                "link": link,

                "summary": summary,

                "category": category,

                "source": source,

                "published": published_dt,

                "collected_at": collected_at,

                "image_url": image_url,
            }

            articles.append(
                article
            )

    except Exception as e:

        print(
            f"❌ RSS collection error: {e}"
        )

    return articles


# ============================================================
# COLLECT FROM MULTIPLE SOURCES
# ============================================================

def collect_from_sources(
    sources,
    category="unknown",
    limit=20
):
    """
    Collect news from multiple RSS sources.
    """

    all_articles = []

    for url in sources:

        articles = collect_from_rss(
            url=url,
            category=category,
            limit=limit
        )

        all_articles.extend(
            articles
        )

        print(
            f"   ✅ Collected: "
            f"{len(articles)}"
        )

    return all_articles


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24")
    print("V2.7.2 RSS + IMAGE TEST")
    print("=" * 60)

    test_url = (
        "https://feeds.bbci.co.uk/"
        "news/world/rss.xml"
    )

    articles = collect_from_rss(
        url=test_url,
        category="world",
        limit=5
    )

    print(
        "\n" + "=" * 60
    )

    print(
        f"📰 Articles collected: "
        f"{len(articles)}"
    )

    print(
        "=" * 60
    )

    for index, article in enumerate(
        articles,
        start=1
    ):

        print(
            "\n" + "-" * 60
        )

        print(
            f"#{index}"
        )

        print(
            f"📰 Title: "
            f"{article.get('title', '')[:100]}"
        )

        print(
            f"📌 Source: "
            f"{article.get('source', '')}"
        )

        print(
            f"📂 Category: "
            f"{article.get('category', '')}"
        )

        print(
            f"🔗 Link: "
            f"{article.get('link', '')}"
        )

        image_url = article.get(
            "image_url",
            ""
        )

        if image_url:

            print(
                "🖼️ Image: FOUND"
            )

            print(
                f"   {image_url}"
            )

        else:

            print(
                "🖼️ Image: NOT FOUND"
            )

    print(
        "\n" + "=" * 60
    )

    found_images = sum(
        1
        for article in articles
        if article.get(
            "image_url"
        )
    )

    print(
        f"🖼️ Images found: "
        f"{found_images}/{len(articles)}"
    )

    print(
        "✅ RSS + IMAGE TEST COMPLETE"
    )

    print(
        "=" * 60
    )