"""
KHMER NEWS 24
AI Package
"""

from .processor import (
    process_news_batch,
    process_single_news,
)

__all__ = [
    "process_news_batch",
    "process_single_news",
]