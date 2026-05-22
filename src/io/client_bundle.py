import getpass
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

    def __init__(self, http_client: httpx.AsyncClient, reddit_sign_in=False):

        self.http = http_client

        load_dotenv()

        if reddit_sign_in:
            self.reddit = self.reddit_sign_in(
                input("Reddit Username: "), getpass.getpass("Password: ")
            )
        else:
            self.reddit = self.reddit_sign_in()

        self.imgur = self.APIClient("IMGUR")

    @staticmethod
    def reddit_sign_in(username: str = None, password: str = None) -> asyncpraw.Reddit:
        """
        Signs in to reddit

        :raises OAuthException:
        """
        if username and password:
            return asyncpraw.Reddit(
                client_id=os.environ.get("REDDIT_CLIENT_ID"),
                client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
                user_agent="PaperScraper",
                username=username,
                password=password,
            )
        return asyncpraw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent="PaperScraper",
        )
