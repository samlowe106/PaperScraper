from getpass import getpass
from typing import Any


class View():
    """
    Interface representing a way to interact with PaperScraper
    """


    def output(self, message: str):
        pass


    def get_input(self, prompt: str) -> str:
        pass


    def get_password(self, prompt: str) -> str:
        pass


class TextView(View):
    """
    Class representing a way to interact with PaperScraper through the Terminal or Command Line
    """


    def print_message(self, message: Any):
        print(message)


    def get_input(self, prompt: str) -> str:
        return input(prompt)


    def get_password(self, prompt: str) -> str:
        return getpass(prompt)
