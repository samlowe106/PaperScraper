from collections.abc import AsyncIterable
from typing import Self

import asyncpraw

from ..core import AsyncClientBundle, Predicate, afilter, amap, merge
from .sortoption import SortOption
from .submission_wrapper import SubmissionWrapper


class StreamBuilder:

    # currently does not support custom predicates for each source
    #  i.e. one predicate for redditor saved, another for subreddit 1,
    #  a third for subreddit 2, etc etc -- we insist on one predicate
    #  to rule them all

    def __init__(
        self,
        sortby: SortOption = SortOption.HOT,
        predicate: Predicate[SubmissionWrapper] = lambda x: True,
    ):
        self.sortby = sortby
        self.predicate = predicate
        # per-subreddit predicates aren't supported right now
        self.subreddits: list[tuple[str, SortOption]] = []
        self.redditor: tuple[str, str] = None

    def add_subreddit(self, name: str, sortby: SortOption = None) -> Self:
        name = name.lower().removeprefix("r/")
        if sortby is None:
            sortby = self.sortby
        self.subreddits.append((name, sortby))
        return self

    def set_redditor(self, username: str, password: str) -> Self:
        self.redditor = (username, password)
        return self

    # def set_default_predicate(self, predicate: Predicate) -> Self:
    #    self.predicate = predicate
    #    return self

    def set_default_sortby(self, sortby: SortOption) -> Self:
        self.sortby = sortby
        return self

    def build(self, clients: AsyncClientBundle) -> AsyncIterable[SubmissionWrapper]:

        reddit = clients.set_reddit(
            username=self.redditor[0] if self.redditor else None,
            password=self.redditor[1] if self.redditor else None,
        )

        streams: asyncpraw.models.ListingGenerator = []

        if self.redditor:
            streams.append(reddit.redditor(self.redditor[0]))

        for name, sortby in self.subreddits:
            streams.append(sortby(reddit.subreddit(name)))

        stream: AsyncIterable[asyncpraw.models.Submission] = merge(streams)

        def mapfunc(submission: asyncpraw.models.Submission) -> SubmissionWrapper:
            return SubmissionWrapper(submission, clients.http)

        return afilter(self.predicate, amap(mapfunc, stream))


"""
class SubredditStream:

    def __init__(
        self,
        predicate: Callable[[SubmissionWrapper], bool],
        subreddit: asyncpraw.models.Subreddit,
        sortby: SortOption,
        *args,
        **kwargs,
    ):
        self.predicate = predicate
        self.stream = subreddit.top(*args, **kwargs)  # example

    def __iter__(self) -> Self:
        return self

    async def __anext__(self) -> AsyncIterator[SubmissionWrapper]:
        async for wrapped in self.stream:
            if self.predicate(wrapped):
                yield wrapped


class SavedStream:

    def __init__(
        self,
        predicate: Callable[[SubmissionWrapper], bool],
        redditor: asyncpraw.models.Redditor,
        *args,
        **kwargs,
    ):
        self.predicate = predicate
        self.stream = redditor.saved(*args, **kwargs)

    def __iter__(self) -> Self:
        return self

    async def __anext__(self) -> AsyncIterator[SubmissionWrapper]:
        async for wrapped in self.stream:
            if self.predicate(wrapped):
                yield wrapped


from collections.abc import AsyncIterable
from dataclasses import dataclass

@dataclass
class SubmissionStream:

    predicate: Callable[[SubmissionWrapper], bool]
    stream: AsyncIterable[SubmissionWrapper]

    def __iter__(self) -> Self:
        return self

    async def __anext__(self) -> AsyncIterator[SubmissionWrapper]:
        async for wrapped in self.stream:
            if self.predicate(wrapped):
                yield wrapped
"""
