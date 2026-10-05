import asyncio

from publisher.telegram import publish_news


TEST_ARTICLE = {
    "title": "🧪 តេស្តប្រព័ន្ធ Khmer News 24",
    "khmer_summary": (
        "នេះជាសារសាកល្បងសម្រាប់ពិនិត្យថា "
        "ប្រព័ន្ធរៀបចំព័ត៌មាន និង Telegram Publisher "
        "អាចផ្ញើព័ត៌មានទៅកាន់ Telegram Channel បានត្រឹមត្រូវ។"
    ),
    "source": "Khmer News 24 Test",
    "link": "https://example.com/test",
    "image_url": "",
    "ai_score": 90,
    "quality_score": 100,
}


async def main():
    print("=" * 40)
    print("🧪 TELEGRAM PIPELINE TEST")
    print("=" * 40)

    print("📰 Article prepared")
    print("📝 Title:", TEST_ARTICLE["title"])
    print("🤖 AI Score:", TEST_ARTICLE["ai_score"])
    print("✅ Quality Score:", TEST_ARTICLE["quality_score"])

    print("\n📤 Sending to Telegram...")

    try:
        result = await publish_news(TEST_ARTICLE)

        print("\n📋 Result:")
        print(result)

        print("\n" + "=" * 40)
        print("✅ TELEGRAM PIPELINE TEST PASSED")
        print("=" * 40)

    except Exception as e:
        print("\n" + "=" * 40)
        print("❌ TELEGRAM PIPELINE TEST FAILED")
        print("=" * 40)
        print("Error:", e)


if __name__ == "__main__":
    asyncio.run(main())