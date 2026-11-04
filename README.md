# Paper Scraper for Reddit

[![Tests](https://github.com/samlowe106/PaperScraper/actions/workflows/tests.yml/badge.svg)](https://github.com/samlowe106/PaperScraper/actions/workflows/tests.yml) [![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)](https://github.com/samlowe106/PaperScraper/actions/workflows/tests.yml)

Paper Scraper is an asynchronous Python tool that downloads images from Reddit, either from your **saved posts** or from any **subreddits** you specify.

It recognizes direct image links, Reddit image/gallery posts (`i.redd.it`, `preview.redd.it`), Imgur images/albums/galleries, and Flickr photos. Posts that don't resolve to a downloadable image are skipped.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- A Reddit account with a registered **script** app
- An Imgur account with a registered app (its client ID is used to resolve Imgur links)
- _(optional)_ a Flickr API key, only needed to resolve Flickr links

## Summary

- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Technical Overview](#technical-overview)
- [License](#license)

## Installation

1. Clone this repository:

   ```sh
   git clone https://github.com/samlowe106/PaperScraper.git
   cd PaperScraper
   ```

2. Ensure [uv](https://docs.astral.sh/uv/) is installed, then create the environment:

   ```sh
   uv sync
   ```

3. Create a Reddit app at your [app preferences](https://www.reddit.com/prefs/apps/) and choose **script** as the app type.

4. Create an Imgur app at your [application settings](https://imgur.com/account/settings/apps).

5. Create a file named `.env` in the project root with your credentials:

   ```dotenv
   REDDIT_CLIENT_ID="..."
   REDDIT_CLIENT_SECRET="..."
   IMGUR_CLIENT_ID="..."
   FLICKR_CLIENT_ID="..."   # optional, only needed to resolve Flickr links
   ```

## Usage

After `uv sync`, run it via the `paperscraper` command (equivalently `uv run python -m src.main`):

```sh
uv run paperscraper [options]
```

Some common options (run with `--help` for the full list):

| Flag | Description |
| --- | --- |
| `-r`, `--subreddit` | Include posts from a subreddit (repeatable) |
| `--sortby` | How to sort subreddit posts: `hot`, `new`, `controversial`, or `top_all` / `top_day` / `top_week` / `top_month` / `top_year` / `top_hour` |
| `--limit` | Max **submissions** to pull from each source (default: `10`); an album submission may still yield several images |
| `-k`, `--karma` | Only download posts with at least this score |
| `--hours` / `--days` / `--years` | Only download posts at most this old (mutually exclusive) |
| `-d`, `--dir` | Output directory (default: `Output`) |
| `--organize` | Sort downloaded images into per-subreddit subfolders |
| `--nolog` | Disable the per-run JSON log (written into the output dir by default) |
| `-u`, `--saved` | Include your saved posts; prompts for Reddit login (see note) |
| `--unsave` | Un-save saved posts after a successful download (opt-in; requires login) |

### Examples:

```sh
# Download images from r/wallpapers, sorted by top of all time, into ./pics
uv run paperscraper -r wallpapers --sortby top_all -d pics

# Top posts from the last week with >= 100 score, at most 5 per subreddit
uv run paperscraper -r wallpapers -r art --sortby top_week --days 7 -k 100 --limit 5
```

Files are written to a timestamped directory (e.g. `Output/PaperScraper 2026-06-20 08-30/`, with ` (1)`, ` (2)`, ... added if that already exists). A post with one image is saved as `<title>.<ext>`; a gallery or album becomes a `<title>/` folder of files numbered by position (`0.jpg`, `1.png`, ...). If one image in an album can't be downloaded, the others keep their numbers, so the gap shows what's missing.

> **Note:** the saved-posts flow (`--saved` / `--unsave`) is implemented but has only been exercised against mocked Reddit responses, so it needs a real login to verify end-to-end. `--saved` also uses `getpass`, so it needs a real terminal (not an IDE console).

## Testing

The test suite uses `pytest` (with `pytest-asyncio` for the async code and `vcrpy` cassettes for recorded HTTP interactions).

```sh
uv run pytest
```

`pyproject.toml` configures pytest to measure coverage and block live network access, so recorded cassettes are the only source of HTTP responses.

As of the latest run, **199 tests pass with ~96% coverage**. CI runs the suite on the pinned Python version and fails the build if coverage drops below 80%.

This repo also ships a [pre-commit](https://pre-commit.com/) config (`ruff`, `black`, `ty`, and assorted file checks):

```sh
uv run pre-commit install      # hooks will now run on every commit
uv run pre-commit run --all-files
```

## Technical Overview

After argument parsing, `main()` runs a fully asynchronous pipeline:

1. **Stream building**: `StreamBuilder` (see [`src/reddit/submission_source.py`](src/reddit/submission_source.py)) signs into Reddit via [asyncpraw](https://asyncpraw.readthedocs.io/) and turns the requested subreddits into async listing generators (capped per source by `--limit`). These are interleaved with `merge()` and adapted with `amap()` / `afilter()` (see [`src/core/functional.py`](src/core/functional.py)), yielding each submission as a `SubmissionWrapper`. A predicate built from `--karma` and the age flags (`--hours`/`--days`/`--years`) filters out submissions that don't qualify.

2. **URL finding**: Reddit-hosted images and galleries are read straight from the listing data, with no extra request. For any other link, `SubmissionWrapper.find_urls()` runs every parser (`single_image`, `reddit`, `imgur`, `flickr` in [`src/parsing/`](src/parsing/)) concurrently in a strategy pattern and collects the direct media links they resolve, in order (so gallery and album order is kept). A parser that fails is reported and skipped, so it can't cost a post the links the other parsers found.

3. **Downloading & saving**: Resolved URLs are streamed with [`httpx`](https://www.python-httpx.org/) straight to disk with [`aiofiles`](https://github.com/Tinche/aiofiles), so memory use doesn't grow with file or album size. `UniqueDirectoryFileManager` claims each name atomically, so concurrent posts with the same title can't overwrite each other, and (with `--organize`) sorts posts into per-subreddit folders. Transient errors, including a connection dropping partway through a file, are retried with exponential backoff, waiting longer if the server's `Retry-After` asks.

Concurrency is limited in two places. Every HTTP request, from parsers and downloads alike, goes through `HostLimitedTransport` (see [`src/core/host_limiter.py`](src/core/host_limiter.py)), which allows 8 requests at once to any one host and 32 in total, matching the connection pool so requests never time out waiting for a connection. A 429 or 503 with `Retry-After` pauses that host for every request, not just the one that got it. Separately, `main()` lets 32 posts be in progress at once, so posts finish roughly in the order they arrive. Reddit API calls go through asyncpraw, which follows Reddit's own rate limits. The whole pipeline runs inside an `asyncio.TaskGroup` so submissions are processed as they stream in rather than in fixed batches. Each submission is handled independently: a failure is logged and skipped rather than aborting the run, and individual downloads retry transient errors with backoff. Unless `--nolog` is passed, a JSON record of each processed post is appended to a log in the output directory.

## License

Since August 24th, 2026, Paper Scraper is licensed under [AGPLv3](LICENSE). Previous versions of Paper Scraper were licensed under the [MIT license](https://github.com/samlowe106/PaperScraper/blob/207b804b9e2b74060df930ff44c9647796acc65a/LICENSE).
