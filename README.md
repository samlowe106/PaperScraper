# Paper Scraper for Reddit

Paper Scraper is a Python script that downloads images from the user's saved category on Reddit.

Posts linking directly to an image or imgur page will be downloaded and unsaved; all other posts will be ignored.

## Requirements

- Python 3.11
- A reddit account

## Summary

- [Installation](#installation)
- [Usage](#usage)
- [Technical Overview](#technical-overview)
- [License](#license)

## Installation

1. Clone this repository: `git clone https://github.com/samlowe106/PaperScraper.git`

2. (Optional) Create a virtual environment with `python -m venv [PATH]` and activate that virtual environment with `source [PATH]/bin/activate`

3. Install all requirements: `pip install -r requirements.txt`

4. Install pre-commit via `pre-commit install`. Ensure pre-commit is working by running `pre-commit run --all-files`

5. Go to your [app preferences](https://www.reddit.com/prefs/apps/) on Reddit

6. Create a new app and choose **script** as the app type

7. Go to your [Applications setting](https://imgur.com/account/settings/apps) on imgur

8. Create a new app

9. Configure your Python environment variables, adding the reddit client ID as "REDDIT_CLIENT_ID", reddit client secret as "REDDIT_CLIENT_SECRET", and imgur client ID as "IMGUR_CLIENT_ID"

## Usage

Paper Scraper uses getpass to securely read in passwords, so it's incompatible with Python consoles like those in PyCharm. For that reason, it's recommended to run it from the Terminal or Command Line using `python main.py`

Paper Scraper also comes with a handful of flags, which can be found by running Paper Scraper with the `--help` flag.

## Technical Overview

Paper Scraper is fairly simple. After basic argument parsing is done, the program has two major steps:

### Batch parsing

First, reddit submissions are fetched from reddit via [PRAW](https://praw.readthedocs.io/en/stable/index.html). PRAW provides submissions through "listing generators", which Paper Scraper wraps with `from_saved` and `from_subreddit` functions. These provide submissions as `SubmissionWrapper` objects to provide a simpler API for interacting with submissions and managing Paper Scraper-related data.

The url that each `SubmissionWrapper` links to is asynchronously scraped by parser objects (`flickr_parser`, `imgur_parser`, and `single_image_parser`) in a strategy pattern. If any of the and appended to the `SubmissionWrapper.urls` field. If the urls couldn't be accessed, the parsers couldn't find any urls, or if the post fails some other criteria specified in the command line arguments, the `SubmissionWrapper` is filtered out of the batch. This process repeats until a batch of valid `SubmissionWrapper`s of the desired size is created, or the underlying generator runs out of new posts.

### Batch downloading

After a batch of valid `SubmissionWrapper`s is created, each of the images linked to in the `SubmissionWrapper.urls` field are downloaded asynchronously and the resulting files are saved. If the `organize` flag is specified, images are also sorted into subdirectories by subreddit. Post data is written to a log file, and the program ends.

## License

Paper Scraper is licensed under the [MIT license.](https://github.com/samlowe106/PaperScraper/blob/master/LICENSE)
