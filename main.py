import argparse
from getpass import getpass
from os import chdir, listdir, makedirs, path, remove
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


# region Globals

# region Constants

# Current date (in Greenwich Mean Time) formatted in month-day-year
DATE = strftime("%m-%d-%y", gmtime())

# Directory where images will be saved
DIRECTORY = DATE + "\\"

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

LOGGING = True

SORT = False

ADD_POSTER_NAME = False

TITLE = True

with open("info.txt", 'r') as info_file:
    CLIENT_ID = info_file.readline()
    CLIENT_SECRET = info_file.readline()

# endregion

# Dictionary of domains incompatible with the program in the form domain (str) : number of appearances (int)
incompatible_domains = {}

# endregion

# region Initiation

parser = argparse.ArgumentParser(description="Scrapes images from the user's saved posts on Reddit")
parser.add_argument("-l", "--limit",     type=int, default=1000,
                    help="max number of images to download")
parser.add_argument("-s", "--sort",      action='store_false',
                    help="sort images into folders by subreddit")
parser.add_argument("-p", "--png",       action='store_true',
                    help="convert .jpg files to .png files")
parser.add_argument("-n", "--name",      action='store_false',
                    help="append OP's name to the filename")
parser.add_argument("-d", "--directory", type=str,
                    help="directory that files should be saved to")
parser.add_argument("--nolog",           type=bool, action='store_true',
                    help="disable logging")
parser.add_argument("-t", "--titlecase", type=bool, action='store_true',
                    help="saves filenames in title case")
args = parser.parse_args()

# (str) : (str) dictionary of commands (key) and their corresponding descriptions (val)
COMMANDS = {"-png": "Convert all JPG/JPEG images to PNG images",
            "-dir=": "Set the output directory",
            "-nolog": "Disable logging (not recommended!)",
            "-sort": "Place all images into folders named after the subreddits they were downloaded from",
            "-name": "Append the OP's name to the end of file names",
            "-t": "Put file names in title case",
            "-lim=": "Specify how many files should be downloaded (default is limitless)"
            }

# endregion


def attempt_sign_in():
    """
    Prompts the user to sign in
    :return: Reddit object
    """
    username = input("Username: ")
    password = getpass("Password: ")  # Only works through the command line!

    print("Signing in...", end="")
    reddit = sign_in(username, password)

    # If login was successful, continue with the program
    if reddit is not None:
        print("signed in as " + str(reddit.user.me()) + ".\n")
        return reddit

    print("unrecognized username or password.\n")
    return


def create_directory(dirpath: str) -> None:
    """
    Creates a directory with the specified name if that directory doesn't already exist
    :param dirpath: name of the directory
    :return: None
    """
    if not exists(dirpath):
        makedirs(dirpath)
    return


def log_post(post) -> None:
    """
    Logs a given post
    :param post: post to be logged
    :return: None
    """
    log_url(post.title, post.url, post.images_downloaded != [])
    return


def main() -> None:
    """
    Scrapes and downloads any images from posts in the user's saved posts category on Reddit

    :return:
    """

    global PNG_PREFERRED, LOGGING, SORT, ADD_POSTER_NAME, TITLE

    # Tentative working directory
    working_directory = "Output\\"
    # Tentative download limit
    download_limit = -1

    reddit = attempt_sign_in()

    # Make directories
    create_directory(working_directory)
    chdir(working_directory)
    create_directory(LOG_DIRECTORY)

    # Retrieve saved posts
    saved_posts = reddit.redditor(str(reddit.user.me())).saved()

    # Loop through saved posts
    index = 0
    for post in saved_posts:

        # Sanitize the post
        post = sanitize_post(post)

        # Move on if the post is just a selfpost or link to a reddit thread
        if post.skippable:
            continue

        index += 1

        # Parse the image link
        post.images_downloaded = [download_image(post.title, url, DIRECTORY) for url in post.recognized_urls]

        log_post(post)
        post.unsave()

        # If we've downloaded as many issues as desired, break out
        if index >= download_limit > 0:
            break

    print_unrecognized_domains()

    """ End-of-program cleanup goes here """

    return


