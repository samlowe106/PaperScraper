import random
import uuid
from collections.abc import AsyncIterable, AsyncIterator
from datetime import datetime
from unittest.mock import MagicMock, Mock

import httpx

from src.core import make_http_client
from src.reddit import SubmissionWrapper


async def async_iter(items) -> AsyncIterator:
    """Yields each item from a sync iterable as an async iterator (test helper)"""
    for item in items:
        yield item


async def acollect(stream: AsyncIterable) -> list:
    """Drains an async iterable into a list (test helper)"""
    return [item async for item in stream]


# the fields every listing Submission has that the code reads
_SUBMISSION_FIELDS = [
    "id",
    "title",
    "subreddit",
    "url",
    "author",
    "over_18",
    "score",
    "created_utc",
    "unsave",
]


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
    # spec: like a real Submission, reading a field it doesn't have raises
    # AttributeError. A bare Mock would invent is_gallery, gallery_data, etc.,
    # and every fake post would look like a gallery
    submission_mock = Mock(spec=_SUBMISSION_FIELDS)

    submission_mock.id = uuid.uuid4().hex[:7]
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
        setattr(submission_mock, arg, value)

    return submission_mock


def SubmissionWrapperFactory(submission=None, *args, **kwargs) -> SubmissionWrapper:
    if not submission:
        submission = SubmissionMockFactory(*args, **kwargs)

    return SubmissionWrapper(submission=submission)


def mock_http_bundle(handler) -> MagicMock:
    """
    A client bundle whose http client is the real, production-configured one,
    with requests answered by handler (an httpx.Request -> httpx.Response
    function) instead of the network. Unlike an AsyncMock client, this rejects
    calls httpx wouldn't accept and behaves like httpx does (redirects,
    streaming, headers).
    """
    bundle = MagicMock()
    bundle.http = make_http_client(transport=httpx.MockTransport(handler))
    return bundle
