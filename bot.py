import os
import html
import asyncio
import logging

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from news import (
    get_news,
    get_latest_news,
)

from ai import process_news_batch

from database import (
    init_database,
    news_already_sent,
    save_sent_news,
    get_sent_news_count,
    get_category_count,
)


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

NEWS_LIMIT = 5

AUTO_INTERVAL = 5 * 60

AUTO_NEWS_PER_CATEGORY = 1


# =========================================================
# ENV CHECK
# =========================================================

if not BOT_TOKEN:
    raise ValueError(
        "❌ TELEGRAM_BOT_TOKEN not found in .env"
    )

if not CHANNEL_ID:
    raise ValueError(
        "❌ CHANNEL_ID not found in .env"
    )


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# GLOBAL
# =========================================================

application = None
auto_news_task = None


# =========================================================
# MENU
# =========================================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "⚽ បាល់ទាត់",
                callback_data="football"
            ),

            InlineKeyboardButton(
                "🌍 ពិភពលោក",
                callback_data="war"
            ),
        ],

        [
            InlineKeyboardButton(
                "🏛️ នយោបាយ",
                callback_data="politics"
            ),

            InlineKeyboardButton(
                "🇰🇭 កម្ពុជា",
                callback_data="cambodia"
            ),
        ],

        [
            InlineKeyboardButton(
                "🔥 Breaking News",
                callback_data="breaking"
            ),

            InlineKeyboardButton(
                "📰 ព័ត៌មានថ្មីៗ",
                callback_data="latest"
            ),
        ],

    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# CATEGORY NAME
# =========================================================

def category_name(category):

    names = {

        "football": "⚽ បាល់ទាត់",

        "war": "🌍 ពិភពលោក",

        "politics": "🏛️ នយោបាយ",

        "cambodia": "🇰🇭 កម្ពុជា",

        "breaking": "🔥 Breaking News",

        "latest": "📰 ព័ត៌មានថ្មីៗ",

    }

    return names.get(
        category,
        "📰 ព័ត៌មាន"
    )


# =========================================================
# START
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = """
📰 <b>Khmer News 24</b>

សួស្តី 👋

សូមជ្រើសរើសប្រភេទព័ត៌មាន៖

⚽ បាល់ទាត់
🌍 ព័ត៌មានពិភពលោក
🏛️ នយោបាយ
🇰🇭 ព័ត៌មានកម្ពុជា
🔥 Breaking News
📰 ព័ត៌មានថ្មីៗ

🤖 AI បកប្រែ និងសង្ខេបជាភាសាខ្មែរ

🔥 Auto Breaking News
⏱️ Update រៀងរាល់ 5 នាទី
"""

    await update.message.reply_text(
        text,
        reply_markup=main_menu(),
        parse_mode="HTML",
    )


# =========================================================
# HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = """
📖 <b>Khmer News 24 Help</b>

/start
បើក Menu ព័ត៌មាន

/status
មើលស្ថានភាព Bot

/help
បង្ហាញជំនួយ

/testchannel
Test Channel

🔥 Auto Breaking News
ពិនិត្យព័ត៌មានរៀងរាល់ 5 នាទី
"""

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================================================
# STATUS
# =========================================================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    total = get_sent_news_count()

    football = get_category_count(
        "football"
    )

    world = get_category_count(
        "war"
    )

    politics = get_category_count(
        "politics"
    )

    cambodia = get_category_count(
        "cambodia"
    )

    text = f"""
📊 <b>Khmer News 24 Status</b>

🤖 Bot: <b>ONLINE</b>

🔥 Auto Breaking News:
<b>ON</b>

⏱️ Update:
<b>Every 5 minutes</b>

🗄️ Database:
<b>CONNECTED</b>

📢 Channel:
<b>CONNECTED</b>

━━━━━━━━━━━━━━━━━━

📰 News Sent:

⚽ Football: {football}
🌍 World: {world}
🏛️ Politics: {politics}
🇰🇭 Cambodia: {cambodia}

