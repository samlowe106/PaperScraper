# Paper Scraper for Reddit
PaperScraper is a Python script that downloads images from the user's saved category on Reddit.

Posts linking directly to an image or imgur page will be downloaded and unsaved; all other posts will be ignored.

## Summary

   - [Installation](#installation)
   - [Usage](#usage)
   - [License](#license)

## Installation

1. Clone this repository: ``` git clone https://github.com/samlowe106/PaperScraper.git ```

2. Install all requirements: ``` pip install -r requirements.txt ```

3. Go to your [app preferences](https://www.reddit.com/prefs/apps/) on Reddit

4. Click "create app"

5. Fill out the app's info, choosing script as the app type

6. Configure your Python environment variables, adding the client ID as "CLIENT_ID" and client secret as "CLIENT_SECRET"

## Usage

PaperScraper uses getpass to securely read in passwords, so it's incompatible with Python consoles like those in PyCharm. For that reason, it's recommended to run it from the Terminal or Command Line using ``` python src/main.py ```

PaperScraper also comes with a handful of flags, which can be found by running PaperScraper with the `--help` flag. 

## License

PaperScraper is licensed under the [MIT license.](https://github.com/samlowe106/PaperScraper/blob/master/LICENSE)
