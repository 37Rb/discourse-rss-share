from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass
class Config:
    feed_url: str
    discourse_url: str
    discourse_api_key: str
    discourse_api_username: str
    category_id: int
    tags: List[str] = field(default_factory=list)


REQUIRED_KEYS = {
    "feed_url",
    "discourse_url",
    "discourse_api_key",
    "discourse_api_username",
    "category_id",
}


def load_config(config_path: Path) -> Config:
    with config_path.open() as f:
        data = yaml.safe_load(f)

    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"Config missing required keys: {missing}")

    return Config(
        feed_url=data["feed_url"],
        discourse_url=data["discourse_url"].rstrip("/"),
        discourse_api_key=data["discourse_api_key"],
        discourse_api_username=data["discourse_api_username"],
        category_id=int(data["category_id"]),
        tags=data.get("tags", []),
    )
