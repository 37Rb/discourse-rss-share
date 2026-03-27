# discourse-rss-share

Monitors an RSS feed and automatically posts new articles to a Discourse forum as topics. Each run posts at most one new item — the oldest unposted entry — leaving the rest queued for subsequent runs. Designed to be called by cron.

## How it works

1. Fetches the RSS feed and collects all entries.
2. Compares entry URLs against a local state file to find unposted items.
3. For the oldest unposted item, fetches the actual article page and extracts the first 55 words of content as a teaser.
4. Creates a Discourse topic with the article title, a link, and the teaser.
5. Records the URL as posted so it won't be submitted again.

One item per run. If five new articles appeared since the last run, only the oldest is posted; the other four are queued and will be posted on subsequent runs.

## Requirements

- Python 3.9+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone <repo-url>
cd discourse-rss-share
uv sync
```

## Configuration

Copy `config.example.yml` to `configs/your-feed-name.yml` and fill in your values:

```yaml
# RSS feed to monitor
feed_url: "https://example.com/feed.rss"

# Discourse instance
discourse_url: "https://your-discourse.example.com"
discourse_api_key: "your_api_key_here"
discourse_api_username: "your_bot_username"

# Target category numeric ID (find it in Discourse admin or via /categories.json)
category_id: 5

# Optional: tags to apply to every topic (tags must already exist in Discourse)
tags:
  - rss
  - automated
```

**Getting a Discourse API key:** In your Discourse admin panel, go to Admin → API → New API Key. Create a key scoped to a specific user (the bot account) with write permissions.

**Finding a category ID:** Visit `https://your-discourse.example.com/categories.json` and look for the `id` field of your target category.

**Tags:** Any tags listed must already exist in Discourse. Tags are applied to every topic created from that feed.

## Running

```bash
uv run python -m rss_share.main configs/your-feed-name.yml
```

### Flags

`--verbose` / `-v` — Print progress to stdout. By default only errors are printed to stderr.

`--dry-run` — Fetch the feed and show what would be posted without calling the Discourse API or updating state. Implies `--verbose`. Use this to verify your config before going live.

```bash
# Preview what would be posted
uv run python -m rss_share.main --dry-run configs/your-feed-name.yml

# Run with verbose output
uv run python -m rss_share.main --verbose configs/your-feed-name.yml
```

## Monitoring multiple feeds

Each config file is independent. To monitor multiple feeds, create one config file per feed and run each separately:

```
configs/
  blog.yml
  news.yml
  podcast.yml
```

```bash
uv run python -m rss_share.main configs/blog.yml
uv run python -m rss_share.main configs/news.yml
uv run python -m rss_share.main configs/podcast.yml
```

Each feed maintains its own state and log files, isolated under `data/<config-stem>/`.

## Automating with cron

Add a crontab entry for each feed. This example runs each feed every two hours, staggered:

```cron
0  */2 * * *  cd /path/to/discourse-rss-share && uv run python -m rss_share.main configs/blog.yml
30 */2 * * *  cd /path/to/discourse-rss-share && uv run python -m rss_share.main configs/news.yml
```

Because each run posts only one item, running every hour with a backlog of 10 articles will post them one per hour over 10 hours rather than flooding the forum all at once.

## State and logs

For each config file, two files are maintained under `data/<config-stem>/`:

```
data/
  blog/
    posted_urls.json   # JSON list of all article URLs that have been posted
    rss-share.log      # timestamped log of every run
  news/
    posted_urls.json
    rss-share.log
```

**`posted_urls.json`** is the source of truth for what has been posted. To re-post an article, remove its URL from this file. To prevent an article from ever being posted, add its URL to this file manually.

**`rss-share.log`** records every run with timestamps. Errors are also written to stderr, making them visible in cron mail or system logs.

## Post format

Each Discourse topic is created with:

- **Title:** The article title from the RSS feed
- **Body:** The article URL, followed by the first 55 words extracted from the article's paragraph content, followed by a "Read more" link

The teaser is fetched from the live article page — not the RSS feed description — by extracting text from `<article>` or `<main>` content (falling back to all `<p>` tags), skipping short fragments like datelines and bylines.

## Troubleshooting

**Nothing is being posted:** Run with `--dry-run` to see what the script finds. Check `data/<config-stem>/posted_urls.json` — if all feed entries are already listed there, the queue is empty.

**Discourse API errors:** Verify your `discourse_api_key` and `discourse_api_username`. Ensure the API key has permission to create topics and that `category_id` exists. Check that any configured tags exist in Discourse before posting.

**Bad teaser content:** The teaser extractor looks for `<article>` or `<main>` tags first, then falls back to all `<p>` tags, skipping any paragraph with fewer than 8 words. If a site has an unusual structure, the teaser may pull in non-article text. Use `--dry-run` to inspect the output before letting it post.
