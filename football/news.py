"""
🇰🇭 Khmer News 24
Football News Module
"""

from news.collector import collect_from_sources
from news.sources import get_sources
from news.cleaner import clean_articles
from news.duplicate import remove_duplicates


def collect_football_news(limit=10):
    """
    Collect football news from configured football RSS sources.
    """

    print("=" * 60)
    print("⚽ KHMER NEWS 24 — FOOTBALL NEWS")
    print("=" * 60)

    sources = get_sources("football")

    if not sources:
        print("❌ No football RSS sources configured")
        return []

    print(f"⚽ Football sources: {len(sources)}")

    # --------------------------------------------------------
    # Collect
    # --------------------------------------------------------

    articles = collect_from_sources(
        sources,
        category="football",
        limit=limit
    )

    print(
        f"📥 Football collected: "
        f"{len(articles)}"
    )

    if not articles:
        return []

    # --------------------------------------------------------
    # Clean
    # --------------------------------------------------------

    articles = clean_articles(
        articles
    )

    print(
        f"🧹 Football cleaned: "
        f"{len(articles)}"
    )

    # --------------------------------------------------------
    # Duplicate
    # --------------------------------------------------------

    articles = remove_duplicates(
        articles
    )

    print(
        f"🧹 Football unique: "
        f"{len(articles)}"
    )

    return articles


def print_football_news(
    articles
):
    """
    Print football news for testing.
    """

    print("\n⚽ FOOTBALL NEWS")

    if not articles:
        print("❌ No football news")
        return

    for index, article in enumerate(
        articles,
        start=1
    ):

        print(
            f"\n{index}. "
            f"{article.get('title', '')}"
        )

        print(
            f"   🖼️ Image: "
            f"{article.get('image_url', '')}"
        )

        print(
            f"   🔗 Link: "
            f"{article.get('link', '')}"
        )


if __name__ == "__main__":

    articles = collect_football_news(
        limit=5
    )

    print_football_news(
        articles
    )