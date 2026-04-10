from dataclasses import dataclass
from typing import List

import feedparser


@dataclass
class FeedItem:
    id: str
    title: str
    link: str
    content: str


def fetch_feed(url: str) -> List[FeedItem]:
    parsed = feedparser.parse(url, request_headers={
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })

    if parsed.bozo and parsed.bozo_exception and not parsed.entries:
        raise RuntimeError(
            f"Failed to parse feed {url!r}: {parsed.bozo_exception}"
        )

    items = []
    for entry in parsed.entries:
        item_id = entry.get("id") or entry.get("link")
        if not item_id:
            continue

        if entry.get("content"):
            content = entry.content[0].value
        else:
            content = entry.get("summary", "")

        items.append(FeedItem(
            id=item_id,
            title=entry.get("title", "(no title)"),
            link=entry.get("link", item_id),
            content=content,
        ))

    # feedparser returns newest-first; reverse to get oldest-first
    items.reverse()
    return items
