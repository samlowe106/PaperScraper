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

# region Initiation

# Directory where images will be saved
DIRECTORY = strftime("%m-%d-%y", gmtime()) + "\\"

# Directory where logs will be stored
LOG_DIRECTORY = DIRECTORY + "Logs\\"

# Log of all urls from which image(s) were downloaded
LOG_FILEPATH = LOG_DIRECTORY + "Log.txt"

# List of currently unrecognized links (so compatibility can be added later)
INCOMPATIBLE_DOMAIN_LOG = LOG_DIRECTORY + "Incompatible URL Log.txt"

with open("info.txt", 'r') as info_file:
    CLIENT_ID = info_file.readline()
    CLIENT_SECRET = info_file.readline()

# Dictionary of domains incompatible with the program in the form domain (str) : number of appearances (int)
incompatible_domains = {}

parser = argparse.ArgumentParser(description="Scrapes images from the user's saved posts on Reddit")

parser.add_argument("-l", "--limit",     type=int, default=1000,
                    help="max number of images to download")
parser.add_argument("-p", "--png",       action='store_true',
                    help="convert .jpg files to .png files")
parser.add_argument("-d", "--directory", type=str, default="Output\\",
                    help="directory that files should be saved to")
parser.add_argument("-t", "--titlecase", type=bool, action='store_true',
                    help="saves filenames in title case")

# region NOT YET IMPLEMENTED
parser.add_argument("-n", "--name",      action='store_false',
                    help="append OP's name to the filename")
parser.add_argument("-s", "--sort",      action='store_false',
                    help="sort images into folders by subreddit")
parser.add_argument("--nolog",           type=bool, action='store_true',
                    help="disable logging")
# endregion

args = parser.parse_args()

# endregion


def main() -> None:
    """
    Scrapes and downloads any images from posts in the user's saved posts category on Reddit
    :return: None
    """

    reddit = attempt_sign_in()

    # Make directories
    create_directory(args.directory)
    chdir(args.directory)
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
        for i, url in enumerate(post.recognized_urls):
            downloaded_file = download_image(post.new_title, url, DIRECTORY)
            if downloaded_file != "":
                post.images_downloaded.append(downloaded_file)
                if args.png:
                    convert_to_png(DIRECTORY, downloaded_file)

        # post.images_downloaded = [download_image(post.new_title, url, DIRECTORY) for url in post.recognized_urls]

        log_post(post)
        post.unsave()

        # End if we've downloaded as many issues as desired
        if index >= args.limit > 0:
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
    Attempts to sign into Reddit
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
    Changes post data to prevent errors
    :param post: a post object
    :return: the same post with edited data to prevent errors
    """

    # If the post links somewhere, find scrape-able images
    if hasattr(post, 'title'):
        post.is_comment = False
        post.recognized_urls = find_urls(post.url)
        post.new_title = retitle(post.title)
        if args.titlecase:
            post.new_title = title_case(post.new_title)

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

    with open(LOG_FILEPATH, "a", encoding="utf-8") as log_file:
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
        print("\nSeveral domains were unrecognized:")
        for domain in sorted(incompatible_domains.items(), key=lambda x: x[1], reverse=True):
            print("\t{0}: {1}".format(domain[0], domain[1]))
    return


if __name__ == "__main__":
    main()
