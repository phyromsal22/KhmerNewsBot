from news.collector import collect_from_sources
from news.sources import get_sources
from ai.filter import filter_article
from ai.summary import generate_summary
from ai.quality import check_quality


print("=" * 50)
print("⚽ FOOTBALL AI TEST")
print("=" * 50)

# 1. Collect football news
sources = get_sources("football")

articles = collect_from_sources(
    sources,
    category="football",
    limit=1
)

if not articles:
    print("❌ No football article found")
    raise SystemExit

article = articles[0]

print("\n📰 ARTICLE")
print("Title:", article.get("title", ""))
print("Source:", article.get("source", ""))
print("Link:", article.get("link", ""))


# 2. AI Filter
print("\n[1/3] 🤖 AI FILTER")

filter_result = filter_article(article)

print("Important:", filter_result.get("important"))
print("Score:", filter_result.get("score"))
print("Reason:", filter_result.get("reason"))


if not filter_result.get("important"):
    print("\n⚠️ Article rejected by AI filter")
    raise SystemExit


# 3. Khmer Summary
print("\n[2/3] 🇰🇭 KHMER SUMMARY")

summary = generate_summary(article)

print("\n" + summary)


# 4. Quality Check
print("\n[3/3] 🔍 QUALITY CHECK")

quality = check_quality(summary)

print("Valid:", quality.get("valid"))
print("Score:", quality.get("score"))
print("Issues:", quality.get("issues"))


# Final result
print("\n" + "=" * 50)

if quality.get("valid"):
    print("🎉 FOOTBALL AI TEST PASSED")
else:
    print("❌ FOOTBALL AI TEST FAILED")

print("=" * 50)