import argparse
from getpass import getpass
from filehelpers import convert_to_png, create_directory
from imagehelpers import download_image, find_urls
from os import chdir
import praw                         # PRAW
import prawcore.exceptions          # PRAW
from strhelpers import *
from time import gmtime
from time import strftime
from urllib.parse import urlparse

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

        for i, url in enumerate(post.recognized_urls):
            downloaded_file = download_image(post.title, url, DIRECTORY)
            if downloaded_file != "":
                post.images_downloaded.append(downloaded_file)
                if PNG_PREFERRED:
                    convert_to_png(DIRECTORY, downloaded_file)

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


def log_post(post) -> None:
    """
    Logs a given post
    :param post: post to be logged
    :return: None
    """
    log_url(post.title, post.url, post.images_downloaded != [])
    return


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


def print_post_info(index: int, post) -> None:
    """
    Prints out information about the specified post

    :param index: the index number of the post
    :param post: a post object
    :return: None
    """
    print("\n{0}. {1}".format(index, post.old_title))
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


if __name__ == "__main__":
    main()
