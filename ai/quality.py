"""
Khmer News 24 - V2
AI Output Quality Checker
"""

import re


# ============================================================
# SCRIPT DETECTION
# ============================================================

def has_thai(text):
    return bool(re.search(r"[\u0E00-\u0E7F]", text or ""))


def has_lao(text):
    return bool(re.search(r"[\u0E80-\u0EFF]", text or ""))


def has_burmese(text):
    return bool(re.search(r"[\u1000-\u109F]", text or ""))


def has_khmer(text):
    return bool(re.search(r"[\u1780-\u17FF]", text or ""))


def has_georgian(text):
    return bool(re.search(r"[\u10A0-\u10FF]", text or ""))


def has_greek(text):
    return bool(re.search(r"[\u0370-\u03FF]", text or ""))


def has_cyrillic(text):
    return bool(re.search(r"[\u0400-\u04FF]", text or ""))


def has_arabic(text):
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def clean_text(text):
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    return re.sub(r"\s+", " ", text).strip()


# ============================================================
# SCRIPT COUNTS
# ============================================================

def get_script_counts(text):
    text = text or ""

    khmer_count = len(
        re.findall(r"[\u1780-\u17FF]", text)
    )

    latin_count = len(
        re.findall(r"[A-Za-z]", text)
    )

    unwanted_count = (
        len(re.findall(r"[\u0E00-\u0E7F]", text)) +   # Thai
        len(re.findall(r"[\u0E80-\u0EFF]", text)) +   # Lao
        len(re.findall(r"[\u1000-\u109F]", text)) +   # Burmese
        len(re.findall(r"[\u10A0-\u10FF]", text)) +   # Georgian
        len(re.findall(r"[\u0370-\u03FF]", text)) +   # Greek
        len(re.findall(r"[\u0400-\u04FF]", text)) +   # Cyrillic
        len(re.findall(r"[\u0600-\u06FF]", text))     # Arabic
    )

    return khmer_count, latin_count, unwanted_count


def khmer_ratio(text):
    khmer_count, latin_count, unwanted_count = get_script_counts(text)

    total = (
        khmer_count
        + latin_count
        + unwanted_count
    )

    if total == 0:
        return 0.0

    return (khmer_count / total) * 100


def check_khmer_ratio(text, minimum=55.0):
    if not text:
        return False

    khmer_count, latin_count, unwanted_count = get_script_counts(text)

    # Require enough actual Khmer characters.
    if khmer_count < 20:
        return False

    # Any clearly unwanted writing system invalidates the output.
    if unwanted_count > 0:
        return False

    total = khmer_count + latin_count

    if total == 0:
        return False

    return (khmer_count / total) * 100 >= minimum


# ============================================================
# LENGTH / SUMMARY
# ============================================================

def check_length(text, minimum=50):
    text = clean_text(text)

    return bool(text) and len(text) >= minimum


def get_article_summary(article):
    if not isinstance(article, dict):
        return clean_text(article)

    for field in (
        "khmer_summary",
        "ai_summary",
        "summary",
    ):
        summary = article.get(field, "")

        if summary:
            return clean_text(summary)

    return ""


# ============================================================
# QUALITY CHECK
# ============================================================

def check_quality(text):
    issues = []

    text = clean_text(text)

    if not text:
        issues.append("Empty summary")

    if text and not check_length(text):
        issues.append("Summary is too short")

    if text and not has_khmer(text):
        issues.append("No Khmer characters detected")

    script_checks = [
        (has_thai(text), "Thai characters detected"),
        (has_lao(text), "Lao characters detected"),
        (has_burmese(text), "Burmese characters detected"),
        (has_georgian(text), "Georgian characters detected"),
        (has_greek(text), "Greek characters detected"),
        (has_cyrillic(text), "Cyrillic characters detected"),
        (has_arabic(text), "Arabic characters detected"),
    ]

    for detected, issue in script_checks:
        if detected:
            issues.append(issue)

    if text and has_khmer(text):
        if not check_khmer_ratio(text):
            issues.append("Khmer character ratio is too low")

    score = 100

    for issue in issues:
        if issue == "Empty summary":
            score -= 100

        elif issue == "Summary is too short":
            score -= 25

        elif issue == "No Khmer characters detected":
            score -= 50

        elif issue in {
            "Thai characters detected",
            "Lao characters detected",
            "Burmese characters detected",
            "Georgian characters detected",
            "Greek characters detected",
            "Cyrillic characters detected",
            "Arabic characters detected",
        }:
            score -= 40

        elif issue == "Khmer character ratio is too low":
            score -= 30

    score = max(
        0,
        min(100, score)
    )

    unwanted_present = any(
        [
            has_thai(text),
            has_lao(text),
            has_burmese(text),
            has_georgian(text),
            has_greek(text),
            has_cyrillic(text),
            has_arabic(text),
        ]
    )

    valid = (
        score >= 70
        and has_khmer(text)
        and not unwanted_present
        and check_length(text)
        and check_khmer_ratio(text)
    )

    return {
        "valid": valid,
        "score": score,
        "issues": issues,
    }


# ============================================================
# ARTICLE VALIDATION
# ============================================================

def validate_summary(article):
    if not isinstance(article, dict):
        return {
            "quality_valid": False,
            "quality_score": 0,
            "quality_issues": [
                "Invalid article format"
            ],
        }

    article = article.copy()

    summary = get_article_summary(article)

    result = check_quality(summary)

    article["quality_valid"] = result["valid"]
    article["quality_score"] = result["score"]
    article["quality_issues"] = result["issues"]

    if summary:
        article["khmer_summary"] = summary

    return article


def filter_quality_articles(
    articles,
    min_score=70
):
    valid_articles = []

    if not articles:
        return valid_articles

    for article in articles:
        checked = validate_summary(article)

        if (
            checked.get("quality_valid", False)
            and checked.get("quality_score", 0) >= min_score
        ):
            valid_articles.append(checked)

    return valid_articles


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    good = """
    ថ្នាក់ដឹកនាំ G7 បានប្រកាសវិធានការណ៍បន្ទាន់
    បន្ទាប់ពីមានការរំខានយ៉ាងខ្លាំងលើទីផ្សារប្រេងសកល
    និងការផ្គត់ផ្គង់ថាមពល។
    """

    bad = """
    ថ្នាក់ដឹកនាំ G7 បានពិភាក្សាអំពីទីផ្សារប្រេង
    និងភាព არასწორი នៅក្នុងការផ្គត់ផ្គង់ថាមពលសកល។
    """

    print("GOOD:", check_quality(good))
    print("BAD:", check_quality(bad))
