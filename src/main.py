import argparse
import os
from typing import List, Optional
from prawcore.exceptions import OAuthException
from praw import Reddit
from praw.models import Submission
from .view import TerminalView, FlaskWebView, View
from .model import SubmissionWrapper

LOG_DIRECTORY = "Logs"
LOG_PATH = os.path.join("Logs", "log.txt")


def main() -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    if args.web:
        view = FlaskWebView()
    else:
        view = TerminalView()

    run_info = view.get_run_info(args)
    reddit = sign_in(run_info["username"], run_info["password"])

    if reddit is None:
        view.output("Unrecognized username or password.", error=True)
        if not args.web:
            return

    for path in [args.directory, LOG_DIRECTORY]:
        os.makedirs(path, exist_ok=True)

    download_from_list(reddit.user.me().saved(), view, limit=args.limit)

    view.show_results(args.directory)



def sign_in(username: str, password: str) -> Optional[Reddit]:
    """Signs in to reddit"""
    if not (username and password):
        return None
    try:
        return Reddit(client_id=os.environ.get("CLIENT_ID"),
                      client_secret=os.environ.get("CLIENT_SECRET"),
                      user_agent='PaperScraper',
                      username=username,
                      password=password)
    except OAuthException:
        return None


def download_from_list(submissions: List[Submission], view: View, limit: int = 1000) -> int:
    """
    Downloads all posts from the given list
    """
    count = 0
    for submission in submissions:
        wrapped = SubmissionWrapper(submission)
        wrapped.download_all(args.directory, args.title)
        if args.logging:
            wrapped.log(LOG_PATH)
        if wrapped.count_parsed() > 0:
            index += 1
            view.output_submission_wrapper(count, wrapped)
            wrapped.unsave()
            # End if the desired number of posts have had their images downloaded
            if count >= limit:
                break
    return count


if __name__ == "__main__":

    # region Argument Parsing

    parser = argparse.ArgumentParser(
            description="Scrapes images from the user's saved posts on Reddit")

    """ Required arguments """

    parser.add_argument("username",
                        type=str,
                        help="username of the reddit account from which to get saved posts")

    """ Optional arguments """

    parser.add_argument("-l",
                        "--limit",
                        type=int,
                        default=1000,
                        help="max number of images to download")
    parser.add_argument("-w",
                        "--web",
                        action="store_true",
                        help="runs in web mode")
    parser.add_argument("-d",
                        "--directory",
                        type=str,
                        default="Output",
                        help="directory that files should be saved to")
    parser.add_argument("-t",
                        "--title",
                        type=str,
                        default="%T",
                        help="specify how the title should be saved. specifiers are:"\
                            "%t: current title\n"\
                            "%T: current title in Title Case\n"\
                            "%s: subreddit\n"\
                            "%a: author\n"\
                            "%u: submission's url\n"\
                            "%p: number of parsed urls\n"\
                            "%f: number of found urls\n"
                            "%%: %")
    parser.add_argument("--logging",
                        action='store_true',
                        help="enable logging")

    """ NOT YET IMPLEMENTED """

    parser.add_argument("-o",
                        "--organize",
                        action='store_false',
                        help="organize images into folders by subreddit")

    parser.add_argument("-s",
                        "--source",
                        type=str,
                        help="specify where posts should be taken from. choices are:"\
                            "saved: user saved posts"\
                            "r/<subreddit>: posts from <>")

    parser.add_argument("-a",
                        "--age",
                        type=str,
                        help="specify the maximum age in hours a post can be to be downloaded")

    parser.add_argument("-k",
                        "--karma",
                        type=int,
                        help="specify the minimum karma a post must have to be downloaded")

    parser.add_argument("--sort",
                        type=str,
                        help="specify whether to sort the given subreddit source by 'top', 'new', 'hot', or 'controversial'")
    # TODO: add more options based on what praw offers

    args = parser.parse_args()

    # endregion

    main()
