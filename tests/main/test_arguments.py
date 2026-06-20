import unittest

from src.main import build_parser
from src.reddit import SortOption


class TestBuildParser(unittest.TestCase):

    def setUp(self):
        self.parser = build_parser()

    def test_defaults(self):
        args = self.parser.parse_args([])
        self.assertFalse(args.saved)
        self.assertEqual(args.subreddit, [])
        self.assertEqual(args.directory, "Output")
        self.assertEqual(args.sortby, SortOption.HOT)
        self.assertFalse(args.organize)

    def test_subreddit_is_repeatable(self):
        args = self.parser.parse_args(["-r", "pics", "-r", "art"])
        self.assertEqual(args.subreddit, ["pics", "art"])

    def test_saved_flag(self):
        self.assertTrue(self.parser.parse_args(["-u"]).saved)

    def test_organize_flag(self):
        self.assertTrue(self.parser.parse_args(["--organize"]).organize)

    def test_dir_maps_to_directory(self):
        # -d/--dir is stored as `directory` (what main() reads)
        self.assertEqual(self.parser.parse_args(["-d", "/tmp/x"]).directory, "/tmp/x")

    def test_sortby_string_converts_to_enum(self):
        self.assertEqual(
            self.parser.parse_args(["--sortby", "new"]).sortby, SortOption.NEW
        )
        self.assertEqual(
            self.parser.parse_args(["--sortby", "top_all"]).sortby, SortOption.TOP_ALL
        )
