import os
from dataclasses import dataclass
from importlib.metadata import version

import asyncpraw
import httpx
from dotenv import load_dotenv

# reddit asks for "<platform>:<app id>:<version> (by <contact>)" and throttles
# generic user agents harder
USER_AGENT = (
    f"python:paperscraper:{version('paperscraper')}"
    " (by https://github.com/samlowe106/PaperScraper)"
)


def make_http_client(**kwargs) -> httpx.AsyncClient:
    """
    The http client every request goes through. Tests build theirs here too
    (passing a mock transport) so they exercise the same configuration.
    """
    # image hosts and short links commonly redirect, and httpx doesn't follow
    # redirects unless asked
    return httpx.AsyncClient(follow_redirects=True, **kwargs)


@dataclass
class AsyncClientBundle:
    """
    A bundle of clients for different services. Currently includes:
    - http client (httpx.AsyncClient)
    - reddit client (asyncpraw)
    """

    reddit: asyncpraw.Reddit | None = None
    http: httpx.AsyncClient | None = None

    def __init__(self):

        load_dotenv()

    async def __aenter__(self):

        self.http = make_http_client()

        return self

    async def __aexit__(self, exc_type, exc, tb):
        # close http even if closing reddit fails
        try:
            if self.reddit is not None:
                await self.reddit.close()
        finally:
            if self.http is not None:
                await self.http.aclose()

    def set_reddit(
        self, username: str | None = None, password: str | None = None
    ) -> asyncpraw.Reddit:
        """
        Signs into a new reddit instance (and stores it in this client bundle)

        :param username: username of reddit account to sign into
        :param password: password of reddit account to sign into
        :returns: reddit instance
        :raises OAuthException:
        """
        self.reddit = asyncpraw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=USER_AGENT,
            username=username if username and password else None,
            password=password if username and password else None,
            # don't make a runtime PyPI request to check for asyncpraw updates
            check_for_updates=False,
        )
        return self.reddit