📊 Total:
<b>{total}</b>
"""

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================================================
# FORMAT NEWS
# =========================================================

def format_news_message(
    news_list,
    ai_results,
    category
):

    if not news_list:
        return "❌ មិនមានព័ត៌មានទេ។"

    result_map = {}

    for item in ai_results:

        try:

            item_id = int(
                item.get("id")
            )

            result_map[item_id] = item

        except Exception:

            continue

    message = (
        f"<b>{category_name(category)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
    )

    for index, news in enumerate(
        news_list,
        start=1
    ):

        ai = result_map.get(
            index,
            {}
        )

        title = ai.get(
            "title_kh",
            news.get(
                "title",
                "ព័ត៌មាន"
            )
        )

        summary = ai.get(
            "summary_kh",
            news.get(
                "summary",
                ""
            )
        )

        source = news.get(
            "source",
            "Unknown"
        )

        link = news.get(
            "link",
            ""
        )

        title = html.escape(
            str(title)
        )

        summary = html.escape(
            str(summary)
        )

        source = html.escape(
            str(source)
        )

        article = (
            f"<b>{index}. {title}</b>\n\n"
            f"{summary}\n\n"
            f"📰 ប្រភព: {source}\n"
        )

        if link:

            safe_link = html.escape(
                link,
                quote=True
            )

            article += (
                f'🔗 <a href="{safe_link}">'
                f'អានព័ត៌មានដើម</a>\n'
            )

        article += "\n"

        message += article

    return message


# =========================================================
# SHOW NEWS
# =========================================================

async def show_category_news(
    query,
    category
):

    await query.answer()

    await query.edit_message_text(
        "⏳ កំពុងទាញព័ត៌មាន...\n\n"
        "🤖 AI កំពុងបកប្រែ និងសង្ខេប..."
    )

    news_list = get_news(
        category,
        limit=NEWS_LIMIT
    )

    if not news_list:

        await query.edit_message_text(
            "❌ មិនអាចទាញព័ត៌មានបានទេ។\n\n"
            "សូមសាកល្បងម្ដងទៀត។",
            reply_markup=main_menu(),
        )

        return

    ai_results = process_news_batch(
        news_list
    )

    message = format_news_message(
        news_list,
        ai_results,
        category
    )

    # =====================================================
    # MESSAGE SPLIT
    # =====================================================

    if len(message) <= 4000:

        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

        return

    chunks = []

    while message:

        chunk = message[:3900]

        if len(message) > 3900:

            last_newline = chunk.rfind(
                "\n"
            )

            if last_newline > 2000:
                chunk = chunk[
                    :last_newline
                ]

        chunks.append(chunk)

        message = message[
            len(chunk):
        ]

    await query.edit_message_text(
        chunks[0],
        parse_mode="HTML",
    )

    for chunk in chunks[1:]:

        await query.message.reply_text(
            chunk,
            parse_mode="HTML",
        )

    await query.message.reply_text(
        "👇 ជ្រើសរើសព័ត៌មានបន្ថែម៖",
        reply_markup=main_menu(),
    )


# =========================================================
# LATEST NEWS
# =========================================================

async def show_latest_news(query):

    await query.answer()

    await query.edit_message_text(
        "⏳ កំពុងស្វែងរកព័ត៌មានថ្មីបំផុត...\n\n"
        "🤖 AI កំពុងសង្ខេប..."
    )

    news_list = get_latest_news(
        limit=NEWS_LIMIT
    )

    if not news_list:

        await query.edit_message_text(
            "❌ មិនមានព័ត៌មានថ្មីៗទេ។",
            reply_markup=main_menu(),
        )

        return

    ai_results = process_news_batch(
        news_list
    )

    message = format_news_message(
        news_list,
        ai_results,
        "latest"
    )

    if len(message) <= 4000:

        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

        return

    chunks = []

    while message:

        chunk = message[:3900]

        if len(message) > 3900:

            last_newline = chunk.rfind(
                "\n"
            )

            if last_newline > 2000:
                chunk = chunk[
                    :last_newline
                ]

        chunks.append(chunk)

        message = message[
            len(chunk):
        ]

    await query.edit_message_text(
        chunks[0],
        parse_mode="HTML",
    )

    for chunk in chunks[1:]:

        await query.message.reply_text(
            chunk,
            parse_mode="HTML",
        )

    await query.message.reply_text(
        "👇 Menu:",
        reply_markup=main_menu(),
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    category = query.data

    # =====================================================
    # BREAKING
    # =====================================================

    if category == "breaking":

        await query.answer()

        await query.edit_message_text(
            "🔥 <b>Breaking News</b>\n\n"
            "🟢 Auto System: ON\n"
            "⏱️ Check: Every 5 minutes\n"
            "📢 Channel: Connected\n"
            "🗄️ Database: Connected\n"
            "🚫 Duplicate: Protected",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

        return

    # =====================================================
    # LATEST
    # =====================================================

    if category == "latest":

        await show_latest_news(
            query
        )

        return

    # =====================================================
    # NORMAL
    # =====================================================

    if category in [
        "football",
        "war",
        "politics",
        "cambodia",
    ]:

        await show_category_news(
            query,
            category
        )

        return


# =========================================================
# TEST CHANNEL
# =========================================================

async def test_channel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        message = """
🧪 <b>Khmer News 24 Test</b>

