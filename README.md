# Paper Scraper for Reddit
PaperScraper is a Python script that downloads images from the user's saved category on Reddit.

Posts linking directly to an image or imgur page will be downloaded and unsaved; all other posts will be ignored.

## Summary

   - [Usage](#usage)
   - [License](#license)

## Usage

1. Go to your [app preferences](https://www.reddit.com/prefs/apps/) on Reddit
2. Click "create app"
3. Fill out the app's info, choosing script as the app type
4. In PaperScraper's app directory, create a file named info.txt 
5. Put the client ID in the first line and the client secret in the second line
6. Launch PaperScraper from the command prompt (PaperScraper uses getpass, so it's incompatible with Python consoles like those in PyCharm)

## License

PaperScraper is licensed under the [MIT](https://github.com/samlowe106/PaperScraper/blob/master/LICENSE) license.