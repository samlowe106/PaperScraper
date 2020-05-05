import ntpath
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


def convert_file(filepath: str, new_ext: str) -> str:
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


def get_file_extension(filepath: str) -> str:
    """
    Gets the file extension from a filepath
    :param filepath: the path to the file
    :return: the specified file's extension
    """
    return os.path.splitext(filepath)[1]


def get_file_title(filepath: str) -> str:
    """
    Gets the title of a file without the extension or root
    :param filepath: the path to the file
    :return: the title of the file
    """
    return os.path.splitext(os.path.basename(filepath))[0]


def prevent_conflicts(title: str, extension: str, directory: str):
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
