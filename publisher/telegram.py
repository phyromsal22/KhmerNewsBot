"""
Khmer News 24 - V2
Telegram Publisher

V2.7.5
Supports:
- Text news publishing
- Image + safe caption publishing
- Full text after image when needed
- Automatic fallback to text
- Batch publishing with successful article tracking
"""

import os
import asyncio

from telegram import Bot
from dotenv import load_dotenv

from publisher.formatter import format_news


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN not found in .env"
    )

if not CHANNEL_ID:
    raise RuntimeError(
        "CHANNEL_ID not found in .env"
    )


# ============================================================
# TELEGRAM BOT
# ============================================================

bot = Bot(token=BOT_TOKEN)


# ============================================================
# CAPTION LIMIT
# ============================================================

MAX_CAPTION_LENGTH = 1000


def make_safe_caption(message):
    """
    Create a safe caption for Telegram photo publishing.
    """

    if len(message) <= MAX_CAPTION_LENGTH:
        return message, False

    caption = message[:MAX_CAPTION_LENGTH]

    last_tag_start = caption.rfind("<")
    last_tag_end = caption.rfind(">")

    if last_tag_start > last_tag_end:
        caption = caption[:last_tag_start]

    caption = caption.rstrip()

    caption += "\n\n📖 អត្ថបទពេញនៅខាងក្រោម"

    return caption, True


# ============================================================
# PUBLISH ONE NEWS
# ============================================================

async def publish_news(article):
    """
    Publish one news article to Telegram.

    Returns:
        True  = published successfully
        False = publishing failed
    """

    message = format_news(article)

    if not message:
        print("⚠️ Empty Telegram message")
        return False

    image_url = (
        article.get("image_url", "")
        or ""
    ).strip()

    # ========================================================
    # IMAGE PUBLISH
    # ========================================================

    if image_url:

        try:

            print(
                "🖼️ Sending image to Telegram..."
            )

            caption, was_truncated = make_safe_caption(
                message
            )

            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=image_url,
                caption=caption,
                parse_mode="HTML"
            )

            if was_truncated:

                print(
                    "📝 Sending full news text..."
                )

                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=message,
                    parse_mode="HTML",
                    disable_web_page_preview=False
                )

            print(
                "📤 News + image published to Telegram"
            )

            return True

        except Exception as image_error:

            print(
                f"⚠️ Image publish failed: "
                f"{image_error}"
            )

            print(
                "↪️ Falling back to text message..."
            )

    # ========================================================
    # TEXT PUBLISH
    # ========================================================

    try:

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        print(
            "📤 News published to Telegram"
        )

        return True

    except Exception as error:

        print(
            f"❌ Telegram publish error: {error}"
        )

        return False


# ============================================================
# PUBLISH MULTIPLE NEWS
# ============================================================

async def publish_news_batch(
    articles,
    delay_seconds=2
):
    """
    Publish multiple news articles.

    Returns:
        {
            "published_count": int,
            "published_articles": list,
            "failed_articles": list
        }
    """

    published_articles = []
    failed_articles = []

    for article in articles:

        success = await publish_news(
            article
        )

        if success:

            published_articles.append(
                article
            )

        else:

            failed_articles.append(
                article
            )

        await asyncio.sleep(
            delay_seconds
        )

    print(
        f"📊 Published: "
        f"{len(published_articles)}/{len(articles)}"
    )

    print(
        f"❌ Failed: "
        f"{len(failed_articles)}/{len(articles)}"
    )

    return {
        "published_count": len(
            published_articles
        ),
        "published_articles": published_articles,
        "failed_articles": failed_articles
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24")
    print("V2.7.5 TELEGRAM PUBLISHER")
    print("=" * 60)

    print(
        "⚠️ Direct publishing test is disabled."
    )

    print(
        "ℹ️ The pipeline will publish real articles."
    )