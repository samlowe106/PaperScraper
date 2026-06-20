import argparse
import asyncio
import os
from getpass import getpass

import httpx
from dotenv import load_dotenv

from .core import AsyncClientBundle, UniqueDirectoryFileManager

# from parsing import parsers
from .reddit import SortOption, StreamBuilder, SubmissionWrapper  # get_source

LOG_PATH = os.path.join("Logs", "log.txt")

MAX_FINDERS = 10
MAX_DOWNLOADS = 100


async def main(args) -> None:
    """Scrapes and downloads any images from posts in the user's saved posts category on Reddit"""

    # TODO: handle age argument and prevent user from entering multiple age args at once
    # age = None
    # if args.hours:
    #    age = args.hours * 3600
    # elif args.days:
    #    age = args.days * 3600 * 24
    # elif args.years:
    #    age = args.years * 3600 * 24 * 365

    # os.makedirs(args.directory, exist_ok=True)
    # os.chdir(args.directory)
    file_manager = UniqueDirectoryFileManager(args.directory, organize=args.organize)

    # semaphores are created here (not at module scope) so they bind to the event
    # loop running this call rather than whichever loop first touched them
    find_urls_sem = asyncio.Semaphore(MAX_FINDERS)
    download_sem = asyncio.Semaphore(MAX_DOWNLOADS)

    tasks: list[asyncio.Task[list[str]]] = []
    async with asyncio.TaskGroup() as task_group, AsyncClientBundle() as clients:

        stream = await build_stream(args, clients)
        # endregion

        async for wrapped in stream:
            tasks.append(
                task_group.create_task(
                    process_submission(
                        wrapped, clients, file_manager, find_urls_sem, download_sem
                    )
                )
            )

    # the TaskGroup has joined, so every task is finished and (since any failure
    # would have aborted the group) succeeded -- .result() is safe here
    results: list[str] = [path for task in tasks for path in task.result()]

    for i, result in enumerate(results):
        print(f"({i}) {result}")


async def build_stream(args, clients):
    builder = StreamBuilder()

    if args.saved:
        # input()/getpass() are blocking -- offload them so the loop stays free
        username = await asyncio.to_thread(input, "Reddit Username: ")
        password = await asyncio.to_thread(getpass, "Password: ")
        builder.set_redditor(username, password)

    for subreddit in args.subreddit:
        builder.add_subreddit(subreddit, args.sortby)

    return builder.build(clients)


async def process_submission(
    wrapped: SubmissionWrapper,
    clients: AsyncClientBundle,
    file_manager: UniqueDirectoryFileManager,
    find_urls_sem: asyncio.Semaphore,
    download_sem: asyncio.Semaphore,
) -> list[str]:
    # find_urls needs the full bundle (parsers use http AND reddit)
    async with find_urls_sem:
        await wrapped.find_urls(clients)

    # download only needs the http client; awaiting inline keeps the result
    # reachable for collection while the download semaphore still bounds concurrency
    return await process_download(wrapped, clients.http, file_manager, download_sem)


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


# async def download_all(
#    source: Iterable[SubmissionWrapper], client: httpx.AsyncClient
# ) -> list[tuple[SubmissionWrapper, list[tuple[bytes, str]]]]:
#    return await asyncio.gather(
#        *(
#            (wrapped, await wrapped.find_urls(parsers).download(client))
#            for wrapped in source
#        )
#    )

# async def urls_responses(
#    urls: str, client: httpx.AsyncClient
# ) -> Future[list[tuple[str, httpx.Response]]]:
#    """
#    Gets the responses for a list of urls
#    :param urls: a list of urls to get responses for
#    :param client: the httpx.AsyncClient to use for getting responses
#    :return: a list of tuples, where the first element is the url and the second element is the response for that url
#    """
#
#    async def fetch(url: str) -> tuple[str, httpx.Response]:
#        return url, await client.get(url, timeout=10)
#
#    return asyncio.gather(*(fetch(url) for url in urls))


async def handle_wrapped(
    wrapped: SubmissionWrapper,
    client: httpx.AsyncClient,
    organize: bool,
    title: str,
    log_path: str = None,
    dry: bool = True,
) -> str:
    exception = ""
    try:
        # download_dir = "" if not organize else wrapped.subreddit
        await wrapped.download(client)
        if not dry:
            await wrapped.unsave()
        return str(wrapped)  # .summary_string()
    except Exception as e:
        exception = str(e)
        return f"Encountered exception parsing {wrapped.url}:\n{exception}"
    finally:
        if log_path is not None:
            await wrapped.log(log_path, exception=exception)


if __name__ == "__main__":

    load_dotenv()

    # region Argument Parsing

    parser = argparse.ArgumentParser(description="Scrapes images from Reddit")
    parser.add_argument("--nolog", action="store_false", help="enable logging")
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
        help="max number of images to download from each source",
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=str,
        default="Output",
        help="directory that files should be saved to",
    )
    parser.add_argument(
        "-t" "--title",
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
        help="specify how to sort the given subreddits",
    )
    parser.add_argument(
        "--dry",
        action="store_false",
        help="do not unsave any posts, even those that were completely parsed",
    )
    parser.add_argument(
        "--organize",
        action="store_true",
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
