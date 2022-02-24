import argparse
import os
from typing import Dict
from .view import View, view_factory
from .model import SubmissionSource, SORT_OPTIONS

LOG_DIRECTORY = "Logs"
LOG_PATH = os.path.join("Logs", "log.txt")



def main() -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    view = view_factory(args.web)

    run_info = view.get_run_info(args)

    for path in [run_info.directory, LOG_DIRECTORY]:
        os.makedirs(path, exist_ok=True)

    try:
        run(run_info, view)
    except Exception as e:
        view.output(str(e), error=True)

    view.show_results(run_info.directory)


def run(run_info: Dict[str, str], view: View) -> int:
    """
    Downloads all posts
    """
    i = 0
    for i, wrapped in enumerate(SubmissionSource(args, view)):
        wrapped.download_all(args.directory, run_info.title)
        if args.logging:
            wrapped.log(LOG_PATH)
        view.output_submission_wrapper(i, wrapped)
        if not args.dry:
            wrapped.unsave()
    return i


if __name__ == "__main__":

    # region Argument Parsing

    parser = argparse.ArgumentParser(
            description="Scrapes images from the user's saved posts on Reddit")

    parser.add_argument("source",
                        type=str,
                        help="specify where posts should be taken from. choices are:"\
                             "saved: user saved posts"\
                             "r/<subreddit>: posts from <>")

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
                        help="organize images from saved into folders by subreddit")
    parser.add_argument("-a",
                        "--age",
                        type=str,
                        # TODO: hours, days, months, etc?
                        help="specify the maximum age in hours a post can be to be downloaded")
    parser.add_argument("-k",
                        "--score",
                        type=int,
                        help="specify the minimum score a post must have to be downloaded")
    parser.add_argument("-s"
                        "--sortby",
                        type=str,
                        choices=SORT_OPTIONS,
                        default="hot",
                        help="specify how to sort the given source if it's a subreddit")
    parser.add_argument("--dry",
                        action='store_false',
                        help="do not unsave any posts, even those that were completely parsed")


    args = parser.parse_args()

    # endregion

    main()
