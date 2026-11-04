import os
from dataclasses import dataclass
from importlib.metadata import version

import asyncpraw
import httpx
from dotenv import load_dotenv

from .host_limiter import HostLimitedTransport

# reddit asks for "<platform>:<app id>:<version> (by <contact>)" and throttles
# generic user agents harder
USER_AGENT = (
    f"python:paperscraper:{version('paperscraper')}"
    " (by https://github.com/samlowe106/PaperScraper)"
)


# connections in the pool, and so requests in flight at once. The limiter's total
# must equal the pool size so requests wait in the limiter (no timeout) rather
# than in the pool (where waiting counts against the request's timeout)
MAX_CONNECTIONS = 32
# requests in flight to any one host; nearly every download goes to one of a few
# hosts (i.redd.it, i.imgur.com), and imgur answers bursts with 429s
MAX_PER_HOST = 8


def make_http_client(
    transport: httpx.AsyncBaseTransport | None = None, **kwargs
) -> httpx.AsyncClient:
    """
    The http client every request goes through. Tests build theirs here too
    (passing a mock transport) so they exercise the same configuration.
    """
    if transport is None:
        transport = httpx.AsyncHTTPTransport(
            limits=httpx.Limits(
                max_connections=MAX_CONNECTIONS,
                # the default (20) would drop connections to the busy hosts
                max_keepalive_connections=MAX_CONNECTIONS,
            )
        )
    return httpx.AsyncClient(
        transport=HostLimitedTransport(
            transport, per_host=MAX_PER_HOST, total=MAX_CONNECTIONS
        ),
        # image hosts and short links commonly redirect, and httpx doesn't
        # follow redirects unless asked
        follow_redirects=True,
        **kwargs,
    )


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
