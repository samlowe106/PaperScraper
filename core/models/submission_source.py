from enum import Enum
from typing import Callable
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


class SubmissionSource:
    """
    Represents a source of reddit posts, such as a subreddit or user's saved posts
    """

    def __init__(self, source, limit):
        self.source = source
        self.limit = limit
        self.index = 0

        # raise ValueError(f"Expected source to be saved or a subreddit, got {args.source}")

    def __iter__(self) -> SubmissionWrapper:
        for submission in self.source:
            wrapper = SubmissionWrapper(submission)
            if (self.index < self.limit
#               and wrapper.score_at_least(self.score_minimum)
#               and wrapper.posted_after()
                and wrapper.count_parsed() > 0):
                self.index += 1
                yield SubmissionWrapper(submission)


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
            return SubmissionSource(self.source_func(score=self.score, age=self.age), self.limit)


        def from_user_saved(self, reddit):
            """
            Generates a source from a user's saved posts
            """
            self.source_func = reddit.user.me().saved
            return self


        def from_subreddit(self, subreddit_name: str, sortby: SortOption, reddit: Reddit):
            """
            Generates a source from a subreddit
            """
            subreddit = reddit.subreddit(subreddit_name.rstrip("r/"))
            self.source_func = lambda score, age: sortby(subreddit, score=score, age=age)
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
