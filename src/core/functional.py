import asyncio
from collections.abc import AsyncIterable, AsyncIterator
from typing import Callable, TypeVar

T = TypeVar("T")
S = TypeVar("S")

type Predicate[T] = Callable[[T], bool]

# unique per-call-agnostic sentinel meaning "a generator is exhausted". Identity
# comparison (`is`) makes it distinct from every real value -- including None --
# so merge() works even on streams that legitimately yield None.
_DONE = object()


async def amap(func: Callable[[T], S], iterable: AsyncIterable[T]) -> AsyncIterator[S]:
    async for item in iterable:
        yield func(item)


async def afilter(
    predicate: Predicate[T], iterable: AsyncIterable[T]
) -> AsyncIterator[T]:
    async for item in iterable:
        if predicate(item):
            yield item


async def merge(*gens: AsyncIterable[T]) -> AsyncIterable[T]:
    # Interleaves several async iterables into one, yielding items as they arrive.
    # A unique _DONE sentinel (not None) marks each generator's completion, so any
    # value -- including None -- may flow through as a real item.
    queue: asyncio.Queue = asyncio.Queue()

    async def pump(gen):
        try:
            async for item in gen:
                await queue.put(item)
        finally:
            # signal that this generator is exhausted (fires even on error)
            await queue.put(_DONE)

    async with asyncio.TaskGroup() as tg:
        for g in gens:
            tg.create_task(pump(g))

        active = len(gens)

        while active:
            item = await queue.get()
            if item is _DONE:
                active -= 1
            else:
                yield item
