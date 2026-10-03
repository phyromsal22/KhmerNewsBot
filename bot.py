import os
import html
import asyncio
import json
import urllib.request

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.constants import ParseMode

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from news import (
    get_news,
    get_latest_news,
    get_breaking_news,
)

from ai import (
    process_news_batch,
)

from ai_filter import (
    filter_important_news,
)

from database import (
    init_database,
    news_already_sent,
    save_sent_news,
    get_sent_news_count,
    get_category_count,
)

# ============================================================
# ENV
# ============================================================

load_dotenv()

BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

if not BOT_TOKEN:
    BOT_TOKEN = os.getenv(
        "BOT_TOKEN"
    )

CHANNEL_ID = os.getenv(
    "CHANNEL_ID"
)

if not BOT_TOKEN:
    raise ValueError(
        "❌ TELEGRAM_BOT_TOKEN not found in .env"
    )

if not CHANNEL_ID:
    raise ValueError(
        "❌ CHANNEL_ID not found in .env"
    )


# ============================================================
# SETTINGS
# ============================================================

NEWS_LIMIT = 5

AUTO_INTERVAL = 5 * 60

BREAKING_MINUTES = 15

AUTO_NEWS_PER_CATEGORY = 1

# Cambodia channel news (non-breaking)
CAMBODIA_AUTO_INTERVAL = 15 * 60
CAMBODIA_NEWS_MINUTES = 60
CAMBODIA_AUTO_PER_CYCLE = 2

# Channel posts BREAKING NEWS and selected Cambodia news.
# Cambodia is checked first.


# ============================================================
# CAMBODIA TIMEZONE
# ============================================================

# Cambodia = GMT+7
#
# Fixed timezone is used instead of ZoneInfo
# so Windows/Python does not require tzdata.

CAMBODIA_TZ = timezone(
    timedelta(hours=7)
)


# ============================================================
# NEWS CATEGORIES
# ============================================================

CATEGORIES = {

    "football":
        "⚽ បាល់ទាត់",

    "war":
        "🌍 ពិភពលោក",

    "politics":
        "🏛️ នយោបាយ",

    "cambodia":
        "🇰🇭 កម្ពុជា",

}


# ============================================================
# FOOTBALL COMPETITIONS
# ============================================================

FOOTBALL_LEAGUES = {

    # --------------------------------------------------------
    # ENGLAND
    # --------------------------------------------------------

    "Premier League":
        "eng.1",

    "FA Cup":
        "eng.fa",

    "Carabao Cup":
        "eng.league_cup",

    "Community Shield":
        "eng.comm_shield",


    # --------------------------------------------------------
    # SPAIN
    # --------------------------------------------------------

    "La Liga":
        "esp.1",

    "Copa del Rey":
        "esp.copa_del_rey",


    # --------------------------------------------------------
    # ITALY
    # --------------------------------------------------------

    "Serie A":
        "ita.1",

    "Coppa Italia":
        "ita.coppa_italia",


    # --------------------------------------------------------
    # GERMANY
    # --------------------------------------------------------

    "Bundesliga":
        "ger.1",

    "DFB-Pokal":
        "ger.dfb_pokal",


    # --------------------------------------------------------
    # FRANCE
    # --------------------------------------------------------

    "Ligue 1":
        "fra.1",

    "Coupe de France":
        "fra.coupe_de_france",


    # --------------------------------------------------------
    # UEFA CLUB COMPETITIONS
    # --------------------------------------------------------

    "Champions League":
        "uefa.champions",

    "Europa League":
        "uefa.europa",

    "Conference League":
        "uefa.europa.conf",

    "UEFA Super Cup":
        "uefa.super_cup",


    # --------------------------------------------------------
    # UEFA NATIONAL TEAMS
    # --------------------------------------------------------

    "UEFA Nations League":
        "uefa.nations",

    "UEFA Euro":
        "uefa.euro",


    # --------------------------------------------------------
    # FIFA
    # --------------------------------------------------------

    "FIFA World Cup":
        "fifa.world",


    # --------------------------------------------------------
    # USA
    # --------------------------------------------------------

    "MLS":
        "usa.1",

}


# ============================================================
# HTML ESCAPE
# ============================================================

def esc(text):

    return html.escape(
        str(text or "")
    )


