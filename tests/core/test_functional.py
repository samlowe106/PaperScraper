import unittest


class TestAfilter(unittest.IsolatedAsyncioTestCase):

    async def test_identity(self):
        pass

    async def test_filters_some(self):
        pass

    async def test_removes_all_with_const_false_predicate(self):
        pass

    async def test_can_remove_truthy(self):
        pass

    async def test_can_keep_falsy(self):
        pass

    async def test_removes_none_with_const_true_predicate(self):
        pass


class TestAmap(unittest.IsolatedAsyncioTestCase):

    async def test_identity(self):
        pass

    async def test_keeps_duplicates(self):
        pass


class TestMerge(unittest.IsolatedAsyncioTestCase):

    async def test_two_iterables(self):
        pass

    async def test_three_iterables(self):
        pass

    async def test_empty_iterables(self):
        pass
