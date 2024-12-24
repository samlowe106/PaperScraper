import unittest
from unittest.mock import patch  # MagicMock,

from core.parsers.flickr import flickr_parser  # _get_flickr_photo_id,


class TestFlickrRegex(unittest.TestCase):
    # TODO
    pass


class TestGetFlickrPhotoID(unittest.TestCase):
    # TODO
    pass


class TestFlickrParser(unittest.TestCase):
    @patch("core.parsers.flickr._get_flickr_photo_id")
    def test_returns_empty_set_if_no_id(self, mock_get_flickr_photo_id):
        mock_get_flickr_photo_id.return_value = None
        result = flickr_parser("mock url", "mock client")
        self.assertEqual(result, set())
        mock_get_flickr_photo_id.assert_called_once_with("mock url", "mock client")

    def test_makes_api_call(self):
        # TODO
        pass


if __name__ == "__main__":
    unittest.main()
