"""
KHMER NEWS 24
AI Processor Compatibility Layer
"""

from .filter import filter_article
from .summary import (
    generate_summary,
    extract_khmer_title,
)
from .quality import check_quality


# ============================================================
# PROCESS NEWS BATCH
# ============================================================

def process_news_batch(news_list):

    if not news_list:
        return []

    results = []

    for index, article in enumerate(news_list, start=1):

        try:

            # ==================================================
            # ARTICLE DATA
            # ==================================================

            title = article.get(
                "title",
                ""
            )

            source = article.get(
                "source",
                ""
            )

            category = article.get(
                "category",
                ""
            )

            # ==================================================
            # AI FILTER
            # ==================================================

            try:

                filter_result = filter_article(
                    article
                )

            except Exception as error:

                print(
                    f"⚠️ AI filter error: {error}"
                )

                filter_result = {
                    "important": True,
                    "score": 60,
                    "reason": "Fallback"
                }

            # ==================================================
            # FILTER RESULT
            # ==================================================

            if isinstance(
                filter_result,
                dict
            ):

                ai_score = filter_result.get(
                    "score",
                    60
                )

                important = filter_result.get(
                    "important",
                    True
                )

            else:

                ai_score = 60
                important = True

            # ==================================================
            # AI KHMER SUMMARY
            # ==================================================

            try:

                summary_result = generate_summary(
                    article
                )

            except Exception as error:

                print(
                    f"⚠️ AI summary error: {error}"
                )

                summary_result = ""

            # ==================================================
            # KHMER TITLE + SUMMARY
            # ==================================================

            khmer_title = ""
            khmer_summary = ""

            # --------------------------------------------------
            # CURRENT summary.py RETURNS STRING
            # --------------------------------------------------

            if isinstance(
                summary_result,
                str
            ):

                khmer_summary = (
                    summary_result.strip()
                )

                # Extract Khmer title from AI output
                try:

                    khmer_title = (
                        extract_khmer_title(
                            khmer_summary
                        )
                    )

                except Exception as error:

                    print(
                        "⚠️ Khmer title extraction error: "
                        f"{error}"
                    )

                    khmer_title = ""

            # --------------------------------------------------
            # SUPPORT DICTIONARY RESULT
            # --------------------------------------------------

            elif isinstance(
                summary_result,
                dict
            ):

                khmer_title = (
                    summary_result.get(
                        "khmer_title",
                        summary_result.get(
                            "title_kh",
                            ""
                        )
                    )
                )

                khmer_summary = (
                    summary_result.get(
                        "khmer_summary",
                        summary_result.get(
                            "summary_kh",
                            summary_result.get(
                                "summary",
                                ""
                            )
                        )
                    )
                )

            # ==================================================
            # CLEAN VALUES
            # ==================================================

            if not isinstance(
                khmer_title,
                str
            ):

                khmer_title = ""

            if not isinstance(
                khmer_summary,
                str
            ):

                khmer_summary = ""

            khmer_title = khmer_title.strip()
            khmer_summary = khmer_summary.strip()

            # ==================================================
            # QUALITY CHECK
            # ==================================================

            try:

                quality_result = check_quality(
                    khmer_summary
                )

            except Exception as error:

                print(
                    f"⚠️ AI quality error: {error}"
                )

                quality_result = {
                    "valid": False,
                    "score": 0
                }

            # ==================================================
            # QUALITY RESULT
            # ==================================================

            if isinstance(
                quality_result,
                dict
            ):

                quality_score = (
                    quality_result.get(
                        "score",
                        0
                    )
                )

                quality_valid = (
                    quality_result.get(
                        "valid",
                        False
                    )
                )

            else:

                quality_score = 0
                quality_valid = False

            # ==================================================
            # LOG
            # ==================================================

            if khmer_title:

                print(
                    f"📰 Khmer Title: "
                    f"{khmer_title}"
                )

            else:

                print(
                    "⚠️ Khmer title is empty"
                )

            if khmer_summary:

                print(
                    "📝 Khmer summary ready"
                )

            else:

                print(
                    "⚠️ Khmer summary is empty"
                )

            # ==================================================
            # FINAL RESULT
            #
            # IMPORTANT:
            # bot.py uses:
            #
            # title_kh
            # summary_kh
            # ==================================================

            result = {

                "id": index,

                # Original title
                "title": title,

                # Khmer title
                "title_kh": khmer_title,

                # Source
                "source": source,

                # Category
                "category": category,

                # AI filter
                "important": important,

                "ai_score": ai_score,

                # Khmer summary
                "summary": khmer_summary,

                "summary_kh": khmer_summary,

                # Compatibility fields
                "khmer_title": khmer_title,

                "khmer_summary": khmer_summary,

                # Quality
                "quality_score": quality_score,

                "quality_valid": quality_valid,
            }

            results.append(
                result
            )

        # ======================================================
        # ARTICLE ERROR
        # ======================================================

        except Exception as error:

            print(
                f"❌ AI processing error "
                f"[{index}]: {error}"
            )

            results.append({

                "id": index,

                "title": article.get(
                    "title",
                    ""
                ),

                "title_kh": "",

                "source": article.get(
                    "source",
                    ""
                ),

                "category": article.get(
                    "category",
                    ""
                ),

                "important": True,

                "ai_score": 60,

                "summary": "",

                "summary_kh": "",

                "khmer_title": "",

                "khmer_summary": "",

                "quality_score": 0,

                "quality_valid": False,
            })

    return results


# ============================================================
# PROCESS SINGLE NEWS
# ============================================================

def process_single_news(news):

    results = process_news_batch(
        [news]
    )

    if not results:
        return None

    return results[0]