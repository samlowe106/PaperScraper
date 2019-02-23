from getpass import getpass
from os import listdir
from os import makedirs
from os import remove
from os.path import exists
from os.path import splitext
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
Updated on Mon Dec 8 6:50am 2018

@author: Sam

Scrapes a specified amount of image posts from the user's saved posts and saves those images to a file
Bookmarks non-image links to a txt file
"""

# Current date formatted in month-day-year
DATE = strftime("%m-%d-%y", gmtime())

# Directory where images will be saved
IMAGE_DOWNLOAD_DIRECTORY = "Output\\" + DATE + "\\"

# Directory where logs will be stored
LOG_DIRECTORY = "Logs\\"

# Log of all urls from which image(s) were downloaded
LOG_FILE = LOG_DIRECTORY + DATE + ".txt"

# List of currently unrecognized links (so compatibility can be added later)
INCOMPATIBLE_LINK_LOG_FILE = LOG_DIRECTORY + "Incompatible Link Log.txt"

# Character that windows won't allow in a filename
INVALID_CHARS = ["\\", "/", ":", "*", "?", "<", ">", "|"]

# Dictionary of domains incompatible with the program in the form domain (str) : number of appearances (int)
incompatible_domains = {}


def main() -> None:
    """
    Takes the Reddit username, password, and number of posts to be sorted (int)

    Retrieve all posts just in case there are a lot of selfposts (or this script has been run recently)
    Loop through each post:

    If the post links to an image, download and unsave that image (DOES count towards download_limit)
    If the post is a selfpost or comment, move on to the next post (doesn't count towards download_limit)
    If it links to a non-link image, bookmark and unsave it (doesn't count towards download_limit)
    """

    # Ensure the directories exist
    if not exists(LOG_DIRECTORY):
        makedirs(LOG_DIRECTORY)

    if not exists(IMAGE_DOWNLOAD_DIRECTORY):
        makedirs(IMAGE_DOWNLOAD_DIRECTORY)

    # Sign in
    reddit = None
    while reddit is None:
        username = input("Username: ")
        # password = input("Password: ")
        password = getpass("Password: ")    # Will only work via command line
        print("Signing in...")
        reddit = sign_in(username, password)

    # Establish the download limit
    download_limit = None
    while download_limit is None:
        try:
            download_limit = int(input("How many posts would you like to download? "))
        except ValueError:
            pass

    # Retrieve saved posts
    saved_posts = reddit.redditor(str(reddit.user.me())).saved(limit=None)

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
        images_downloaded = [download_image(post.title, url, IMAGE_DOWNLOAD_DIRECTORY) for url in post.recognized_urls]

        # Print out information about the post
        print("\n{0}. {1}".format(index, post.title))
        print("   r/" + str(post.subreddit))
        print("   " + post.url)
        for image in images_downloaded:
            print("   Downloaded " + image)

        # Log the post
        log_url(post.title, post.url, LOG_FILE)

        # If no images could be downloaded, write the url to the list of incompatible urls as well
        if images_downloaded is None:
            log_url("Unparsed URL ", post.url, INCOMPATIBLE_LINK_LOG_FILE)

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

    return


def sign_in(username: str, password: str):
    """
    Attempts to sign into Reddit taking the first two CLAs

    Returns Reddit object if successful
    """
    # Try to sign in until it works
    try:
        reddit = praw.Reddit(client_id='scNa87aJbSIcUQ',
                             client_secret='034VwNRplArCc-Y3niSpin0yFqY',
                             user_agent='Saved Sorter',
                             username=username,
                             password=password)
        print("Signed in as " + str(reddit.user.me()) + ".\n")
        return reddit
    except prawcore.exceptions.OAuthException:
        print("Unrecognized username or password.\n")
        return None


def sanitize_post(post):
    """
    Takes a post object

    Returns the same post but with edited data to prevent errors
    """

    # If the post is a comment, mark it as a selfpost
    if not hasattr(post, 'is_self'):
        post.is_self = True

    # If the post isn't a comment
    elif hasattr(post, 'title'):

        # Recapitalize and remove non-ASCII characters from the title
        new_title = ""
        for i, char in enumerate(post.title):
            # Only include ASCII characters in the title
            if ord(char) < 128:
                # If the character is invalid, add a space instead
                if char in INVALID_CHARS:
                    new_title += " "
                # Otherwise, if the character is the first in the string or after a space, capitalize it
                elif i == 0 or post.title[i - 1] == ' ':
                    new_title += (char.upper())
                # Otherwise, just add it normally
                else:
                    new_title += char
        post.title = new_title

        # Replaces " with ' in the title
        post.title = post.title.replace('"', "'")

        # Remove any trailing periods or spaces
        while post.title.endswith('.') or post.title.endswith(' '):
            post.title = post.title[:-1]

        # Remove any preceding periods or spaces
        while post.title.startswith('.') or post.title.startswith(' '):
            post.title = post.title[1:]

        # Ensure the url starts with https://
        if not post.url.startswith("https://"):
            post.url = post.url.lstrip("http://")
            post.url = "https://" + post.url

        # Establish the list of recognized urls in the post
        post.recognized_urls = []

        # If the url links to Artstation, remove the trailing ? and numbers they append to the end of their urls
        if "artstation" in post.url:
            post.recognized_urls = [post.url.split('?')[0]]

        # Imgur albums have multiple images in them
        # TODO: TEST
        elif "imgur.com/a/" in post.url:
            """
            Credit to Al Sweigart for some of this code
            http://inventwithpython.com/blog/2013/09/30/downloading-imgur-posts-linked-from-reddit-with-python/
            """

            # Get the parsed page
            soup = BeautifulSoup(get(post.url).text)
            post.recognized_urls = ["https:" + match["href"] for match in soup.select('.album-view-image-link a')]

        # TODO: TEST
        elif "/imgur.com/" in post.url:
            # Get the parsed page
            soup = BeautifulSoup(get(post.url).text)
            return [soup.select('.image a')[0]['href']]

        # i.redd.it and i.imgur.com are single-image pages
        elif "i.redd.it" in post.url or "i.imgur.com/" in post.url:
                post.url_list = [post.url]

    return post


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

    # If the image couldn't be downloaded, return an empty string
    if image.status_code != 200:
        print("Error retrieving image from " + url)
        exit(1)

    file_extension = splitext(url)[1]

    # Set up the output path if it doesn't already exist
    if not exists(path):
        makedirs(path)

    # If the title is too long, limit it to the first sentence
    if len(title) > 250:
        title = title.split('.', 1)[0]

    # Define what the filename will (probably) be
    file_title = title

    # Start a loop (prevents this file from overwriting another with the same name by adding (i) before the extension)
    for i in range(len(listdir(path) + 1)):

        # Insert a number in the filename to prevent conflicts
        if i > 0:
            file_title = "{0} ({1})".format(title, i)

        # If no files share the same name, write the file
        if (file_title + file_extension) not in listdir(path):

            # Write the file
            with open(path + file_title + file_extension, "wb") as File:
                for chunk in image.iter_content(4096):
                    File.write(chunk)

            # If the file is a jpg, resave it as a png
            if file_extension == ".jpg":
                im = Image.open(file_title + file_extension)
                file_extension = ".png"
                rgb_im = im.convert('RGB')
                rgb_im.save(file_title + file_extension)
                # Delete the previous jpg file
                remove(file_title + ".jpg")

            # Return the final name of the file (means it was successfully downloaded there)
            return file_title + file_extension


def log_url(title: str, url: str, filepath: str) -> None:
    """
    Writes the given title and url to the specified file, and  adds the url's domain to
    the dictionary of incompatible domains

    Returns: nothing
    """

    # Adds this link to the list of incompatible links
    with open(filepath, "a") as bookmark_file:
        bookmark_file.write(title + " : " + url + "\n")

    # Establish the post's domain
    uri = urlparse(url)
    domain = '{0}://{1}'.format(uri.scheme, uri.netloc)

    # Save that url to a dictionary
    if domain in incompatible_domains.keys():
        incompatible_domains[domain] += 1
    else:
        incompatible_domains[domain] = 1

    return


if __name__ == "__main__":
    main()
