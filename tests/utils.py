import random
import uuid
from collections.abc import AsyncIterable, AsyncIterator
from datetime import datetime
from unittest.mock import Mock

from src.reddit import SubmissionWrapper


async def async_iter(items) -> AsyncIterator:
    """Yields each item from a sync iterable as an async iterator (test helper)"""
    for item in items:
        yield item


async def acollect(stream: AsyncIterable) -> list:
    """Drains an async iterable into a list (test helper)"""
    return [item async for item in stream]


def SubmissionMockFactory(
    title=None,
    subreddit=None,
    url=None,
    author=None,
    over_18=False,
    score=None,
    created_utc=None,
    *args,
    **kwargs,
):
    # generate unique values per call (defaults must not be shared across calls,
    # since several tests rely on distinct titles/urls)
    submission_mock = Mock()

    submission_mock.title = title if title is not None else str(uuid.uuid4())
    submission_mock.subreddit = subreddit if subreddit is not None else uuid.uuid4()
    submission_mock.url = url if url is not None else str(uuid.uuid4())
    submission_mock.author = author if author is not None else str(uuid.uuid4())
    submission_mock.over_18 = over_18
    submission_mock.score = score if score is not None else random.randint(-100, 100)
    submission_mock.created_utc = (
        created_utc if created_utc is not None else datetime.now()
    )

    submission_mock.unsave = Mock()

    for arg, value in kwargs.items():
        setattr(Mock, arg, value)

    return submission_mock


def SubmissionWrapperFactory(
    submission=None, client=Mock(), dry=True, *args, **kwargs
) -> SubmissionWrapper:
    if not submission:
        submission = SubmissionMockFactory(*args, **kwargs)

    return SubmissionWrapper(submission=submission, client=client, dry=dry)
