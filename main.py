import argparse
import getpass
import os
from typing import Iterable

from core import SortOption, sign_in
from core.reddit import SubmissionWrapper, from_saved_posts, from_subreddit

LOG_PATH = os.path.join("Logs", "log.txt")


def main() -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    os.makedirs(args.directory, exist_ok=True)
    os.chdir(args.directory)

    for i, wrapped in enumerate(get_source()):
        download_dir = "" if not args.organize else wrapped.subreddit
        try:
            wrapped.download_all(download_dir, title=args.title, organize=args.organize)
            if wrapped.can_unsave:
                wrapped.unsave()
            print(wrapped.summary_string(i))
        except Exception as exception:
            print(f"Encountered exception parsing {wrapped.url}:\n{exception}")
            return
        finally:
            if args.logging:
                wrapped.log(LOG_PATH)


def get_source() -> Iterable[SubmissionWrapper]:
    """Gets the program's submission source based on user args"""
    source_name = args.source.lower()
    if source_name == "saved":
        return from_saved_posts(
            redditor=sign_in(input("Username: "), getpass.getpass("Password: ")),
            score=args.karma,
            age=args.age,
            limit=args.limit,
            dry=args.dry,
        )
    if source_name.startswith("r/"):
        return from_subreddit(
            subreddit_name=source_name,
            sortby=args.sortby,
            score=args.karma,
            age=args.age,
            limit=args.limit,
        )
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
