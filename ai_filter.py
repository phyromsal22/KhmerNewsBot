import os
import json
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=GEMINI_API_KEY)
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")

# Category-specific editorial thresholds.
# Cambodia gets slightly lower threshold because it is the main focus of the channel.
CATEGORY_THRESHOLDS = {
    "cambodia": 65,
    "war": 70,
    "politics": 70,
    "football": 75,
}
DEFAULT_THRESHOLD = 70

PRIORITY_ORDER = {
    "CRITICAL": 4,
    "HIGH": 3,
    "NORMAL": 2,
    "LOW": 1,
}


def get_threshold(category):
    return CATEGORY_THRESHOLDS.get(str(category or "").lower(), DEFAULT_THRESHOLD)


def _clean_json(text):
    text = (text or "").strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _normalize_title(title):
    """Normalize titles for cheap exact/near-exact duplicate detection."""
    text = str(title or "").lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^\w\u1780-\u17ff\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _local_duplicate_filter(news_list):
    """Remove exact normalized-title duplicates before spending Gemini credits."""
    unique = []
    duplicate_indexes = set()
    seen_titles = {}

    for index, article in enumerate(news_list):
        normalized = _normalize_title(article.get("title", ""))
        if normalized and normalized in seen_titles:
            duplicate_indexes.add(index)
            continue
        if normalized:
            seen_titles[normalized] = index
        unique.append(article)

    return unique, duplicate_indexes


def _prompt(articles):
    article_rules = []
    for article in articles:
        category = article.get("category", "")
        article_rules.append({
            **article,
            "auto_post_threshold": get_threshold(category),
        })

    return f"""
You are the editorial news filter for Khmer News 24.

Your ONLY job is to decide which articles are important enough for automatic posting to a public Telegram news channel.
Do not invent facts. Do not rewrite the news. Do not give political opinions or recommend political choices.

Evaluate newsworthiness using concrete editorial criteria:
- public impact: how many people may be affected
- urgency: whether people need to know now
- seriousness: safety, disasters, major government decisions, major economic changes, major public-health developments, major international events, major football events
- practical relevance to Cambodia when applicable
- source/article specificity and whether it reports a concrete event

Usually reject:
- advertisements and promotions
- generic evergreen articles
- celebrity gossip
- opinion pieces
- clickbait without a concrete event
- minor routine updates
- low-impact stories

For politics/government, judge only newsworthiness and public impact, not whether a policy or politician is good or bad.
For allegations or unverified claims, do not treat them as confirmed. They may still be newsworthy if the source clearly reports the allegation.

DUPLICATE CHECK:
- If two articles describe essentially the same event, mark the later/less useful one as duplicate=true.
- If an article is a duplicate, set important=false.
- duplicate_of should be the id of the article it duplicates, otherwise null.

PRIORITY:
- CRITICAL = urgent, major public-safety/security/disaster event or other event requiring immediate attention
- HIGH = major national/international event with substantial public impact
- NORMAL = useful important news but not urgent
- LOW = low-impact or routine news

SCORING:
Score 0-100.
The required automatic-post threshold depends on category:
- Cambodia: 65
- World: 70
- Politics: 70
- Football: 75
- Other: 70

Set important=true ONLY when score >= the threshold for that article's category AND duplicate=false AND the article is genuinely newsworthy.
Keep reason factual and very short (5-15 words).

Return ONLY valid JSON array. Keep the same id.

Format:
[
  {{"id":1,"important":true,"score":85,"priority":"HIGH","duplicate":false,"duplicate_of":null,"reason":"ប៉ះពាល់ដល់ប្រជាជនកម្ពុជាច្រើន"}}
]

ARTICLES:
{json.dumps(article_rules, ensure_ascii=False, indent=2)}
"""


def _call(model, prompt):
    response = client.models.generate_content(model=model, contents=prompt)
    return _clean_json(response.text)


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() == "true"


def _parse_priority(value):
    value = str(value or "NORMAL").strip().upper()
    return value if value in PRIORITY_ORDER else "NORMAL"


def filter_important_news(news_list, threshold=None):
    """Return (selected, rejected) with editorial metadata attached."""
    if not news_list:
        return [], []

    # Cheap local duplicate protection before using Gemini.
    unique_input, local_duplicate_indexes = _local_duplicate_filter(news_list)

    articles = []
    for i, news in enumerate(unique_input, start=1):
        articles.append({
            "id": i,
            "title": news.get("title", ""),
            "summary": news.get("summary", ""),
            "source": news.get("source", ""),
            "category": news.get("category", ""),
        })

    data = None
    prompt = _prompt(articles)

    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        if not model:
            continue
        try:
            print(f"🧠 News filter: {model}")
            parsed = json.loads(_call(model, prompt))
            if isinstance(parsed, list):
                data = parsed
                break
        except Exception as error:
            print(f"⚠️ News filter {model} failed: {error}")
            data = None

    if not isinstance(data, list):
        # Fail closed: if the editorial AI cannot evaluate an article,
        # do not auto-post it.
        return [], list(news_list)

    decisions = {}
    for item in data:
        try:
            article_id = int(item.get("id"))
            score = max(0, min(100, int(item.get("score", 0))))
            important = _parse_bool(item.get("important", False))
            duplicate = _parse_bool(item.get("duplicate", False))
            duplicate_of = item.get("duplicate_of")
            priority = _parse_priority(item.get("priority", "NORMAL"))
            reason = str(item.get("reason", ""))[:250]

            category = articles[article_id - 1].get("category", "") if 1 <= article_id <= len(articles) else ""
            required = get_threshold(category)

            decisions[article_id] = {
                "important": important and not duplicate and score >= required,
                "score": score,
                "priority": priority,
                "duplicate": duplicate,
                "duplicate_of": duplicate_of,
                "reason": reason,
            }
        except Exception:
            continue

    selected = []
    rejected = []

    # Map AI ids back to the original unique_input list.
    for i, article in enumerate(unique_input, start=1):
        decision = decisions.get(
            i,
            {
                "important": False,
                "score": 0,
                "priority": "LOW",
                "duplicate": False,
                "duplicate_of": None,
                "reason": "No valid AI decision",
            },
        )

        article_copy = dict(article)
        article_copy["importance_score"] = decision["score"]
        article_copy["importance_priority"] = decision["priority"]
        article_copy["importance_reason"] = decision["reason"]
        article_copy["is_duplicate"] = decision["duplicate"]
        article_copy["duplicate_of"] = decision["duplicate_of"]

        if decision["important"]:
            selected.append(article_copy)
        else:
            rejected.append(article_copy)

    # Add locally detected exact-title duplicates to rejected list.
    for index in sorted(local_duplicate_indexes):
        article_copy = dict(news_list[index])
        article_copy["importance_score"] = 0
        article_copy["importance_priority"] = "LOW"
        article_copy["importance_reason"] = "Duplicate headline"
        article_copy["is_duplicate"] = True
        article_copy["duplicate_of"] = None
        rejected.append(article_copy)

    return selected, rejected
