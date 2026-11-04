import asyncio
import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

from src.core import UniqueDirectoryFileManager
from src.core.file_manager import MAX_NAME_BYTES


class TestUniqueDirectoryFileManagerConstructor(unittest.TestCase):
    now = datetime(2000, 1, 2, 12, 0, 0)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = patch("src.core.file_manager.datetime")
        mock_datetime = patcher.start()
        self.addCleanup(patcher.stop)
        mock_datetime.today.return_value = self.now

    def test_correct_directory_name(self):
        manager = UniqueDirectoryFileManager(self._tmp.name)
        # no colon: it's invalid in Windows paths
        self.assertEqual(
            manager.directory,
            os.path.join(self._tmp.name, "PaperScraper 2000-01-02 12-00"),
        )
        self.assertTrue(os.path.isdir(manager.directory))

    def test_second_run_in_same_minute_gets_its_own_directory(self):
        # used to raise FileExistsError
        first = UniqueDirectoryFileManager(self._tmp.name)
        second = UniqueDirectoryFileManager(self._tmp.name)
        self.assertEqual(second.directory, first.directory + " (1)")

    def test_creates_missing_parent(self):
        parent = os.path.join(self._tmp.name, "does", "not", "exist")
        manager = UniqueDirectoryFileManager(parent)
        self.assertTrue(os.path.isdir(manager.directory))


class _TempManagerTestCase(unittest.IsolatedAsyncioTestCase):
    """Base case giving each test a manager rooted in a fresh temp directory"""

    organize = False

    async def asyncSetUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.manager = UniqueDirectoryFileManager(
            self._tmp.name, organize=self.organize
        )

    async def asyncTearDown(self):
        self._tmp.cleanup()


class TestLog(_TempManagerTestCase):

    async def test_appends_json_lines(self):
        path1 = await self.manager.log({"a": 1})
        path2 = await self.manager.log({"b": 2})
        self.assertEqual(path1, path2)  # same default log file
        with open(path1, encoding="utf-8") as f:
            records = [json.loads(line) for line in f.read().splitlines()]
        self.assertEqual(records, [{"a": 1}, {"b": 2}])

    async def test_concurrent_logs_are_serialized(self):
        # the lock must keep concurrent appends from interleaving; every line
        # should be independently valid JSON
        await asyncio.gather(*(self.manager.log({"i": i}) for i in range(20)))
        path = os.path.join(self.manager.directory, "log.txt")
        with open(path, encoding="utf-8") as f:
            records = [json.loads(line) for line in f.read().splitlines()]
        self.assertEqual(sorted(r["i"] for r in records), list(range(20)))


def _relpaths(manager, paths):
    """paths relative to the manager's directory, so tests check exact locations"""
    return [os.path.relpath(path, manager.directory) for path in paths]


class TestSaveFiles(_TempManagerTestCase):

    async def test_single_file(self):
        paths = await self.manager.save_files("My Title", [(b"data", ".jpg")])
        self.assertEqual(_relpaths(self.manager, paths), ["My Title.jpg"])
        with open(paths[0], "rb") as f:
            self.assertEqual(f.read(), b"data")

    async def test_empty_downloads_returns_empty(self):
        self.assertEqual(await self.manager.save_files("t", []), [])

    async def test_album_creates_dir_and_numbered_files(self):
        paths = await self.manager.save_files("Album", [(b"a", ".jpg"), (b"b", ".png")])
        # exactly these paths: albums used to land in a second copy of the
        # output path, with "0..jpg" names
        self.assertEqual(
            _relpaths(self.manager, paths),
            [os.path.join("Album", "0.jpg"), os.path.join("Album", "1.png")],
        )
        with open(paths[0], "rb") as f:
            self.assertEqual(f.read(), b"a")
        with open(paths[1], "rb") as f:
            self.assertEqual(f.read(), b"b")

    async def test_relative_output_directory(self):
        # the default --dir is the relative "Output"; joining two relative paths
        # is what nested albums under a second copy of it
        with tempfile.TemporaryDirectory() as cwd:
            previous = os.getcwd()
            os.chdir(cwd)
            try:
                manager = UniqueDirectoryFileManager("Output", organize=True)
                paths = await manager.save_files(
                    "A", [(b"a", ".jpg"), (b"b", ".jpg")], subreddit="pics"
                )
            finally:
                os.chdir(previous)
        self.assertEqual(
            _relpaths(manager, paths),
            [os.path.join("pics", "A", "0.jpg"), os.path.join("pics", "A", "1.jpg")],
        )

    async def test_unique_filename_on_collision(self):
        await self.manager.save_files("Dup", [(b"1", ".jpg")])
        paths = await self.manager.save_files("Dup", [(b"2", ".jpg")])
        self.assertEqual(_relpaths(self.manager, paths), ["Dup (1).jpg"])

    async def test_unique_album_on_collision(self):
        await self.manager.save_files("Dup", [(b"1", ".jpg"), (b"2", ".jpg")])
        paths = await self.manager.save_files("Dup", [(b"3", ".jpg"), (b"4", ".jpg")])
        self.assertEqual(
            _relpaths(self.manager, paths),
            [os.path.join("Dup (1)", "0.jpg"), os.path.join("Dup (1)", "1.jpg")],
        )

    async def test_concurrent_same_title_files_dont_overwrite(self):
        # names used to be checked and written in separate steps, so concurrent
        # saves all picked "Same.jpg" and overwrote each other
        results = await asyncio.gather(
            *(self.manager.save_files("Same", [(b"%d" % i, ".jpg")]) for i in range(5))
        )
        paths = [path for result in results for path in result]
        self.assertEqual(len(set(paths)), 5)
        contents = set()
        for path in paths:
            with open(path, "rb") as f:
                contents.add(f.read())
        self.assertEqual(contents, {b"%d" % i for i in range(5)})

    async def test_concurrent_same_title_albums(self):
        # the second album used to fail with FileExistsError
        results = await asyncio.gather(
            *(
                self.manager.save_files("Same", [(b"a", ".jpg"), (b"b", ".jpg")])
                for _ in range(3)
            )
        )
        dirs = {os.path.dirname(result[0]) for result in results}
        self.assertEqual(len(dirs), 3)

    async def test_invalid_chars_in_title(self):
        paths = await self.manager.save_files("a/b:c", [(b"x", ".jpg")])
        self.assertEqual(_relpaths(self.manager, paths), ["a_b_c.jpg"])

    async def test_long_multibyte_title(self):
        # 200 CJK characters is 600 bytes; cutting to 250 characters still
        # exceeded the 255-byte name limit
        title = "猫" * 200
        single = await self.manager.save_files(title, [(b"x", ".jpg")])
        album = await self.manager.save_files(title, [(b"x", ".jpg"), (b"y", ".jpg")])
        for path in [single[0], os.path.dirname(album[0])]:
            self.assertLessEqual(len(os.path.basename(path).encode()), 255)
            self.assertTrue(os.path.exists(path))

    async def test_extension_without_name_is_kept(self):
        paths = await self.manager.save_files("T", [(b"x", "")])
        self.assertEqual(_relpaths(self.manager, paths), ["T"])


