from app.strhelpers import *
from app.filehelpers import convert_to_png, create_directory
from app.imagehelpers import download_image, find_urls
import argparse
from getpass import getpass
from os import chdir
from prawcore.exceptions import OAuthException
import praw
from time import gmtime
from time import strftime
from typing import Dict, Optional
from urllib.parse import urlparse


def main() -> None:
    """
    Scrapes and downloads any images from posts in the user's saved posts category on Reddit
    :return: None
    """
    reddit = attempt_sign_in()

    # Change to specified output directory
    create_directory(args.directory)
    chdir(args.directory)

    # Image directory
    image_directory = strftime("%m-%d-%y", gmtime()) + "\\"

    # Log file path
    log_directory = args.directory + "Logs\\"
    log_path = log_directory + "log.txt"
    domain_log_path = log_directory + "incompatible.txt"
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

        index += 1

        post = sanitize_post(post)

        # Parse the image link
        for i, url in enumerate(post.recognized_urls):
            downloaded_file = download_image(post.new_title, url, image_directory)
            if downloaded_file != "":
                post.images_downloaded.append(downloaded_file)
                if args.png:
                    convert_to_png(image_directory, downloaded_file)

        log_post(post, log_path)

        if post.images_downloaded:
            post.unsave()
        else:
            log_domain(post.url, domain_log_path, post.images_downloaded)

        # End if the desired number of images has been downloaded
        if index >= args.limit:
            break

    """ End-of-program cleanup """

    if incompatible_domains:
        print("\nSeveral domains were unrecognized:")

    print_dict(incompatible_domains)

    return


def attempt_sign_in() -> Optional[praw.Reddit]:
    """
    Prompts the user to sign in
    :return: Reddit object
    """
    username = input("Username: ")
    password = getpass("Password: ")  # Only works through the command line!

    print("Signing in...", end="")
    reddit = sign_in(username, password)

    if reddit is not None:
        print("signed in as " + str(reddit.user.me()) + ".\n")
    else:
        print("unrecognized username or password.\n")

    return reddit


def sign_in(username: str, password: str) -> Optional[praw.Reddit]:
    """
    Attempts to sign into Reddit
    :param username: The user's username
    :param password: The user's password
    :return: reddit object if successful, else None
    """

    reddit = None

    if username and password:  # (praw stack overflows if both username and password are "")
        with open("info.txt", 'r') as info_file:
            try:
                reddit = praw.Reddit(client_id=info_file.readline(),
                                     client_secret=info_file.readline(),
                                     user_agent='PaperScraper',
                                     username=username,
                                     password=password)
            # Suppress error if username/password were unrecognized
            except OAuthException:
                pass

    return reddit


def is_skippable(post) -> bool:
    """
    Determines if a given reddit post can be skipped or not
    :param post: a reddit post object
    :return: True if the given post is a comment, selfpost, or links to another reddit post, else False
    """
    return (not hasattr(post, 'title')) or post.is_self or "https://reddit.com/" in post.url


def sanitize_post(post):
    """
    Fixes post's title and finds post's urls
    :param post: a post object
    :return: the same post with additional new_title and recognized_urls fields
    """
    post.recognized_urls = find_urls(post.url)
    post.new_title = retitle(post.title)
    if args.titlecase:
        post.new_title = title_case(post.new_title)
    return post


def log_post(post, file_path: str) -> None:
    """
    Writes the given post's title and url to the specified file
    :param post: reddit post object
    :param file_path: log file path
    :return: None
    """
    with open(file_path, "a", encoding="utf-8") as log_file:
        log_file.write(post.title + " : " + post.url + " : " + str(bool(post.images_downloaded)) + '\n')

    return


def log_domain(url: str, file_path: str, domain_dict: Dict[str, int]) -> None:
    """
    Logs the domain of an url that wasn't compatible with the program
    :param url: url that wasn't compatible
    :param file_path: the path of the log file to be written to
    :param domain_dict: dictionary mapping each incompatible domain (str) to the number of times it's appeared (int)
    :return: None
    """
    # Establish the post's domain
    uri = urlparse(url)
    domain = '{0}://{1}'.format(uri.scheme, uri.netloc)

    # Save that domain to a dictionary
    if domain in domain_dict.keys():
        domain_dict[domain] += 1
    else:
        domain_dict[domain] = 1

    # Update the log file
    with open(file_path, "a") as log_file:
        for domain in domain_dict.keys():
            log_file.write(domain + " : " + str(domain_dict[domain]) + "\n")

    return None


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

    # region NOT YET IMPLEMENTED
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
    # endregion

    args = parser.parse_args()

    # endregion

    main()
