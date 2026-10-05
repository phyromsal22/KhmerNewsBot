"""
KHMER NEWS 24
Database Package Compatibility Layer
"""

from database_old import (
    init_database,
    news_already_sent,
    save_sent_news,
    get_sent_news_count,
    get_category_count,
)

__all__ = [
    "init_database",
    "news_already_sent",
    "save_sent_news",
    "get_sent_news_count",
    "get_category_count",
]