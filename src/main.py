import argparse
import asyncio
import time
from getpass import getpass

import httpx
from dotenv import load_dotenv

from .core import AsyncClientBundle, Predicate, UniqueDirectoryFileManager
from .reddit import SortOption, StreamBuilder, SubmissionWrapper

MAX_FINDERS = 10
MAX_DOWNLOADS = 100


async def main(args: argparse.Namespace) -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    file_manager = UniqueDirectoryFileManager(args.directory, organize=args.organize)

    # semaphores are created here (not at module scope) so they bind to the event
    # loop running this call rather than whichever loop first touched them
    find_urls_sem = asyncio.Semaphore(MAX_FINDERS)
    download_sem = asyncio.Semaphore(MAX_DOWNLOADS)

    predicate = build_predicate(
        args.karma, max_age_seconds(args.hours, args.days, args.years)
    )

    tasks: list[asyncio.Task[list[str]]] = []
    async with asyncio.TaskGroup() as task_group, AsyncClientBundle() as clients:
        stream = await build_stream(
            clients,
            saved=args.saved,
            subreddits=args.subreddit,
            sortby=args.sortby,
            limit=args.limit,
            predicate=predicate,
        )

        async for wrapped in stream:
            tasks.append(
                task_group.create_task(
                    process_submission(
                        wrapped,
                        clients,
                        file_manager,
                        find_urls_sem,
                        download_sem,
                        log=args.log,
                        unsave=args.unsave,
                    )
                )
            )

    # process_submission never raises, so the group always joins cleanly and
    # every .result() is a (possibly empty) list of saved paths
    results: list[str] = [path for task in tasks for path in task.result()]

    print(f"Done -- saved {len(results)} file(s) from {len(tasks)} submission(s).")


def max_age_seconds(
    hours: int | None, days: int | None, years: int | None
) -> float | None:
    """The maximum post age in seconds implied by --hours/--days/--years, if any."""
    if hours is not None:
        return hours * 3600
    if days is not None:
        return days * 86400
    if years is not None:
        return years * 365 * 86400
    return None


def build_predicate(
    min_score: int | None, max_age: float | None
) -> Predicate[SubmissionWrapper]:
    """Builds a SubmissionWrapper filter from a score floor and a max age (seconds)."""

    def predicate(wrapped: SubmissionWrapper) -> bool:
        if min_score is not None and wrapped.score < min_score:
            return False
        if max_age is not None and (time.time() - wrapped.created_utc) > max_age:
            return False
        return True

    return predicate


async def build_stream(
    clients: AsyncClientBundle,
    *,
    saved: bool,
    subreddits: list[str],
    sortby: SortOption,
    limit: int,
    predicate: Predicate[SubmissionWrapper],
):
    builder = StreamBuilder(predicate=predicate, limit=limit)

    if saved:
        # input()/getpass() are blocking -- offload them so the loop stays free
        username = await asyncio.to_thread(input, "Reddit Username: ")
        password = await asyncio.to_thread(getpass, "Password: ")
        builder.set_redditor(username, password)

    for subreddit in subreddits:
        builder.add_subreddit(subreddit, sortby)

    return await builder.build(clients)


async def process_submission(
    wrapped: SubmissionWrapper,
    clients: AsyncClientBundle,
    file_manager: UniqueDirectoryFileManager,
    find_urls_sem: asyncio.Semaphore,
    download_sem: asyncio.Semaphore,
    *,
    log: bool = False,
    unsave: bool = False,
) -> list[str]:
    # Catch everything: this runs in a TaskGroup, so a propagating exception would
    # cancel every other submission and abort the whole run. One bad post should
    # just be skipped (and logged), not fatal.
    try:
        # find_urls needs the full bundle (parsers use http AND reddit)
        async with find_urls_sem:
            await wrapped.find_urls(clients)

        # download only needs the http client; awaiting inline keeps the result
        # reachable for collection while the download semaphore bounds concurrency
        saved = await process_download(
            wrapped, clients.http, file_manager, download_sem
        )

        # only un-save posts we actually downloaded something from
        if unsave and saved:
            await wrapped.unsave()

        if log:
            await file_manager.log(wrapped.log_record())

        if saved:
            print(f"saved {len(saved)} file(s): {wrapped.title}")

        return saved
    except Exception as e:
        print(f"error processing {wrapped.url}: {e}")
        if log:
            await file_manager.log(wrapped.log_record(exception=str(e)))
        return []


async def process_download(
    wrapped: SubmissionWrapper,
    client: httpx.AsyncClient,
    file_manager: UniqueDirectoryFileManager,
    download_sem: asyncio.Semaphore,
) -> list[str]:
    async with download_sem:
        return await file_manager.save_files(
            wrapped.title,
            await wrapped.download(client),
            subreddit=wrapped.subreddit,
        )


def build_parser() -> argparse.ArgumentParser:
    """Builds the CLI argument parser for the scraper."""
    parser = argparse.ArgumentParser(description="Scrapes images from Reddit")
    parser.add_argument(
        "--nolog",
        dest="log",
        action="store_false",
        help="disable writing a JSON log of processed posts",
    )
    parser.add_argument(
        "-u",
        "--saved",
        action="store_true",
        help="include saved posts from a reddit acount (requires login)",
    )
    parser.add_argument(
        "-r",
        "--subreddit",
        action="append",
        default=[],
        help="include posts from subreddit (repeatable)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="max number of submissions to pull from each source "
        "(an album submission may yield several images)",
    )
    parser.add_argument(
        "-d",
        "--dir",
        dest="directory",
        type=str,
        default="Output",
        help="directory that files should be saved to",
    )
    parser.add_argument(
        "-k",
        "--karma",
        type=int,
        help="specify the minimum score a post must have to be downloaded",
    )
    parser.add_argument(
        "--sortby",
        type=lambda s: SortOption[s.upper()],
        choices=list(SortOption),
        default=SortOption.HOT,
        # show lowercase names (e.g. {new,hot,top_all}) instead of "SortOption.NEW"
        metavar=f"{{{','.join(o.name.lower() for o in SortOption)}}}",
        help="specify how to sort the given subreddits",
    )
    parser.add_argument(
        "--unsave",
        action="store_true",
        help="un-save saved posts after successfully downloading them (requires login)",
    )
    parser.add_argument(
        "--organize",
        action="store_true",
        help="organize images from saved into folders by subreddit",
    )

    # only one age limit may be given at a time
    age = parser.add_mutually_exclusive_group()
    age.add_argument(
        "--hours", type=int, help="only include posts at most this many hours old"
    )
    age.add_argument(
        "--days", type=int, help="only include posts at most this many days old"
    )
    age.add_argument(
        "--years", type=int, help="only include posts at most this many years old"
    )
    return parser


def cli() -> None:
    """Console entry point: load env, parse args, and run the scraper."""
    load_dotenv()
    asyncio.run(main(build_parser().parse_args()))


if __name__ == "__main__":
    cli()
