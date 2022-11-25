import asyncio
from datetime import timedelta
from enum import Enum
from typing import AsyncGenerator, Iterable, Iterator, Union

import praw
from praw.models import Comment, Submission
from praw.models.subreddits import Subreddit

from .submission_wrapper import SubmissionWrapper


class SortOption(Enum):
    """
    Represents the ways a subreddit's submissions can be sorted
    """

    def TOP_ALL(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="all", **kwargs)

    def TOP_DAY(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="day", **kwargs)

    def TOP_HOUR(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="hour", **kwargs)

    def TOP_WEEK(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="week", **kwargs)

    def TOP_MONTH(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="month", **kwargs)

    def TOP_YEAR(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="year", **kwargs)

    NEW = Subreddit.new
    HOT = Subreddit.hot
    CONTROVERSIAL = Subreddit.controversial
    GILDED = Subreddit.gilded

    def __call__(self, *args, **kwargs):
        self.value(*args, **kwargs)


class SubmissionSource:
    """
    Represents a source of reddit posts, such as a subreddit or user's saved posts
    """

    def __init__(
        self,
        source,
        download_limit: int,
        score_minimum: int = None,
        age_limit: timedelta = None,
    ):
        self.source = source
        self.limit = download_limit
        self.index = 0
        self.score_minimum = score_minimum
        self.age_limit = age_limit

        # raise ValueError(f"Expected source to be saved or a subreddit, got {args.source}")

        # Concurrently parse a handful of submissions up-front
        #  Very likely to save time, especially if there are enough valid posts
        self.initial_batch: Iterable[SubmissionWrapper] = [
            SubmissionWrapper(submission)
            for i, submission in enumerate(self.source)
            if i < 2 * self.limit
        ]
        asyncio.gather(submission.find_urls() for submission in self.initial_batch)
        self.initial_batch = (
            wrapper for wrapper in self.source if self.is_valid(wrapper)
        )

    def is_valid(self, wrapper: SubmissionWrapper) -> bool:
        """
        :return: True if the given post meets the minimum criteria to be parsed, else False
        """
        return (
            wrapper.score_at_least(self.score_minimum)
            and wrapper.older_than(self.age_limit)
            and len(wrapper.urls) > 0
        )

    # TODO: type should be Generator[Self, None, None], but mypy doesn't yet
    #  support the Self type (failing with 'typing.Self is not a valid type')
    async def __iter__(self) -> AsyncGenerator:
        for wrapper in self.initial_batch:
            yield wrapper
        for submission in self.source:
            wrapper = SubmissionWrapper(submission)
            await wrapper.find_urls()
            if self.index < self.limit and self.is_valid(wrapper):
                self.index += 1
                yield wrapper

    class Builder:
        """
        Builds SubmissionSources
        """

        def __init__(self) -> None:
            self._download_limit: int = None
            self._age_limit: timedelta = None
            self._score_min: int = None
            self.source: Iterator[Union[Comment, Submission]] = None

        def build(self):
            """
            Builds the SubmissionSource
            """
            return SubmissionSource(
                self.source, self._download_limit, self._score_min, self._age_limit
            )

        def from_user_saved(self, reddit: praw.Reddit):
            """
            Generates a source from a user's saved posts
            """
            self.source = reddit.user.me().saved(
                limit=None, score=self._score_min, age=self._age_limit
            )
            return self

        def from_subreddit(
            self, subreddit_name: str, sortby: SortOption, reddit: praw.Reddit
        ):
            """
            Generates a source from a subreddit
            """
            subreddit = reddit.subreddit(subreddit_name.rstrip("r/"))
            self.source_func = lambda score, age: sortby(
                subreddit, score=score, age=age
            )
            return self

        def download_limit(self, limit: int):
            """
            Sets the maximum number of files that will be downloaded and saved
            """
            self._download_limit = limit
            return self

        def score_min(self, score: int):
            """
            Sets the score min
            """
            self._score_min = score
            return self

        def age_limit(self, limit: timedelta):
            """
            Sets how old posts can be before they're ignored
            """
            self._age_limit = limit
            return self
