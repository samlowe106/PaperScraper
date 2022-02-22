from getpass import getpass
from sys import argv
from typing import Dict
from PaperScraper.src.model.submission_wrapper import SubmissionWrapper
from praw import Reddit


class View():
    """
    Interface representing a way to interact with PaperScraper
    """

    def get_run_info(self) -> Dict[str, str]:
        """

        """

    def output_submission_wrapper(self, index: int, post: SubmissionWrapper):
        """
        """

    def print_message(self, message: str):
        """
        Shows output to the user
        :param message: message to show the user
        """

class TextView(View):
    """
    Class representing a way to interact with PaperScraper through the Terminal or Command Line
    """

    def __init__(self):
        return


    def get_run_info(self, args) -> Dict[str, str]:
        """

        """
        args["password"] = getpass("Password: ")
        return args


    def print_message(self, message: str):
        """
        Shows output to the user
        :param message: message to show the user
        """
        print(message)
