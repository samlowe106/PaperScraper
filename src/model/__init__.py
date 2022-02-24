from praw import Reddit
from .parsers import *
from .strings import *
from .submission_wrapper import *
from .urls import *
from .source import SORT_OPTIONS, SubmissionSource


def sign_in(username: str = None, password: str = None) -> Reddit:
    """
    Signs in to reddit

    :raises OAuthException:
    """
    if username and password:
        return Reddit(
            client_id=os.environ.get("CLIENT_ID"),
            client_secret=os.environ.get("CLIENT_SECRET"),
            user_agent='PaperScraper',
            username=username,
            password=password)
    return Reddit(
        client_id=os.environ.get("CLIENT_ID"),
        client_secret=os.environ.get("CLIENT_SECRET"),
        user_agent='PaperScraper')
