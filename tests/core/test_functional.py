import asyncio
import unittest
from collections import Counter

from src.core.functional import afilter, amap, merge
from tests import acollect, async_iter


class TestAfilter(unittest.IsolatedAsyncioTestCase):

    async def test_identity(self):
        result = await acollect(afilter(bool, async_iter([1, 2, 0, 3])))
        self.assertEqual(result, [1, 2, 3])

    async def test_filters_some(self):
        result = await acollect(afilter(lambda x: x % 2 == 0, async_iter(range(6))))
        self.assertEqual(result, [0, 2, 4])

    async def test_keeps_all_with_const_true_predicate(self):
        result = await acollect(afilter(lambda _: True, async_iter([1, 2, 3])))
        self.assertEqual(result, [1, 2, 3])

    async def test_removes_all_with_const_false_predicate(self):
        result = await acollect(afilter(lambda _: False, async_iter([1, 2, 3])))
        self.assertEqual(result, [])

    async def test_can_remove_truthy(self):
        # 5 is truthy but the predicate rejects it -> filtering is on the
        # predicate's result, not the item's truthiness
        result = await acollect(afilter(lambda x: x != 5, async_iter([5, 6])))
        self.assertEqual(result, [6])

    async def test_can_keep_falsy(self):
        # falsy items survive when the predicate says to keep them
        result = await acollect(afilter(lambda _: True, async_iter([0, "", None])))
        self.assertEqual(result, [0, "", None])

    async def test_removes_none_with_predicate(self):
        result = await acollect(
            afilter(lambda x: x is not None, async_iter([None, 1, None, 2]))
        )
        self.assertEqual(result, [1, 2])


class TestAmap(unittest.IsolatedAsyncioTestCase):

    async def test_identity(self):
        result = await acollect(amap(lambda x: x, async_iter([1, 2, 3])))
        self.assertEqual(result, [1, 2, 3])

    async def test_maps_values(self):
        result = await acollect(amap(lambda x: x * 2, async_iter([1, 2, 3])))
        self.assertEqual(result, [2, 4, 6])

    async def test_keeps_duplicates(self):
        # amap is 1:1 -- it never dedupes
        result = await acollect(amap(lambda x: x, async_iter([1, 1, 2])))
        self.assertEqual(result, [1, 1, 2])


class TestMerge(unittest.IsolatedAsyncioTestCase):
    # merge's order is non-deterministic (queue-based), so compare with Counter.
    # merge uses a unique object() sentinel, so None is a valid item (see
    # test_passes_none_through). Each test is wrapped in wait_for so a sentinel
    # regression fails instead of hanging the whole suite.

    async def test_two_iterables(self):
        result = await asyncio.wait_for(
            acollect(merge(async_iter([1, 2, 3]), async_iter([4, 5]))), timeout=2
        )
        self.assertEqual(Counter(result), Counter([1, 2, 3, 4, 5]))

    async def test_three_iterables(self):
        result = await asyncio.wait_for(
            acollect(merge(async_iter([1, 2]), async_iter([3, 4]), async_iter([5, 6]))),
            timeout=2,
        )
        self.assertEqual(Counter(result), Counter([1, 2, 3, 4, 5, 6]))
        self.assertEqual(len(result), 6)

    async def test_empty_iterables(self):
        # the case the old (sentinel-less) merge deadlocked on
        result = await asyncio.wait_for(
            acollect(merge(async_iter([]), async_iter([]))), timeout=2
        )
        self.assertEqual(result, [])

    async def test_mix_empty_and_nonempty(self):
        result = await asyncio.wait_for(
            acollect(merge(async_iter([]), async_iter([1, 2]))), timeout=2
        )
        self.assertEqual(Counter(result), Counter([1, 2]))

    async def test_single_iterable(self):
        result = await asyncio.wait_for(acollect(merge(async_iter([1, 2]))), timeout=2)
        self.assertEqual(result, [1, 2])

    async def test_no_iterables(self):
        result = await asyncio.wait_for(acollect(merge()), timeout=2)
        self.assertEqual(result, [])

    async def test_passes_none_through(self):
        # None is a legitimate item -- the sentinel is a unique object(), not None
        result = await asyncio.wait_for(
            acollect(merge(async_iter([None, 1]), async_iter([None]))), timeout=2
        )
        self.assertEqual(Counter(result), Counter([None, None, 1]))
        self.assertEqual(sum(1 for x in result if x is None), 2)
