import unittest

# from datetime import datetime
from unittest.mock import AsyncMock, mock_open, patch

from tests import SubmissionWrapperFactory

"""
class TestRetitle(unittest.TestCase):

    def test_retitle(self):
        self.assertEqual(retitle("mock title"), "mock title")
        self.assertEqual(retitle("mock title: \\"), "mock title")
        self.assertEqual(retitle("mock title: ??"), "mock title")
        self.assertEqual(retitle("mock ?? title: \\"), "mock title")


class TestConstructor(unittest.TestCase):
    def test_constructor(self):
        submission_mock = MagicMock()
        submission_mock.title = "mock ?? title: \\"
        submission_mock.subreddit = uuid.uuid4()
        submission_mock.url = str(uuid.uuid4())
        submission_mock.author = str(uuid.uuid4())
        submission_mock.over_18 = False
        submission_mock.score = 10
        submission_mock.created_utc = datetime.now()
        submission_mock.saved = MagicMock()

        client_mock = MagicMock()

        dry = True

        wrapper = SubmissionWrapper(submission_mock, client_mock, dry=dry)

        # Assert that the wrapper has the correct values
        self.assertEqual(wrapper.title, submission_mock.title)
        self.assertEqual(wrapper.subreddit, str(submission_mock.subreddit))
        self.assertEqual(wrapper.url, submission_mock.url)
        self.assertEqual(wrapper.author, submission_mock.author)
        self.assertEqual(wrapper.nsfw, submission_mock.over_18)
        self.assertEqual(wrapper.score, submission_mock.score)
        self.assertEqual(wrapper.created_utc, submission_mock.created_utc)
        # Assert that the file title has the special characters removed
        self.assertEqual(wrapper.base_file_title, "mock title")
        # Assert values like responses and urls are not set
        self.assertIsNone(wrapper.response)
        self.assertEqual(wrapper.urls, set())
        # Assert that the submission is has not been unsaved
        submission_mock.unsave.assert_not_called()
"""


class TestFindUrls(unittest.IsolatedAsyncioTestCase):

    async def test_find_urls(self):
        wrapped = SubmissionWrapperFactory()
        await wrapped.find_urls()


class TestUnsave(unittest.IsolatedAsyncioTestCase):

    async def test_calls_unsave(self):
        wrapper = SubmissionWrapperFactory()
        with patch.object(
            wrapper._submission,
            "unsave",
            new_callable=AsyncMock,
        ) as mock_unsave:

            await wrapper.unsave()
            mock_unsave.assert_awaited_once()


class TestDownload(unittest.IsolatedAsyncioTestCase):

    async def test_download_empty(self):
        # Assert that an empty list of urls returns an empty dictionary
        wrapper = SubmissionWrapperFactory()
        self.assertEqual(wrapper.urls, set())
        mock_client = AsyncMock()
        self.assertEqual(await wrapper.download(mock_client), list())

    async def test_download_nonempty(self):
        mock_client = AsyncMock()

        urls_extensions = {
            "url1": "jpg",
            "url2": "png",
            "url3": "gif",
            "url4": "webm",
        }

        class MockResponse:
            def __init__(self, content_mock, file_ext="jpg"):
                self.status_code = 200
                self.content = content_mock
                self.headers = {"Content-type": f"image/{file_ext}"}

        async def mock_response_contents(mock_url, **kwargs):
            return MockResponse(
                mock_url + " mock content", file_ext=urls_extensions[mock_url]
            )

        mock_client.get.side_effect = mock_response_contents

        wrapper = SubmissionWrapperFactory()
        wrapper.subreddit = "mock subreddit"
        wrapper.title = "mock title"
        wrapper.urls = list(urls_extensions.keys())
        print(f"{wrapper.urls=}")

        contents_extensions = await wrapper.download(mock_client)

        expected = [
            ("url1 mock content", ".jpg"),
            ("url2 mock content", ".png"),
            ("url3 mock content", ".gif"),
            ("url4 mock content", ".webm"),
        ]

        print(mock_client.get.call_args_list)

        for url in urls_extensions.keys():
            mock_client.get.assert_any_call(url, timeout=10)

        self.assertListEqual(contents_extensions, expected)


class TestStr(unittest.TestCase):

    def test_str_contains_info(self):

        wrapper = SubmissionWrapperFactory()

        self.assertIn(wrapper.title, str(wrapper))
        self.assertIn(wrapper.subreddit, str(wrapper))
        self.assertIn(wrapper.author, str(wrapper))
        self.assertIn(wrapper.url, str(wrapper))


class TestLog(unittest.TestCase):

    @patch("json.dump")
    def test_log_no_exception(self, mock_json_dump):

        wrapped = SubmissionWrapperFactory()

        log_file_path = "log/path.txt"

        m = mock_open()
        file_handle = m.return_value.__enter__.return_value

        with patch("builtins.open", m):
            wrapped.log(log_file_path)

        m.assert_called_once_with(log_file_path, "a", encoding="utf-8")

        mock_json_dump.assert_called_once_with(
            {
                "title": wrapped._submission.title,
                "id": wrapped._submission.id,
                "url": wrapped._submission.url,
                "recognized_urls": wrapped.urls,
                "exception": "",
            },
            file_handle,
        )

    @patch("json.dump")
    def test_log_with_exception(self, mock_json_dump):

        wrapped = SubmissionWrapperFactory()

        log_file_path = "log/path.txt"

        m = mock_open()
        file_handle = m.return_value.__enter__.return_value

        mock_exception = Exception("Mock exception message")

        with patch("builtins.open", m):
            wrapped.log(log_file_path, mock_exception)

        m.assert_called_once_with(log_file_path, "a", encoding="utf-8")

        mock_json_dump.assert_called_once_with(
            {
                "title": wrapped._submission.title,
                "id": wrapped._submission.id,
                "url": wrapped._submission.url,
                "recognized_urls": wrapped.urls,
                "exception": mock_exception,
            },
            file_handle,
        )


