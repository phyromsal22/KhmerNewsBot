import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=GEMINI_API_KEY)

# Fast model for translation and summarization
MODEL_NAME = "gemini-3.5-flash-lite"


def process_news_batch(news_list):

    if not news_list:
        return []

    articles = []

    for i, news in enumerate(news_list, start=1):

        articles.append({
            "id": i,
            "title": news.get("title", ""),
            "summary": news.get("summary", ""),
            "source": news.get("source", "")
        })

    prompt = f"""
You are the Khmer News 24 AI editor.

Translate and summarize the following news articles into natural Khmer.

IMPORTANT RULES:

1. Do not invent information.
2. Do not add facts that are not in the source.
3. Keep names, places, organizations and numbers accurate.
4. Keep the meaning of the original article.
5. If something is an allegation, clearly say:
   "បានអះអាងថា" or "តាមការរាយការណ៍".
6. Do not give your personal opinion.
7. Do not present unverified claims as confirmed facts.
8. Keep each summary short: 2-4 Khmer sentences.
9. Return ONLY valid JSON.
10. Do not use markdown.

JSON FORMAT:

[
  {{
    "id": 1,
    "title_kh": "Khmer title",
    "summary_kh": "Khmer summary"
  }}
]

NEWS:

{json.dumps(articles, ensure_ascii=False, indent=2)}
"""

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        result = response.text.strip()

        # Remove accidental markdown code fences
        if result.startswith("```"):
            result = result.replace("```json", "")
            result = result.replace("```", "")
            result = result.strip()

        data = json.loads(result)

        return data

    except Exception as error:

        print(f"❌ Gemini Error: {error}")

        return []