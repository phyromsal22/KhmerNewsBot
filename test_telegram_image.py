import asyncio

from publisher.telegram import publish_news


TEST_ARTICLE = {
    "khmer_title": "🧪 តេស្តព័ត៌មានជាមួយរូបភាព BBC",
    "khmer_summary": (
        "នេះជាការធ្វើតេស្តប្រព័ន្ធ Telegram Publisher "
        "ដើម្បីពិនិត្យថា Bot អាចផ្ញើព័ត៌មានជាមួយរូបភាពបានត្រឹមត្រូវ។"
    ),
    "source": "BBC News",
    "link": "https://www.bbc.co.uk/news/articles/ckreyjzzzywqo",
    "ai_score": 95,
    "image_url": (
        "https://ichef.bbci.co.uk/ace/standard/240/"
        "cpsprodpb/a1e6/live/c07550e0-bfd1-11f1-a000-7b944ef8fdad.jpg"
    ),
}


async def main():

    print("=" * 60)
    print("KHMER NEWS 24")
    print("V2.7.3 TELEGRAM IMAGE TEST")
    print("=" * 60)

    print()
    print("Sending test image to Telegram...")

    result = await publish_news(TEST_ARTICLE)

    print()
    print("=" * 60)

    if result:
        print("TEST PASSED")
        print("Telegram publishing successful.")
    else:
        print("TEST FAILED")
        print("Telegram publishing failed.")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())