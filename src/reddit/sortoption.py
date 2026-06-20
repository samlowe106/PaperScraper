from enum import Enum, member
from functools import partial


class SortOption(Enum):
    """
    Represents the ways a subreddit's submissions can be sorted.

    Each member's value is a ``functools.partial`` wrapping a small lambda that
    delegates to the subreddit's listing method, so ``SortOption.HOT(subreddit)``
    is equivalent to ``subreddit.hot()``. ``enum.member()`` is required because a
    bare ``partial`` is treated as a method descriptor (not a member) on modern
    Python.
    """

    NEW = member(partial(lambda s, **kw: s.new(**kw)))
    HOT = member(partial(lambda s, **kw: s.hot(**kw)))
    CONTROVERSIAL = member(partial(lambda s, **kw: s.controversial(**kw)))
    GILDED = member(partial(lambda s, **kw: s.gilded(**kw)))  # probably deprecated?
    TOP_ALL = member(partial(lambda s, **kw: s.top(time_filter="all", **kw)))
    TOP_DAY = member(partial(lambda s, **kw: s.top(time_filter="day", **kw)))
    TOP_HOUR = member(partial(lambda s, **kw: s.top(time_filter="hour", **kw)))
    TOP_WEEK = member(partial(lambda s, **kw: s.top(time_filter="week", **kw)))
    TOP_MONTH = member(partial(lambda s, **kw: s.top(time_filter="month", **kw)))
    TOP_YEAR = member(partial(lambda s, **kw: s.top(time_filter="year", **kw)))

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)
