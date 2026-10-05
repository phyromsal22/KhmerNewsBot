"""
Khmer News 24 - V2
News Database
"""

import sqlite3
import os
from datetime import datetime, timezone


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "data",
    "news.db"
)


# ============================================================
# CONNECTION
# ============================================================

def get_connection():
    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_news_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE,
            source TEXT,
            category TEXT,
            published_at TEXT,
            collected_at TEXT,
            ai_score INTEGER DEFAULT 0,
            quality_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'collected',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            image_url TEXT
        )
        """
    )

    # --------------------------------------------------------
    # DATABASE MIGRATION
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(news)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "updated_at" not in columns:
        cursor.execute(
            """
            ALTER TABLE news
            ADD COLUMN updated_at TEXT
            """
        )
        print("✅ Added missing column: updated_at")

    if "image_url" not in columns:
        cursor.execute(
            """
            ALTER TABLE news
            ADD COLUMN image_url TEXT
            """
        )
        print("✅ Added missing column: image_url")

    connection.commit()
    connection.close()

    print("✅ News database initialized")


# ============================================================
# CHECK EXISTING NEWS
# ============================================================

def news_exists(link):

    if not link:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM news
        WHERE link = ?
        LIMIT 1
        """,
        (link,)
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


# ============================================================
# SAVE NEWS
# ============================================================

def save_news(article, status="collected"):

    link = article.get(
        "link",
        ""
    ).strip()

    if not link:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    image_url = article.get(
        "image_url",
        ""
    )

    try:

        cursor.execute(
            """
            INSERT INTO news (
                title,
                link,
                source,
                category,
                published_at,
                collected_at,
                ai_score,
                quality_score,
                status,
                created_at,
                updated_at,
                image_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article.get("title", ""),
                link,
                article.get("source", ""),
                article.get("category", ""),
                article.get(
                    "published",
                    article.get("published_at", "")
                ),
                article.get("collected_at", ""),
                article.get("ai_score", 0),
                article.get("quality_score", 0),
                status,
                now,
                now,
                image_url
            )
        )

        connection.commit()

        return True

    except sqlite3.IntegrityError:

        connection.rollback()

        return False

    except Exception as e:

        connection.rollback()

        print(
            f"❌ Save news error: {e}"
        )

        return False

    finally:

        connection.close()


# ============================================================
# UPDATE NEWS STATUS
# ============================================================

def update_news_status(news_id, status):

    if not news_id:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    try:

        cursor.execute(
            """
            UPDATE news
            SET
                status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                now,
                news_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:

        connection.rollback()

        print(
            f"❌ Status update error: {e}"
        )

        return False

    finally:

        connection.close()


# ============================================================
# UPDATE AI SCORE
# ============================================================

def update_ai_score(news_id, score):

    if not news_id:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    try:

        cursor.execute(
            """
            UPDATE news
            SET
                ai_score = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                score,
                now,
                news_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:

        connection.rollback()

        print(
            f"❌ AI score update error: {e}"
        )

        return False

    finally:

        connection.close()


# ============================================================
# UPDATE QUALITY SCORE
# ============================================================

def update_quality_score(news_id, score):

    if not news_id:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    try:

        cursor.execute(
            """
            UPDATE news
            SET
                quality_score = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                score,
                now,
                news_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:

        connection.rollback()

        print(
            f"❌ Quality score update error: {e}"
        )

        return False

    finally:

        connection.close()


# ============================================================
# UPDATE IMAGE URL
# ============================================================

def update_image_url(news_id, image_url):

    if not news_id:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    try:

        cursor.execute(
            """
            UPDATE news
            SET
                image_url = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                image_url or "",
                now,
                news_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:

        connection.rollback()

        print(
            f"❌ Image URL update error: {e}"
        )

        return False

    finally:

        connection.close()


# ============================================================
# GET NEWS
# ============================================================

def get_news(news_id):

    if not news_id:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM news
        WHERE id = ?
        LIMIT 1
        """,
        (news_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row:
        return dict(row)

    return None


# ============================================================
# GET NEWS BY STATUS
# ============================================================

def get_news_by_status(status, limit=100):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM news
        WHERE status = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            status,
            limit
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# GET PUBLISHED NEWS
# ============================================================

def get_published_news(limit=20):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM news
        WHERE status = 'published'
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# GET NEWS COUNT
# ============================================================

def get_news_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM news
        """
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count


# ============================================================
# GET STATUS COUNTS
# ============================================================

def get_status_counts():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            status,
            COUNT(*) AS count
        FROM news
        GROUP BY status
        """
    )

    rows = cursor.fetchall()

    connection.close()

    result = {}

    for row in rows:
        result[row["status"]] = row["count"]

    return result


# ============================================================
# GET NEWS WITH IMAGE
# ============================================================

def get_news_with_image(limit=20):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM news
        WHERE image_url IS NOT NULL
        AND image_url != ''
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24")
    print("DATABASE TEST")
    print("=" * 60)

    init_news_table()

    print("\n📊 Status counts:")
    print(get_status_counts())

    print("\n🖼️ News with images:")

    image_news = get_news_with_image(
        limit=5
    )

    for article in image_news:

        print(
            f"ID: {article.get('id')}"
        )

        print(
            f"Title: {article.get('title', '')[:70]}"
        )

        print(
            f"Image: {article.get('image_url', '')[:100]}"
        )

        print()