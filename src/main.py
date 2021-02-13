from utils import files, strings
from utils.submission_wrapper import SubmissionWrapper
import argparse
import getpass
import os
from prawcore.exceptions import OAuthException
import praw
from praw import Reddit

from typing import List, Optional, Tuple


# Represents a tuple in the form (URL (str), whether the URL was correctly downloaded (bool))
URLTuple = Tuple[str, bool]


temp_dir = "temp"
log_directory = "Logs"
log_path = os.path.join("Logs", "log.txt")


def main() -> None:
    """
    Scrapes and downloads any images from posts in the user's saved posts category on Reddit
    """
    read_client_info()

    if (reddit := prompt_sign_in()) is None:
        print("Username and password unrecognized.")
        return

    files.create_directory(temp_dir)
    files.create_directory(args.directory)    
    files.create_directory(log_directory)

    index = 0
    for post in reddit.user.me().saved():

        post = SubmissionWrapper(post, args.directory, args.png)
        
        if post.url_tuples:

            index += 1

            if not args.nolog:
                post.log(log_path)

            post.print_self(index)

            post.unsave()
            
            # End if the desired number of posts have had their images downloaded
            if index >= args.limit:
                break
    
    cleanup()


def cleanup():
    """ End-of-program cleanup """
    os.rmdir(temp_dir)

    """
    if incompatible_domains:
        print("\nSeveral domains were unrecognized:")
        for domain in sorted(incompatible_domains.items(), key=lambda x: x[1], reverse=True):
            print("\t{0}: {1}".format(domain[0], domain[1]))
    """


def prompt_sign_in() -> Optional[Reddit]:
    """
    Prompts the user to sign in
    :return: Reddit object
    """
    # getpass only works through the command line!
    if (username := input("Username: ")) and (password := getpass.getpass("Password: ")):
        print("Signing in...", end="")
        return sign_in(username, password)


def sign_in(username: str, password: str) -> Optional[Reddit]:
    """
    Attempts to sign into Reddit
    :param username: The user's username
    :param password: The user's password
    :return: reddit object if successful, else None
    :raises ConnectionException: if username and password were unrecognized
    """
    client_id, client_secret = read_client_info()

    try:
        return praw.Reddit(client_id=client_id,
                           client_secret=client_secret,
                           user_agent='PaperScraper',
                           username=username,
                           password=password)
    # Catch and re-raise error with a more helpful message
    except OAuthException:
        return None


def read_client_info(filepath: str = "info.txt") -> Tuple[str, str]:
    """
    Reads the client ID and client secret from the specified file
    :param filepath: filepath of the file to read the client id and secret from
    :return: tuple containing the client ID and secret in that order
    """
    assert os.path.isfile(filepath), filepath + " couldn't be found!"
    with open(filepath, 'r') as info_file:
        client_id = info_file.readline()
        client_secret = info_file.readline()
    # praw returns an invalid reddit instance if the  client id or client secret are ""
    assert client_id, "Client ID is blank!"
    assert client_secret, "Client Secret is blank!"
    return (client_id, client_secret)


if __name__ == "__main__":

    # region Argument Parsing

    parser = argparse.ArgumentParser(
        description="Scrapes images from the user's saved posts on Reddit")
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
