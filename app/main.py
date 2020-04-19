from app.strhelpers import retitle, title_case
from app.filehelpers import convert_to_png, create_directory
from app.imagehelpers import download_image, ExtensionUnrecognizedError, find_urls
import argparse
from getpass import getpass
from json import dump
from os import chdir
from os.path import isfile
from prawcore.exceptions import OAuthException
import praw
from praw.models import Submission
from time import gmtime
from time import strftime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


def main() -> None:
    """
    Scrapes and downloads any images from posts in the user's saved posts category on Reddit
    :return: None
    """
    reddit = attempt_sign_in()

    if reddit is None:
        return

    # Change to specified output directory
    create_directory(args.directory)
    chdir(args.directory)

    # Image directory
    image_directory = strftime("%m-%d-%y", gmtime()) + "\\"

    # Log file path
    log_directory = args.directory + "Logs\\"
    log_path = log_directory + "log.txt"
    create_directory(log_directory)

    # Dictionary of domains incompatible with the program in the form domain (str) : number of appearances (int)
    incompatible_domains = {}

    # Retrieve user's saved posts
    saved_posts = reddit.redditor(str(reddit.user.me())).saved()

    index = 0
    for post in saved_posts:

        # Move on if the post is just a selfpost or link to a reddit thread
        if is_skippable(post):
            continue

        post = sanitize_post(post)

        post.recognized_urls = parse_urls(post.recognized_urls, post.new_title, image_directory)

        log_post(post, log_path)

        if is_parsed(post.recognized_urls):
            index += 1
            post.unsave()

        # End if the desired number of posts have had their images downloaded
        if index >= args.limit:
            break

    """ End-of-program cleanup """

    if incompatible_domains:
        print("\nSeveral domains were unrecognized:")
        print_dict(incompatible_domains)

    return


def is_parsed(url_tuples: List[Tuple[str, bool]]) -> bool:
    """
    Determines if every url in the list was parsed correctly
    :param url_tuples: list of tuples
    :return: True if the second element of each tuple in the list is True, else False
    """
    for _, parsed in url_tuples:
        if not parsed:
            return False

    return True


def parse_urls(url_tuples: List[Tuple[str, bool]], title: str, dir: str) -> Submission:
    """
    Attempts to download images from the given post's recognized urls to the specified directory
    """
    for i in range(len(url_tuples)):
        url, parsed = url_tuples[i]
        try:
            path = download_image(title, url, dir)
            parsed = True
            
            if args.png:
                convert_to_png(path)
       
        except (ConnectionError, ExtensionUnrecognizedError) as e:
            print("\n" + e)

        finally:
            url_tuples[i] = (url, parsed)

    return url_tuples


def attempt_sign_in() -> Optional[praw.Reddit]:
    """
    Prompts the user to sign in
    :return: Reddit object
    """
    username = input("Username: ")
    password = getpass("Password: ")  # Only works through the command line!

    print("Signing in...", end="")
    reddit = None

    try:
        reddit = sign_in(username, password)
        print("signed in as " + str(reddit.user.me()) + ".\n")
    except ConnectionError as e:
        print(str(e).lower() + "\n")
    finally:
        return reddit


def sign_in(username: str, password: str) -> Optional[praw.Reddit]:
    """
    Attempts to sign into Reddit
    :param username: The user's username
    :param password: The user's password
    :return: reddit object if successful, else None
    :raises ConnectionException: if username and password were unrecognized
    """

    assert isfile("info.txt"), "info.txt couldn't be found!"

    with open("info.txt", 'r') as info_file:
        client_id = info_file.readline()
        client_secret = info_file.readline()

    # praw returns an invalid reddit instance if the  client id or client secret are ""
    assert client_id, "Client ID is blank!"
    assert client_secret, "Client Secret is blank!"

    # praw stack overflows if both username and password are ""
    if not (username and password and client_id and client_secret):
        raise ConnectionError("Username and password unrecognized.")

    try:
        return praw.Reddit(client_id=client_id,
                           client_secret=client_secret,
                           user_agent='PaperScraper',
                           username=username,
                           password=password)
    # Catch and re-raise error with a more helpful message
    except OAuthException:
        raise ConnectionError("Username and password unrecognized.")


def is_skippable(post: Submission) -> bool:
    """
    Determines if a given reddit post can be skipped or not
    :param post: a reddit post object
    :return: True if the given post is a comment, selfpost, or links to another reddit post, else False
    """
    return (not hasattr(post, 'title')) or post.is_self or "https://reddit.com/" in post.url


def sanitize_post(post: Submission) -> Submission:
    """
    Fixes post's title and finds post's urls
    :param post: a post object
    :return: the same post with additional new_title and recognized_urls fields
    """
    post.new_title = retitle(post.title)
    if args.titlecase:
        post.new_title = title_case(post.new_title)
    
    # recognized_urls is a List[Tuple[str, bool]] representing an image url associated with
    #  the given post, and whether the image at that url was downloaded
    post.recognized_urls = []
    for url in find_urls(post.url):
        post.recognized_urls.append(url, False)
    
    return post


def log_post(post: Submission, file: str) -> None:
    """
    Writes the given post's title and url to the specified file
    :param post: reddit post object
    :param file: log file path
    :return: None
    """

    post_dict = {
        "title"           : post.title,
        "id"              : post.id,
        "url"             : post.url,
        "recognized_urls" : post.recognized_urls
    }

    with open(file, "a", encoding="utf-8") as logfile:
        dump(post_dict, logfile)

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


def print_dict(dictionary: Dict[str, int]) -> None:
    """
    Prints keys (str) from a dictionary, sorted by their value (int)
    :param dictionary: dictionary in the form str : int
    :return: None
    """

    for domain in sorted(dictionary.items(), key=lambda x: x[1], reverse=True):
        print("\t{0}: {1}".format(domain[0], domain[1]))
    return


if __name__ == "__main__":

    # region Argument Parsing

    parser = argparse.ArgumentParser(description="Scrapes images from the user's saved posts on Reddit")
    parser.add_argument("-l",
                        "--limit",
                        type=int,
                        default=1000,
                        help="max number of images to download")
    parser.add_argument("-d",
                        "--directory",
                        type=str,
                        default="Output\\",
                        help="directory that files should be saved to")
    parser.add_argument("-t",
                        "--titlecase",
                        action='store_true',
                        help="saves filenames in title case")
    parser.add_argument("-p",
                        "--png",
                        action='store_true',
                        help="convert .jpg files to .png files")

    """
    NOT YET IMPLEMENTED
    
    parser.add_argument("-n",
                        "--name",
                        action='store_false',
                        help="append OP's name to the filename")

    parser.add_argument("-s",
                        "--sort",
                        action='store_false',
                        help="sort images into folders by subreddit")

    parser.add_argument("--nolog",
                        action='store_true',
                        help="disable logging")
    """

    args = parser.parse_args()

    # endregion

    main()
