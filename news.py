import feedparser
import re

from html import unescape
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


# =========================================================
# NEWS SOURCES
# =========================================================
#
# Source មួយ error -> bot នៅតែបន្តប្រើ source ផ្សេង
#
# =========================================================

NEWS_SOURCES = {

    # -----------------------------------------------------
    # FOOTBALL
    # -----------------------------------------------------

    "football": [

        {
            "name": "The Guardian Football",
            "url": "https://www.theguardian.com/football/rss",
            "priority": 1,
        },

        {
            "name": "Sky Sports Football",
            "url": "https://www.skysports.com/rss/12040",
            "priority": 2,
        },

    ],


    # -----------------------------------------------------
    # WORLD
    # -----------------------------------------------------

    "war": [

        {
            "name": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "priority": 1,
        },

        {
            "name": "The Guardian World",
            "url": "https://www.theguardian.com/world/rss",
            "priority": 2,
        },

    ],


    # -----------------------------------------------------
    # POLITICS
    # -----------------------------------------------------

    "politics": [

        {
            "name": "The Guardian Politics",
            "url": "https://www.theguardian.com/politics/rss",
            "priority": 1,
        },

        {
            "name": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "priority": 2,
        },

    ],


    # -----------------------------------------------------
    # CAMBODIA
    # -----------------------------------------------------
    #
    # VOA Khmer removed because its RSS endpoint
    # returned EMPTY in our test.
    #
    # -----------------------------------------------------

    "cambodia": [

        {
            "name": "Google News Cambodia",
            "url": (
                "https://news.google.com/rss/search?"
                "q=Cambodia&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 1,
        },

    ],
}


# =========================================================
# CATEGORY KEYWORDS
# =========================================================

CATEGORY_KEYWORDS = {

    "football": [

        "football",
        "soccer",
        "fifa",
        "uefa",

        "premier league",
        "champions league",

        "la liga",
        "serie a",
        "bundesliga",
        "ligue 1",

        "manchester",
        "liverpool",
        "chelsea",
        "arsenal",

        "barcelona",
        "real madrid",

        "messi",
        "ronaldo",

    ],


    "war": [

        "war",
        "conflict",
        "attack",
        "missile",
        "military",
        "army",
        "airstrike",
        "ceasefire",

        "iran",
        "israel",
        "gaza",
        "ukraine",
        "russia",

        "middle east",

    ],


    "politics": [

        "president",
        "prime minister",
        "government",
        "election",
        "parliament",
        "politics",
        "minister",
        "senate",
        "congress",
        "political",

    ],


    "cambodia": [

        "cambodia",
        "cambodian",
        "phnom penh",
        "siem reap",
        "battambang",
        "banteay meanchey",
        "preah vihear",
        "oddar meanchey",
        "kampot",
        "sihanoukville",
        "khmer",

    ],
}


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):

    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    # Convert HTML entities
    text = unescape(text)

    # Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# NORMALIZE URL
# =========================================================

def normalize_url(url):

    if not url:
        return ""

    url = url.strip()

    # Remove common tracking parameters
    tracking_parameters = (
        "utm_source|"
        "utm_medium|"
        "utm_campaign|"
        "utm_term|"
        "utm_content|"
        "gclid|"
        "fbclid"
    )

    url = re.sub(
        rf"[?&](?:{tracking_parameters})=[^&]*",
        "",
        url,
        flags=re.IGNORECASE
    )

    # Remove trailing ? or &
    url = url.rstrip(
        "&?"
    )

    return url


# =========================================================
# NORMALIZE TITLE
# =========================================================

