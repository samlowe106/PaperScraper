import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from src.main import handle_wrapped


class TestMain(unittest.IsolatedAsyncioTestCase):

    def test_logs_exception(self):
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Test exception")

        wrapped = MagicMock()
        wrapped.url = "https://example.com"
        wrapped.download_all.side_effect = Exception("Test exception")
        wrapped.can_unsave = False
        wrapped.log = MagicMock()

        result = asyncio.run(
            handle_wrapped(wrapped, mock_client, False, "test_title", "test_log_path")
        )

        self.assertIn("Encountered exception parsing https://example.com", result)
        self.assertIn("Test exception", result)
        wrapped.log.assert_called_once_with("test_log_path", exception="Test exception")
        wrapped.download_all.assert_called_once_with(
            "", mock_client, title="test_title", organize=False
        )

    async def test_returns_summary_string(self):
        mock_client = MagicMock()

        wrapped = MagicMock()
        wrapped.url = "https://example.com"
        wrapped.download_all = AsyncMock()
        wrapped.download_all.return_value = None
        wrapped.can_unsave = False
        wrapped.summary_string.return_value = "Summary string"

        result = await handle_wrapped(wrapped, mock_client, False, "test_title")

        self.assertEqual(result, "Summary string")
        wrapped.download_all.assert_called_once_with(
            "", mock_client, title="test_title", organize=False
        )

    async def test_unsaves(self):
        mock_client = MagicMock()

        wrapped = MagicMock()
        wrapped.url = "https://example.com"
        wrapped.download_all = AsyncMock()
        wrapped.download_all.return_value = None
        wrapped.can_unsave = True
        wrapped.unsave = MagicMock()
        wrapped.summary_string.return_value = "Summary string"

        result = await handle_wrapped(wrapped, mock_client, False, "test_title")

        self.assertEqual(result, "Summary string")
        wrapped.download_all.assert_called_once_with(
            "", mock_client, title="test_title", organize=False
        )
        wrapped.unsave.assert_called_once()

    # todo: test with different parameters that should be passed to download_all
    async def test_organize_parameter(self):
        mock_client = MagicMock()

        wrapped = MagicMock()
        wrapped.url = "https://example.com"
        wrapped.download_all = AsyncMock()
        wrapped.download_all.return_value = None
        wrapped.can_unsave = False
        wrapped.summary_string.return_value = "Summary string"
        wrapped.subreddit = "mock_subreddit"

        result = await handle_wrapped(
            wrapped, mock_client, organize=True, title="test_title"
        )

        self.assertEqual(result, "Summary string")
        wrapped.download_all.assert_called_once_with(
            "mock_subreddit", mock_client, title="test_title", organize=True
        )


"""
async def handle_wrapped(
    wrapped: SubmissionWrapper,
    client: httpx.AsyncClient,
    organize: bool,
    title: str,
    log_path: str = None,
) -> str:
    exception = ""
    try:
        download_dir = "" if not organize else wrapped.subreddit
        await wrapped.download_all(
            download_dir,
            client,
            title=title,
            organize=organize,
        )
        if wrapped.can_unsave:
            wrapped.unsave()
        return wrapped.summary_string()
    except Exception as e:
        exception = str(e)
        return f"Encountered exception parsing {wrapped.url}:\n{exception}"
    finally:
        if log_path is not None:
            wrapped.log(log_path, exception=exception)
"""
