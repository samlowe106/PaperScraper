from getpass import getpass
from os import listdir
from os import makedirs
from os import remove
from os.path import exists
from os.path import splitext
from sys import argv
from time import gmtime
from time import strftime
from urllib.parse import urlparse

import praw                         # PRAW
import prawcore.exceptions          # PRAW

from bs4 import BeautifulSoup       # bs4
from PIL import Image               # Pillow
from requests import get            # Requests

"""
Created on Wed Aug 30 16:52:56 2017
First version released on Sat Sept 14
Updated on Sun Sept 15 2:00am 2019

@author: Sam

Scrapes a specified amount of image posts from the user's saved posts on Reddit and saves those images to a file
"""

# region Globals

# Current date (in Greenwich Mean Time) formatted in month-day-year
DATE = strftime("%m-%d-%y", gmtime())

# Directory where images will be saved
DIRECTORY = "Output\\" + DATE + "\\"

# Directory where logs will be stored
LOG_DIRECTORY = DIRECTORY + "Logs\\"

# Log of all urls from which image(s) were downloaded
LOG = LOG_DIRECTORY + "Log.txt"

# List of currently unrecognized links (so compatibility can be added later)
INCOMPATIBLE_DOMAIN_LOG = LOG_DIRECTORY + "Incompatible URL Log.txt"

# Character that Windows won't allow in a filename
INVALID_CHARS = ["\\", "/", ":", "*", "?", "<", ">", "|"]

# File extensions that this program should recognize
RECOGNIZED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif"]

# True if the user would like all jpg images converted into png images, else false
PNG_PREFERRED = False

# Dictionary of domains incompatible with the program in the form domain (str) : number of appearances (int)
incompatible_domains = {}

# endregion


def main() -> None:
    """
    Takes the Reddit username, password, and number of posts to be sorted (int)

    Retrieve all posts just in case there are a lot of selfposts (or this script has been run recently)
    Loop through each post:

    If the post links to an image, download and unsave that image (DOES count towards download_limit)
    If the post is a selfpost or comment, move on to the next post (doesn't count towards download_limit)
    If it links to a non-link image, bookmark and unsave it (doesn't count towards download_limit)
    """

    # Make directories
    if not exists(LOG_DIRECTORY):
        makedirs(LOG_DIRECTORY)

    # Sign in
    while True:
        username = input("Username: ")
        password = input("Password: ")
        # password = getpass("Password: ")    # Only works on the command line

        print("Signing in...", end="")
        reddit = sign_in(username, password)

        # If login was successful, continue with the program
        if reddit is not None:
            print("signed in as " + str(reddit.user.me()) + ".\n")
            break

        print("unrecognized username or password!\n")

    # Retrieve saved posts
    saved_posts = reddit.redditor(str(reddit.user.me())).saved(limit=None)

    # Main loop
    running = True
    while running:

        # Establish the download limit
        while True:
            try:
                download_limit = int(input("How many posts would you like to download? "))
                break
            except ValueError:
                pass

        # Begin looping through saved posts
        index = 0
        for post in saved_posts:

            # Sanitize the post
            post = sanitize_post(post)

            # Move on if the post is just a selfpost or link to a reddit thread
            if post.is_self or "https://reddit.com/" in post.url:
                continue

            # Increase the index
            index += 1

            # Parse the image link
            images_downloaded = [download_image(post.title, url, DIRECTORY) for url in post.recognized_urls]

            # Print out information about the post
            print("\n{0}. {1}".format(index, post.title))
            print("   r/" + str(post.subreddit))
            print("   " + post.url)
            for image in images_downloaded:
                print("   Saved as " + image)

            # Log the post
            log_url(post.title, post.url, images_downloaded != [])

            # Unsave the post
            post.unsave()

            # If we've downloaded as many (or more) images as was specified, break out
            if index >= download_limit:
                break

        # Print out which domains were unrecognized (so compatibility can be added later)
        if len(incompatible_domains) > 0:
            print()
            print("Several domains were unrecognized:")
            for domain in sorted(incompatible_domains.items(), key=lambda x: x[1], reverse=True):
                print("\t{0}: {1}".format(domain[0], domain[1]))

        # End if the program was run from the command line
        if len(argv) > 0:
            break

        # Ask the user if they'd like to download more posts
        while True:
            response = input("\nWould you like to download more images? (y/n) ")
            if response.lower() == 'y':
                break
            elif response.lower() == 'n':
                running = False
                break

    # Any cleanup goes here

    return


