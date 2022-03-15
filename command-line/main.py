import argparse
import getpass
import os
from PaperScraper.core.models import SubmissionSource, SortOption
from PaperScraper.core import sign_in

LOG_DIRECTORY = "Logs"
LOG_PATH = os.path.join("Logs", "log.txt")


def main() -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    for path in [args.directory, LOG_DIRECTORY]:
        os.makedirs(path, exist_ok=True)

    source_builder = (SubmissionSource.Builder()
            .age_max(args.age)
            .submission_limit(args.limit)
            .score_min(args.karma))

    if args.source == "saved":
        if not args.username:
            print("Source was specified as saved posts, but no username was given")
            return
        source = (source_builder
            .from_user_saved(sign_in(args.username, getpass.getpass("Password: ")))
            .build())
    elif args.source.startswith("r/"):
        source = (source_builder
            .from_subreddit(args.source, args.sortby, sign_in())
            .build())
    else:
        print(f'Expected source to be "saved" or a subreddit beginning with "r/", got {args.source}')
        return

    for i, wrapped in enumerate(source):
        try:
            wrapped.download_all(args.directory, args.title)
            print(
                f"({i})\t{wrapped.title}\n"\
                f"\t{wrapped.url}\n"
                f"\t{wrapped.parsed} / {wrapped.found} posts parsed")
            if not args.dry:
                wrapped.unsave()
        except Exception as exception:
            print(f"Encountered uncaught exception parsing post with url {wrapped.url}\n{exception}")
            return
        finally:
            if args.logging:
                wrapped.log(os.path.join(args.directory, LOG_PATH))


if __name__ == "__main__":

    # region Argument Parsing

    parser = argparse.ArgumentParser(
            description="Scrapes images from Reddit")

    parser.add_argument("--logging",
                        action='store_true',
                        help="enable logging")
    parser.add_argument("source",
                        type=str,
                        help="specify where posts should be taken from. choices are:"\
                             "saved: user saved posts"\
                             "r/<subreddit>: posts from <>")
    parser.add_argument("--limit",
                        type=int,
                        default=1000,
                        help="max number of images to download")
    parser.add_argument("--directory",
                        type=str,
                        default="Output",
                        help="directory that files should be saved to")
    parser.add_argument("--title",
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
    parser.add_argument("--karma",
                        type=int,
                        help="specify the minimum score a post must have to be downloaded")
    parser.add_argument("--sortby",
                        type=str,
                        choices=SortOption,
                        default="hot",
                        help="specify how to sort the given source if it's a subreddit")
    parser.add_argument("--dry",
                        action='store_false',
                        help="do not unsave any posts, even those that were completely parsed")

    # TODO
    parser.add_argument("--organize",
                        action='store_false',
                        help="organize images from saved into folders by subreddit")
    parser.add_argument("--age",
                        type=str,
                        # TODO: hours, days, months, etc?
                        help="specify the maximum age in hours a post can be to be downloaded")


    args = parser.parse_args()

    # endregion

    main()
