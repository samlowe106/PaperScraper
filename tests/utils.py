import random
import uuid
from datetime import datetime
from unittest.mock import Mock

from core.reddit import SubmissionWrapper


def SubmissionMockFactory(
    title=str(uuid.uuid4()),
    subreddit=uuid.uuid4(),
    url=str(uuid.uuid4()),
    author=str(uuid.uuid4()),
    over_18=False,
    score=random.randint(-100, 100),
    created_utc=datetime.now(),
    *args,
    **kwargs
):
    submission_mock = Mock()

    submission_mock.title = title
    submission_mock.subreddit = subreddit
    submission_mock.url = url
    submission_mock.author = author
    submission_mock.over_18 = over_18
    submission_mock.score = score
    submission_mock.created_utc = created_utc

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