# ============================================================
# MAIN MENU
# ============================================================

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
                "📅 ប្រកួតថ្ងៃនេះ",
                callback_data="matches_today"
            ),

            InlineKeyboardButton(
                "📆 ប្រកួតថ្ងៃស្អែក",
                callback_data="matches_tomorrow"
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

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# FOOTBALL MENU
# ============================================================

def football_menu():

    keyboard = [

        [

            InlineKeyboardButton(
                "📰 ព័ត៌មានបាល់ទាត់",
                callback_data="football"
            ),

        ],

        [

            InlineKeyboardButton(
                "📅 ប្រកួតថ្ងៃនេះ",
                callback_data="matches_today"
            ),

            InlineKeyboardButton(
                "📆 ប្រកួតថ្ងៃស្អែក",
                callback_data="matches_tomorrow"
            ),

        ],

        [

            InlineKeyboardButton(
                "🔙 Menu",
                callback_data="home"
            ),

        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# MATCH MENU
# ============================================================

def match_menu(offset):

    if offset == 0:

        refresh_callback = (
            "matches_today"
        )

        other_callback = (
            "matches_tomorrow"
        )

        other_text = (
            "📆 ថ្ងៃស្អែក"
        )

    else:

        refresh_callback = (
            "matches_tomorrow"
        )

        other_callback = (
            "matches_today"
        )

        other_text = (
            "📅 ថ្ងៃនេះ"
        )


    keyboard = [

        [

            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data=refresh_callback
            ),

        ],

        [

            InlineKeyboardButton(
                other_text,
                callback_data=other_callback
            ),

        ],

        [

            InlineKeyboardButton(
                "⚽ Football Menu",
                callback_data="football_menu"
            ),

        ],

        [

            InlineKeyboardButton(
                "🔙 Menu",
                callback_data="home"
            ),

        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )
# ============================================================
# FORMAT PUBLISHED TIME — CAMBODIA GMT+7
# ============================================================

def format_published_cambodia(value):
    """
    Convert a news source publication time to Cambodia time (GMT+7).

    Examples:
        Sat, 03 Oct 2026 05:39:22 GMT
        -> 03/10/2026 12:39

        2026-10-03T05:39:22Z
        -> 03/10/2026 12:39
    """
    if not value:
        return ""

    raw = str(value).strip()
    kh_tz = timezone(timedelta(hours=7))

    # RFC 2822 / RSS dates, e.g. "Sat, 03 Oct 2026 05:39:22 GMT"
    try:
        dt = parsedate_to_datetime(raw)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(kh_tz).strftime(
            "%d/%m/%Y %H:%M"
        )
    except Exception:
        pass

    # ISO-8601 dates, e.g. "2026-10-03T05:39:22Z"
    try:
        dt = datetime.fromisoformat(
            raw.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(kh_tz).strftime(
            "%d/%m/%Y %H:%M"
        )
    except Exception:
        return raw


# ============================================================
# FORMAT NEWS
# ============================================================

def format_news(
    article,
    ai_result=None,
    breaking=False
):

    title = article.get(
        "title",
        ""
    )

    summary = article.get(
        "summary",
        ""
    )

    source = article.get(
        "source",
        "Unknown"
    )

    url = article.get(
        "url",
        ""
    )

    published = article.get(
        "published",
        ""
    )

    category = article.get(
        "category",
        ""
    )


    if ai_result:

        title_kh = ai_result.get(
            "title_kh"
        ) or title

        summary_kh = ai_result.get(
            "summary_kh"
        ) or summary

    else:

        title_kh = title

        summary_kh = summary


    if breaking:

        header = (
            "🔥 <b>BREAKING NEWS</b>"
        )

    else:

        header = (
            "📰 <b>KHMER NEWS 24</b>"
        )


    category_name = CATEGORIES.get(
        category,
        ""
    )


    message = (

        f"{header}\n\n"

        f"{category_name}\n\n"

        f"<b>{esc(title_kh)}</b>\n\n"

        f"{esc(summary_kh)}\n\n"

        f"📰 <b>ប្រភព:</b> "
        f"{esc(source)}\n"

    )


    if published:

        published_kh = format_published_cambodia(
            published
        )

        message += (

            f"🕐 <b>ពេលវេលា (កម្ពុជា):</b> "
            f"{esc(published_kh)}\n"

        )


    if url:

        safe_url = (

            str(url)

            .replace(
                "&",
                "&amp;"
            )

            .replace(
                '"',
                "&quot;"
            )

        )


        message += (

            f'\n🔗 <a href="{safe_url}">'
            f'អានព័ត៌មានដើម</a>'

        )


    return message


# ============================================================
# SEND SAFE MESSAGE
# ============================================================

async def send_message_safe(
    bot,
    chat_id,
    text,
    reply_markup=None
):

    MAX_LENGTH = 3900


    if len(text) <= MAX_LENGTH:

        await bot.send_message(

            chat_id=chat_id,

            text=text,

            parse_mode=ParseMode.HTML,

            disable_web_page_preview=True,

            reply_markup=reply_markup,

        )

        return


    parts = []

    remaining = text


    while remaining:

        if len(remaining) <= MAX_LENGTH:

            parts.append(
                remaining
            )

            break


        cut = remaining.rfind(
            "\n",
            0,
            MAX_LENGTH
        )


        if cut < 500:

            cut = MAX_LENGTH


        parts.append(
            remaining[:cut]
        )


        remaining = (
            remaining[cut:]
            .lstrip("\n")
        )


    for index, part in enumerate(parts):

        await bot.send_message(

            chat_id=chat_id,

            text=part,

            parse_mode=ParseMode.HTML,

            disable_web_page_preview=True,

            reply_markup=(

                reply_markup

                if index == len(parts) - 1

                else None

            ),

        )


# ============================================================
# START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (

        "<b>📰 Khmer News 24</b>\n\n"

        "សូមស្វាគមន៍! 🇰🇭\n\n"

        "ព័ត៌មានថ្មីៗអំពី៖\n\n"

        "⚽ បាល់ទាត់\n"

        "📅 ការប្រកួតថ្ងៃនេះ\n"

        "📆 ការប្រកួតថ្ងៃស្អែក\n"

        "🌍 ពិភពលោក\n"

        "🏛️ នយោបាយ\n"

        "🇰🇭 កម្ពុជា\n"

        "🔥 Breaking News\n\n"

        "ជ្រើសរើសខាងក្រោម 👇"

    )


    await update.message.reply_text(

        text,

        parse_mode=ParseMode.HTML,

        reply_markup=main_menu()

    )


# ============================================================
# HELP
# ============================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (

        "<b>📖 Khmer News 24 - Help</b>\n\n"

        "<b>Commands:</b>\n\n"

        "/start - ចាប់ផ្តើម\n"

        "/help - ជំនួយ\n"

        "/status - ស្ថានភាព Bot\n"

        "/latest - ព័ត៌មានថ្មីៗ\n"

        "/breaking - Breaking News\n"

        "/football - បាល់ទាត់\n"

        "/today - ប្រកួតថ្ងៃនេះ\n"

        "/tomorrow - ប្រកួតថ្ងៃស្អែក\n"
"/world - ពិភពលោក\n"

        "/politics - នយោបាយ\n"

        "/cambodia - កម្ពុជា\n"

        "/testchannel - Test Channel\n\n"

        "🕐 ម៉ោងប្រកួត = Cambodia Time (GMT+7)"

    )


    await update.message.reply_text(

        text,

        parse_mode=ParseMode.HTML,

        reply_markup=main_menu()

    )


# ============================================================
# SEND CATEGORY NEWS
# ============================================================

async def send_category_news(
    bot,
    chat_id,
    category
):

    await bot.send_message(

        chat_id=chat_id,

        text=(

            f"🔎 កំពុងស្វែងរក "

            f"{CATEGORIES.get(category, '')}..."

        )

    )


    try:

        articles = await asyncio.to_thread(

            get_news,

            category,

            NEWS_LIMIT

        )

    except Exception as error:

        print(
            f"❌ News error "
            f"[{category}]: {error}"
        )

        await bot.send_message(

            chat_id=chat_id,

            text=(
                "❌ មានបញ្ហាក្នុងការទាញព័ត៌មាន។ "
                "សូមសាកល្បងម្តងទៀត។"
            ),

            reply_markup=main_menu()

        )

        return


    if not articles:

        await bot.send_message(

            chat_id=chat_id,

            text=(
                "⚠️ មិនទាន់រកឃើញព័ត៌មាន។"
            ),

            reply_markup=main_menu()

        )

        return


    try:

        results = await asyncio.to_thread(

            process_news_batch,

            articles

        )

    except Exception as error:

        print(
            f"❌ AI error: {error}"
        )

        results = []


    result_map = {}


    for result in results:

        try:

            result_map[
                int(
                    result.get("id")
                )
            ] = result

        except Exception:

            pass


    for index, article in enumerate(

        articles,

        start=1

    ):

        await send_message_safe(

            bot,

            chat_id,

            format_news(

                article,

                result_map.get(
                    index
                )

            )

        )

        await asyncio.sleep(
            0.3
        )


    await bot.send_message(

        chat_id=chat_id,

        text=(
            "👇 ជ្រើសរើសព័ត៌មានបន្ត"
        ),

        reply_markup=(

            football_menu()

            if category == "football"

            else main_menu()

        )

    )
# ============================================================
# LATEST NEWS
# ============================================================

async def send_latest(
    bot,
    chat_id
):

    await bot.send_message(

        chat_id=chat_id,

        text=(
            "📰 កំពុងរកព័ត៌មានថ្មីៗ..."
        )

    )


    try:

        articles = await asyncio.to_thread(

            get_latest_news,

            NEWS_LIMIT

        )

    except Exception as error:

        print(
            f"❌ Latest error: {error}"
        )

        articles = []


    if not articles:

        await bot.send_message(

            chat_id=chat_id,

            text="⚠️ មិនមានព័ត៌មាន។",

            reply_markup=main_menu()

        )

        return


    try:

        results = await asyncio.to_thread(

            process_news_batch,

            articles

        )

    except Exception as error:

        print(
            f"❌ AI error: {error}"
        )

        results = []


    result_map = {}


    for result in results:

        try:

            result_map[
                int(
                    result.get("id")
                )
            ] = result

        except Exception:

            pass


    for index, article in enumerate(

        articles,

        start=1

    ):

        await send_message_safe(

            bot,

            chat_id,

            format_news(

                article,

                result_map.get(
                    index
                )

            )

        )

        await asyncio.sleep(
            0.3
        )


    await bot.send_message(

        chat_id=chat_id,

        text="👇",

        reply_markup=main_menu()

    )


# ============================================================
# BREAKING NEWS
# ============================================================

async def send_breaking(
    bot,
    chat_id
):

    await bot.send_message(

        chat_id=chat_id,

        text=(
            "🔥 កំពុងស្វែងរក Breaking News..."
        )

    )


    all_breaking = []


    for category in CATEGORIES:

        try:

            articles = await asyncio.to_thread(

                get_breaking_news,

                category,

                minutes=BREAKING_MINUTES,

                limit=3

            )

            all_breaking.extend(
                articles
            )

        except Exception as error:

            print(
                f"⚠️ Breaking "
                f"[{category}]: {error}"
            )


    unique = []

    seen = set()


    for article in all_breaking:

        url = article.get(
            "url",
            ""
        )


        if not url:

            continue


        if url in seen:

            continue


        seen.add(url)

        unique.append(
            article
        )


    unique.sort(

        key=lambda x:

        -x.get(
            "timestamp",
            0
        )

    )


    unique = unique[
        :NEWS_LIMIT
    ]


    if not unique:

        await bot.send_message(

            chat_id=chat_id,

            text=(

                "ℹ️ ឥឡូវនេះមិនទាន់មាន "
                "Breaking News ក្នុង "

                f"{BREAKING_MINUTES} "

                "នាទីចុងក្រោយទេ។"

            ),

            reply_markup=main_menu()

        )

        return


    try:

        results = await asyncio.to_thread(

            process_news_batch,

            unique

        )

    except Exception as error:

        print(
            f"❌ AI error: {error}"
        )

        results = []


    result_map = {}


    for result in results:

        try:

            result_map[
                int(
                    result.get("id")
                )
            ] = result

        except Exception:

            pass


    for index, article in enumerate(

        unique,

        start=1

    ):

        await send_message_safe(

            bot,

            chat_id,

            format_news(

                article,

                result_map.get(
                    index
                ),

                breaking=True

            )

        )

        await asyncio.sleep(
            0.3
        )


    await bot.send_message(

        chat_id=chat_id,

        text="👇",

        reply_markup=main_menu()

    )


# ============================================================
# MATCH DATE
# ============================================================

def get_match_date(
    offset=0
):

    now = datetime.now(
        CAMBODIA_TZ
    )


    target = (

        now

        + timedelta(
            days=offset
        )

    )


    return target.strftime(
        "%Y%m%d"
    )


# ============================================================
# ESPN REQUEST
# ============================================================

def espn_request(
    url
):

    request = urllib.request.Request(

        url,

        headers={

            "User-Agent":
                "Mozilla/5.0 "
                "KhmerNews24/1.0",

            "Accept":
                "application/json",

        }

    )


    try:

        with urllib.request.urlopen(

            request,

            timeout=10

        ) as response:

            raw = response.read()

            if not raw:

                return None


            return json.loads(
                raw.decode(
                    "utf-8"
                )
            )


    except Exception as error:

        print(
            f"⚠️ ESPN request error: "
            f"{error}"
        )

        return None


# ============================================================
# FETCH MATCHES FROM ESPN
# ============================================================

def fetch_matches(
    league_name,
    league_code,
    date
):

    url = (

        "https://site.api.espn.com/"

        "apis/site/v2/sports/"

        "soccer/"

        f"{league_code}/"

        f"scoreboard?"

        f"dates={date}"

        "&limit=200"

    )


    data = espn_request(
        url
    )


    if not data:

        return []


    matches = []


    for event in data.get(
        "events",
        []
    ):

        try:

            competitions = event.get(

                "competitions",

                []

            )


            if not competitions:

                continue


            competition = (
                competitions[0]
            )


            competitors = (

                competition.get(

                    "competitors",

                    []

                )

            )


            if len(competitors) < 2:

                continue


            home = next(

                (

                    team

                    for team
                    in competitors

                    if team.get(
                        "homeAway"
                    ) == "home"

                ),

                None

            )


            away = next(

                (

                    team

                    for team
                    in competitors

                    if team.get(
                        "homeAway"
                    ) == "away"

                ),

                None

            )


            if not home or not away:

                continue


            # ------------------------------------------------
            # MATCH TIME
            # ------------------------------------------------

            event_date = event.get(
                "date",
                ""
            )


            try:

                dt = (

                    datetime

                    .fromisoformat(

                        event_date.replace(

                            "Z",

                            "+00:00"

                        )

                    )

                    .astimezone(
                        CAMBODIA_TZ
                    )

                )


                time_text = (
                    dt.strftime(
                        "%H:%M"
                    )
                )


            except Exception:

                time_text = "--:--"


            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            status_type = (

                competition

                .get(
                    "status",
                    {}
                )

                .get(
                    "type",
                    {}
                )

            )


            state = status_type.get(

                "state",

                "pre"

            )


            detail = status_type.get(

                "shortDetail",

                ""

            )


            # ------------------------------------------------
            # TEAM NAMES
            # ------------------------------------------------

            home_team = (

                home

                .get(
                    "team",
                    {}
                )

                .get(

                    "displayName",

                    "Home"

                )

            )


            away_team = (

                away

                .get(
                    "team",
                    {}
                )

                .get(

                    "displayName",

                    "Away"

                )

            )


            # ------------------------------------------------
            # SCORE
            # ------------------------------------------------

            home_score = home.get(

                "score",

                ""

            )


            away_score = away.get(

                "score",

                ""

            )


            # ------------------------------------------------
            # EVENT NAME
            # ------------------------------------------------

            event_name = event.get(
                "name",
                ""
            )


            # ------------------------------------------------
            # COMPETITION NAME FROM API
            # ------------------------------------------------

            competition_name = (

                competition

                .get(
                    "type",
                    {}
                )

                .get(
                    "text",
                    ""
                )

            )


            # ------------------------------------------------
            # MATCH OBJECT
            # ------------------------------------------------

            matches.append({

                "id":

                    str(

                        event.get(

                            "id",

                            ""

                        )

                    ),

                "league":

                    league_name,

                "league_code":

                    league_code,

                "home":

                    home_team,

                "away":

                    away_team,

                "time":

                    time_text,

                "datetime":

                    event_date,

                "state":

                    state,

                "detail":

                    detail,

                "home_score":

                    home_score,

                "away_score":

                    away_score,

                "event_name":

                    event_name,

                "competition_name":

                    competition_name,

            })


        except Exception as error:

            print(

                f"⚠️ Match parse "

                f"[{league_name}]: "

                f"{error}"

            )


    return matches


# ============================================================
# FETCH ONE COMPETITION SAFELY
# ============================================================

async def fetch_competition(
    league_name,
    league_code,
    date
):

    try:

        # Small delay prevents sending
        # too many ESPN requests at once.

        await asyncio.sleep(
            0.15
        )


        matches = await asyncio.to_thread(

            fetch_matches,

            league_name,

            league_code,

            date

        )


        return matches


    except Exception as error:

        print(

            f"⚠️ Competition error "

            f"[{league_name}]: "

            f"{error}"

        )

        return []


# ============================================================
# GET ALL MATCHES
# ============================================================

async def get_matches_async(
    offset=0
):

    date = get_match_date(
        offset
    )


    all_matches = []


    # --------------------------------------------------------
    # Fetch competitions in small batches
    # instead of a huge simultaneous request.
    # --------------------------------------------------------

    competitions = list(
        FOOTBALL_LEAGUES.items()
    )


    batch_size = 4


    for start in range(

        0,

        len(competitions),

        batch_size

    ):

        batch = competitions[
            start:
            start + batch_size
        ]


        tasks = []


        for (

            league_name,

            league_code

        ) in batch:

            tasks.append(

                fetch_competition(

                    league_name,

                    league_code,

                    date

                )

            )


        results = await asyncio.gather(

            *tasks,

            return_exceptions=True

        )


        for result in results:

            if isinstance(

                result,

                Exception

            ):

                continue


            if not result:

                continue


            all_matches.extend(
                result
            )


        # Small pause between batches.

        if (

            start + batch_size

            < len(competitions)

        ):

            await asyncio.sleep(
                0.4
            )


    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique = {}


    for match in all_matches:

        key = match.get(
            "id"
        )


        if not key:

            key = (

                match.get(
                    "league",
                    ""
                ),

                match.get(
                    "home",
                    ""
                ),

                match.get(
                    "away",
                    ""
                ),

                match.get(
                    "time",
                    ""
                ),

            )


        unique[key] = match


    matches = list(
        unique.values()
    )


    # --------------------------------------------------------
    # SORT BY TIME
    # --------------------------------------------------------

    matches.sort(

        key=lambda x: (

            x.get(
                "datetime",
                ""
            ),

            x.get(
                "league",
                ""
            )

        )

    )


    return matches


# ============================================================
# SYNC WRAPPER
# ============================================================

def get_matches(
    offset=0
):

    return asyncio.run(

        get_matches_async(
            offset
        )

    )


# ============================================================
# COMPETITION TYPE
# ============================================================

def competition_group(
    league
):

    league_lower = (
        league.lower()
    )


    # International

    if any(

        word in league_lower

        for word in [

            "nations",

            "euro",

            "world cup",

        ]

    ):

        return "🌍 INTERNATIONAL"


    # UEFA

    if (

        "champions" in league_lower

        or "europa" in league_lower

        or "conference" in league_lower

        or "uefa" in league_lower

    ):

        return "🏆 UEFA"


    # Cups

    if any(

        word in league_lower

        for word in [

            "cup",

            "copa",

            "coppa",

            "pok al",

            "coupe",

            "shield",

            "community",

            "carabao",

            "dfb",

        ]

    ):

        return "🏆 DOMESTIC CUPS"


    return "⚽ LEAGUES"


# ============================================================
# FORMAT MATCHES
# ============================================================

def format_matches(
    matches,
    offset=0
):

    date = (

        datetime.now(
            CAMBODIA_TZ
        )

        + timedelta(
            days=offset
        )

    )


    date_text = date.strftime(
        "%d/%m/%Y"
    )


    if offset == 0:

        title = (

            "📅 <b>"
            "ការប្រកួតបាល់ទាត់ថ្ងៃនេះ"
            "</b>"

        )

    else:

        title = (

            "📆 <b>"
            "ការប្រកួតបាល់ទាត់ថ្ងៃស្អែក"
            "</b>"

        )


    header = (

        f"{title}\n"

        f"📆 {date_text}\n"

        "🕐 Cambodia Time (GMT+7)\n\n"

    )


    if not matches:

        return [

            header

            + "❌ មិនរកឃើញការប្រកួត "
              "សម្រាប់ថ្ងៃនេះក្នុង "
              "ប្រភពដែលបានភ្ជាប់ទេ។\n\n"

            + "📡 Match data: ESPN"

        ]


    MAX_LENGTH = 3800

    messages = []

    current = header

    current_group = None


    # --------------------------------------------------------
    # GROUP MATCHES
    # --------------------------------------------------------

    for number, match in enumerate(

        matches,

        start=1

    ):

        league = match.get(

            "league",

            "Unknown"

        )


        group = competition_group(
            league
        )


        # ----------------------------------------------------
        # GROUP HEADER
        # ----------------------------------------------------

        if group != current_group:

            group_header = (

                f"\n━━━━━━━━━━━━━━━━━━\n"

                f"<b>{esc(group)}</b>\n"

                f"━━━━━━━━━━━━━━━━━━\n"

            )


            if (

                len(current)

                + len(group_header)

                > MAX_LENGTH

            ):

                messages.append(
                    current
                )

                current = header


            current += group_header

            current_group = group


        # ----------------------------------------------------
        # LEAGUE HEADER
        # ----------------------------------------------------

        league_header = (

            f"\n⚽ <b>"
            f"{esc(league)}"
            f"</b>\n"

        )


        # Only add league heading
        # when it changes.

        previous_league = None


        if number > 1:

            previous_league = (

                matches[number - 2]

                .get(
                    "league",
                    ""
                )

            )


        if (

            league != previous_league

        ):

            if (

                len(current)

                + len(league_header)

                > MAX_LENGTH

            ):

                messages.append(
                    current
                )

                current = header


            current += league_header


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        state = match.get(

            "state",

            "pre"

        )


        if state == "post":

            home_score = esc(

                match.get(
                    "home_score",
                    ""
                )

            )

            away_score = esc(

                match.get(
                    "away_score",
                    ""
                )

            )


            status_line = (

                f"   "
                f"{home_score}"
                f" - "
                f"{away_score}"
                f" • ✅ FT\n"

            )


        elif state == "in":

            detail = match.get(

                "detail",

                ""

            )


            if detail:

                detail_text = (

                    f" {esc(detail)}"

                )

            else:

                detail_text = ""


            status_line = (

                f"   "

                f"{esc(match.get('home_score', '0'))}"

                f" - "

                f"{esc(match.get('away_score', '0'))}"

                f" • 🔴 LIVE"

                f"{detail_text}\n"

            )


        else:

            status_line = (

                f"   🕐 "

                f"{esc(match.get('time', '--:--'))}"

                f"\n"

            )


        # ----------------------------------------------------
        # MATCH BLOCK
        # ----------------------------------------------------

        block = (

            f"\n"

            f"<b>{number}. "

            f"{esc(match.get('home', 'Home'))}"

            f"</b>\n"

            f"   🆚 "

            f"<b>"

            f"{esc(match.get('away', 'Away'))}"

            f"</b>\n"

            f"{status_line}"

        )


        if (

            len(current)

            + len(block)

            > MAX_LENGTH

        ):

            messages.append(
                current
            )


            current = (

                header

                + f"⚽ <b>"
                  f"{esc(league)}"
                  f"</b>\n"

                + block

            )

        else:

            current += block


    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    footer = (

        "\n━━━━━━━━━━━━━━━━━━\n"

        "🇰🇭 <b>Khmer News 24</b>\n"

        "📡 Match data: ESPN\n"

        "🕐 Cambodia Time (GMT+7)"

    )


    if (

        len(current)

        + len(footer)

        <= 4096

    ):

        current += footer


    messages.append(
        current
    )


    return messages


# ============================================================
# SEND MATCHES
# ============================================================

async def send_matches(
    bot,
    chat_id,
    offset
):

    if offset == 0:

        loading = (

            "📅 កំពុងទាញ "
            "ការប្រកួតថ្ងៃនេះ..."

        )

    else:

        loading = (

            "📆 កំពុងទាញ "
            "ការប្រកួតថ្ងៃស្អែក..."

        )


    await bot.send_message(

        chat_id=chat_id,

        text=loading

    )


    try:

        matches = await asyncio.to_thread(

            get_matches,

            offset

        )


        messages = format_matches(

            matches,

            offset

        )


    except Exception as error:

        print(

            f"❌ Match error: "
            f"{error}"

        )


        await bot.send_message(

            chat_id=chat_id,

            text=(

                "❌ មិនអាចទាញ "
                "ទិន្នន័យការប្រកួតបានទេ។\n\n"

                "សូមសាកល្បង Refresh។"

            ),

            reply_markup=main_menu()

        )

        return


    for index, message in enumerate(
        messages
    ):

        if index == 0:

            await bot.send_message(

                chat_id=chat_id,

                text=message,

                parse_mode=ParseMode.HTML,

                disable_web_page_preview=True,

                reply_markup=match_menu(
                    offset
                )

            )

        else:

            await bot.send_message(

                chat_id=chat_id,

                text=message,

                parse_mode=ParseMode.HTML,

                disable_web_page_preview=True

            )

# ============================================================
# CALLBACK HANDLER
# ============================================================


# ============================================================
# CALLBACK HANDLER
# ============================================================

async def button_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    query = (
        update.callback_query
    )


    await query.answer()


    callback = query.data


    chat_id = (
        query.message.chat_id
    )


    bot = context.bot

    # ========================================================
    # HOME
    # ========================================================

    if callback == "home":

        await query.edit_message_text(

            "<b>📰 Khmer News 24</b>\n\n"

            "👇 ជ្រើសរើសប្រភេទព័ត៌មាន៖",

            parse_mode=ParseMode.HTML,

            reply_markup=main_menu()

        )

        return


    # ========================================================
    # FOOTBALL MENU
    # ========================================================

    if callback == "football_menu":

        await query.edit_message_text(

            "⚽ <b>Football</b>\n\n"

            "ជ្រើសរើសអ្វីដែលអ្នកចង់មើល៖",

            parse_mode=ParseMode.HTML,

            reply_markup=football_menu()

        )

        return


    # ========================================================
    # TODAY / TOMORROW
    # ========================================================

    if callback in (

        "matches_today",

        "matches_tomorrow"

    ):

        if callback == "matches_today":

            offset = 0

        else:

            offset = 1


        await query.edit_message_text(

            "⏳ កំពុងទាញ "
            "ទិន្នន័យការប្រកួត..."

        )


        try:

            matches = await asyncio.to_thread(

                get_matches,

                offset

            )


            messages = format_matches(

                matches,

                offset

            )


        except Exception as error:

            print(

                f"❌ Match callback error: "
                f"{error}"

            )


            await query.edit_message_text(

                "❌ មិនអាចទាញ "
                "ទិន្នន័យការប្រកួតបានទេ។\n\n"

                "សូមចុច 🔄 Refresh ម្តងទៀត។",

                reply_markup=main_menu()

            )

            return


        # ----------------------------------------------------
        # First message replaces loading message
        # ----------------------------------------------------

        await query.edit_message_text(

            messages[0],

            parse_mode=ParseMode.HTML,

            disable_web_page_preview=True,

            reply_markup=match_menu(
                offset
            )

        )


        # ----------------------------------------------------
        # Additional messages
        # ----------------------------------------------------

        for message in messages[1:]:

            await bot.send_message(

                chat_id=chat_id,

                text=message,

                parse_mode=ParseMode.HTML,

                disable_web_page_preview=True

            )


        return

    # ========================================================
    # LATEST
    # ========================================================

    if callback == "latest":

        await send_latest(

            bot,

            chat_id

        )

        return


    # ========================================================
    # BREAKING
    # ========================================================

    if callback == "breaking":

        await send_breaking(

            bot,

            chat_id

        )

        return


    # ========================================================
    # NEWS CATEGORIES
    # ========================================================

    if callback in CATEGORIES:

        await send_category_news(

            bot,

            chat_id,

            callback

        )

        return


# ============================================================
# CATEGORY COMMAND
# ============================================================

async def category_command(

    update,

    context,

    category

):

    await send_category_news(

        context.bot,

        update.effective_chat.id,

        category

    )


# ============================================================
# FOOTBALL COMMAND
# ============================================================

async def football(

    update,

    context

):

    await category_command(

        update,

        context,

        "football"

    )


# ============================================================
# TODAY COMMAND
# ============================================================

async def today(

    update,

    context

):

    await send_matches(

        context.bot,

        update.effective_chat.id,

        0

    )


# ============================================================
# TOMORROW COMMAND
# ============================================================

async def tomorrow(

    update,

    context

):

    await send_matches(

        context.bot,

        update.effective_chat.id,

        1

    )


# ============================================================
# WORLD
# ============================================================

# ============================================================
# WORLD
# ============================================================

async def world(

    update,

    context

):

    await category_command(

        update,

        context,

        "war"

    )


# ============================================================
# POLITICS
# ============================================================

async def politics(

    update,

    context

):

    await category_command(

        update,

        context,

        "politics"

    )


# ============================================================
# CAMBODIA
# ============================================================

async def cambodia(

    update,

    context

):

    await category_command(

        update,

        context,

        "cambodia"

    )


# ============================================================
# LATEST
# ============================================================

async def latest(

    update,

    context

):

    await send_latest(

        context.bot,

        update.effective_chat.id

    )


# ============================================================
# BREAKING
# ============================================================

async def breaking(

    update,

    context

):

    await send_breaking(

        context.bot,

        update.effective_chat.id

    )


# ============================================================
# STATUS
# ============================================================

async def status(

    update,

    context

):

    try:

        total = (
            get_sent_news_count()
        )


        football_count = (
            get_category_count(
                "football"
            )
        )


        war_count = (
            get_category_count(
                "war"
            )
        )


        politics_count = (
            get_category_count(
                "politics"
            )
        )


        cambodia_count = (
            get_category_count(
                "cambodia"
            )
        )


    except Exception as error:

        print(
            f"❌ Status error: {error}"
        )


        total = 0

        football_count = 0

        war_count = 0

        politics_count = 0

        cambodia_count = 0


    text = (

        "<b>📊 Khmer News 24 Status</b>\n\n"

        "🟢 Bot: Running\n\n"

        f"📰 Sent News: {total}\n\n"

        f"⚽ Football: "
        f"{football_count}\n"

        f"🌍 World: "
        f"{war_count}\n"

        f"🏛️ Politics: "
        f"{politics_count}\n"

        f"🇰🇭 Cambodia: "
        f"{cambodia_count}\n\n"

        "🔥 Auto Breaking:\n"

        "Every 5 minutes\n\n"

        "⚽ Football Matches:\n"

        "Today + Tomorrow\n\n"


        "🏆 Competitions:\n"

        "Premier League\n"
        "FA Cup\n"
        "Carabao Cup\n"
        "La Liga\n"
        "Copa del Rey\n"
        "Serie A\n"
        "Coppa Italia\n"
        "Bundesliga\n"
        "DFB-Pokal\n"
        "Ligue 1\n"
        "Coupe de France\n"
        "Champions League\n"
        "Europa League\n"
        "Conference League\n"
        "UEFA Nations League\n"
        "UEFA Euro\n"
        "FIFA World Cup\n"
        "MLS\n\n"

        "🕐 Cambodia Time (GMT+7)"

    )


    await update.message.reply_text(

        text,

        parse_mode=ParseMode.HTML

    )


# ============================================================
# TEST CHANNEL
# ============================================================

async def test_channel(

    update,

    context

):

    try:

        await context.bot.send_message(

            chat_id=CHANNEL_ID,

            text=(

                "✅ <b>Khmer News 24</b>\n\n"

                "Channel connection test "
                "successful! 🇰🇭"

            ),

            parse_mode=ParseMode.HTML

        )


        await update.message.reply_text(

            "✅ Test message sent to channel."

        )


    except Exception as error:

        await update.message.reply_text(

            f"❌ Channel error:\n{error}"

        )


# ============================================================
# AUTO BREAKING NEWS
# ============================================================

async def auto_breaking_news(
    application
):

    print()
    print("🔥 Auto Breaking News started")
    print("⏰ Checking every 5 minutes")
    print("🧠 AI importance filter ENABLED")
    print()

    await asyncio.sleep(30)

    while True:

        try:

            breaking_categories = [
                "cambodia",
                "football",
                "war",
                "politics",
            ]

            candidates = []

            # Collect first, then run ONE Gemini filter for the whole cycle.
            for category in breaking_categories:
                articles = await asyncio.to_thread(
                    get_breaking_news,
                    category,
                    minutes=BREAKING_MINUTES,
                    limit=5
                )

                for article in articles:
                    url = article.get("url", "")
                    if not url or news_already_sent(url):
                        continue
                    candidates.append(article)

            # Remove duplicate URLs while preserving source order.
            unique = []
            seen = set()
            for article in candidates:
                url = article.get("url", "")
                if url in seen:
                    continue
                seen.add(url)
                unique.append(article)

            if unique:
                selected, rejected = await asyncio.to_thread(
                    filter_important_news,
                    unique
                )

                # Editorial priority first, then Cambodia, newest, and score.
                priority_rank = {
                    "CRITICAL": 0,
                    "HIGH": 1,
                    "NORMAL": 2,
                    "LOW": 3,
                }
                selected.sort(
                    key=lambda x: (
                        priority_rank.get(
                            x.get("importance_priority", "NORMAL"),
                            2,
                        ),
                        0 if x.get("category") == "cambodia" else 1,
                        -x.get("timestamp", 0),
                        -x.get("importance_score", 0),
                    )
                )

                # Keep the channel from being flooded in one cycle.
                selected = selected[:4]

                if not selected:
                    print("🧠 No breaking article passed importance filter")

                for article in selected:
                    try:
                        results = await asyncio.to_thread(
                            process_news_batch,
                            [article]
                        )
                    except Exception as error:
                        print(f"❌ Auto AI summary error: {error}")
                        results = []

                    ai_result = results[0] if results else None
                    message = format_news(
                        article,
                        ai_result,
                        breaking=True
                    )

                    await send_message_safe(
                        application.bot,
                        CHANNEL_ID,
                        message
                    )

                    save_sent_news(
                        article.get("url", ""),
                        article.get("title", ""),
                        article.get("source", ""),
                        article.get("category", "")
                    )

                    print(
                        f"🔥 Sent important breaking "
                        f"[{article.get('importance_score', 0)}]: "
                        f"{article.get('title', '')}"
                    )
                    await asyncio.sleep(1)

        except Exception as error:
            print(f"❌ Auto Breaking Error: {error}")

        await asyncio.sleep(AUTO_INTERVAL)


# ============================================================
# AUTO CAMBODIA NEWS
# ============================================================

async def auto_cambodia_news(
    application
):

    print()
    print("🇰🇭 Auto Cambodia News started")
    print("⏰ Checking every 15 minutes")
    print("🧠 AI importance filter ENABLED")
    print()

    await asyncio.sleep(45)

    while True:

        try:
            articles = await asyncio.to_thread(
                get_news,
                "cambodia",
                20
            )

            now = datetime.now(timezone.utc).timestamp()
            cutoff = now - (CAMBODIA_NEWS_MINUTES * 60)

            fresh = []
            for article in articles:
                url = article.get("url", "")
                timestamp = article.get("timestamp", 0)

                if not url or news_already_sent(url):
                    continue
                if timestamp <= 0 or timestamp < cutoff:
                    continue
                fresh.append(article)

            if fresh:
                selected, rejected = await asyncio.to_thread(
                    filter_important_news,
                    fresh
                )

                priority_rank = {
                    "CRITICAL": 0,
                    "HIGH": 1,
                    "NORMAL": 2,
                    "LOW": 3,
                }
                selected.sort(
                    key=lambda x: (
                        priority_rank.get(
                            x.get("importance_priority", "NORMAL"),
                            2,
                        ),
                        -x.get("importance_score", 0),
                        -x.get("timestamp", 0),
                    )
                )
                selected = selected[:CAMBODIA_AUTO_PER_CYCLE]

                if not selected:
                    print("🧠 No Cambodia article passed importance filter")

                for article in selected:
                    try:
                        results = await asyncio.to_thread(
                            process_news_batch,
                            [article]
                        )
                    except Exception as error:
                        print(f"❌ Cambodia AI summary error: {error}")
                        results = []

                    ai_result = results[0] if results else None
                    message = format_news(
                        article,
                        ai_result,
                        breaking=False
                    )

                    await send_message_safe(
                        application.bot,
                        CHANNEL_ID,
                        message
                    )

                    save_sent_news(
                        article.get("url", ""),
                        article.get("title", ""),
                        article.get("source", ""),
                        article.get("category", "cambodia")
                    )

                    print(
                        f"🇰🇭 Sent important Cambodia news "
                        f"[{article.get('importance_score', 0)}]: "
                        f"{article.get('title', '')}"
                    )
                    await asyncio.sleep(1)

            else:
                print("🇰🇭 No new Cambodia news in the last 60 minutes")

        except Exception as error:
            print(f"❌ Auto Cambodia News Error: {error}")

        await asyncio.sleep(CAMBODIA_AUTO_INTERVAL)


# ============================================================
# POST INIT
# ============================================================

async def post_init(
    application
):

    # Initialize SQLite database

    init_database()


    # Start automatic Breaking News

    application.create_task(

        auto_breaking_news(

            application

        )

    )


    # Start automatic Cambodia News

    application.create_task(

        auto_cambodia_news(

            application

        )

    )


    print()

    print(
        "===================================="
    )

    print(
        "📰 KHMER NEWS 24"
    )

    print(
        "🤖 BOT STARTED"
    )

    print(
        "🔥 AUTO BREAKING ENABLED"
    )

    print(
        "🇰🇭 AUTO CAMBODIA NEWS ENABLED"
    )

    print(
        "⚽ MATCHES TODAY + TOMORROW ENABLED"
    )

    print(
        "🏆 FA CUP ENABLED"
    )

    print(
        "🌍 UEFA NATIONS LEAGUE ENABLED"
    )

    print(
        "🏆 MAJOR CUPS ENABLED"
    )

    print(
        "🕐 CAMBODIA TIME GMT+7"
    )

    print(
        "===================================="
    )

    print()


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(

    update,

    context

):

    print(

        f"❌ Telegram Error: "
        f"{context.error}"

    )


# ============================================================
# MAIN
# ============================================================

def main():

    application = (

        Application.builder()

        .token(
            BOT_TOKEN
        )

        .post_init(
            post_init
        )

        .build()

    )


    # ========================================================
    # COMMANDS
    # ========================================================

    application.add_handler(

        CommandHandler(

            "start",

            start

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

            status

        )

    )


    application.add_handler(

        CommandHandler(

            "testchannel",

            test_channel

        )

    )


    application.add_handler(

        CommandHandler(

            "football",

            football

        )

    )


    application.add_handler(

        CommandHandler(

            "today",

            today

        )

    )


    application.add_handler(

        CommandHandler(

            "tomorrow",

            tomorrow

        )

    )
    application.add_handler(

        CommandHandler(

            "world",

            world

        )

    )


    application.add_handler(

        CommandHandler(

            "politics",

            politics

        )

    )


    application.add_handler(

        CommandHandler(

            "cambodia",

            cambodia

        )

    )


    application.add_handler(

        CommandHandler(

            "latest",

            latest

        )

    )


    application.add_handler(

        CommandHandler(

            "breaking",

            breaking

        )

    )


    # ========================================================
    # CALLBACK BUTTONS
    # ========================================================

    application.add_handler(

        CallbackQueryHandler(

            button_handler

        )

    )


    # ========================================================
    # ERROR
    # ========================================================

    application.add_error_handler(

        error_handler

    )


    # ========================================================
    # START BOT
    # ========================================================

    print(
        "🚀 Starting Telegram bot..."
    )


    application.run_polling(

        drop_pending_updates=True

    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()