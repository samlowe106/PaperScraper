import app.strhelpers
import os
from PIL import Image


def create_directory(directory: str) -> None:
    """
    Creates a directory with the specified name if that directory doesn't already exist
    :param directory: name of the directory
    :return: None
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    return


def convert(filepath: str, new_ext: str = ".png") -> str:
    """
    Converts the given image to the specified new extension
    :param path: path that the image is located in
    :param filename: title of the file to be converted
    :return: filename (with new extension)
    """
    new_path = os.path.splitext(filepath)[0] + new_ext
    with Image.open(filepath) as im:
        rgb_im = im.convert('RGB')
        rgb_im.save(new_path)
        # delete old file
        os.remove(filepath)
    return new_path

    
def prevent_collisions(title: str, extension: str, directory: str):
    """
    Generates a filename based on the specified title that does not conflict with any of the
    filenames in the specified directory
    :param title: the desired title of the file
    :param extension: the extension of the file
    :param directory: the directory to check the file's filename against
    :return: a filename that will not have any name conflicts in the specified directory
    """
    filename = title + extension
    index = 1
    while filename in os.listdir(directory):
        filename = "{0} ({1}).{2}".format(title, index, extension)
        index += 1

    return filename


def remove_invalid(s: str) -> str:
    """
    Removes characters that Windows doesn't allow in filenames from the specified string
    :param s: string to remove characters from
    :return: the given string without invalid characters
    """
    s = s.replace('"', "'")
    for invalid_char in ["\\", "/", ":", "*", "?", "<", ">", "|"]:
        s = s.replace(invalid_char, "")
    return s


def file_title(directory: str, title: str, extension: str) -> str:
    """
    """
    title = remove_invalid(title)
    title = app.strhelpers.shorten(title)
    title = prevent_collisions(title, extension, directory)

    return title
