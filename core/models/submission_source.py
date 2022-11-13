import asyncio
from enum import Enum
from typing import AsyncGenerator, Callable, Iterable

from praw import Reddit
from praw.models.subreddits import Subreddit

from .submission_wrapper import SubmissionWrapper


class SortOption(Enum):
    """
    Represents the ways a subreddit's submissions can be sorted
    """

    TOP = Subreddit.top
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

    def __init__(self, source, limit: int):
        self.source = source
        self.limit = limit
        self.index = 0

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
        # TODO
        # and wrapper.score_at_least(self.score_minimum)
        # and wrapper.posted_after()
        return len(wrapper.urls) > 0

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
            self.limit: int = None
            self.age = None
            self.score: int = None
            self.source_func: Callable = None

        def build(self):
            """
            Builds the SubmissionSource
            """
            return SubmissionSource(
                self.source_func(score=self.score, age=self.age), self.limit
            )

        def from_user_saved(self, reddit):
            """
            Generates a source from a user's saved posts
            """
            self.source_func = reddit.user.me().saved
            return self

        def from_subreddit(
            self, subreddit_name: str, sortby: SortOption, reddit: Reddit
        ):
            """
            Generates a source from a subreddit
            """
            subreddit = reddit.subreddit(subreddit_name.rstrip("r/"))
            self.source_func = lambda score, age: sortby(
                subreddit, score=score, age=age
            )
            return self

        def submission_limit(self, limit: int):
            """
            Sets the submission limit
            """
            self.limit = limit
            return self

        def score_min(self, score: int):
            """
            Sets the score min
            """
            self.score = score
            return self

        def age_max(self, age_max):
            """
            Sets how old posts can be before they're ignored
            """
            self.age = age_max
            return self