def parse_clas() -> None:
    """
    Parses command line arguments

    :return: nothing
    """

    USAGE = "Usage: ./ssfr username [args]"

    # If too few commands were sent, print usage and exit
    if len(argv) == 1:
        print(USAGE)
        return

    # (str) : (str) dictionary of commands (key) and their corresponding descriptions (val)
    COMMANDS = {"-png": "Convert all JPG/JPEG images to PNG images",
                "-dir=": "Set the output directory",
                "-nolog": "Disable logging (not recommended!)",
                "-sort": "Place all images into folders named after the subreddits they were downloaded from",
                "-name": "Append the OP's name to the end of file names",
                "-t": "Put file names in title case",
                "-lim=": "Specify how many files should be downloaded (default is limitless)"
                }

    # Print help if the user needs it
    if str(argv[1]).lower() == "help":
        print(USAGE)
        for key in COMMANDS.keys():
            print("\t{0}\t{1}".format(key, COMMANDS[key]))
        print()
        return
    else:
        usern = argv[1]

    # Parse optional arguments
    if len(argv) > 2:
        for i in range(2, len(argv)):
            # The user prefers png images to jpg images
            if str(argv[i]).lower() == "-png":
                PNG_PREFERRED = True

            # The user has specified the download directory
            elif str(argv[i]).lower().startswith("-dir="):
                DIRECTORY = argv[i][5:]

            # The user has disabled logging
            elif str(argv[i]).lower() == "-nolog":
                LOGGING = False

            # The user wants images placed into folders by subreddit
            elif str(argv[i]).lower() == "-sort":
                SORT = True

            # The user wants the image poster's name appended to the end of file names
            elif str(argv[i]).lower() == "-name":
                ADD_POSTER_NAME = True

            # The user wants file names in title case
            elif str(argv[i]).lower() == "-t":
                TITLE = True

            # The user wants file names in title case
            elif str(argv[i]).lower() == "-lim=":
                try:
                    DOWNLOAD_LIMIT = int(argv[i][5:])
                except ValueError:
                    print("lim must be an int!")

    # Securely get password
    passw = getpass("Password: ")

    return


def download_image(title: str, url: str, path: str) -> str:
    """
    Downloads the image from the given url to a file with the name title

    Args:
        title: Title of the image (not including (i))
        url: A URL containing a single image, (the one to be downloaded)
        path: The filepath that the file should be saved to

    Returns:
        filepath that the image was downloaded to (str)
        empty string if failed

    Raises:
        IOError
        FileNotFoundError
    """

    # Try to download image data
    image = get(url)

    # If the image page couldn't be reached, return an empty string for failure
    if image.status_code != 200:
        print("\nERROR: Couldn't retrieve image from " + url + " , skipping...")
        return ""

    # Remove any query strings with split, then find the file extension with splitext
    file_extension = splitext(url.split('?')[0])[1]

    # If the file extension is unrecognized, don't try to download the file
    if file_extension not in RECOGNIZED_EXTENSIONS:
        return ""

    # Set up the output path if it doesn't already exist
    if not exists(path):
        makedirs(path)

    # Define a working filename
    file_title = retitle(title)

    # Start a loop (prevents this file from overwriting another with the same name by adding (i) before the extension)
    for i in range(len(listdir(path)) + 1):

        # Insert a number in the filename to prevent conflicts
        if i > 0:
            file_title = "{0} ({1})".format(file_title, i)

        # If no files share the same name, write the file
        if (file_title + file_extension) not in listdir(path):

            # Write the file
            with open(path + file_title + file_extension, "wb") as File:
                for chunk in image.iter_content(4096):
                    File.write(chunk)

            # If the user prefers PNG images and the file is a jpg, re-save it as a png
            if PNG_PREFERRED and file_extension == ".jpg":
                im = Image.open(path + file_title + file_extension)
                file_extension = ".png"
                rgb_im = im.convert('RGB')
                rgb_im.save(path + file_title + file_extension)
                # Delete the previous jpg file
                remove(path + file_title + ".jpg")

            # Return the final name of the file (means it was successfully downloaded there)
            return file_title + file_extension


def find_urls(url: str) -> list:
    """
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """
    # If the URL (without query strings) ends with any recognized file extension, this is a direct link to an image
    # Should match artstation, i.imgur.com, i.redd.it, and other pages
    for extension in RECOGNIZED_EXTENSIONS:
        if url.split('?')[0].endswith(extension):  # .split() removes any query strings from the URL
            return [url]

    # Imgur albums
    if "imgur.com/a/" in url:
        return parse_imgur_album(url)

    # Imgur single-image pages
    elif "imgur.com" in url:
        return [parse_imgur_single(url)]

    return []


