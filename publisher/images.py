"""
Khmer News 24 - V2
Image Utilities

V2.7.1
Extract images from RSS articles.

Priority:
1. media_content
2. media_thumbnail
3. enclosures
4. image field
5. HTML content
"""

import re
from html import unescape
from urllib.parse import urlparse


# ============================================================
# IMAGE URL VALIDATION
# ============================================================

IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
)


def is_valid_image_url(url):
    """
    Check whether a URL looks like an image URL.
    """

    if not url:
        return False

    url = url.strip()

    if not url.startswith(
        ("http://", "https://")
    ):
        return False

    parsed = urlparse(url)

    if not parsed.netloc:
        return False

    path = parsed.path.lower()

    # Direct image extension
    if path.endswith(IMAGE_EXTENSIONS):
        return True

    # Some CDN URLs have no extension.
    # Allow common image query parameters.
    query = parsed.query.lower()

    image_keywords = [
        "image",
        "img",
        "photo",
        "picture",
        "media",
    ]

    return any(
        keyword in query
        for keyword in image_keywords
    )


# ============================================================
# CLEAN IMAGE URL
# ============================================================

def clean_image_url(url):
    """
    Clean an image URL.
    """

    if not url:
        return ""

    url = unescape(
        str(url)
    ).strip()

    # Remove surrounding quotes
    url = url.strip(
        "\"'"
    )

    return url


# ============================================================
# EXTRACT FROM RSS MEDIA
# ============================================================

def extract_media_content(entry):
    """
    Extract image from RSS media_content.
    """

    media_content = entry.get(
        "media_content",
        []
    )

    if not media_content:
        return ""

    if isinstance(
        media_content,
        dict
    ):
        media_content = [
            media_content
        ]

    for media in media_content:

        if not isinstance(
            media,
            dict
        ):
            continue

        url = (
            media.get("url")
            or media.get("href")
            or ""
        )

        url = clean_image_url(
            url
        )

        if is_valid_image_url(
            url
        ):
            return url

    return ""


# ============================================================
# EXTRACT FROM RSS THUMBNAIL
# ============================================================

def extract_media_thumbnail(entry):
    """
    Extract image from RSS media_thumbnail.
    """

    thumbnails = entry.get(
        "media_thumbnail",
        []
    )

    if not thumbnails:
        return ""

    if isinstance(
        thumbnails,
        dict
    ):
        thumbnails = [
            thumbnails
        ]

    for thumbnail in thumbnails:

        if not isinstance(
            thumbnail,
            dict
        ):
            continue

        url = (
            thumbnail.get("url")
            or thumbnail.get("href")
            or ""
        )

        url = clean_image_url(
            url
        )

        if is_valid_image_url(
            url
        ):
            return url

    return ""


# ============================================================
# EXTRACT FROM ENCLOSURES
# ============================================================

def extract_enclosure_image(entry):
    """
    Extract image from RSS enclosure.
    """

    enclosures = entry.get(
        "enclosures",
        []
    )

    if not enclosures:
        return ""

    for enclosure in enclosures:

        if not isinstance(
            enclosure,
            dict
        ):
            continue

        url = clean_image_url(
            enclosure.get(
                "href"
            )
            or enclosure.get(
                "url"
            )
            or ""
        )

        media_type = str(
            enclosure.get(
                "type",
                ""
            )
        ).lower()

        if (
            media_type.startswith(
                "image/"
            )
            and url
        ):
            return url

        if is_valid_image_url(
            url
        ):
            return url

    return ""


# ============================================================
# EXTRACT IMAGE FIELD
# ============================================================

def extract_image_field(entry):
    """
    Extract image from common RSS fields.
    """

    fields = [
        "image",
        "image_url",
        "thumbnail",
    ]

    for field in fields:

        value = entry.get(
            field
        )

        if isinstance(
            value,
            dict
        ):
            value = (
                value.get("url")
                or value.get("href")
                or ""
            )

        value = clean_image_url(
            value
        )

        if is_valid_image_url(
            value
        ):
            return value

    return ""


# ============================================================
# EXTRACT IMAGE FROM HTML
# ============================================================

def extract_image_from_html(html):
    """
    Find the first image URL from HTML.
    """

    if not html:
        return ""

    html = unescape(
        str(html)
    )

    patterns = [
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r'<img[^>]+data-src=["\']([^"\']+)["\']',
        r'<img[^>]+data-original=["\']([^"\']+)["\']',
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            flags=re.IGNORECASE
        )

        for url in matches:

            url = clean_image_url(
                url
            )

            if is_valid_image_url(
                url
            ):
                return url

    return ""


# ============================================================
# MAIN IMAGE EXTRACTION
# ============================================================

def extract_image_from_entry(entry):
    """
    Extract the best available image from an RSS entry.

    Priority:
        media_content
        media_thumbnail
        enclosure
        image field
        HTML
    """

    if not entry:
        return ""

    # 1. media_content
    image_url = extract_media_content(
        entry
    )

    if image_url:
        return image_url

    # 2. media_thumbnail
    image_url = extract_media_thumbnail(
        entry
    )

    if image_url:
        return image_url

    # 3. enclosure
    image_url = extract_enclosure_image(
        entry
    )

    if image_url:
        return image_url

    # 4. image field
    image_url = extract_image_field(
        entry
    )

    if image_url:
        return image_url

    # 5. HTML content
    html_fields = [
        "summary",
        "description",
        "content",
    ]

    for field in html_fields:

        value = entry.get(
            field,
            ""
        )

        if isinstance(
            value,
            list
        ):
            for item in value:

                if isinstance(
                    item,
                    dict
                ):
                    value = item.get(
                        "value",
                        ""
                    )
                    break

        image_url = extract_image_from_html(
            value
        )

        if image_url:
            return image_url

    return ""


# ============================================================
# ADD IMAGE TO ARTICLE
# ============================================================

def add_image_to_article(
    article,
    entry
):
    """
    Add image_url to an article.

    Does not overwrite an existing image.
    """

    if not article:
        return article

    article = article.copy()

    existing = article.get(
        "image_url",
        ""
    )

    if existing:
        return article

    image_url = extract_image_from_entry(
        entry
    )

    article["image_url"] = (
        image_url
    )

    return article


# ============================================================
# SIMPLE ARTICLE IMAGE HELPER
# ============================================================

def get_image_url(article):
    """
    Get image URL from an article.
    """

    if not article:
        return ""

    return clean_image_url(
        article.get(
            "image_url",
            ""
        )
    )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("🇰🇭 KHMER NEWS 24")
    print("V2.7.1 IMAGE SYSTEM TEST")
    print("=" * 60)

    test_entry = {
        "title": "Test News",

        "media_content": [
            {
                "url": (
                    "https://example.com/"
                    "news-image.jpg"
                ),
                "type": "image/jpeg",
            }
        ],
    }

    image_url = extract_image_from_entry(
        test_entry
    )

    if image_url:

        print(
            "✅ Image found:"
        )

        print(
            image_url
        )

    else:

        print(
            "❌ No image found"
        )

    article = {
        "title": "Test News",
        "link": "https://example.com/news",
    }

    updated = add_image_to_article(
        article,
        test_entry
    )

    print("\n📦 Article:")

    print(
        updated
    )

    print(
        "\n✅ Image system test complete"
    )