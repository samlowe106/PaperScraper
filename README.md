# Paper Scraper for Reddit

PaperScraper is a Python script that downloads images from the user's saved category on Reddit.

Posts linking directly to an image or imgur page will be downloaded and unsaved; all other posts will be ignored.

## Requirements

* Python (3.11)

## Summary

   - [Installation](#installation)
   - [Usage](#usage)
   - [Technical Overview](#technical-overview)
   - [License](#license)

## Installation

1. Clone this repository: ``` git clone https://github.com/samlowe106/PaperScraper.git ```

2. (Optional) Create a virtual environment with `python -m venv [PATH]` and activate that virtual environment with `source [PATH]/bin/activate`

3. Install all requirements: ```pip install -r requirements.txt```

4. Go to your [app preferences](https://www.reddit.com/prefs/apps/) on Reddit

5. Click "create app"

6. Fill out the app's info, choosing **script** as the app type

7. Configure your Python environment variables, adding the client ID as "CLIENT_ID" and client secret as "CLIENT_SECRET"

## Usage

PaperScraper uses getpass to securely read in passwords, so it's incompatible with Python consoles like those in PyCharm. For that reason, it's recommended to run it from the Terminal or Command Line using ``` python src/main.py ```

PaperScraper also comes with a handful of flags, which can be found by running PaperScraper with the `--help` flag.

## Technical Overview

PaperScraper is fairly simple. After basic argument parsing is done, the program has two major steps:

### Batch parsing
First, reddit submissions are fetched from reddit via [PRAW](https://praw.readthedocs.io/en/stable/index.html). PRAW provides submissions through "listing generators", which PaperScraper wraps with `from_saved` and `from_subreddit` functions. These provide submissions as `SubmissionWrapper` objects to provide a simpler API for interacting with submissions and managing PaperScraper-related data.

The url that each `SubmissionWrapper` links to is asynchronously scraped by parser objects (`flickr_parser`, `imgur_parser`, and `single_image_parser`) in a strategy pattern. If any of the and appended to the `SubmissionWrapper.urls` field. If the urls couldn't be accessed, the parsers couldn't find any urls, or if the post fails some other criteria specified in the command line arguments, the `SubmissionWrapper` is filtered out of the batch. This process repeats until a batch of valid `SubmissionWrapper`s of the desired size is created, or the underlying generator runs out of new posts.

### Batch downloading

After a batch of valid `SubmissionWrapper`s is created, each of the images linked to in the `SubmissionWrapper.urls` field are downloaded asynchronously and the resulting files are saved. If the `organize` flag is specified, images are also sorted into subdirectories by subreddit. Post data is written to a log file, and the program ends.

## License

PaperScraper is licensed under the [MIT license.](https://github.com/samlowe106/PaperScraper/blob/master/LICENSE)
