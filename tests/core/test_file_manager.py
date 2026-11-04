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


async def _chunks(*parts: bytes):
    for part in parts:
        await asyncio.sleep(0)  # arrive over time, like a response body
        yield part


def _read(path):
    with open(path, "rb") as f:
        return f.read()


class TestWriteUnique(_TempManagerTestCase):

    async def _write(self, title, extension=".jpg", *parts, directory=None):
        return await self.manager.write_unique(
            directory or self.manager.directory,
            title,
            extension,
            _chunks(*(parts or (b"data",))),
        )

    async def test_writes_chunks_in_order(self):
        path = await self._write("My Title", ".jpg", b"a", b"b", b"c")
        self.assertEqual(_relpaths(self.manager, [path]), ["My Title.jpg"])
        self.assertEqual(_read(path), b"abc")

    async def test_unique_filename_on_collision(self):
        await self._write("Dup")
        path = await self._write("Dup")
        self.assertEqual(_relpaths(self.manager, [path]), ["Dup (1).jpg"])

    async def test_concurrent_same_title_files_dont_overwrite(self):
        # names used to be checked and written in separate steps, so concurrent
        # saves all picked "Same.jpg" and overwrote each other
        paths = await asyncio.gather(
            *(self._write("Same", ".jpg", b"%d" % i) for i in range(5))
        )
        self.assertEqual(len(set(paths)), 5)
        self.assertEqual({_read(path) for path in paths}, {b"%d" % i for i in range(5)})

    async def test_failure_partway_leaves_no_file(self):
        async def broken():
            yield b"partial"
            raise OSError("connection dropped")

        with self.assertRaises(OSError):
            await self.manager.write_unique(
                self.manager.directory, "T", ".jpg", broken()
            )
        self.assertEqual(os.listdir(self.manager.directory), [])
        # and the name is free again
        path = await self._write("T")
        self.assertEqual(_relpaths(self.manager, [path]), ["T.jpg"])

    async def test_invalid_chars_in_title(self):
        path = await self._write("a/b:c")
        self.assertEqual(_relpaths(self.manager, [path]), ["a_b_c.jpg"])

    async def test_long_multibyte_title(self):
        # 200 CJK characters is 600 bytes; cutting to 250 characters still
        # exceeded the 255-byte name limit
        path = await self._write("猫" * 200)
        self.assertLessEqual(len(os.path.basename(path).encode()), 255)
        self.assertEqual(_read(path), b"data")

    async def test_no_extension(self):
        path = await self._write("T", "")
        self.assertEqual(_relpaths(self.manager, [path]), ["T"])


class TestMakeAlbum(_TempManagerTestCase):

    async def test_creates_album_in_directory(self):
        album = await self.manager.make_album(self.manager.directory, "Album")
        self.assertEqual(_relpaths(self.manager, [album]), ["Album"])
        self.assertTrue(os.path.isdir(album))

    async def test_unique_album_on_collision(self):
        await self.manager.make_album(self.manager.directory, "Dup")
        album = await self.manager.make_album(self.manager.directory, "Dup")
        self.assertEqual(_relpaths(self.manager, [album]), ["Dup (1)"])

    async def test_concurrent_same_title_albums(self):
        # the second album used to fail with FileExistsError
        albums = await asyncio.gather(
            *(self.manager.make_album(self.manager.directory, "Same") for _ in range(3))
        )
        self.assertEqual(len(set(albums)), 3)

    async def test_long_multibyte_title(self):
        album = await self.manager.make_album(self.manager.directory, "猫" * 200)
        self.assertLessEqual(len(os.path.basename(album).encode()), 255)
        self.assertTrue(os.path.isdir(album))

    async def test_relative_output_directory(self):
        # the default --dir is the relative "Output"; joining two relative paths
        # is what used to nest albums under a second copy of it
        with tempfile.TemporaryDirectory() as cwd:
            previous = os.getcwd()
            os.chdir(cwd)
            try:
                manager = UniqueDirectoryFileManager("Output", organize=True)
                directory = await manager.post_directory("pics")
                album = await manager.make_album(directory, "A")
                self.assertTrue(os.path.isdir(album))
            finally:
                os.chdir(previous)
        self.assertEqual(_relpaths(manager, [album]), [os.path.join("pics", "A")])


class TestPostDirectory(_TempManagerTestCase):

    async def test_not_organized(self):
        self.assertEqual(
            await self.manager.post_directory("pics"), self.manager.directory
        )


class TestPostDirectoryOrganized(_TempManagerTestCase):
    organize = True

    async def test_subreddit_folder(self):
        directory = await self.manager.post_directory("pics")
        self.assertEqual(_relpaths(self.manager, [directory]), ["pics"])
        self.assertTrue(os.path.isdir(directory))
        # shared by every post from the subreddit
        self.assertEqual(await self.manager.post_directory("pics"), directory)

    async def test_album_uniqueness_is_checked_in_subreddit_folder(self):
        # a same-named album in a different subreddit isn't a conflict
        await self.manager.make_album(await self.manager.post_directory("pics"), "A")
        album = await self.manager.make_album(
            await self.manager.post_directory("art"), "A"
        )
        self.assertEqual(_relpaths(self.manager, [album]), [os.path.join("art", "A")])

    async def test_no_subreddit(self):
        self.assertEqual(
            await self.manager.post_directory(None), self.manager.directory
        )


class TestDiscardIfEmpty(_TempManagerTestCase):

    async def test_removes_empty(self):
        album = await self.manager.make_album(self.manager.directory, "A")
        await self.manager.discard_if_empty(album)
        self.assertFalse(os.path.exists(album))

    async def test_keeps_nonempty(self):
        album = await self.manager.make_album(self.manager.directory, "A")
        await self.manager.write_unique(album, "0", ".jpg", _chunks(b"x"))
        await self.manager.discard_if_empty(album)
        self.assertTrue(os.path.exists(os.path.join(album, "0.jpg")))


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
