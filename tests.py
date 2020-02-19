import unittest
from app.strhelpers import *
from app.filehelpers import *
from app.imagehelpers import *


class TestStringHelpers(unittest.TestCase):
    def test_trim_string(self):
        self.assertEqual(True, False)

    def test_file_title(self):
        self.assertEqual(True, False)

    def test_retitle(self):
        self.assertEqual(True, False)

    def test_shorten(self):
        self.assertEqual(True, False)

    def test_attempt_shorten(self):
        self.assertEqual(True, False)

    def test_title_case(self):
        self.assertEqual(True, False)


class TestFileHelpers(unittest.TestCase):
    def test_create_directory(self):
        self.assertEqual(True, False)

    def test_convert_to_png(self):
        self.assertEqual(True, False)

    def test_get_extension(self):
        self.assertEqual(True, False)

    def test_save_images(self):
        self.assertEqual(True, False)


class TestImageHelpers(unittest.TestCase):
    def test_parse_imgur_album(self):
        self.assertEqual(True, False)

    def test_parse_imgur_single(self):
        self.assertEqual(True, False)

    def test_find_urls(self):
        self.assertEqual(True, False)

    def test_download_image(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