✅ Bot → Channel: Connected

🔥 Auto Breaking News: ON
⏱️ Every 5 minutes
🗄️ SQLite: ON

📰 Khmer News 24
"""

        await application.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="HTML",
        )

        await update.message.reply_text(
            "✅ Test message បានផ្ញើទៅ Channel!"
        )

    except Exception as error:

        print(
            f"❌ Channel error: {error}"
        )

        await update.message.reply_text(
            f"❌ Channel Error:\n{error}"
        )


# =========================================================
# AUTO BREAKING NEWS
# =========================================================

async def auto_breaking_news():

    print(
        "🔥 Auto Breaking News started"
    )

    # Give Telegram time to initialize
    await asyncio.sleep(20)

    while True:

        try:

            print("")
            print(
                "===================================="
            )

            print(
                "🔎 Checking latest news..."
            )

            print(
                "===================================="
            )

            categories = [
                "football",
                "war",
                "politics",
                "cambodia",
            ]

            all_new_news = []

            # =================================================
            # CHECK CATEGORIES
            # =================================================

            for category in categories:

                try:

                    news_list = get_news(
                        category,
                        limit=5
                    )

                    if not news_list:
                        continue

                    new_articles = []

                    for news in news_list:

                        link = news.get(
                            "link",
                            ""
                        ).strip()

                        if not link:
                            continue

                        if news_already_sent(
                            link
                        ):
                            continue

                        new_articles.append(
                            news
                        )

                    # Only newest one/category
                    new_articles = (
                        new_articles[
                            :AUTO_NEWS_PER_CATEGORY
                        ]
                    )

                    for news in new_articles:

                        news[
                            "auto_category"
                        ] = category

                        all_new_news.append(
                            news
                        )

                except Exception as error:

                    print(
                        f"❌ {category} error: "
                        f"{error}"
                    )

            # =================================================
            # NO NEW NEWS
            # =================================================

            if not all_new_news:

                print(
                    "ℹ️ No new news."
                )

            else:

                print(
                    f"📰 Found "
                    f"{len(all_new_news)} "
                    f"new article(s)."
                )

                # =================================================
                # AI BATCH
                # =================================================

                ai_results = (
                    process_news_batch(
                        all_new_news
                    )
                )

                result_map = {}

                for item in ai_results:

                    try:

                        item_id = int(
                            item.get("id")
                        )

                        result_map[
                            item_id
                        ] = item

                    except Exception:

                        continue

                # =================================================
                # SEND
                # =================================================

                for index, news in enumerate(
                    all_new_news,
                    start=1
                ):

                    link = news.get(
                        "link",
                        ""
                    ).strip()

                    if not link:
                        continue

                    if news_already_sent(
                        link
                    ):
                        continue

                    ai = result_map.get(
                        index,
                        {}
                    )

                    title = ai.get(
                        "title_kh",
                        news.get(
                            "title",
                            "ព័ត៌មាន"
                        )
                    )

                    summary = ai.get(
                        "summary_kh",
                        news.get(
                            "summary",
                            ""
                        )
                    )

                    source = news.get(
                        "source",
                        "Unknown"
                    )

                    category = news.get(
                        "auto_category",
                        "news"
                    )

                    title = html.escape(
                        str(title)
                    )

                    summary = html.escape(
                        str(summary)
                    )

                    source = html.escape(
                        str(source)
                    )

                    safe_link = html.escape(
                        link,
                        quote=True
                    )

                    message = f"""
