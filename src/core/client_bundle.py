import os
from dataclasses import dataclass
from typing import Optional

import asyncpraw
import httpx
from dotenv import load_dotenv


@dataclass
class AsyncClientBundle:
    """
    A bundle of clients for different services. Currently includes:
    - http client (httpx.AsyncClient)
    - reddit client (praw)
    - imgur client (client id and secret)
    """

    reddit: Optional[asyncpraw.Reddit] = None
    http: Optional[httpx.AsyncClient] = None

    @dataclass
    class APIClient:

        def __init__(self, client_name):
            self.client_id = os.environ.get(f"{client_name}_CLIENT_ID")
            self.client_secret = os.environ.get(f"{client_name}_CLIENT_SECRET")

    def __init__(self):

        load_dotenv()

        self.imgur = self.APIClient("IMGUR")

    async def __aenter__(self):

        self.http = httpx.AsyncClient()

        return self

    async def __aexit__(self, exc_type, exc, tb):
        # consider contextlib.AsyncExitStack

        if self.reddit is not None:
            await self.reddit.close()

        if self.http is not None:
            await self.http.aclose()

    def set_reddit(
        self, username: str = None, password: str = None
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
            user_agent="PaperScraper",
            username=username if username and password else None,
            password=password if username and password else None,
        )
        return self.reddit
