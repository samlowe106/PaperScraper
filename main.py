from bs4 import BeautifulSoup
from flask import Flask, redirect, render_template, request, session
from os import listdir, remove
from os.path import splitext
from requests import get
from PIL import Image
import praw
import prawcore.exceptions
from urllib.parse import urlparse

# region Constants

# Character that Windows won't allow in a filename
INVALID_CHARS = ["\\", "/", ":", "*", "?", "<", ">", "|"]

# Recognized file extensions
RECOGNIZED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif"]

# Client ID and Secret
with open("info.txt", 'r') as info_file:
    CLIENT_ID = info_file.readline()
    CLIENT_SECRET = info_file.readline()

# endregion

# Initiate app
app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


def main() -> None:
    """
    Loops through the posts saved on a user's Reddit account,
    downloading a certain number of images and ignoring other posts
    """

    # True if the user would like all jpg images converted into png images, else false
    prefer_png = False

    # True if the user wants images sorted by subreddit
    sort_by_sub = False

    # True if the user wants file names in title case
    title_case = True

    # Tentative download limit
    download_limit = -1

    # Retrieve saved posts
    saved_posts = reddit.redditor(str(reddit.user.me())).saved(limit=None)

    # Main loop
    running = True
    while running:

        # Begin looping through saved posts
        index = 0
        for post in saved_posts:

            # Sanitize the post
            post = sanitize_post(post, title_case)

            # Move on if the post is just a selfpost or link to a reddit thread
            if post.is_self or post.url.startswith("https://reddit.com/") or post.url.startswith("https://reddit.com/"):
                continue

            # Increase the index
            index += 1

            # Parse the image link
            images_downloaded = [download_image(post.title, url, DIRECTORY) for url in post.recognized_urls]

            """
             Information about the post
            print("\n{0}. {1}".format(index, post.title))
            print("   r/" + str(post.subreddit))
            print("   " + post.url)
            for image in images_downloaded:
                print("   Saved as " + image)
            """

            # Unsave the post
            post.unsave()

            # If we've downloaded as many issues as desired, break out
            if index >= download_limit > 0:
                break

    # End-of-program cleanup goes here

    return


def download_image(title: str, url: str, path: str) -> str:
    """
    Downloads the image from the given url to a file with the name title

    :param title: Title of the image (not including (i))
    :param url: A URL containing a single image, (the one to be downloaded)
    :param path: The filepath that the file should be saved to
    :return: filepath that the image was downloaded to, empty string if failed
    :raises: IOError, FileNotFoundError
    """

    # Try to download image data
    image = get(url)

    # If the image page couldn't be reached, return an empty string for failure
    if image.status_code != 200:
        return ""

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
            if PNG_PREFERRED and file_extension == ".jpg":
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
    Some imgur pages with one image also include the imgur UI, so the page must be scraped to find a direct link
    to that image
    :param url: A single-image imgur page
    :return: A direct link to the image hosted on that page
    """
    page = get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    return soup.select("link[rel=image_src]")[0]["href"]


def retitle(current_string: str, title_case: bool) -> str:
    """
    Capitalizes the first letter in each word, strips non-ASCII characters and characters Windows doesn't support in
    file names, and removes any preceding or trailing periods and spaces
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

    # If the string is too long, limit it to the first sentence
    if len(new_string) > 250:
        new_string = new_string.split('.', 1)[0]
        # If the string is still too long, truncate it
        if len(new_string) > 250:
            new_string = new_string[:250]

    # Remove any trailing periods or spaces
    while new_string.endswith('.') or new_string.endswith(',') or new_string.endswith(' '):
        new_string = new_string[:-1]

    # Remove any preceding periods, spaces, or commas
    while new_string.startswith('.') or new_string.startswith(',') or new_string.startswith(' '):
        new_string = new_string[1:]

    return new_string


def sanitize_post(post, title_case):
    """
    Adds is_comment properties to posts and is_self property to comments, and finds valid urls in non-self posts
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


@app.route('/signin', methods=["GET", "POST"])
def sign_in():
    """
    Attempts to sign into Reddit taking the first two CLAs
    :return: reddit object if successful, else None
    """

    username = request.form.get("username")
    password = request.form.get("password")

    # Don't bother trying to sign in if username or password are blank
    #  (praw has a stack overflow without this check!)
    if username == "" or password == "":
        return render_template('apology.html')

    # Try to sign in
    try:
        reddit = praw.Reddit(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             user_agent='Saved Sorter',
                             username=username,
                             password=password)
        return reddit
    except prawcore.exceptions.OAuthException:
        return render_template('apology.html')


if __name__ == "__main__":
    main()
