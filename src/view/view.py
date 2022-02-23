from getpass import getpass
from typing import Any, Dict
from shutil import make_archive
from flask import Flask, render_template, request, send_file
from ..model import SubmissionWrapper


class View():
    """
    Interface representing a way to interact with PaperScraper
    """

    def get_run_info(self, args : Dict[str, Any]) -> Dict[str, Any]:
        """
        Gets parameters about this run, based on the given args
        """

    def show_results(self, output_directory: str):
        """
        Displays information about the downloaded files at the end of the run
        """

    def output_submission_wrapper(self, index: int, post: SubmissionWrapper):
        """
        Outputs a submission wrapper so the user can see it
        """

    def print_message(self, message: str):
        """
        Shows output to the user
        :param message: message to show the user
        """

class TerminalView(View):
    """
    Class representing a way to interact with PaperScraper through the Terminal or Command Line
    """

    def __init__(self):
        return


    def get_run_info(self, args) -> Dict[str, Any]:
        """
        Gets parameters about this run
        """
        args["password"] = getpass("Password: ")
        return args


    def print_message(self, message: str):
        """
        Shows output to the user
        :param message: message to show the user
        """
        print(message)


class FlaskWebView():
    """
    Interface representing a way to interact with PaperScraper
    """

    app = Flask(__name__)

    def __init__(self) -> None:
        self.submission_wrappers = []
        self.output_path: str = None
        self.app.run()


    def show_results(self, output_directory: str):
        """
        Displays information about the downloaded files at the end of the run
        """
        self.output_path = make_archive("paperscraper_output", "zip", output_directory)


    @app.route('/', methods=["POST", "GET"])
    def index(self):
        """
        Landing page for PaperScraper, takes user input and run parameters
        """


    @app.route('/download')
    def download_file(self):
        """
        Pushes the zip file to the user
        """
        return send_file(self.output_path, as_attachment=True)


    @app.route('/', methods=["POST", "GET"])
    def result(self):
        """
        Results page, after user has told PaperScraper to start running
        """

    def output(self, message: str, error: bool = False) -> None:
        """
        Shows output to the user
        :param message: message to show the user
        :param error: whether the message is an error message or not
        """
        return render_template('index.html')


    def get_run_info(self, _) -> Dict[str, Any]:
        """
        Gets parameters about this run
        """
        return {"username" : request.form("username"),
                "password" : request.form("password"),
                "limit" : int(request.form("limit")),
                "title" : request.form("title"),
                "organize" : request.form("organize"),
                "directory" : ""} # TBD


    def output_submission_wrapper(self, _, wrapper: SubmissionWrapper):
        """
        Outputs the submission wrapper to the user
        """
        self.submission_wrappers.append(wrapper)