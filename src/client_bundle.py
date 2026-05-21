import getpass
import os
from dataclasses import dataclass

import httpx
import praw
from dotenv import load_dotenv


@dataclass
class ImgurClient:
    client_id: str | None
    client_secret: str | None


@dataclass
class ClientBundle:
    """
    A bundle of clients for different services. Currently includes:
    - http client (httpx)
    - reddit client (praw)
    - imgur client (client id and secret)
    """

    def __init__(self, http_client: httpx.BaseClient, reddit_sign_in=False):

        self.http = http_client

        load_dotenv()

        if reddit_sign_in:
            self.reddit = self.reddit_sign_in(
                input("Reddit Username: "), getpass.getpass("Password: ")
            )
        else:
            self.reddit = self.reddit_sign_in()

        self.imgur = ImgurClient(
            client_id=os.environ.get("IMGUR_CLIENT_ID"),
            client_secret=os.environ.get("IMGUR_CLIENT_SECRET"),
        )

    @staticmethod
    def reddit_sign_in(username: str = None, password: str = None) -> praw.Reddit:
        """
        Signs in to reddit

        :raises OAuthException:
        """
        if username and password:
            return praw.Reddit(
                client_id=os.environ.get("REDDIT_CLIENT_ID"),
                client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
                user_agent="PaperScraper",
                username=username,
                password=password,
            )
        return praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent="PaperScraper",
        )
