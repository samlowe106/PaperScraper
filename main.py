import argparse
import asyncio
import getpass
import os
from typing import Iterable

import httpx
from dotenv import load_dotenv

from core import SortOption, sign_in
from core.reddit import SubmissionWrapper, from_saved, from_subreddit

LOG_PATH = os.path.join("Logs", "log.txt")


async def main() -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    os.makedirs(args.directory, exist_ok=True)
    os.chdir(args.directory)

    async with httpx.AsyncClient() as client:
        batch = await get_source(client)
        results = await asyncio.gather(
            handle_wrapped(wrapped, client) for wrapped in batch
        )

    for i, result in enumerate(results):
        print(f"({i}) {result}")


async def handle_wrapped(wrapped: SubmissionWrapper, client: httpx.AsyncClient) -> str:
    exception = ""
    try:
        download_dir = "" if not args.organize else wrapped.subreddit
        await wrapped.download_all(
            download_dir,
            client,
            title=args.title,
            organize=args.organize,
        )
        if wrapped.can_unsave:
            wrapped.unsave()
        return wrapped.summary_string()
    except Exception as e:
        exception = str(e)
        return f"Encountered exception parsing {wrapped.url}:\n{exception}"
    finally:
        if args.logging:
            wrapped.log(LOG_PATH, exception=exception)


async def get_source(client: httpx.AsyncClient) -> Iterable[SubmissionWrapper]:
    """Gets the program's submission source based on user args"""
    source_name = args.source.lower()
    if source_name == "saved":
        return await from_saved(
            sign_in(input("Username: "), getpass.getpass("Password: ")),
            client,
            amount=args.limit,
            score=args.karma,
            age=args.age,
            dry=args.dry,
        )
    if source_name.startswith("r/"):
        return await from_subreddit(
            sign_in(),
            source_name,
            args.sortby,
            client,
            score=args.karma,
            age=args.age,
            amount=args.limit,
        )
    raise ValueError(
        f'Expected source to be "saved" or a subreddit\
        beginning with "r/", got {args.source}'
    )


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
        "--age",
        type=str,
        # TODO: hours, days, months, etc?
        help="specify the maximum age in hours a post can be to be downloaded",
    )
    """

    args = parser.parse_args()

    # endregion

    with asyncio.get_event_loop() as loop:
        loop.run_until_complete(main())
