import argparse
from shutil import make_archive
from typing import Dict
from flask import Flask, request, send_file, render_template
from prawcore.exceptions import OAuthException
from PaperScraper.core import sign_in
from PaperScraper.core.models import SubmissionSource

app = Flask(__name__)


OUTPUT_DIRECTORY = "TODO"


@app.route('/', methods=["POST", "GET"])
def root():
    """
    Landing page for PaperScraper, takes user input and run parameters
    """
    if request.method == "GET":
        return render_template("root.html")

    elif request.method == "POST":
        error = None
        source = None
        try:
            source = get_source(request.form)
        except OAuthException:
            error = "Invalid username or password."
        except ValueError as error:
            error = str(error)

        return render_template("root.html", error=error, source=source)


def get_source(form: Dict[str, str]) -> SubmissionSource:
    """
    Gets the source from which posts will be parsed and displayed
    """
    username = form["username"]
    password = form["password"]
    subreddit = form["subreddit"]

    if subreddit and username and password:
        raise ValueError("Please specify only a subreddit or a username and password.")
    if not (subreddit and username and password):
        raise ValueError("Please specify a subreddit or a username and password.")

    source_builder = (SubmissionSource.Builder()
        .age_max(form["age"])
        .submission_limit(form["limit"])
        .score_min(form["karma"]))

    if username and password:
        return source_builder.from_user_saved(sign_in(username, password)).build()

    elif subreddit:
        return source_builder.from_subreddit(subreddit, form["sortby"], sign_in()).build()


@app.route('/download')
def download_file():
    """
    Pushes the zip file to the user
    """
    return send_file(
        make_archive("paperscraper_output", "zip", OUTPUT_DIRECTORY),
        as_attachment=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="Scrapes images from Reddit")

    parser.add_argument("--debug",
                        action='store_true',
                        help="run in debug mode")
    args = parser.parse_args()
    app.run(debug=args.debug)