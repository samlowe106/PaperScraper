import os
from dataclasses import dataclass

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

    @dataclass
    class APIClient:

        def __init__(self, client_name):
            self.client_id = os.environ.get(f"{client_name}_CLIENT_ID")
            self.client_secret = os.environ.get(f"{client_name}_CLIENT_SECRET")

    def __init__(self, http_client: httpx.AsyncClient = None):

        self.http = http_client

        load_dotenv()

        self.reddit: asyncpraw.Reddit = None

        self.imgur = self.APIClient("IMGUR")

    def set_reddit(
        self, username: str = None, password: str = None
    ) -> asyncpraw.Reddit:
        """
        Signs into a new reddit instance (and storing it in this client bundle)

        :param username: username of reddit account to sign into
        :param password: password of reddit account to sign into
        :returns: reddit instance
        :raises OAuthException:
        """
        self.reddit = asyncpraw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent="PaperScraper",
            username=username if username else None,
            password=password if password else None,
        )
        return self.reddit
