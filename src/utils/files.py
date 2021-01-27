import utils.strings
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


def convert(filepath: str, new_ext: str = ".png") -> str:
    """
    Converts the given image to the specified new extension
    :param path: path that the image is located in
    :param filename: title of the file to be converted
    :return: filename (with new extension)
    """
    new_path = os.path.splitext(filepath)[0] + new_ext
    with Image.open(filepath) as im:
        im.convert('RGB').save(new_path)
    # delete old file
    os.remove(filepath)
    return new_path

    
def prevent_collisions(title: str, extension: str, directory: str) -> str:
    """
    Generates a filename based on the specified title that does not conflict with any of the
    filenames in the specified directory
    :param title: the desired title of the file
    :param extension: the extension of the file
    :param directory: the directory to check the file's filename against
    :return: a unique filepath that will not conflict with any of the other files in the directory
    """
    filename = title + extension
    index = 1
    while filename in os.listdir(directory):
        filename = "{0} ({1}){2}".format(title, index, extension)
        index += 1

    return os.path.join(directory, filename)


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
    Creates a valid filename based on the given title string. The created filename will not conflict with
    any of the existing files in the specified directory
    :param directory: the directory that the filename should be tailored for
    :param title: the string that the created filename should be based on
    :param extension: the extension of the file
    :return: a valid filename that will not conflict with any file in the specified directory
    """
    return prevent_collisions(utils.strings.shorten(remove_invalid(title)),
                              extension,
                              directory)
