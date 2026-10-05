import feedparser
import re

from html import unescape
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


# =========================================================
# KHMER NEWS 24
# NEWS SOURCES
# =========================================================

NEWS_SOURCES = {

    # =====================================================
    # FOOTBALL
    # =====================================================

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

        {
            "name": "CNA Sport",
            "url": (
                "https://www.channelnewsasia.com/"
                "api/v1/rss-outbound-feed"
                "?_format=xml&category=10296"
            ),
            "priority": 3,
        },

        {
            "name": "Reuters Football",
            "url": (
                "https://news.google.com/rss/search?"
                "q=site%3Areuters.com+football"
                "&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 4,
        },

        {
            "name": "AP Sports",
            "url": (
                "https://news.google.com/rss/search?"
                "q=site%3Aapnews.com+football"
                "&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 5,
        },
    ],


    # =====================================================
    # WORLD / WAR
    # =====================================================

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

        {
            "name": "CNA World",
            "url": (
                "https://www.channelnewsasia.com/"
                "api/v1/rss-outbound-feed"
                "?_format=xml&category=6311"
            ),
            "priority": 3,
        },

        {
            "name": "Reuters World",
            "url": (
                "https://news.google.com/rss/search?"
                "q=site%3Areuters.com+world+war+conflict"
                "&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 4,
        },

        {
            "name": "AP World",
            "url": (
                "https://news.google.com/rss/search?"
                "q=site%3Aapnews.com+world+war+conflict"
                "&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 5,
        },
    ],


    # =====================================================
    # POLITICS
    # =====================================================

    "politics": [

        {
            "name": "The Guardian Politics",
            "url": "https://www.theguardian.com/politics/rss",
            "priority": 1,
        },

        {
            "name": "Al Jazeera Politics",
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "priority": 2,
        },

        {
            "name": "CNA Asia",
            "url": (
                "https://www.channelnewsasia.com/"
                "api/v1/rss-outbound-feed"
                "?_format=xml&category=6511"
            ),
            "priority": 3,
        },

        {
            "name": "Reuters Politics",
            "url": (
                "https://news.google.com/rss/search?"
                "q=site%3Areuters.com+politics"
                "&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 4,
        },

        {
            "name": "AP Politics",
            "url": (
                "https://news.google.com/rss/search?"
                "q=site%3Aapnews.com+politics"
                "&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 5,
        },
    ],


    # =====================================================
    # CAMBODIA
    # =====================================================

    "cambodia": [

        {
            "name": "Google News Cambodia",
            "url": (
                "https://news.google.com/rss/search?"
                "q=Cambodia"
                "&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 1,
        },

        {
            "name": "Reuters Cambodia",
            "url": (
                "https://news.google.com/rss/search?"
                "q=site%3Areuters.com+Cambodia"
                "&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 2,
        },

        {
            "name": "AP Cambodia",
            "url": (
                "https://news.google.com/rss/search?"
                "q=site%3Aapnews.com+Cambodia"
                "&hl=en-US&gl=US&ceid=US:en"
            ),
            "priority": 3,
        },

        {
            "name": "Kampuchea Thmey",
            "url": "https://kampucheathmey.com/feed",
            "priority": 4,
        },

        {
            "name": "CEN",
            "url": "https://cen.com.kh/feed",
            "priority": 5,
        },

        {
            "name": "DAP News",
            "url": "https://dap-news.com/feed",
            "priority": 6,
        },

        {
            "name": "Khmer Breaking News",
            "url": "https://kbn.news/feed",
            "priority": 7,
        },

        {
            "name": "AKP",
            "url": "https://akp.gov.kh/feed",
            "priority": 8,
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
        "premier league",
        "champions league",
        "europa league",
        "conference league",
        "world cup",
        "fifa",
        "uefa",
        "goal",
        "match",
        "manager",
        "coach",
        "transfer",
        "player",
        "club",
        "league",

        "liverpool",
        "arsenal",
        "chelsea",
        "manchester united",
        "manchester city",
        "real madrid",
        "barcelona",
        "bayern",
        "psg",
        "inter",
        "milan",
        "juventus",

        "ronaldo",
        "messi",
        "mbappe",
        "haaland",
    ],


    "war": [

        "war",
        "conflict",
        "attack",
        "airstrike",
        "missile",
        "military",
        "army",
        "troops",
        "soldier",
        "fighting",
        "ceasefire",
        "bomb",
        "bombing",
        "drone",

        "iran",
        "israel",
        "gaza",
        "ukraine",
        "russia",
        "nato",
        "syria",
        "lebanon",
        "hezbollah",
        "houthi",

        "middle east",
        "defence",
        "defense",
    ],


    "politics": [

        "politics",
        "political",
        "president",
        "prime minister",
        "government",
        "parliament",
        "election",
        "minister",
        "senate",
        "congress",
        "party",
        "vote",
        "voting",
        "legislation",
        "law",
        "policy",

        "democrat",
        "republican",

        "government",
        "diplomatic",
        "diplomacy",
    ],


    "cambodia": [

        "cambodia",
        "cambodian",

        "phnom penh",
        "siem reap",
        "battambang",
        "banteay meanchey",
        "sihanoukville",

        "kampong cham",
        "kampot",
        "kandal",
        "takeo",
        "prey veng",
        "svay rieng",
        "kratie",

        "mondulkiri",
        "ratanakiri",
        "stung treng",
        "preah vihear",
        "koh kong",
        "pursat",
        "oddar meanchey",
        "tbong khmum",
        "kep",

        "hun manet",
        "royal government",
        "national assembly",
        "ministry",
    ],
}


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = unescape(str(text))

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

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

    url = re.sub(
        r"[?&]"
        r"(utm_source|utm_medium|utm_campaign|utm_term|utm_content)"
        r"=[^&]*",
        "",
        url,
        flags=re.IGNORECASE
    )

    return url.rstrip("/")


# =========================================================
# NORMALIZE TITLE
# =========================================================

def normalize_title(title):

    if not title:
        return ""

    title = clean_text(
        title
    ).lower()

    title = re.sub(
        r"[^\w\s]",
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
# TIMESTAMP
# =========================================================

def get_published_timestamp(entry):

    try:

        if getattr(
            entry,
            "published_parsed",
            None
        ):

            dt = datetime(
                *entry.published_parsed[:6],
                tzinfo=timezone.utc
            )

            return dt.timestamp()

    except Exception:
        pass


    try:

        if getattr(
            entry,
            "updated_parsed",
            None
        ):

            dt = datetime(
                *entry.updated_parsed[:6],
                tzinfo=timezone.utc
            )

            return dt.timestamp()

    except Exception:
        pass


    for field in [
        "published",
        "updated"
    ]:

        try:

            value = getattr(
                entry,
                field,
                ""
            )

            if value:

                dt = parsedate_to_datetime(
                    value
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
# PUBLISHED TEXT
# =========================================================

def get_published_text(entry):

    value = getattr(
        entry,
        "published",
        ""
    )

    if value:
        return clean_text(value)


    value = getattr(
        entry,
        "updated",
        ""
    )

    if value:
        return clean_text(value)


    return ""


# =========================================================
# ORIGINAL SOURCE
# =========================================================

def get_original_source(
    entry,
    default_source
):

    try:

        source = getattr(
            entry,
            "source",
            None
        )

        if source:

            if isinstance(
                source,
                dict
            ):

                name = source.get(
                    "title",
                    ""
                )

            else:

                name = getattr(
                    source,
                    "title",
                    ""
                )

            name = clean_text(
                name
            )

            if name:
                return name

    except Exception:
        pass


    return default_source


# =========================================================
# RELEVANCE
# =========================================================

def is_relevant(
    title,
    summary,
    category,
    source_name
):

    text = (
        f"{title} {summary}"
    ).lower()


    # Google News Cambodia
    # is already filtered.

    if (
        category == "cambodia"
        and
        (
            "Cambodia" in source_name
            or
            "Reuters Cambodia" in source_name
            or
            "AP Cambodia" in source_name
            or
            "Google News" in source_name
        )
    ):

        return True


    keywords = CATEGORY_KEYWORDS.get(
        category,
        []
    )


    if not keywords:
        return True


    return any(
        keyword.lower() in text
        for keyword in keywords
    )


# =========================================================
# READ RSS SOURCE
# =========================================================

def read_source(
    source,
    category
):

    articles = []


    source_name = source.get(
        "name",
        "Unknown"
    )


    source_url = source.get(
        "url",
        ""
    )


    priority = source.get(
        "priority",
        99
    )


    try:

        print(
            f"🔎 Reading: {source_name}"
        )


        feed = feedparser.parse(
            source_url
        )


        if not feed.entries:

            print(
                f"⚠️ EMPTY: {source_name}"
            )

            return []


        for entry in feed.entries[:40]:

            title = clean_text(
                getattr(
                    entry,
                    "title",
                    ""
                )
            )


            summary = clean_text(
                getattr(
                    entry,
                    "summary",
                    ""
                )
            )


            url = normalize_url(
                getattr(
                    entry,
                    "link",
                    ""
                )
            )


            if not title or not url:
                continue


            if not is_relevant(
                title,
                summary,
                category,
                source_name
            ):

                continue


            timestamp = (
                get_published_timestamp(
                    entry
                )
            )


            published = (
                get_published_text(
                    entry
                )
            )


            original_source = (
                get_original_source(
                    entry,
                    source_name
                )
            )


            article = {

                "title": title,

                "summary": summary,

                "url": url,

                "source": original_source,

                "feed_source": source_name,

                "category": category,

                "published": published,

                "timestamp": timestamp,

                "priority": priority,

            }


            articles.append(
                article
            )


        print(
            f"✅ {source_name}: "
            f"{len(articles)} articles"
        )


    except Exception as error:

        print(
            f"❌ {source_name}: "
            f"{error}"
        )


    return articles


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicates(
    articles
):

    unique = []


    seen_urls = set()

    seen_titles = set()


    for article in articles:

        url = normalize_url(
            article.get(
                "url",
                ""
            )
        )


        title = normalize_title(
            article.get(
                "title",
                ""
            )
        )


        if (
            url
            and
            url in seen_urls
        ):

            continue


        if (
            title
            and
            title in seen_titles
        ):

            continue


        if url:
            seen_urls.add(url)


        if title:
            seen_titles.add(title)


        unique.append(
            article
        )


    return unique


# =========================================================
# REMOVE VERY SIMILAR TITLES
# =========================================================

def title_words(title):

    title = normalize_title(
        title
    )

    return set(
        title.split()
    )


def is_similar_title(
    title_a,
    title_b
):

    words_a = title_words(
        title_a
    )

    words_b = title_words(
        title_b
    )


    if not words_a or not words_b:
        return False


    intersection = (
        words_a & words_b
    )


    smaller = min(
        len(words_a),
        len(words_b)
    )


    if smaller == 0:
        return False


    similarity = (
        len(intersection)
        /
        smaller
    )


    return similarity >= 0.85


def remove_similar_titles(
    articles
):

    unique = []


    for article in articles:

        duplicate = False


        for existing in unique:

            if is_similar_title(
                article.get(
                    "title",
                    ""
                ),
                existing.get(
                    "title",
                    ""
                )
            ):

                duplicate = True

                break


        if not duplicate:

            unique.append(
                article
            )


    return unique


# =========================================================
# SORT NEWS
# =========================================================

def sort_news(
    articles
):

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


    all_articles = []


    for source in NEWS_SOURCES[
        category
    ]:

        articles = read_source(
            source,
            category
        )


        all_articles.extend(
            articles
        )


    # URL/title duplicates
    all_articles = (
        remove_duplicates(
            all_articles
        )
    )


    # Similar headlines
    all_articles = (
        remove_similar_titles(
            all_articles
        )
    )


    # Newest first
    all_articles = (
        sort_news(
            all_articles
        )
    )


    return all_articles[:limit]


# =========================================================
# GET LATEST
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


    all_articles = []


    for category in categories:

        articles = get_news(
            category,
            limit=10
        )


        all_articles.extend(
            articles
        )


    all_articles = (
        remove_duplicates(
            all_articles
        )
    )


    all_articles = (
        remove_similar_titles(
            all_articles
        )
    )


    all_articles = (
        sort_news(
            all_articles
        )
    )


    return all_articles[:limit]


# =========================================================
# BREAKING NEWS
# =========================================================

def get_breaking_news(
    category,
    minutes=15,
    limit=5
):

    articles = get_news(
        category,
        limit=30
    )


    now = datetime.now(
        timezone.utc
    ).timestamp()


    cutoff = (
        now
        -
        (
            minutes * 60
        )
    )


    breaking = []


    for article in articles:

        timestamp = article.get(
            "timestamp",
            0
        )


        if timestamp <= 0:
            continue


        if timestamp >= cutoff:

            breaking.append(
                article
            )


    return breaking[:limit]


# =========================================================
# SOURCE HEALTH CHECK
# =========================================================

def check_sources():

    print()

    print(
        "=" * 70
    )

    print(
        "🔍 KHMER NEWS 24 "
        "SOURCE HEALTH CHECK"
    )

    print(
        "=" * 70
    )


    total_sources = 0

    working_sources = 0

    empty_sources = 0

    failed_sources = 0


    for category, sources in (
        NEWS_SOURCES.items()
    ):

        print()

        print(
            f"📂 {category.upper()}"
        )

        print(
            "-" * 50
        )


        for source in sources:

            total_sources += 1


            try:

                feed = feedparser.parse(
                    source["url"]
                )


                count = len(
                    feed.entries
                )


                if count > 0:

                    working_sources += 1


                    print(
                        f"✅ "
                        f"{source['name']}: "
                        f"{count}"
                    )


                else:

                    empty_sources += 1


                    print(
                        f"⚠️ "
                        f"{source['name']}: "
                        f"EMPTY"
                    )


            except Exception as error:

                failed_sources += 1


                print(
                    f"❌ "
                    f"{source['name']}: "
                    f"{error}"
                )


    print()

    print(
        "=" * 70
    )

    print(
        "📊 SOURCE SUMMARY"
    )

    print(
        "=" * 70
    )


    print(
        f"Total sources: "
        f"{total_sources}"
    )


    print(
        f"Working: "
        f"{working_sources}"
    )


    print(
        f"Empty: "
        f"{empty_sources}"
    )


    print(
        f"Failed: "
        f"{failed_sources}"
    )


    print()

    print(
        "✅ SOURCE CHECK FINISHED"
    )

    print()


# =========================================================
# TEST CATEGORY
# =========================================================

def test_category(
    category,
    limit=5
):

    print()

    print(
        "=" * 70
    )

    print(
        f"🧪 TEST: "
        f"{category.upper()}"
    )

    print(
        "=" * 70
    )


    articles = get_news(
        category,
        limit
    )


    if not articles:

        print(
            "⚠️ No articles found."
        )

        return


    for index, article in enumerate(
        articles,
        1
    ):

        print()

        print(
            f"#{index}"
        )


        print(
            "📰 "
            +
            article.get(
                "title",
                ""
            )
        )


        print(
            "📌 Source: "
            +
            article.get(
                "source",
                ""
            )
        )


        print(
            "📡 Feed: "
            +
            article.get(
                "feed_source",
                ""
            )
        )


        print(
            "🕐 Published: "
            +
            article.get(
                "published",
                ""
            )
        )


        print(
            "🔗 "
            +
            article.get(
                "url",
                ""
            )
        )


    print()

    print(
        f"✅ Found "
        f"{len(articles)} articles"
    )


# =========================================================
# LOCAL TEST
# =========================================================

if __name__ == "__main__":

    print()

    print(
        "📰 KHMER NEWS 24"
    )

    print(
        "NEWS SYSTEM TEST"
    )

    print()


    check_sources()


    print(
        "🧪 TESTING CAMBODIA"
    )


    test_category(
        "cambodia",
        10
    )