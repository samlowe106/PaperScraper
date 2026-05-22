import asyncio
from collections.abc import AsyncIterable, AsyncIterator
from typing import Callable, List, TypeVar

T = TypeVar("T")
S = TypeVar("S")

type Predicate[T] = Callable[[T], bool]


async def amap(func: Callable[[T], S], iterable: AsyncIterable[T]) -> AsyncIterator[S]:
    async for item in iterable:
        yield func(item)


async def afilter(
    predicate: Predicate[T], iterable: AsyncIterable[T]
) -> AsyncIterator[T]:
    async for item in iterable:
        if predicate(item):
            yield item


async def merge(*gens: List[AsyncIterable[T]]) -> AsyncIterable[T]:
    queue: asyncio.Queue[T] = asyncio.Queue()

    async def pump(gen):
        async for item in gen:
            await queue.put(item)

    async with asyncio.TaskGroup() as tg:
        for g in gens:
            tg.create_task(pump(g))

        active = len(gens)

        while active:
            item = await queue.get()
            if item is None:
                active -= 1
            else:
                yield item


# async def a_filter_map(
#    iterable: AsyncIterable[T],
#    func: Callable[[T], S] = lambda x: x,  # type: ignore
#    predicate: Predicate[S] = lambda x: True,
# ) -> AsyncIterator[S]:
#    return afilter(predicate, amap(func, xs))
