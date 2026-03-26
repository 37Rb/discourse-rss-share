from typing import List

import requests


class DiscourseError(Exception):
    pass


def post_topic(
    base_url: str,
    api_key: str,
    api_username: str,
    category_id: int,
    tags: List[str],
    title: str,
    body: str,
) -> dict:
    url = f"{base_url}/posts.json"
    headers = {
        "Api-Key": api_key,
        "Api-Username": api_username,
        "Content-Type": "application/json",
    }
    payload = {
        "title": title,
        "raw": body,
        "category": category_id,
    }
    if tags:
        payload["tags"] = tags

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if not response.ok:
        raise DiscourseError(
            f"Discourse API error {response.status_code}: {response.text}"
        )

    return response.json()


def build_topic_body(item_url: str, teaser: str) -> str:
    return f"{item_url}\n\n{teaser}\n\n[Read more]({item_url})"
