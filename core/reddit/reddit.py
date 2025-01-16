import asyncio
import itertools
import os
from datetime import timedelta
from typing import Callable, Iterable, List

import httpx
import praw
from praw.models import ListingGenerator, Redditor

from .sortoption import SortOption
from .submission_wrapper import SubmissionWrapper


def sign_in(username: str = None, password: str = None) -> praw.Reddit:
    """
    Signs in to reddit

    :raises OAuthException:
    """
    if username and password:
        return praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent="PaperScraper",
            username=username,
            password=password,
        )
    return praw.Reddit(
        client_id=os.environ.get("REDDIT_CLIENT_ID"),
        client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
        user_agent="PaperScraper",
    )


def has_urls(wrapped: SubmissionWrapper) -> bool:
    """
    Returns True if the given SubmissionWrapper has at least one url, else False
    """
    return len(wrapped.urls) > 0


async def _from_source(
    source: ListingGenerator,
    client: httpx.AsyncClient,
    amount: int = 10,
    dry: bool = True,
    criteria: Callable[[SubmissionWrapper], bool] = has_urls,
) -> List[SubmissionWrapper]:
    """
    Returns a list containing at most amount number of SubmissionWrappers,
    created from posts from the given source
    """
    if amount < 1:
        raise ValueError("Amount must be a positive integer")
    # get batches of 2 * amount and filter out the ones that don't have urls
    #  until we have enough. Worst case (for a single iteration) is that we only need 1
    #  additional post to reach the desired amount but try_amount is large
    try_amount = 2 * amount
    batch: List[SubmissionWrapper] = []
    exhausted = False
    while (not exhausted) and len(batch) < amount:
        prospective = [
            SubmissionWrapper(submission, client, dry=dry)
            for submission in itertools.islice(source, try_amount)
        ]
        # await all the urls
        await asyncio.gather(
            *(submission.find_urls(client) for submission in prospective)
        )
        if len(prospective) <= try_amount:
            exhausted = True

        batch += list(filter(criteria, prospective))
    return batch[:amount]


async def from_saved(
    redditor: Redditor,
    client: httpx.AsyncClient,
    score: int = None,
    age: timedelta = None,
    amount: int = 10,
    dry: bool = True,
    criteria: Callable[[SubmissionWrapper], bool] = has_urls,
) -> List[SubmissionWrapper]:
    """Generates a batch of at most (amount) SubmissionWrappers from the given users' saved posts"""
    if amount < 1:
        raise ValueError("Amount must be a positive integer")
    return await _from_source(
        redditor.saved(limit=None, score=score, age=age),
        client,
        amount=amount,
        dry=dry,
        criteria=criteria,
    )


async def from_subreddit(
    reddit: praw.Reddit,
    subreddit_name: str,
    sort_by: SortOption,
    client: httpx.AsyncClient,
    score: int = None,
    age: timedelta = None,
    amount: int = 10,
    criteria: Callable[[SubmissionWrapper], bool] = has_urls,
) -> Iterable[SubmissionWrapper]:
    """Generates a batch of at most (amount) SubmissionWrappers from the given subreddit"""
    if amount < 1:
        raise ValueError("Amount must be a positive integer")
    return await _from_source(
        sort_by(
            reddit.subreddit(subreddit_name.removeprefix("r/")), score=score, age=age
        ),
        client,
        amount=amount,
        dry=True,  # Can't/shouldn't unsave posts from subreddits
        criteria=criteria,
    )
