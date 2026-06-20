import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

from src.core import UniqueDirectoryFileManager


class TestUniqueDirectoryFileManagerConstructor(unittest.TestCase):
    now = datetime(2000, 1, 2, 12, 0, 0)

    @patch("src.core.file_manager.datetime", return_value=now)
    @patch("os.makedirs")
    def test_correct_directory_name(self, mock_os_makedirs, mock_datetime):
        # this should run on linux
        mock_datetime.today.return_value = self.now
        manager = UniqueDirectoryFileManager("mock_directory")
        self.assertEqual(
            manager.directory, "mock_directory/PaperScraper 2000-01-02 12:00"
        )
        mock_os_makedirs.assert_called_once_with(
            "mock_directory/PaperScraper 2000-01-02 12:00", exist_ok=False
        )


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


class TestSaveFiles(_TempManagerTestCase):

    async def test_single_file(self):
        paths = await self.manager.save_files("My Title", [(b"data", "jpg")])
        self.assertEqual(len(paths), 1)
        self.assertTrue(paths[0].endswith("My Title.jpg"))
        with open(paths[0], "rb") as f:
            self.assertEqual(f.read(), b"data")

    async def test_empty_downloads_returns_empty(self):
        self.assertEqual(await self.manager.save_files("t", []), [])

    async def test_album_creates_dir_and_numbered_files(self):
        paths = await self.manager.save_files("Album", [(b"a", "jpg"), (b"b", "png")])
        self.assertEqual(len(paths), 2)
        self.assertTrue(paths[0].endswith(os.path.join("Album", "0.jpg")))
        self.assertTrue(paths[1].endswith(os.path.join("Album", "1.png")))
        with open(paths[0], "rb") as f:
            self.assertEqual(f.read(), b"a")
        with open(paths[1], "rb") as f:
            self.assertEqual(f.read(), b"b")

    async def test_unique_filename_on_collision(self):
        await self.manager.save_files("Dup", [(b"1", "jpg")])
        paths = await self.manager.save_files("Dup", [(b"2", "jpg")])
        self.assertTrue(paths[0].endswith("Dup (1).jpg"))

    async def test_invalid_chars_in_title(self):
        paths = await self.manager.save_files("a/b:c", [(b"x", "jpg")])
        self.assertTrue(paths[0].endswith("a_b_c.jpg"))


class TestSaveFilesOrganized(_TempManagerTestCase):
    organize = True

    async def test_organize_creates_subreddit_dir(self):
        paths = await self.manager.save_files("T", [(b"x", "jpg")], subreddit="pics")
        self.assertIn(os.path.join("pics", "T.jpg"), paths[0])


class TestGetUniqueFilepath(_TempManagerTestCase):

    async def test_returns_title_when_no_conflict(self):
        path = await self.manager.get_unique_filepath(
            self.manager.directory, "title", "jpg"
        )
        self.assertTrue(path.endswith("title.jpg"))

    async def test_appends_counter_on_conflict(self):
        open(os.path.join(self.manager.directory, "title.jpg"), "w").close()
        path = await self.manager.get_unique_filepath(
            self.manager.directory, "title", "jpg"
        )
        self.assertTrue(path.endswith("title (1).jpg"))

    async def test_multiple_conflicts(self):
        open(os.path.join(self.manager.directory, "title.jpg"), "w").close()
        open(os.path.join(self.manager.directory, "title (1).jpg"), "w").close()
        path = await self.manager.get_unique_filepath(
            self.manager.directory, "title", "jpg"
        )
        self.assertTrue(path.endswith("title (2).jpg"))

    async def test_invalid_chars_replaced(self):
        path = await self.manager.get_unique_filepath(
            self.manager.directory, "a?b*c", "jpg"
        )
        self.assertTrue(path.endswith("a_b_c.jpg"))


class TestGetUniqueDirname(_TempManagerTestCase):

    async def test_no_conflict(self):
        dirname = await self.manager.get_unique_dirname("album")
        self.assertEqual(dirname, os.path.join(self.manager.directory, "album"))

    async def test_conflict_appends_counter(self):
        # dirname offset starts at 0 (unlike filepath, which starts at 1)
        os.makedirs(os.path.join(self.manager.directory, "album"))
        dirname = await self.manager.get_unique_dirname("album")
        self.assertEqual(dirname, os.path.join(self.manager.directory, "album (0)"))


class TestEnsureValidFilename(_TempManagerTestCase):

    async def test_keeps_valid(self):
        self.assertEqual(
            self.manager.ensure_valid_filename("hello world.jpg"), "hello world.jpg"
        )

    async def test_replaces_each_invalid_char(self):
        for char in r'\/:*?"<>|':
            self.assertEqual(self.manager.ensure_valid_filename(f"a{char}b"), "a_b")

    async def test_empty_string(self):
        self.assertEqual(self.manager.ensure_valid_filename(""), "")


class TestEnsureValidDirname(_TempManagerTestCase):

    async def test_keeps_valid(self):
        self.assertEqual(self.manager.ensure_valid_dirname("my album"), "my album")

    async def test_replaces_each_invalid_char(self):
        for char in r'\/:*?"<>|':
            self.assertEqual(self.manager.ensure_valid_dirname(f"a{char}b"), "a_b")
