import html
import re

TEASER_MAX_CHARS = 500


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_teaser(raw_content: str, max_chars: int = TEASER_MAX_CHARS) -> str:
    plain = _strip_html(raw_content)
    if len(plain) <= max_chars:
        return plain

    truncated = plain[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        truncated = truncated[:last_space]

    return truncated + "..."
