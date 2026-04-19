import html
import re

import requests
from bs4 import BeautifulSoup

TEASER_WORD_COUNT = 55
TEASER_MAX_CHARS = 500


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _first_n_words(text: str, n: int) -> str:
    words = text.split()
    if len(words) <= n:
        return " ".join(words)
    return " ".join(words[:n]) + "..."


def fetch_article_teaser(url: str, word_count: int = TEASER_WORD_COUNT) -> str:
    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    for tag in soup.find_all(class_="c-post-byline"):
        tag.decompose()

    # Prefer <article> or <main>, fall back to all <p> tags
    container = soup.find("article") or soup.find("main")
    if container:
        paragraphs = container.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    text = " ".join(
        p.get_text(" ", strip=True)
        for p in paragraphs
        if len(p.get_text(" ", strip=True).split()) >= 8
    )
    text = re.sub(r"\s+", " ", text).strip()

    return _first_n_words(text, word_count)


def make_teaser(raw_content: str, max_chars: int = TEASER_MAX_CHARS) -> str:
    plain = _strip_html(raw_content)
    if len(plain) <= max_chars:
        return plain

    truncated = plain[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        truncated = truncated[:last_space]

    return truncated + "..."
