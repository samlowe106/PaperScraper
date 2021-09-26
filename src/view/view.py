from getpass import getpass
from typing import Any


class View():
    """
    Interface representing a way to interact with PaperScraper
    """


    def output(self, message: str) -> None:
        """
        Shows output to the user
        :param message: message to show the user
        """


    def get_input(self, prompt: str, field: str) -> str:
        """
        Gets user input
        NOTE: DO NOT USE FOR SENSITIVE DATA! For sensitive data such as passwords,
        use get_password instead!
        :param prompt: prompt to show the user
        :param field: the field from which to retrieve user input (if necessary)
        :return: user input
        """


    def get_password(self, prompt: str) -> str:
        """
        Gets sensitive user input, such as a password, in a secure way
        :param prompt: prompt to show the user
        :return: user input
        """


class TextView(View):
    """
    Class representing a way to interact with PaperScraper through the Terminal or Command Line
    """

    def __init__(self):
        return


    def print_message(self, message: Any):
        """
        Shows output to the user
        :param message: message to show the user
        """
        print(message)


    def get_input(self, prompt: str, field = None) -> str:
        """
        Gets user input
        NOTE: DO NOT USE FOR SENSITIVE DATA! For sensitive data such as passwords,
        use get_password instead!
        :param prompt: prompt to show the user
        :param field: (not used)
        :return: user input
        :raise ValueError:
        """
        if field is not None:
            raise ValueError("No value should be passed for field!")
        return input(prompt)


    def get_password(self, prompt: str) -> str:
        return getpass(prompt)


class FlaskWebView(View):
    """
    Class representing a way to interact with PaperScraper through a Flask website
    """

    def print_message(self, message: Any):
        """
        Shows output to the user
        :param message: message to show the user
        """
        #TODO
        str(message)


    def get_input(self, prompt: str, field: str) -> str:
        """
        Gets user input
        NOTE: DO NOT USE FOR SENSITIVE DATA! For sensitive data such as passwords,
        use get_password instead!
        :param prompt: prompt to show the user
        :param field: the field from which to retrieve user input
        :return: user input
        """
        #TODO


    def get_password(self, prompt: str) -> str:
        """
        Gets sensitive user input, such as a password, in a secure way
        :param prompt: prompt to show the user
        :return: user input
        """
        #TODO