def normalize_title(title):

    if not title:
        return ""

    title = clean_text(
        title
    ).lower()

    # Keep English, numbers and Khmer
    title = re.sub(
        r"[^a-z0-9\u1780-\u17ff\s]",
        " ",
        title
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


# =========================================================
# DUPLICATE KEY
# =========================================================

def make_duplicate_key(
    title,
    link
):

    normalized_link = normalize_url(
        link
    )

    if normalized_link:

        return (
            "url:"
            + normalized_link.lower()
        )

    return (
        "title:"
        + normalize_title(title)
    )


# =========================================================
# GET PUBLISHED TIMESTAMP
# =========================================================

def get_published_timestamp(item):

    # -----------------------------------------------------
    # published_parsed
    # -----------------------------------------------------

    parsed_time = item.get(
        "published_parsed"
    )

    if parsed_time:

        try:

            dt = datetime(
                parsed_time.tm_year,
                parsed_time.tm_mon,
                parsed_time.tm_mday,
                parsed_time.tm_hour,
                parsed_time.tm_min,
                parsed_time.tm_sec,
                tzinfo=timezone.utc
            )

            return dt.timestamp()

        except Exception:
            pass


    # -----------------------------------------------------
    # updated_parsed
    # -----------------------------------------------------

    parsed_time = item.get(
        "updated_parsed"
    )

    if parsed_time:

        try:

            dt = datetime(
                parsed_time.tm_year,
                parsed_time.tm_mon,
                parsed_time.tm_mday,
                parsed_time.tm_hour,
                parsed_time.tm_min,
                parsed_time.tm_sec,
                tzinfo=timezone.utc
            )

            return dt.timestamp()

        except Exception:
            pass


    # -----------------------------------------------------
    # Raw date
    # -----------------------------------------------------

    raw_date = (
        item.get("published")
        or item.get("updated")
        or ""
    )

    if raw_date:

        try:

            dt = parsedate_to_datetime(
                raw_date
            )

            if dt.tzinfo is None:

                dt = dt.replace(
                    tzinfo=timezone.utc
                )

            return dt.timestamp()

        except Exception:
            pass


    return 0


# =========================================================
# GET PUBLISHED TEXT
# =========================================================

def get_published_text(item):

    return (
        item.get("published")
        or item.get("updated")
        or ""
    )


# =========================================================
# CATEGORY RELEVANCE
# =========================================================

def is_relevant(
    title,
    summary,
    category,
    source_name
):

    # -----------------------------------------------------
    # Cambodia Google News feed
    # is already Cambodia-focused
    # -----------------------------------------------------

    if category == "cambodia":

        if source_name == "Google News Cambodia":

            return True


    text = (
        f"{title} {summary}"
        .lower()
    )

    keywords = CATEGORY_KEYWORDS.get(
        category,
        []
    )

    # If no keyword rules
    if not keywords:

        return True


    for keyword in keywords:

        if keyword.lower() in text:

            return True


    return False


# =========================================================
# READ SOURCE
# =========================================================

def read_source(
    source,
    category
):

    source_name = source.get(
        "name",
        "Unknown"
    )

    source_url = source.get(
        "url",
        ""
    )

    if not source_url:

        print(
            f"❌ No URL for {source_name}"
        )

        return []


    try:

        print(
            f"📰 Reading: "
            f"{source_name}"
        )


        # -------------------------------------------------
        # Parse RSS
        # -------------------------------------------------

        feed = feedparser.parse(
            source_url
        )


        # -------------------------------------------------
        # Feed warning
        # -------------------------------------------------

        if getattr(
            feed,
            "bozo",
            False
        ):

            print(
                f"⚠️ Feed warning: "
                f"{source_name}"
            )


        entries = getattr(
            feed,
            "entries",
            []
        )


        # -------------------------------------------------
        # Empty
        # -------------------------------------------------

        if not entries:

            print(
                f"🟡 {source_name} → EMPTY"
            )

            return []


        articles = []


        # -------------------------------------------------
        # Read latest 20
        # -------------------------------------------------

        for item in entries[:20]:

            title = clean_text(
                item.get(
                    "title",
                    ""
                )
            )


            summary = clean_text(
                item.get(
                    "summary",
                    item.get(
                        "description",
                        ""
                    )
                )
            )


            link = normalize_url(
                item.get(
                    "link",
                    ""
                )
            )


            published = (
                get_published_text(
                    item
                )
            )


            timestamp = (
                get_published_timestamp(
                    item
                )
            )


            # -------------------------------------------------
            # Skip invalid article
            # -------------------------------------------------

            if not title:
                continue

            if not link:
                continue


            # -------------------------------------------------
            # Relevance filter
            # -------------------------------------------------

            if not is_relevant(
                title,
                summary,
                category,
                source_name
            ):

                continue


            # -------------------------------------------------
            # Article object
            # -------------------------------------------------

            articles.append({

                "title": title,

                "summary": summary,

                "link": link,

                "source": source_name,

                "published": published,

                "timestamp": timestamp,

                "priority": source.get(
                    "priority",
                    99
                ),

                "category": category,

            })


        print(
            f"🟢 {source_name} → "
            f"{len(articles)} article(s)"
        )


        return articles


    except Exception as error:

        print(
            f"🔴 Error reading "
            f"{source_name}: "
            f"{error}"
        )

        return []


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicates(
    articles
):

    unique_articles = []

    seen_urls = set()

    seen_titles = set()


    for article in articles:

        title = article.get(
            "title",
            ""
        )

        link = article.get(
            "link",
            ""
        )


        # -------------------------------------------------
        # URL duplicate
        # -------------------------------------------------

        normalized_link = normalize_url(
            link
        )

        if normalized_link:

            url_key = (
                normalized_link.lower()
            )

            if url_key in seen_urls:

                continue

            seen_urls.add(
                url_key
            )


        # -------------------------------------------------
        # Title duplicate
        # -------------------------------------------------

        normalized_title = normalize_title(
            title
        )

        if normalized_title:

            if normalized_title in seen_titles:

                continue

            seen_titles.add(
                normalized_title
            )


        unique_articles.append(
            article
        )


    return unique_articles


# =========================================================
# SORT NEWS
# =========================================================

def sort_news(
    articles
):

    # Newest timestamp first.
    #
    # If timestamps are identical,
    # smaller priority number wins.
    #
    # priority 1 = higher priority
    # priority 2 = lower priority
    #

    return sorted(
        articles,
        key=lambda article: (
            -article.get(
                "timestamp",
                0
            ),
            article.get(
                "priority",
                99
            ),
        )
    )


# =========================================================
# GET NEWS
# =========================================================

def get_news(
    category,
    limit=5
):

    if category not in NEWS_SOURCES:

        print(
            f"❌ Unknown category: "
            f"{category}"
        )

        return []


    all_news = []


    # -----------------------------------------------------
    # Read all sources
    # -----------------------------------------------------

    for source in NEWS_SOURCES[
        category
    ]:

        articles = read_source(
            source,
            category
        )

        all_news.extend(
            articles
        )


    # -----------------------------------------------------
    # Remove duplicates
    # -----------------------------------------------------

    all_news = remove_duplicates(
        all_news
    )


    # -----------------------------------------------------
    # Sort newest first
    # -----------------------------------------------------

    all_news = sort_news(
        all_news
    )


    # -----------------------------------------------------
    # Limit
    # -----------------------------------------------------

    final_news = all_news[
        :limit
    ]


    # -----------------------------------------------------
    # Debug
    # -----------------------------------------------------

    print(
        f"✅ Selected "
        f"{len(final_news)} "
        f"news for "
        f"{category}"
    )


    for index, news in enumerate(
        final_news,
        start=1
    ):

        print(
            f"{index}. "
            f"{news.get('title', '')} "
            f"| "
            f"{news.get('source', '')}"
        )


    return final_news


# =========================================================
# GET LATEST NEWS
# =========================================================

def get_latest_news(
    limit=5
):

    categories = [
        "football",
        "war",
        "politics",
        "cambodia",
    ]


    all_news = []


    # -----------------------------------------------------
    # Collect news from all categories
    # -----------------------------------------------------

    for category in categories:

        news_list = get_news(
            category,
            limit=10
        )


        for news in news_list:

            news[
                "category"
            ] = category


        all_news.extend(
            news_list
        )


    # -----------------------------------------------------
    # Remove duplicates
    # -----------------------------------------------------

    all_news = remove_duplicates(
        all_news
    )


    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    all_news = sort_news(
        all_news
    )


    # -----------------------------------------------------
    # Return latest N
    # -----------------------------------------------------

    final_news = all_news[
        :limit
    ]


    print(
        f"📰 Latest News selected: "
        f"{len(final_news)}"
    )


    return final_news


# =========================================================
# SOURCE HEALTH CHECK
# =========================================================

def check_sources():

    print("")

    print(
        "===================================="
    )

    print(
        "🔎 SOURCE HEALTH CHECK"
    )

    print(
        "===================================="
    )


    total_ok = 0

    total_empty = 0

    total_error = 0


    for category, sources in (
        NEWS_SOURCES.items()
    ):

        print(
            f"\n📂 {category.upper()}"
        )


        for source in sources:

            source_name = source.get(
                "name",
                "Unknown"
            )

            source_url = source.get(
                "url",
                ""
            )


            try:

                feed = feedparser.parse(
                    source_url
                )


                entries = getattr(
                    feed,
                    "entries",
                    []
                )


                if entries:

                    total_ok += 1

                    print(
                        f"🟢 "
                        f"{source_name}"
                        f" → OK "
                        f"({len(entries)} items)"
                    )


                else:

                    total_empty += 1

                    print(
                        f"🟡 "
                        f"{source_name}"
                        f" → EMPTY"
                    )


            except Exception as error:

                total_error += 1

                print(
                    f"🔴 "
                    f"{source_name}"
                    f" → ERROR: "
                    f"{error}"
                )


    print("")

    print(
        "===================================="
    )

    print(
        f"🟢 OK: {total_ok}"
    )

    print(
        f"🟡 EMPTY: {total_empty}"
    )

    print(
        f"🔴 ERROR: {total_error}"
    )

    print(
        "===================================="
    )


# =========================================================
# TEST CATEGORY
# =========================================================

def test_category(
    category,
    limit=5
):

    print("")

    print(
        "===================================="
    )

    print(
        f"🧪 TEST CATEGORY: {category}"
    )

    print(
        "===================================="
    )


    news_list = get_news(
        category,
        limit=limit
    )


    if not news_list:

        print(
            "❌ No news found."
        )

        return


    for index, news in enumerate(
        news_list,
        start=1
    ):

        print("")

        print(
            f"#{index}"
        )

        print(
            f"Title: "
            f"{news.get('title', '')}"
        )

        print(
            f"Source: "
            f"{news.get('source', '')}"
        )

        print(
            f"Published: "
            f"{news.get('published', '')}"
        )

        print(
            f"Link: "
            f"{news.get('link', '')}"
        )


    print("")

    print(
        "===================================="
    )