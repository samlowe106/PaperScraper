from bs4 import BeautifulSoup
from flask import Flask, redirect, render_template, request, session
from flask_bootstrap import Bootstrap
from os import listdir, mkdir, remove, walk
from os.path import exists, join, splitext
from requests import get
from PIL import Image
import praw
import prawcore.exceptions
from shutil import rmtree
from urllib.parse import urlparse
import zipfile

"""
Some code was taken from Harvard's CS50 Problem Set 7, W3Schools, and StackOverflow
"""

# region Constants

# Character that Windows won't allow in a filename
INVALID_CHARS = ["\\", "/", ":", "*", "?", "<", ">", "|"]

# Recognized file extensions
RECOGNIZED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif"]

OPTIONS = ["prefer_png",    # True if user wants jpg/jpeg images converted to png images
           "sort_by_sub",   # True if the user wants images sorted by subreddit
           "title_case",    # True if the user wants file names in title case
           "unsave",        # True if the user wants to unsave posts after downloading that post's image
           "limit",         # Download limit
           "desired_title"  # Format that the user wants file titles to have
           ]

# Load sensitive information from a file
with open("info.txt", 'r') as info_file:
    CLIENT_ID = info_file.readline()
    CLIENT_SECRET = info_file.readline()
    SECRET_KEY = info_file.readline()

# To prevent errors, file names (excluding extensions) shouldn't exceed 250 chars
MAX_FILE_NAME_LEN = 250

# endregion

# region Initiation

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = SECRET_KEY
session.clear()
reddit = None

# endregion

# region Error Handling


