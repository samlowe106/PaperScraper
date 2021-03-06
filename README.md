# Paper Scraper for Reddit
PaperScraper is a Python script that downloads images from the user's saved category on Reddit.

Posts linking directly to an image or imgur page will be downloaded and unsaved; all other posts will be ignored.

## Summary

   - [Usage](#usage)
   - [License](#license)

## Usage

1. Clone this repository: ``` git clone https://github.com/samlowe106/PaperScraper.git ```

2. Install all requirements: ``` pip install -r requirements.txt ```

3. Go to your [app preferences](https://www.reddit.com/prefs/apps/) on Reddit

4. Click "create app"

5. Fill out the app's info, choosing script as the app type

6. In PaperScraper's app directory, create a file named ```info.txt```

7. Put the client ID in the first line and the client secret in the second line

8. Launch PaperScraper from the command prompt (PaperScraper uses getpass, so it's incompatible with Python consoles like those in PyCharm)

## License

PaperScraper is licensed under the [MIT](https://github.com/samlowe106/PaperScraper/blob/master/LICENSE) license.
