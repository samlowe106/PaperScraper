import argparse
import getpass
import os

from core import sign_in
from core.models import SortOption, SubmissionSource

LOG_PATH = os.path.join("Logs", "log.txt")


def main() -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    os.makedirs(args.directory, exist_ok=True)
    os.chdir(args.directory)

    download_dir = ""

    for i, wrapped in enumerate(get_source()):
        if args.organize:
            download_dir = wrapped.subreddit
        try:
            wrapped.download_all(download_dir, args.title)
            if not args.dry:
                wrapped.unsave()
            print(wrapped.summary_string(i))
        except Exception as exception:
            print(f"Encountered exception parsing {wrapped.url}:\n{exception}")
            return
        finally:
            if args.logging:
                wrapped.log(LOG_PATH)


def get_source() -> SubmissionSource:
    """Gets the program's submission source based on user args"""
    source_builder = (
        SubmissionSource.Builder()
        .age_max(args.age)
        .submission_limit(args.limit)
        .score_min(args.karma)
    )
    source_name = args.source.lower()
    if source_name == "saved":
        return source_builder.from_user_saved(
            sign_in(input("Username: "), getpass.getpass("Password: "))
        ).build()
    if source_name.startswith("r/"):
        return source_builder.from_subreddit(
            source_name, args.sortby, sign_in()
        ).build()
    raise ValueError(
        f'Expected source to be "saved" or a subreddit\
        beginning with "r/", got {args.source}'
    )


if __name__ == "__main__":

    # region Argument Parsing

    parser = argparse.ArgumentParser(description="Scrapes images from Reddit")

    parser.add_argument("--logging", action="store_true", help="enable logging")
    parser.add_argument(
        "source",
        type=str,
        help="specify where posts should be taken from. choices are:"
        "saved: user saved posts"
        "r/<subreddit>: posts from <>",
    )
    parser.add_argument(
        "--limit", type=int, default=1000, help="max number of images to download"
    )
    parser.add_argument(
        "--directory",
        type=str,
        default="Output",
        help="directory that files should be saved to",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="%T",
        help="specify how the title should be saved. specifiers are:"
        "%t: current title\n"
        "%T: current title in Title Case\n"
        "%s: subreddit\n"
        "%a: author\n"
        "%u: submission's url\n"
        "%p: number of parsed urls\n"
        "%f: number of found urls\n"
        "%%: %",
    )
    parser.add_argument(
        "--karma",
        type=int,
        help="specify the minimum score a post must have to be downloaded",
    )
    parser.add_argument(
        "--sortby",
        choices=SortOption,
        default="hot",
        help="specify how to sort the given source if it's a subreddit",
    )
    parser.add_argument(
        "--dry",
        action="store_false",
        help="do not unsave any posts, even those that were completely parsed",
    )

    # TODO
    parser.add_argument(
        "--organize",
        action="store_false",
        help="organize images from saved into folders by subreddit",
    )
    parser.add_argument(
        "--age",
        type=str,
        # TODO: hours, days, months, etc?
        help="specify the maximum age in hours a post can be to be downloaded",
    )

    args = parser.parse_args()

    # endregion

    main()
