#from app.strhelpers import retitle, title_case
#from app.imagehelpers import convert_file, create_directory, download_image, find_urls, prevent_conflicts
import app
import argparse
import getpass
import os
from prawcore.exceptions import OAuthException
import praw
from praw import Reddit
import shutil
import time
from typing import Optional
from urllib.parse import urlparse


def main() -> None:
    """
    Scrapes and downloads any images from posts in the user's saved posts category on Reddit
    :return: None
    """
    reddit = prompt_sign_in()

    if reddit is None:
        return

    # Change to specified output directory
    app.filehelpers.create_directory(args.directory)
    os.chdir(args.directory)

    # Temp directory
    temp_dir = "temp"
    app.filehelpers.create_directory(temp_dir)

    # Image directory
    image_directory = time.strftime("%m-%d-%y", time.gmtime()) + "\\"

    # Log file path
    log_directory = args.directory + "Logs\\"
    log_path = log_directory + "log.txt"
    app.filehelpers.create_directory(log_directory)

    # Dictionary of domains incompatible with the program in the form domain (str) : number of appearances (int)
    incompatible_domains = {}

    # Retrieve user's saved posts
    saved_posts = reddit.redditor(str(reddit.user.me())).saved()

    index = 0
    for post in saved_posts:

        # Move on if the post is just a selfpost or link to a reddit thread
        if app.submissionhelpers.is_skippable(post):
            continue

        post = app.submissionhelpers.sanitize_post(post)

        # Attempt to download image from the url and record the result
        for i in range(len(post.recognized_urls)):
            url = post.recognized_urls[i][0]
            post.recognized_urls[i] = (url, app.urlhelpers.download_img_from(url,
                                                                             post.new_title,
                                                                             image_directory,
                                                                             temp=temp_dir))

        app.submissionhelpers.log_post(post, log_path)

        if app.submissionhelpers.is_parsed(post.recognized_urls):
            index += 1
            post.unsave()

        app.submissionhelpers.print_post(index, post)

        # End if the desired number of posts have had their images downloaded
        if index >= args.limit:
            break

    """ End-of-program cleanup """

    os.rmdir(temp_dir)

    if incompatible_domains:
        print("\nSeveral domains were unrecognized:")
        app.strhelpers.print_dict(incompatible_domains)

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
        print("signed in as " + str(reddit.user.me()) + ".\n")
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


def is_recognized(extension: str) -> bool:
    """
    Checks if the specified extension is recognized
    :param extension: the extension to check
    :return: True if the extension is recognized, False otherwise
    """
    return extension.lower() in [".png", ".jpg", ".jpeg", ".gif"]


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
