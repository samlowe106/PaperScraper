import asyncio
import unittest
from unittest.mock import AsyncMock

from src.main import handle_wrapped


class TestMain(unittest.IsolatedAsyncioTestCase):

    def test_logs_exception(self):
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Test exception")

        wrapped = AsyncMock()
        wrapped.url = "https://example.com"
        wrapped.download.side_effect = Exception("Test exception")
        wrapped.can_unsave = False
        wrapped.log = AsyncMock()
        wrapped.__str__.return_value = "Summary string"

        result = asyncio.run(
            handle_wrapped(wrapped, mock_client, False, "test_title", "test_log_path")
        )

        self.assertIn("Encountered exception parsing https://example.com", result)
        self.assertIn("Test exception", result)
        wrapped.log.assert_awaited_once_with(
            "test_log_path", exception="Test exception"
        )
        wrapped.download.assert_called_once_with(mock_client)

    async def test_returns_summary_string(self):
        mock_client = AsyncMock()

        wrapped = AsyncMock()
        wrapped.url = "https://example.com"
        wrapped.download = AsyncMock()
        wrapped.download.return_value = None
        wrapped.can_unsave = False
        wrapped.__str__.return_value = "Summary string"

        result = await handle_wrapped(wrapped, mock_client, False, "test_title")

        self.assertEqual(result, "Summary string")
        wrapped.download.assert_called_once_with(mock_client)

    async def test_unsaves(self):
        mock_client = AsyncMock()

        wrapped = AsyncMock()
        wrapped.url = "https://example.com"
        wrapped.download = AsyncMock()
        wrapped.download.return_value = None
        wrapped.can_unsave = True
        wrapped.unsave = AsyncMock()
        wrapped.__str__.return_value = "Summary string"

        result = await handle_wrapped(
            wrapped, mock_client, False, "test_title", dry=False
        )

        self.assertEqual(result, "Summary string")
        wrapped.download.assert_called_once_with(mock_client)
        wrapped.unsave.assert_called_once()

    async def test_does_not_unsave_if_dry_false(self):
        mock_client = AsyncMock()

        wrapped = AsyncMock()
        wrapped.url = "https://example.com"
        wrapped.download = AsyncMock()
        wrapped.download.return_value = None
        wrapped.can_unsave = True
        wrapped.unsave = AsyncMock()
        wrapped.__str__.return_value = "Summary string"

        result = await handle_wrapped(
            wrapped, mock_client, False, "test_title", dry=True
        )

        self.assertEqual(result, "Summary string")
        wrapped.download.assert_called_once_with(mock_client)
        wrapped.unsave.assert_not_called()

    # todo: test with different parameters that should be passed to download
    async def test_organize_parameter(self):
        mock_client = AsyncMock()

        wrapped = AsyncMock()
        wrapped.url = "https://example.com"
        wrapped.download = AsyncMock()
        wrapped.download.return_value = None
        wrapped.can_unsave = False
        wrapped.__str__.return_value = "Summary string"
        wrapped.subreddit = "mock_subreddit"

        result = await handle_wrapped(
            wrapped, mock_client, organize=True, title="test_title"
        )

        self.assertEqual(result, "Summary string")
        wrapped.download.assert_called_once_with(mock_client)


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
        await wrapped.download(
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