<b>🔥 BREAKING NEWS</b>

{category_name(category)}

<b>{title}</b>

{summary}

📰 ប្រភព: {source}

🔗 <a href="{safe_link}">អានព័ត៌មានដើម</a>

━━━━━━━━━━━━━━━━━━
📰 <b>Khmer News 24</b>
"""

                    try:

                        await application.bot.send_message(
                            chat_id=CHANNEL_ID,
                            text=message,
                            parse_mode="HTML",
                            disable_web_page_preview=False,
                        )

                        save_sent_news(
                            url=link,
                            title=news.get(
                                "title",
                                ""
                            ),
                            source=news.get(
                                "source",
                                ""
                            ),
                            category=category,
                        )

                        print(
                            f"✅ Sent: "
                            f"{news.get('title', '')}"
                        )

                        await asyncio.sleep(
                            2
                        )

                    except Exception as error:

                        print(
                            f"❌ Send error: "
                            f"{error}"
                        )

        except asyncio.CancelledError:

            print(
                "🛑 Auto system stopped."
            )

            break

        except Exception as error:

            print(
                f"❌ Auto system error: "
                f"{error}"
            )

        print(
            "⏳ Next check in 5 minutes..."
        )

        await asyncio.sleep(
            AUTO_INTERVAL
        )


# =========================================================
# POST INIT
# =========================================================

async def post_init(
    app: Application
):

    global auto_news_task

    print(
        "🚀 Starting Auto Breaking News..."
    )

    auto_news_task = asyncio.create_task(
        auto_breaking_news()
    )


# =========================================================
# POST SHUTDOWN
# =========================================================

async def post_shutdown(
    app: Application
):

    global auto_news_task

    if auto_news_task:

        print(
            "🛑 Stopping Auto News..."
        )

        auto_news_task.cancel()

        try:

            await auto_news_task

        except asyncio.CancelledError:

            pass


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Telegram error:",
        exc_info=context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    global application

    # Database
    init_database()

    # Telegram
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Commands
    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status_command
        )
    )

    application.add_handler(
        CommandHandler(
            "testchannel",
            test_channel
        )
    )

    # Buttons
    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # Error
    application.add_error_handler(
        error_handler
    )

    # =====================================================
    # START
    # =====================================================

    print("")
    print(
        "========================================"
    )
    print(
        "📰 Khmer News 24"
    )
    print(
        "========================================"
    )
    print(
        "🤖 Telegram Bot: READY"
    )
    print(
        f"📢 Channel: {CHANNEL_ID}"
    )
    print(
        "🗄️ SQLite: ENABLED"
    )
    print(
        "🔥 Breaking News: ENABLED"
    )
    print(
        "⏱️ Interval: 5 minutes"
    )
    print(
        "📰 Latest News: ENABLED"
    )
    print(
        "📊 Status: ENABLED"
    )
    print(
        "🚫 Duplicate Protection: ENABLED"
    )
    print(
        "========================================"
    )
    print(
        "🚀 Bot is running..."
    )
    print("")

    application.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()