class TestHasUrls(unittest.TestCase):

    def test_has_urls_empty(self):
        wrapped = SubmissionWrapperFactory()
        wrapped.urls = set()
        self.assertFalse(wrapped.has_urls())

    def test_has_urls_nonempty(self):
        wrapped = SubmissionWrapperFactory()
        wrapped.urls = set("example_url")
        self.assertTrue(wrapped.has_urls())


"""
    @patch("os.makedirs")
    @patch("src.core.get_response_file_extension")
    @patch("builtins.open", new_callable=mock_open)
    async def test_download_unorganized(
        self,
        file_mock,
        get_extension_mock,
        os_makedirs_mock,
    ):
        directory = "mock directory"
        httpx_client_mock = AsyncMock()

        class MockResponse:
            status_code = 200
            content = "mock content"

        httpx_client_mock.get.return_value = MockResponse()

        wrapper = SubmissionWrapperFactory()
        wrapper.subreddit = "mock subreddit"
        wrapper.title = "mock title"
        wrapper.urls = ["url1", "url2", "url3", "url4"]
        get_extension_mock.return_value = ".jpg"

        # organized is False, so the subreddit subdirectory should not be created
        expected = {
            "url1": os.path.join(directory, "mock title.jpg"),
            "url2": os.path.join(directory, "mock title (1).jpg"),
            "url3": os.path.join(directory, "mock title (2).jpg"),
            "url4": os.path.join(directory, "mock title (3).jpg"),
        }

        listdir_mock_side_effect = [
            [],
            ["mock title.jpg"],
            ["mock title.jpg"],
            ["mock title.jpg", "mock title (1).jpg"],
            ["mock title.jpg", "mock title (1).jpg"],
            [
                "mock title.jpg",
                "mock title (1).jpg",
                "mock title (2).jpg",
            ],
            [
                "mock title.jpg",
                "mock title (1).jpg",
                "mock title (2).jpg",
            ],
        ]

        with patch(
            "os.listdir", side_effect=listdir_mock_side_effect
        ) as os_listdir_mock:
            result = await wrapper.download(client=httpx_client_mock)

        os_listdir_mock.assert_called_with(directory)

        for key in expected.keys():
            httpx_client_mock.get.assert_any_call(key, timeout=10)

        # organized is False, so the subreddit subdirectory should not be created
        os_makedirs_mock.assert_called_with(directory, exist_ok=True)

        for value in expected.values():
            file_mock.assert_any_call(value, "wb")
        self.assertDictEqual(result, expected)

    @patch("os.makedirs")
    @patch("src.core.get_response_file_extension")
    @patch("builtins.open", new_callable=mock_open)
    async def test_download_organized(
        self,
        file_mock,
        get_extension_mock,
        os_makedirs_mock,
    ):
        directory = "mock directory"
        httpx_client_mock = AsyncMock()

        class MockResponse:
            status_code = 200
            content = "mock content"

        httpx_client_mock.get.return_value = MockResponse()

        wrapper = SubmissionWrapperFactory()
        wrapper.subreddit = "mock subreddit"
        wrapper.title = "mock title"
        wrapper.urls = ["url1", "url2", "url3", "url4"]
        get_extension_mock.return_value = ".jpg"

        expected = {
            "url1": os.path.join(directory, wrapper.subreddit, "mock title.jpg"),
            "url2": os.path.join(directory, wrapper.subreddit, "mock title (1).jpg"),
            "url3": os.path.join(directory, wrapper.subreddit, "mock title (2).jpg"),
            "url4": os.path.join(directory, wrapper.subreddit, "mock title (3).jpg"),
        }

        listdir_mock_side_effect = [
            [],
            ["mock title.jpg"],
            ["mock title.jpg"],
            ["mock title.jpg", "mock title (1).jpg"],
            ["mock title.jpg", "mock title (1).jpg"],
            [
                "mock title.jpg",
                "mock title (1).jpg",
                "mock title (2).jpg",
            ],
            [
                "mock title.jpg",
                "mock title (1).jpg",
                "mock title (2).jpg",
            ],
        ]

        with patch(
            "os.listdir", side_effect=listdir_mock_side_effect
        ) as os_listdir_mock:
            result = await wrapper.download(client=httpx_client_mock)

        os_listdir_mock.assert_called_with(os.path.join(directory, wrapper.subreddit))

        for key in expected.keys():
            httpx_client_mock.get.assert_any_call(key, timeout=10)

        os_makedirs_mock.assert_called_with(
            os.path.join(directory, wrapper.subreddit), exist_ok=True
        )

        for value in expected.values():
            file_mock.assert_any_call(value, "wb")
        self.assertDictEqual(result, expected)
"""
