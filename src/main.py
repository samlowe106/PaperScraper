import argparse
import getpass
import os
from typing import Optional
from prawcore.exceptions import OAuthException
import praw
from praw import Reddit
from utils.submission_wrapper import SubmissionWrapper

LOG_DIRECTORY = "Logs"
LOG_PATH = os.path.join("Logs", "log.txt")


def main() -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    if (reddit := sign_in()) is None:
        print("Unrecognized username or password.")
        return

    for path in [args.directory, LOG_DIRECTORY]:
        os.makedirs(path, exist_ok=True)

    index = 0
    for post in reddit.user.me().saved():
        post = SubmissionWrapper(post)
        post.download_all(args.directory)
        if not args.nolog:
            post.log(LOG_PATH)
        if post.count_parsed() > 0:
            index += 1
            post.print_self(index)
            post.unsave()
            # End if the desired number of posts have had their images downloaded
            if index >= args.limit:
                break


def sign_in() -> Optional[Reddit]:
    """
    Attempts to sign into Reddit
    :param filepath: Path to the text file containing the client ID and client secret
    :return: reddit object if successful, else None
    """
    # getpass only works through the command line!
    if (username := input("Username: ")) and (password := getpass.getpass("Password: ")):
        print("Signing in...", end="")
        try:
            return praw.Reddit(client_id=os.environ.get("CLIENT_ID"),
                               client_secret=os.environ.get("CLIENT_SECRET"),
                               user_agent='PaperScraper',
                               username=username,
                               password=password)
        except OAuthException:
            pass
    return None


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

    """ NOT YET IMPLEMENTED
    parser.add_argument("-n",
                        "--name",
                        action='store_false',
                        help="append OP's name to the filename")

    parser.add_argument("-s",
                        "--sort",
                        action='store_false',
                        help="sort images into folders by subreddit")
    """

    parser.add_argument("--nolog",
                        action='store_true',
                        help="disable logging")


    args = parser.parse_args()

    # endregion

    main()
