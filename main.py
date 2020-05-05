import app.urlhelpers as urlhelpers
import app.filehelpers as filehelpers
import app.strhelpers as strhelpers
import argparse
from datetime import datetime
import getpass
import io
import json
import os
from prawcore.exceptions import OAuthException
from PIL import Image
import praw
from praw import Reddit
import requests
import shutil
import time
from typing import List, Optional, Tuple
from urllib.parse import urlparse


# Represents a tuple in the form (URL (str), whether the URL was correctly downloaded (bool))
URLTuple = Tuple[str, bool]


def main() -> None:
    """
    Scrapes and downloads any images from posts in the user's saved posts category on Reddit
    :return: None
    """
    reddit = prompt_sign_in()

    if reddit is None:
        return

    # Change to specified output directory
    filehelpers.create_directory(args.directory)
    os.chdir(args.directory)

    # Temp directory
    temp_dir = "temp"
    filehelpers.create_directory(temp_dir)

    # Image directory
    if args.dmy:
        image_directory = datetime.now.strftime("%d-%m-%y", datetime.now())
    else:
        image_directory = datetime.now.strftime("%m-%d-%y", datetime.now())

    # Log file path
    log_directory = os.path.join(args.directory, "Logs")
    log_path = os.path.join(log_directory, "log.txt")
    filehelpers.create_directory(log_directory)

    # Dictionary of domains incompatible with the program in the form domain (str) : number of appearances (int)
    incompatible_domains = {}

    # Retrieve user's saved posts
    saved_posts = reddit.redditor(str(reddit.user.me())).saved()

    index = 0
    for post in saved_posts:

        # If download failed, move on
        r = requests.get(post.url, headers={'Content-type': 'content_type_value'})
        if r.status_code != 200:
            continue

        recognized_urls = urlhelpers.find_urls(r)
        if recognized_urls:

            title = strhelpers.retitle(post.title)
            url_tuples = []

            # Download all found images and keep track of status
            for url in recognized_urls:
                status = urlhelpers.download_image(url, title, image_directory, png=args.png)
                url_tuples.append((url, status))

            # Log post
            if not args.nolog:
                log(post.title, post.id, post.url, url_tuples, log_path)

            post.unsave()
            index += 1

            print_post(index, post.title, str(post.subreddit), post.url, url_tuples)

            # End if the desired number of posts have had their images downloaded
            if index >= args.limit:
                break

    """ End-of-program cleanup """

    os.rmdir(temp_dir)

    if incompatible_domains:
        print("\nSeveral domains were unrecognized:")
        for domain in sorted(incompatible_domains.items(), key=lambda x: x[1], reverse=True):
            print("\t{0}: {1}".format(domain[0], domain[1]))

    return


def prompt_sign_in() -> Optional[Reddit]:
    """
    Prompts the user to sign in
    :return: Reddit object
    """
    username = input("Username: ")
    password = getpass.getpass("Password: ")  # Only works through the command line!

    print("Signing in...", end="")
    reddit = None

    try:
        reddit = sign_in(username, password)
        print("signed in as {0}.\n".format(reddit.user.me()))
    except ConnectionError as e:
        print(str(e).lower() + "\n")
    finally:
        return reddit


def sign_in(username: str, password: str) -> Optional[Reddit]:
    """
    Attempts to sign into Reddit
    :param username: The user's username
    :param password: The user's password
    :return: reddit object if successful, else None
    :raises ConnectionException: if username and password were unrecognized
    """

    assert os.path.isfile("info.txt"), "info.txt couldn't be found!"

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


def is_parsed(url_tuples: List[URLTuple]) -> bool:
    """
    Determines if every url in the list was parsed correctly
    :param url_tuples: list of tuples
    :return: True if the second element of each tuple in the list is True, else False
    """
    return count_parsed(url_tuples) == len(url_tuples)


def count_parsed(tup_list: List[URLTuple]) -> int:
    """
    Counts the number of urls that were parsed
    :param tup_list: a list of url tuples
    :return: number of tuples in the list who were correctly parsed
    """
    count = 0
    for _, parsed in tup_list:
        if parsed:
            count += 1
    return count


def log(title: str, id: str, url: str, url_tuples: List[URLTuple], file: str) -> None:
    """
    Writes the given post's title and url to the specified file
    :param post: reddit post object
    :param file: log file path
    :return: None
    """

    post_dict = {
        "title"           : title,
        "id"              : id,
        "url"             : url,
        "recognized_urls" : url_tuples
    }

    with open(file, "a", encoding="utf-8") as logfile:
        json.dump(post_dict, logfile)

    return


def print_post(index: int, old_title: str, subreddit: str, url: str, url_tuples: List[URLTuple]) -> None:
    """
    Prints out information about the specified post
    :param index: the index number of the post
    :param post: Reddit post to be printed
    :return: None
    """
    print("\n{0}. {1}".format(index, old_title))
    print("   r/" + subreddit)
    print("   " + url)
    print("   Saved {0} / {1} image(s).".format(count_parsed(url_tuples), len(url_tuples)))
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
                        default="Output",
                        help="directory that files should be saved to")
    parser.add_argument("-t",
                        "--titlecase",
                        action='store_true',
                        help="saves filenames in title case")
    parser.add_argument("-p",
                        "--png",
                        action='store_true',
                        help="convert .jpg/.jpeg files to .png files")
    parser.add_argument("--dmy",
                        action='store_true',
                        help="represent dates in day-month-year format")

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