class TestSaveFilesOrganized(_TempManagerTestCase):
    organize = True

    async def test_organize_creates_subreddit_dir(self):
        paths = await self.manager.save_files("T", [(b"x", ".jpg")], subreddit="pics")
        self.assertEqual(
            _relpaths(self.manager, paths), [os.path.join("pics", "T.jpg")]
        )

    async def test_album_goes_inside_subreddit_dir(self):
        paths = await self.manager.save_files(
            "A", [(b"a", ".jpg"), (b"b", ".jpg")], subreddit="pics"
        )
        self.assertEqual(
            _relpaths(self.manager, paths),
            [os.path.join("pics", "A", "0.jpg"), os.path.join("pics", "A", "1.jpg")],
        )

    async def test_album_uniqueness_is_checked_in_subreddit_dir(self):
        # a same-named album in a different subreddit isn't a conflict
        await self.manager.save_files(
            "A", [(b"a", ".jpg"), (b"b", ".jpg")], subreddit="pics"
        )
        paths = await self.manager.save_files(
            "A", [(b"a", ".jpg"), (b"b", ".jpg")], subreddit="art"
        )
        self.assertEqual(
            os.path.relpath(os.path.dirname(paths[0]), self.manager.directory),
            os.path.join("art", "A"),
        )


class TestUniqueNames(unittest.TestCase):

    def test_sequence(self):
        names = UniqueDirectoryFileManager.unique_names("title", ".jpg")
        self.assertEqual(
            [next(names) for _ in range(3)],
            ["title.jpg", "title (1).jpg", "title (2).jpg"],
        )

    def test_without_extension(self):
        names = UniqueDirectoryFileManager.unique_names("album")
        self.assertEqual([next(names) for _ in range(2)], ["album", "album (1)"])

    def test_fits_byte_limit_with_suffix(self):
        names = UniqueDirectoryFileManager.unique_names("é" * 300, ".jpeg")
        for _ in range(12):
            name = next(names)
            self.assertLessEqual(len(name.encode()), MAX_NAME_BYTES)
            self.assertTrue(name.endswith(".jpeg"))

    def test_does_not_split_multibyte_characters(self):
        name = next(UniqueDirectoryFileManager.unique_names("😀" * 100))
        name.encode()  # would raise on a lone surrogate
        self.assertEqual(set(name), {"😀"})


class TestEnsureValidFilename(unittest.TestCase):

    def test_keeps_valid(self):
        self.assertEqual(
            UniqueDirectoryFileManager.ensure_valid_filename("hello world.jpg"),
            "hello world.jpg",
        )

    def test_replaces_each_invalid_char(self):
        for char in r'\/:*?"<>|' + "\n\t\x00":
            self.assertEqual(
                UniqueDirectoryFileManager.ensure_valid_filename(f"a{char}b"), "a_b"
            )

    def test_unusable_names(self):
        for name in ["", ".", "..", "  ", "..."]:
            self.assertEqual(
                UniqueDirectoryFileManager.ensure_valid_filename(name), "untitled"
            )

    def test_strips_trailing_dots_and_spaces(self):
        self.assertEqual(
            UniqueDirectoryFileManager.ensure_valid_filename("wait... "), "wait"
        )