def print_post_info(index: int, post) -> None:
    """
    Prints out information about the specified post

    :param index: the index number of the post
    :param post: a post object
    :return: None
    """
    print("\n{0}. {1}".format(index, post.title))
    print("   r/" + str(post.subreddit))
    print("   " + post.url)
    for image in post.downloaded_images:
        print("   Saved as " + image)
    return


def print_unrecognized_domains() -> None:
    """
    Prints unrecognized domains (so compatibility can be added later)
    :return: None
    """
    if len(incompatible_domains) > 0:
        print()
        print("Several domains were unrecognized:")
        for domain in sorted(incompatible_domains.items(), key=lambda x: x[1], reverse=True):
            print("\t{0}: {1}".format(domain[0], domain[1]))
    return


def download_image(title: str, url: str, path: str) -> str:
    """
    Attempts to download an image from the given url to a file with the specified title

    :param title: Desired title of the image file
    :param url: A URL containing a direct link to the image to be downloaded
    :param path: The filepath that the file should be saved to
    :return: filepath that the image was downloaded to, empty string if failed
    :raises: IOError, FileNotFoundError
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

    # Set up the output path
    create_directory(path)

    # Start a loop (prevents this file from overwriting another with the same name by adding (i) before the extension)
    for i in range(len(listdir(path)) + 1):

        # Insert a number in the filename to prevent conflicts
        if i > 0:
            file_title = "{0} ({1})".format(title, i)
        else:
            file_title = title

        # If no files share the same name, write the file
        if (file_title + file_extension) not in listdir(path):

            # Write the file
            with open(path + file_title + file_extension, "wb") as File:
                for chunk in image.iter_content(4096):
                    File.write(chunk)

            # If the user prefers PNG images and the file is a jpg, re-save it as a png
            if PNG_PREFERRED and file_extension.lower() in [".jpg", ".jpeg"]:
                convert_to_png(path, file_title, file_extension)
                # Delete the previous jpg file
                remove(path + file_title + ".jpg")

            # Return the final name of the file (means it was successfully downloaded there)
            return file_title + file_extension


def save_image(image, path: str, title: str, extension: str) -> str:
    """
    Saves the specified image to the specified path with the specified title and file extension
    :param image: the image to be saved
    :param path: the path the image should be saved to
    :param title: the title the image file should have
    :param extension: the file extension
    :return: final filename (with extension)
    """
    # Start a loop (prevents this file from overwriting another with the same name by adding (i) before the extension)
    for i in range(len(listdir(path)) + 1):

        # Insert a number in the filename to prevent conflicts
        if i > 0:
            file_title = "{0} ({1})".format(title, i)
        else:
            file_title = title

        # If no files share the same name, write the file
        if (file_title + extension) not in listdir(path):

            # Write the file
            with open(path + file_title + extension, "wb") as File:
                for chunk in image.iter_content(4096):
                    File.write(chunk)

            # Return the final filename (with extension)
            return file_title + extension


def convert_to_png(path: str, file_title: str, current_extension: str) -> str:
    """
    Converts the given image to a .png
    :param path: path that the image is located in
    :param file_title: title of the file to be converted
    :param current_extension: image's current file extension
    :return: filename (with new extension)
    """
    new_extension = ".png"
    with Image.open(path + file_title + current_extension) as im:
        rgb_im = im.convert('RGB')
        rgb_im.save(path + file_title + new_extension)
    return file_title + new_extension


def find_urls(url: str) -> list:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
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
    Scrapes the specified imgur album for direct links to each image
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
    Scrapes regular imgur page for a direct link to the image displayed on that page
    :param url: A single-image imgur page
    :return: A direct link to the image hosted on that page
    """
    page = get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    return soup.select("link[rel=image_src]")[0]["href"]


