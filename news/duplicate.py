"""
Khmer News 24 - V2
Duplicate News Detector
"""

import hashlib
import re


def normalize_title(title):
    """
    Normalize a title so similar titles
    can be compared more easily.
    """

    if not title:
        return ""

    title = title.lower()

    # Remove URLs
    title = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        title
    )

    # Remove punctuation
    title = re.sub(
        r"[^\w\s]",
        " ",
        title
    )

    # Remove extra spaces
    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


def make_title_hash(title):
    """
    Create a SHA256 hash from normalized title.
    """

    normalized = normalize_title(title)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def get_article_key(article):
    """
    Create a unique key for an article.

    Priority:
    1. URL
    2. Title hash
    """

    link = article.get("link", "").strip()

    if link:
        return f"url:{link.lower()}"

    title_hash = make_title_hash(
        article.get("title", "")
    )

    return f"title:{title_hash}"


def remove_duplicates(articles):
    """
    Remove exact duplicates from a list of articles.
    """

    unique_articles = []
    seen = set()

    for article in articles:

        key = get_article_key(article)

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        unique_articles.append(article)

    return unique_articles


def find_duplicates(articles):
    """
    Return duplicate articles separately.
    """

    unique_articles = []
    duplicate_articles = []

    seen = set()

    for article in articles:

        key = get_article_key(article)

        if not key:
            continue

        if key in seen:
            duplicate_articles.append(article)
        else:
            seen.add(key)
            unique_articles.append(article)

    return unique_articles, duplicate_articles