def parse_imgur_album(album_url: str) -> list:
    """
    Imgur albums reference multiple other images hosted on imgur by image ID only, so album pages must be scraped to
    get single-image webpages, then scraped again to get a list of direct links to each image in the album
    :param album_url: url of an imgur album
    :return: direct links to each image in the specified album
    """
    # Find all the single image pages referenced by this album
    album_page = get(album_url)
    album_soup = BeautifulSoup(album_page.text, "html.parser")
    single_images = ["https://imgur.com/" + div["id"] for div in album_soup.select("div[class=post-images] > div[id]")]
    # Make a list of the direct links to the image hosted on each single-image page; return the list of all those images
    return [parse_imgur_single(link) for link in single_images]


def parse_imgur_single(url: str) -> str:
    """
    Some imgur pages with one image also include the imgur UI, so the page must be scraped to find a direct link
    to that image
    :param url: A single-image imgur page
    :return: A direct link to the image hosted on that page
    """
    page = get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    return soup.select("link[rel=image_src]")[0]["href"]


def retitle(current_string: str) -> str:
    """
    Capitalizes the first letter in each word, strips non-ASCII characters and characters Windows doesn't support in
    file names, and removes any preceding or trailing periods and spaces
    :param current_string: the current string
    :return: the new string
    """
    # Recapitalize the title and remove any incompatible characters
    new_string = ""
    # Replace non-ASCII characters with a space
    for i, char in enumerate(current_string):
        if char not in INVALID_CHARS:
            # Replace " with '
            if char == '"':
                new_string += "'"
            # Capitalize the first character and any character after a space
            elif i == 0 or current_string[i - 1] == ' ':
                new_string += (char.upper())
            # Prevent consecutive spaces
            elif char == ' ' and current_string[i - 1] == ' ':
                pass
            else:
                new_string += char

    # If the string is too long, limit it to the first sentence
    if len(new_string) > 250:
        new_string = new_string.split('.', 1)[0]
        # If the string is still too long, truncate it
        if len(new_string) > 250:
            new_string = new_string[:250]

    # Remove any trailing periods or spaces
    while new_string.endswith('.') or new_string.endswith(' '):
        new_string = new_string[:-1]

    # Remove any preceding periods or spaces
    while new_string.startswith('.') or new_string.startswith(' '):
        new_string = new_string[1:]

    return new_string


def sanitize_post(post):
    """
    :param post: a post object
    :return: the same post with edited data to prevent errors
    """

    if hasattr(post, 'title'):
        post.is_comment = False

        post.recognized_urls = find_urls(post.url)

    # If the post is a comment, mark it as a selfpost
    else:
        post.is_self = True
        post.is_comment = True

    return post


def sign_in(username: str, password: str):
    """
    Attempts to sign into Reddit taking the first two CLAs

    Returns Reddit object if successful
    """

    # Don't bother trying to sign in if username or password are blank
    #  (praw has a stack overflow without this check!)
    if username == "" or password == "":
        return None

    # Try to sign in
    try:
        reddit = praw.Reddit(client_id='scNa87aJbSIcUQ',
                             client_secret='034VwNRplArCc-Y3niSpin0yFqY',
                             user_agent='Saved Sorter',
                             username=username,
                             password=password)
        return reddit
    except prawcore.exceptions.OAuthException:
        return None


def log_url(title: str, url: str, compatible: bool) -> None:
    """
    Writes the given title and url to the specified file, and  adds the url's domain to
    the dictionary of incompatible domains

    :param title: Title of the post to be logged
    :param url: The post's URL
    :param compatible: Whether the post was compatible with this program or not
    :return: nothing
    """

    with open(LOG, "a", encoding="utf-8") as log_file:
        log_file.write(title + " : " + url + " : " + str(compatible) + '\n')

    # If the url was incompatible, update the log of incompatible domains
    if not compatible:

        # Establish the post's domain
        uri = urlparse(url)
        domain = '{0}://{1}'.format(uri.scheme, uri.netloc)

        # Save that domain to a dictionary
        if domain in incompatible_domains.keys():
            incompatible_domains[domain] += 1
        else:
            incompatible_domains[domain] = 1

        # Update the log file
        with open(INCOMPATIBLE_DOMAIN_LOG, "a") as incompatible_domain_log_file:
            for domain in incompatible_domains.keys():
                incompatible_domain_log_file.write(domain + " : " + str(incompatible_domains[domain]) + "\n")

    return


if __name__ == "__main__":
    main()