@app.errorhandler(403)
def page_not_found(e):
    return render_template('403.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


def apology(message, code=400):
    """Render message as an apology to the user"""
    return render_template("apology.html", top=code, bottom=message, code=code)

# endregion

# region Main


@app.route('/')
def index():
    # If the user hasn't signed in or come to this page via post, redirect them
    if session["username"] is None:
        redirect("/signin")

    # If the user has signed in and came via POST, begin downloading and saving posts
    if request.method == "POST":
        for option in OPTIONS:
            session[option] = request.form.get[option]

        main()

    return render_template("index.html")


@app.route('/signin', methods=["GET", "POST"])
def sign_in():
    """Attempts to sign into Reddit"""

    # Only allow info to be submitted via POST
    if request.method == "POST":
        # Ensure username and password were provided
        if not request.form.get("username"):
            return apology("Must provide a username", 403)
        if not request.form.get("password"):
            return apology("Must provide a password", 403)

        # Try to sign in
        try:
            session["reddit"] = praw.Reddit(client_id=CLIENT_ID,
                                            client_secret=CLIENT_SECRET,
                                            user_agent='PaperScraper',
                                            username=request.form.get("username"),
                                            password=request.form.get("password"))
            session["username"] = str(session["reddit"].user.me)
            session["directory"] = "\\files\\{}".format(session["username"])
            session["downloads"] = session["directory"] + "downloads"

            # If directory doesn't exist, make it
            if not exists(session["downloads"]):
                mkdir(session["downloads"])

            return redirect("/")

        except prawcore.exceptions.OAuthException:
            return apology("Invalid username or password", 403)
    else:
        return render_template("signin.html")


def main() -> None:
    """
    Loops through the posts saved on a user's Reddit account,
    downloading a certain number of images and ignoring other posts
    """

    # Retrieve saved posts
    saved_posts = session["reddit"].redditor(session["username"]).saved(limit=None)

    # Begin looping through saved posts
    count = 0
    for post in saved_posts:

        # Sanitize the post
        post = sanitize_post(post, session["title_case"])

        # Move on if the post is just a selfpost or link to a reddit thread
        if post.is_self or post.url.startswith("https://reddit.com/") or post.url.startswith("https://reddit.com/"):
            continue

        file_title = generate_title(session["desired_title"], post.title, post.subreddit, post.author)

        # Increase the count
        count += 1

        # Download images from image links
        for url in post.recognized_urls:
            download_image(post.title, url, session["directory"])

        # Unsave the post if the user wants to
        if session["unsave"]:
            post.unsave()

        # If we've downloaded as many posts as desired, break out
        if count >= session["limit"]:
            break

    """ End-of-program cleanup goes here """

    # Zip the folder containing the downloaded images
    zipped_images = zipfile.ZipFile("PaperScraper Download.zip", 'w', zipfile.ZIP_DEFLATED)
    zip_dir(session["downloads"], zipped_images)
    zipped_images.close()

    # TODO: send the zip file to the user

    # Delete the files on the server
    rmtree(session["directory"])

    return


# endregion

# region Helper Functions


def download_image(title: str, url: str, path: str) -> str:
    """
    Downloads the image from the given url to a file with the name title

    :param title: Desired title of the image
    :param url: A direct link to the image that will be downloaded
    :param path: The filepath that the file should be saved to
    :return: filepath that the image was downloaded to, or empty string for failure
    :raises: IOError, FileNotFoundError
    """

    # If the image page couldn't be reached, return an empty string for failure
    image = get(url)
    if image.status_code != 200:
        return ""

    file_title = title

    # Remove any query strings with split, then find the file extension with splitext
    file_extension = splitext(url.split('?')[0])[1]

    # If the file extension is unrecognized, don't try to download the file
    if file_extension not in RECOGNIZED_EXTENSIONS:
        return ""

    # Start a loop (prevents this file from overwriting another with the same name by adding (i) before the extension)
    for i in range(len(listdir(path)) + 1):

        # Insert a number in the filename to prevent conflicts
        if i > 0:
            file_title = "{0} ({1})".format(title, i)

        # If no files share the same name, write the file
        if (title + file_extension) not in listdir(path):

            # Write the file
            with open(path + file_title + file_extension, "wb") as File:
                for chunk in image.iter_content(4096):
                    File.write(chunk)

            # If the user prefers PNG images and the file is a jpg, re-save it as a png
            if session["prefer_png"] and file_extension == ".jpg":
                im = Image.open(path + file_title + file_extension)
                file_extension = ".png"
                rgb_im = im.convert('RGB')
                rgb_im.save(path + file_title + file_extension)
                # Delete the previous jpg file
                remove(path + file_title + ".jpg")

            # Return the final name of the file (means it was successfully downloaded there)
            return file_title + file_extension


def find_urls(url: str) -> list:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages

    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """
    # If the URL (without query strings) ends with any recognized file extension, this is a direct link to an image
    # Should match artstation, i.imgur.com, i.redd.it, and other pages
    for extension in RECOGNIZED_EXTENSIONS:
        if url.split('?')[0].endswith(extension):  # .split() removes any query strings from the URL
            return [url]

    # Imgur albums
    if "imgur.com/a/" in url:
        return parse_imgur_album(url)

    # Imgur single-image pages
    elif "imgur.com" in url:
        return [parse_imgur_single(url)]

    return []


def parse_imgur_album(album_url: str) -> list:
    """
    Imgur albums reference multiple other images hosted on imgur by image ID only, so album pages must be scraped to
    get single-image webpages, then scraped again to get a list of direct links to each image in the album

    :param album_url: url of an imgur album
    :return: direct links to each image in the specified album
    """
    # Find all the single image pages referenced by this album
    album_page = get(album_url)
    album_soup = BeautifulSoup(album_page.text, "html.parser")
    single_images = ["https://imgur.com/" + div["id"] for div in album_soup.select("div[class=post-images] > div[id]")]
    # Make a list of the direct links to the image hosted on each single-image page; return the list of all those images
    return [parse_imgur_single(link) for link in single_images]


def parse_imgur_single(url: str) -> str:
    """
    Scrapes an imgur page containing only a single image (NOT a direct link to the image) and returns
    a direct link to that image

    :param url: A single-image imgur page
    :return: A direct link to the image hosted on that page
    """
    page = get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    return soup.select("link[rel=image_src]")[0]["href"]


def retitle(current_string: str, title_case: bool) -> str:
    """
    Strips non-ASCII characters and characters Windows doesn't support in file names, removes any preceding or
    trailing periods and spaces, and optionally capitalizes the first letter of each word

    :param current_string: the current string
    :param title_case: True if the returned string should be in title case, else False
    :return: valid file name with no leading or trailing spaces, periods, or commas
    """
    # Recapitalize the title and remove any incompatible characters
    new_string = ""
    # Replace non-ASCII characters with a space
    for i, char in enumerate(current_string):
        if char not in INVALID_CHARS:
            # Replace " with '
            if char == '"':
                new_string += "'"
            # If desired, enforce title case
            elif title_case and (i == 0 or current_string[i - 1] == ' '):
                new_string += (char.upper())
            # Prevent consecutive spaces
            elif char == ' ' and current_string[i - 1] == ' ':
                pass
            else:
                new_string += char

    # Remove any trailing periods or spaces
    while new_string.endswith('.') or new_string.endswith(',') or new_string.endswith(' '):
        new_string = new_string[:-1]

    # Remove any preceding periods, spaces, or commas
    while new_string.startswith('.') or new_string.startswith(',') or new_string.startswith(' '):
        new_string = new_string[1:]

    return new_string


def sanitize_post(post, title_case):
    """
    Adds is_comment properties to posts and is_self property to comments, finds valid urls in non-self posts,
    cleans up post title, and adds info about the post's domain

    :param post: a post object
    :param title_case: True if the post title should be in title case, else false
    :return: the same post with edited data to prevent errors
    """

    # If the post links somewhere, find scrape-able images
    if hasattr(post, 'title'):
        # Establish the post's domain
        uri = urlparse(post.url)
        post.domain = '{0}://{1}'.format(uri.scheme, uri.netloc)
        # Define a working filename
        post.title = retitle(post.title, title_case)
        post.is_comment = False
        post.recognized_urls = find_urls(post.url)

    # If the post is a comment, mark it as a selfpost
    else:
        post.is_self = True
        post.is_comment = True

    return post


def generate_title(original_string: str, title: str, subreddit: str, poster: str) -> str:
    """
    Generates a new title based on the layout the user indicated

    :param original_string: way the author wants the post to be sorted
    :param title: title of reddit post
    :param subreddit: title of the subreddit the reddit post is from
    :param poster: title of the author of the reddit post
    :return:
    """
    # TODO: add drag-and-drop so user can only have up to one occurrence of %t, %s, and %p then simplify code

    # Replace special characters in string title (inspired by some of the code in CS50 2018 PSet 7)
    for old, new in [('%s', subreddit), ('%p', poster), ('%t', title)]:
        new_string = original_string.replace(old, new)

    # If the string is too long, limit any occurrences of the title to the first sentence
    if len(new_string) > MAX_FILE_NAME_LEN:
        for old, new in [('%s', subreddit), ('%p', poster), ('%t', title.split('.', 1)[0])]:
            new_string = original_string.replace(old, new)
        # If the string is still too long, truncate it
        if len(new_string) > MAX_FILE_NAME_LEN:
            new_string = new_string[:MAX_FILE_NAME_LEN]

    return new_string


def zip_dir(path: str, zip_handle) -> None:
    """
    Zips the specified path into the specified zipfile
    Credit to https://stackoverflow.com/a/1855118

    :param path:
    :param zip_handle:
    :return:
    """
    for root, dirs, files in walk(path):
        for file in files:
            zip_handle.write(join(root, file))
    return

# endregion
