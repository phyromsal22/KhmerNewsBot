"""
Khmer News 24 - V2
News Cleaner

Cleans RSS article text before sending it
to duplicate checking and AI processing.
"""

import re
from html import unescape


def clean_text(text):
    """
    Clean article text.

    Removes:
    - HTML tags
    - HTML entities
    - Extra spaces
    - Empty lines
    """

    if not text:
        return ""

    # Convert HTML entities
    text = unescape(text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs
    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Replace multiple whitespace with one space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_article(article):
    """
    Clean one article.
    """

    if not article:
        return None

    cleaned = article.copy()

    cleaned["title"] = clean_text(
        cleaned.get("title", "")
    )

    cleaned["summary"] = clean_text(
        cleaned.get("summary", "")
    )

    cleaned["source"] = clean_text(
        cleaned.get("source", "")
    )

    cleaned["category"] = clean_text(
        cleaned.get("category", "")
    )

    return cleaned


def clean_articles(articles):
    """
    Clean multiple articles.
    """

    cleaned_articles = []

    for article in articles:

        cleaned = clean_article(article)

        if cleaned and cleaned.get("title"):
            cleaned_articles.append(cleaned)

    return cleaned_articles