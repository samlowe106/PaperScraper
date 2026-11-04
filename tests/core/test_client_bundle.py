from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.core import AsyncClientBundle
from src.core.client_bundle import USER_AGENT


class TestConstructor:

    def test_http_client_is_none(self, monkeypatch):
        client_bundle = AsyncClientBundle()
        assert client_bundle.http is None
        assert client_bundle.reddit is None

    @pytest.mark.asyncio
    async def test_http_client_is_not_none(self, monkeypatch):
        async with AsyncClientBundle() as clients:
            assert isinstance(clients.http, httpx.AsyncClient)
            assert clients.reddit is None

    @pytest.mark.asyncio
    async def test_http_client_follows_redirects(self):
        # image hosts and short links redirect; without this every redirected
        # url came back as a 3xx and was dropped
        async with AsyncClientBundle() as clients:
            assert clients.http is not None
            assert clients.http.follow_redirects

    @pytest.mark.asyncio
    async def test_http_closed_even_if_reddit_close_fails(self):
        bundle = AsyncClientBundle()
        await bundle.__aenter__()
        http = bundle.http
        assert http is not None
        bundle.reddit = MagicMock()
        bundle.reddit.close = AsyncMock(side_effect=RuntimeError("boom"))
        with pytest.raises(RuntimeError):
            await bundle.__aexit__(None, None, None)
        assert http.is_closed


class TestSetReddit:

    reddit_sentinel = object()

    def test_creates_and_returns_reddit_object(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")

        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None

        # don't patch __new__, it's super invasive and messes up later tests
        with patch(
            "asyncpraw.Reddit", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit()
            mock_reddit.assert_called_once()
            assert reddit == self.reddit_sentinel
            assert client_bundle.reddit == self.reddit_sentinel

    def test_correct_call_if_no_credentials(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None

        with patch(
            "asyncpraw.Reddit", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit()
            mock_reddit.assert_called_once_with(
                client_id="mock reddit client id",
                client_secret="mock reddit client secret",
                user_agent=USER_AGENT,
                username=None,
                password=None,
                check_for_updates=False,
            )
            assert reddit == self.reddit_sentinel
            assert client_bundle.reddit == self.reddit_sentinel

    def test_correct_call_if_only_username(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None
        with patch(
            "asyncpraw.Reddit", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit(username="username")
            mock_reddit.assert_called_once_with(
                client_id="mock reddit client id",
                client_secret="mock reddit client secret",
                user_agent=USER_AGENT,
                username=None,
                password=None,
                check_for_updates=False,
            )
            assert reddit == self.reddit_sentinel
            assert client_bundle.reddit == reddit

    def test_correct_call_if_only_password(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None
        with patch(
            "asyncpraw.Reddit", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit(password="password")
            mock_reddit.assert_called_once_with(
                client_id="mock reddit client id",
                client_secret="mock reddit client secret",
                user_agent=USER_AGENT,
                username=None,
                password=None,
                check_for_updates=False,
            )
            assert reddit == self.reddit_sentinel
            assert client_bundle.reddit == self.reddit_sentinel

    def test_correct_call_if_correct_credentials(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None
        with patch(
            "asyncpraw.Reddit", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit(username="username", password="password")
            mock_reddit.assert_called_once_with(
                client_id="mock reddit client id",
                client_secret="mock reddit client secret",
                user_agent=USER_AGENT,
                username="username",
                password="password",
                check_for_updates=False,
            )
            assert reddit == self.reddit_sentinel

    def test_user_agent_is_descriptive(self):
        # reddit throttles generic user agents; it wants platform:app:version
        platform, app, rest = USER_AGENT.split(":", 2)
        assert (platform, app) == ("python", "paperscraper")
        assert rest[0].isdigit()
