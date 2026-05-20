import argparse
import asyncio
import os

import httpx
from dotenv import load_dotenv

from src.reddit import SortOption, SubmissionWrapper, get_source

LOG_PATH = os.path.join("Logs", "log.txt")


async def main(args) -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    # TODO: handle age argument and prevent user from entering multiple age args at once
    age = None
    if args.hours:
        age = args.hours * 3600
    elif args.days:
        age = args.days * 3600 * 24
    elif args.years:
        age = args.years * 3600 * 24 * 365

    os.makedirs(args.directory, exist_ok=True)
    os.chdir(args.directory)

    async with httpx.AsyncClient() as client:
        batch = await get_source(
            client,
            args.source,
            args.limit,
            args.karma,
            age,
            args.dry,
            args.sortby,
        )
        results = await asyncio.gather(
            *(
                handle_wrapped(wrapped, client, args.organize, args.title, LOG_PATH)
                for wrapped in batch
            )
        )

    for i, result in enumerate(results):
        print(f"({i}) {result}")


async def handle_wrapped(
    wrapped: SubmissionWrapper,
    client: httpx.AsyncClient,
    organize: bool,
    title: str,
    log_path: str = None,
) -> str:
    exception = ""
    try:
        download_dir = "" if not organize else wrapped.subreddit
        await wrapped.download_all(
            download_dir,
            client,
            title=title,
            organize=organize,
        )
        if wrapped.can_unsave:
            wrapped.unsave()
        return wrapped.summary_string()
    except Exception as e:
        exception = str(e)
        return f"Encountered exception parsing {wrapped.url}:\n{exception}"
    finally:
        if log_path is not None:
            wrapped.log(log_path, exception=exception)


if __name__ == "__main__":

    load_dotenv()

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
    """
    parser.add_argument(
        "--hours",
        type=int,
        help="specify the maximum age in hours a post can be to be downloaded",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="specify the maximum age in days a post can be to be downloaded",
    )
    parser.add_argument(
        "--years",
        type=int,
        help="specify the maximum age in years a post can be to be downloaded",
    )
    """

    args = parser.parse_args()

    # endregion

    asyncio.run(main(args))
