import datetime
import random
import uuid
from unittest.mock import Mock

from core.reddit import SubmissionWrapper


def SubmissionMockFactory(
    self,
    over_18=False,
    score=random.randint(-100, 100),
    created_utc=datetime.utcnow(),
    *args,
    **kwargs
):
    submission_mock = Mock()
    submission_mock.title = str(uuid.uuid4())
    submission_mock.subreddit = uuid.uuid4()
    submission_mock.url = str(uuid.uuid4())
    submission_mock.author = str(uuid.uuid4())
    submission_mock.submission.over_18 = over_18
    submission_mock.score = score
    submission_mock.created_utc = created_utc
    submission_mock.saved = Mock()
    return submission_mock


def SubmissionWrapperFactory(
    self, submission=None, client=Mock(), dry=True, *args, **kwargs
):
    if not submission:
        submission = SubmissionMockFactory(*args, **kwargs)

    return SubmissionWrapper(submission=submission, client=client, dry=dry)
