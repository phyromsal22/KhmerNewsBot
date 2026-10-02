import sqlite3
from datetime import datetime


DB_NAME = "news.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            source TEXT,
            category TEXT,
            sent_at TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("✅ Database initialized")


# =========================================================
# CHECK NEWS
# =========================================================

def news_already_sent(url):

    if not url:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM sent_news
        WHERE url = ?
        """,
        (url,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


# =========================================================
# SAVE NEWS
# =========================================================

def save_sent_news(
    url,
    title,
    source,
    category
):

    if not url:
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO sent_news
            (url, title, source, category, sent_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                url,
                title,
                source,
                category,
                datetime.now().isoformat()
            )
        )

        conn.commit()

    except sqlite3.IntegrityError:

        pass

    finally:

        conn.close()


# =========================================================
# COUNT SENT NEWS
# =========================================================

def get_sent_news_count():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM sent_news"
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return 0


# =========================================================
# COUNT BY CATEGORY
# =========================================================

def get_category_count(category):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sent_news
        WHERE category = ?
        """,
        (category,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return 0


# =========================================================
# GET LATEST SENT NEWS
# =========================================================

def get_latest_sent_news(limit=5):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            title,
            source,
            category,
            sent_at
        FROM sent_news
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    results = cursor.fetchall()

    conn.close()

    return results