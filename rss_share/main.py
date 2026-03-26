import argparse
import logging
import sys
from pathlib import Path

from .config import load_config
from .discourse import DiscourseError, build_topic_body, post_topic
from .feed import fetch_feed
from .state import load_state, log_path, save_state, state_path
from .teaser import fetch_article_teaser

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


class _MaxLevelFilter(logging.Filter):
    """Passes only records strictly below a given level (used to keep errors off stdout)."""

    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self.max_level


def setup_logging(file_path: Path, verbose: bool) -> logging.Logger:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("rss_share")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Always write INFO+ to the log file
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Always write ERROR+ to stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    # With --verbose, write INFO (but not ERROR+) to stdout as well
    if verbose:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.addFilter(_MaxLevelFilter(logging.ERROR))
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    return logger


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check an RSS feed and post one new item to Discourse as a topic.\n"
            "Designed to be run periodically by cron. On each run, only the oldest\n"
            "unposted item is published; subsequent items are left for future runs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  uv run python -m rss_share.main configs/my-feed.yml\n"
            "  uv run python -m rss_share.main --verbose configs/my-feed.yml\n"
            "  uv run python -m rss_share.main --dry-run configs/my-feed.yml\n"
            "\n"
            "state and logs are written to data/<config-stem>/ next to this script."
        ),
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the YAML config file (see config.example.yml).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print progress to stdout. By default only errors are printed to stderr.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Fetch the feed and show what would be posted, but do not call the\n"
            "Discourse API and do not update the posted-URLs state file. Implies --verbose."
        ),
    )
    args = parser.parse_args()

    config_path: Path = args.config.resolve()
    verbose: bool = args.verbose or args.dry_run

    # Base dir is the repo root: configs always live in <root>/configs/
    base_dir = config_path.parent.parent

    log = setup_logging(log_path(base_dir, config_path.stem), verbose)
    log.info("--- Run started: %s%s ---", config_path.name, " [DRY RUN]" if args.dry_run else "")

    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError) as e:
        log.error("Config error: %s", e)
        sys.exit(1)

    s_path = state_path(base_dir, config_path.stem)
    posted_urls = load_state(s_path)

    try:
        items = fetch_feed(config.feed_url)
    except RuntimeError as e:
        log.error("Feed error: %s", e)
        sys.exit(1)

    unposted = [item for item in items if item.link not in posted_urls]

    if not unposted:
        log.info("No new items to post.")
        return

    item = unposted[0]
    remaining_after = len(unposted) - 1

    try:
        teaser = fetch_article_teaser(item.link)
    except Exception as e:
        log.error("Failed to fetch article for teaser (%s): %s", item.link, e)
        sys.exit(1)
    body = build_topic_body(item.link, teaser)

    if args.dry_run:
        log.info("DRY RUN — would post: %s", item.title)
        log.info("URL:    %s", item.link)
        log.info("Body:\n%s", body)
        if remaining_after > 0:
            log.info("%d item(s) would remain queued.", remaining_after)
        return

    try:
        result = post_topic(
            base_url=config.discourse_url,
            api_key=config.discourse_api_key,
            api_username=config.discourse_api_username,
            category_id=config.category_id,
            tags=config.tags,
            title=item.title,
            body=body,
        )
    except DiscourseError as e:
        log.error("Failed to post to Discourse: %s", e)
        sys.exit(1)

    topic_url = (
        f"{config.discourse_url}/t/{result.get('topic_slug')}/{result.get('topic_id')}"
    )
    log.info("Posted: %s", item.title)
    log.info("URL:    %s", item.link)
    log.info("Topic:  %s", topic_url)

    posted_urls.add(item.link)
    save_state(s_path, posted_urls)

    if remaining_after > 0:
        log.info("%d item(s) remain queued.", remaining_after)
    else:
        log.info("Queue is now empty.")


if __name__ == "__main__":
    main()
