from PaperScraper.src.model import submission_wrapper
from flask import Flask, render_template, request
from PaperScraper.src.model.submission_wrapper import SubmissionWrapper
from typing import Dict

class FlaskWebView():
    """
    Interface representing a way to interact with PaperScraper
    """
    app = Flask(__name__)
    submission_wrappers = []

    @app.route('/', methods=["GET"])
    def output(self, message: str, error: bool = False) -> None:
        """
        Shows output to the user
        :param message: message to show the user
        :param error: whether the message is an error message or not
        """

        return render_template('index.html')


    @app.route('/', methods=["POST", "GET"])
    def get_run_info(self) -> Dict[str, any]:
        """
        """
        return {"username" : request.form("username"),
                "password" : request.form("password"),
                "limit" : int(request.form("limit")),
                "titlecase" : request.form("titlecase"),
                "title" : request.form("title"),
                "organize" : request.form("organize")}


    def output_submission_wrapper(self, index: int, wrapper: SubmissionWrapper):
        """
        """
        self.submission_wrappers.append(wrapper)
        return render_template("results.html")