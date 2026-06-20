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
        limit: int | None = None,
    ):
        self.sortby = sortby
        self.predicate = predicate
        self.limit = limit  # max submissions to pull from each source
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

    def set_default_sortby(self, sortby: SortOption) -> Self:
        self.sortby = sortby
        return self

    async def build(
        self, clients: AsyncClientBundle
    ) -> AsyncIterable[SubmissionWrapper]:

        reddit = clients.set_reddit(
            username=self.redditor[0] if self.redditor else None,
            password=self.redditor[1] if self.redditor else None,
        )

        streams: list[AsyncIterable[asyncpraw.models.Submission]] = []

        if self.redditor:
            # saved posts belong to the authenticated user; reddit.user.me() and
            # reddit.redditor() are coroutines, so build() has to be async
            me = await reddit.user.me()
            streams.append(me.saved(limit=self.limit))

        for name, sortby in self.subreddits:
            streams.append(sortby(reddit.subreddit(name), limit=self.limit))

        stream: AsyncIterable[asyncpraw.models.Submission] = merge(*streams)

        def mapfunc(submission: asyncpraw.models.Submission) -> SubmissionWrapper:
            return SubmissionWrapper(submission, clients.http)

        # saved() can also yield Comments; we only handle Submissions
        submissions = afilter(
            lambda item: not isinstance(item, asyncpraw.models.Comment), stream
        )

        return afilter(self.predicate, amap(mapfunc, submissions))
