from unittest.mock import patch

import asyncpraw
import httpx
import pytest

from src.core import AsyncClientBundle


class TestConstructor:

    def test_http_client_is_none(self, monkeypatch):
        monkeypatch.setenv("IMGUR_CLIENT_ID", "mock imgur client id")
        monkeypatch.setenv("IMGUR_CLIENT_SECRET", "mock imgur client secret")
        client_bundle = AsyncClientBundle()
        assert client_bundle.http is None
        assert client_bundle.imgur.client_id == "mock imgur client id"
        assert client_bundle.imgur.client_secret == "mock imgur client secret"
        assert client_bundle.reddit is None

    @pytest.mark.asyncio
    async def test_http_client_is_not_none(self, monkeypatch):
        monkeypatch.setenv("IMGUR_CLIENT_ID", "mock imgur client id")
        monkeypatch.setenv("IMGUR_CLIENT_SECRET", "mock imgur client secret")
        async with httpx.AsyncClient() as client:
            client_bundle = AsyncClientBundle(client)
            assert client_bundle.http == client
            assert client_bundle.imgur.client_id == "mock imgur client id"
            assert client_bundle.imgur.client_secret == "mock imgur client secret"
            assert client_bundle.reddit is None


class TestSetReddit:

    reddit_sentinel = object()

    def test_creates_and_returns_reddit_object(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        monkeypatch.setenv("IMGUR_CLIENT_ID", "mock imgur client id")
        monkeypatch.setenv("IMGUR_CLIENT_SECRET", "mock imgur client secret")

        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None

        with patch.object(
            asyncpraw.Reddit, "__new__", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit()
            mock_reddit.assert_called_once()
            assert reddit == self.reddit_sentinel
            assert client_bundle.reddit == self.reddit_sentinel

    def test_correct_call_if_no_credentials(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        monkeypatch.setenv("IMGUR_CLIENT_ID", "mock imgur client id")
        monkeypatch.setenv("IMGUR_CLIENT_SECRET", "mock imgur client secret")
        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None

        with patch.object(
            asyncpraw.Reddit, "__new__", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit()
            mock_reddit.assert_called_once_with(
                asyncpraw.reddit.Reddit,
                client_id="mock reddit client id",
                client_secret="mock reddit client secret",
                user_agent="PaperScraper",
                username=None,
                password=None,
            )
            assert reddit == self.reddit_sentinel
            assert client_bundle.reddit == self.reddit_sentinel

    def test_correct_call_if_only_username(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        monkeypatch.setenv("IMGUR_CLIENT_ID", "mock imgur client id")
        monkeypatch.setenv("IMGUR_CLIENT_SECRET", "mock imgur client secret")
        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None
        with patch.object(
            asyncpraw.Reddit, "__new__", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit(username="username")
            mock_reddit.assert_called_once_with(
                asyncpraw.reddit.Reddit,
                client_id="mock reddit client id",
                client_secret="mock reddit client secret",
                user_agent="PaperScraper",
                username=None,
                password=None,
            )
            assert reddit == self.reddit_sentinel
            assert client_bundle.reddit == reddit

    def test_correct_call_if_only_password(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        monkeypatch.setenv("IMGUR_CLIENT_ID", "mock imgur client id")
        monkeypatch.setenv("IMGUR_CLIENT_SECRET", "mock imgur client secret")
        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None
        with patch.object(
            asyncpraw.Reddit, "__new__", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit(password="password")
            mock_reddit.assert_called_once_with(
                asyncpraw.reddit.Reddit,
                client_id="mock reddit client id",
                client_secret="mock reddit client secret",
                user_agent="PaperScraper",
                username=None,
                password=None,
            )
            assert reddit == self.reddit_sentinel
            assert client_bundle.reddit == self.reddit_sentinel

    def test_correct_call_if_correct_credentials(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        monkeypatch.setenv("IMGUR_CLIENT_ID", "mock imgur client id")
        monkeypatch.setenv("IMGUR_CLIENT_SECRET", "mock imgur client secret")
        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None
        with patch.object(
            asyncpraw.Reddit, "__new__", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit(username="username", password="password")
            mock_reddit.assert_called_once_with(
                asyncpraw.reddit.Reddit,
                client_id="mock reddit client id",
                client_secret="mock reddit client secret",
                user_agent="PaperScraper",
                username="username",
                password="password",
            )
            assert reddit, self.reddit_sentinel
            assert reddit == self.reddit_sentinel
