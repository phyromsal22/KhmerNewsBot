"""
Khmer News 24 - V2
Telegram News Formatter
"""

from html import escape


def format_news(article):
    """
    Format one article for Telegram.
    """

    title = article.get(
        "khmer_title",
        article.get("title", "")
    )

    summary = article.get(
        "khmer_summary",
        ""
    )

    source = article.get(
        "source",
        "Unknown"
    )

    link = article.get(
        "link",
        ""
    )

    score = article.get(
        "ai_score"
    )

    parts = []

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    if title:
        parts.append(
            f"📰 <b>{escape(title)}</b>"
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    if summary:
        parts.append(
            escape(summary)
        )

    # --------------------------------------------------------
    # AI SCORE
    # --------------------------------------------------------

    if score is not None:
        parts.append(
            f"🤖 កម្រិតសារៈសំខាន់៖ "
            f"<b>{score}/100</b>"
        )

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    if source:
        parts.append(
            f"📌 ប្រភព៖ "
            f"<b>{escape(source)}</b>"
        )

    # --------------------------------------------------------
    # ORIGINAL LINK
    # --------------------------------------------------------

    if link:
        parts.append(
            f'🔗 <a href="{escape(link)}">'
            f'អានព័ត៌មានដើម</a>'
        )

    return "\n\n".join(parts)