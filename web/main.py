from typing import Dict, Any
from shutil import make_archive
from flask import Flask, send_file, render_template
from ..core.models import SubmissionWrapper


app = Flask(__name__)

def __init__(self) -> None:
    self.submission_wrappers = []
    self.output_path = None
    self.app.run()


def show_results(self, output_directory: str):
    """
    Displays information about the downloaded files at the end of the run
    """
    self.output_path = make_archive("paperscraper_output", "zip", output_directory)


@app.route('/', methods=["POST", "GET"])
def root(self):
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


def get_run_info(self, request) -> Dict[str, Any]:
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