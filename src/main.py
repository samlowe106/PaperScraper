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

find_urls_sem = asyncio.Semaphore(MAX_FINDERS)
download_sem = asyncio.Semaphore(MAX_DOWNLOADS)


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

    async with asyncio.TaskGroup() as task_group, AsyncClientBundle() as clients:

        stream = build_stream(args, clients)
        # endregion

        results: list[str] = []
        async for wrapped in stream:
            task_group.create_task(
                process_submission(wrapped, clients.http, task_group, file_manager)
            )

            # rework this to do all downloads at once:
            # 1) the batching,
            # 2) the url finding, and
            # 3) the downloading
            # to maximize concurrency and minimize the time spent waiting for a blocking response

            # the solution is that the batch should be the batch of SubmissionWrappers
            # with their urls already found, and then we can just do a big batch of downloads for
            # all the urls in that batch and save them all at once with the file manager

            # results += file_manager.save_files(
            #    title=wrapped.title,
            #    downloads=await wrapped.download(client),
            #    subreddit=wrapped.subreddit,
            # )

        # results = await download_all(await get_source(), client)

    for i, result in enumerate(results):
        print(f"({i}) {result}")


def build_stream(args, clients):
    builder = StreamBuilder()

    if args.saved:
        builder.set_redditor(input("Reddit Username: "), getpass("Password: "))

    for subreddit in args.subreddit:
        builder.add_subreddit(subreddit, args.sortby)

    return builder.build(clients)


async def process_submission(
    wrapped: SubmissionWrapper,
    client: httpx.AsyncClient,
    task_group: asyncio.TaskGroup,
    file_manager: UniqueDirectoryFileManager,
):
    async with find_urls_sem:
        await wrapped.find_urls(client)

    task_group.create_task(process_download(wrapped, client, file_manager))


async def process_download(
    wrapped: SubmissionWrapper,
    client: httpx.AsyncClient,
    file_manager: UniqueDirectoryFileManager,
):
    async with download_sem:
        # ensure file writing is non-blocking
        return await asyncio.to_thread(
            file_manager.save_files,
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
            wrapped.log(log_path, exception=exception)


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
        choices=SortOption,
        default="hot",
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
