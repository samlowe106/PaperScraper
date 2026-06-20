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
        self.assertEqual(args.limit, 10)
        self.assertIsNone(args.karma)
        self.assertTrue(args.log)  # logging on by default
        self.assertFalse(args.unsave)
        self.assertIsNone(args.hours)
        self.assertIsNone(args.days)
        self.assertIsNone(args.years)

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

    def test_limit_and_karma(self):
        args = self.parser.parse_args(["--limit", "3", "-k", "50"])
        self.assertEqual(args.limit, 3)
        self.assertEqual(args.karma, 50)

    def test_nolog_disables_logging(self):
        self.assertFalse(self.parser.parse_args(["--nolog"]).log)

    def test_unsave_flag(self):
        self.assertTrue(self.parser.parse_args(["--unsave"]).unsave)

    def test_age_flag(self):
        self.assertEqual(self.parser.parse_args(["--days", "7"]).days, 7)

    def test_age_flags_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--days", "7", "--hours", "5"])
