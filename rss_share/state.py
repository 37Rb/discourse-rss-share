import json
from pathlib import Path
from typing import Set


def data_dir(base_dir: Path, config_stem: str) -> Path:
    return base_dir / "data" / config_stem


def state_path(base_dir: Path, config_stem: str) -> Path:
    return data_dir(base_dir, config_stem) / "posted_urls.json"


def log_path(base_dir: Path, config_stem: str) -> Path:
    return data_dir(base_dir, config_stem) / "rss-share.log"


def load_state(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    with path.open() as f:
        data = json.load(f)
    return set(data.get("posted_urls", []))


def save_state(path: Path, posted_urls: Set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump({"posted_urls": sorted(posted_urls)}, f, indent=2)