def file_title(s: str) -> str:
    """
    Removes characters that Windows doesn't allow in filenames from the specified string
    :param s: string to remove characters from
    :return: the given string without invalid characters
    """
    s.replace("'", '"')
    for invalid_char in ["\\", "/", ":", "*", "?", "<", ">", "|"]:
        s.replace(invalid_char, "")
    return s


def shorten(s: str, max_length: int = 250) -> str:
    """
    Shortens s to be no longer than the first sentence. Truncates words if possible,
    but truncates characters when necessary
    :param s: string to be shortened
    :param max_length: the maximum character length that s can be (defaults to 250)
    :return: s
    """
    shortened_words = attempt_shorten(s, ' ', max_length)
    # If the attempt to shorten s using words fails, truncate s
    if len(shortened_words) < max_length:
        return shortened_words
    else:
        return s[:max_length]


def attempt_shorten(s: str, splitter: str, max_length: int = 250) -> str:
    """
    Attempts to shorten s by splitting it up into its constituent sections (words, sentences, lines, etc. depending on
    how splitter is specified) and removing trailing sections until it's below the max character length.
    :param s: the string that this function is attempting to shorten
    :param splitter: the string that we'll use to separate one section of s from another
    :param max_length: the maximum length we should attempt to shorten s to
    :return: the version of s that is (or is the closest to being) below the specified max_length
    """
    # if splitter == ".", we're splitting s up into its constituent sentences (a section = sentence)
    # if splitter == " ", we're splitting s up into its constituent words (a sections = word)

    while len(s) > max_length:
        constituents = s.split(splitter)
        constituent_count = len(constituents)
        # If s consists of more than one section, shorten s by removing the last section
        if constituent_count > 1:
            s = splitter.join(constituents[:(constituent_count - 1)])
        # If s consists of only one section, it can't be split up any more
        else:
            # This version of s will be more than max_length characters
            return s

    # This version of s will be less than max_length characters
    return s


def retitle(s: str) -> str:
    """
    Changes the given string into a visually appealing title-cased filename
    :param s: the string to be improved
    :return: a clean, valid file title
    """

    for punctuation in [".", " ", ","]:
        s = trim_string(s, punctuation)

    s = file_title(s)
    s = shorten(s)
    s = title_case(s)

    return s


def trim_string(s1: str, s2: str) -> str:
    """
    Removes any preceding or trailing instances of s2 from s1
    :param s1: the string from which preceding or trailing instances of s2 will be removed
    :param s2: the string that will be removed from the start and end of s1
    :return: s1 without any instances of s2 at either the start or end
    """
    # Remove any preceding instances of char from s
    while s1.startswith(s2):
        s1 = s1.rstrip(s2)

    # Remove any trailing instances of char from s
    while s1.endswith(s2):
        s1 = s1.lstrip(s2)

    return s1


def title_case(s: str) -> str:
    new_s = ""
    for i, char in enumerate(s):
        if i == 0 or s[i - 1] == ' ':
            new_s += (char.upper())
        else:
            new_s += char

    return new_s


def sanitize_post(post):
    """
    Sanitizes post to prevent errors

    :param post: a post object
    :return: the same post with edited data to prevent errors
    """

    # If the post links somewhere, find scrape-able images
    if hasattr(post, 'title'):
        post.is_comment = False
        post.recognized_urls = find_urls(post.url)
        post.title_old = post.title
        post.title = retitle(post.title)

    # If the post is a comment, mark it as a selfpost
    else:
        post.is_self = True
        post.is_comment = True

    post.skippable = post.is_self or "https://reddit.com/" in post.url

    return post


def sign_in(username: str, password: str):
    """
    Attempts to sign into Reddit taking the first two CLAs

    :param username: The user's username
    :param password: The user's password
    :return: reddit object if successful, else None
    """

    # Don't bother trying to sign in if username or password are blank
    #  (praw has a stack overflow without this check!)
    if username == "" or password == "":
        return None

    # Try to sign in
    try:
        reddit = praw.Reddit(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
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

    :param title: title of the post to be logged
    :param url: the post's URL
    :param compatible: whether the post was compatible with this program or not
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
