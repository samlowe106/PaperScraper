from collections.abc import Callable
import os
import shutil
import utils.strings


def create_directory(directory: str) -> None:
    """
    Creates a directory with the specified name if that directory doesn't already exist
    :param directory: name of the directory
    :return: None
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def prevent_collisions(filepath: str, directory: str) -> str:
    """
    Generates a filename based on the specified title that does not conflict with any of the
    filenames in the specified directory
    :param filepath: the current path of the file
    :param directory: the directory to check the file's filename against
    :return: a unique filepath that will not conflict with any of the other files in the directory
    """
    name = os.path.split(os.path.splitext(filepath))[1]
    extension = os.path.splitext(filepath)[1]
    index = 1
    while filepath in os.listdir(directory):
        filename = f"{name} ({index}){extension}"
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


def file_title(directory: str, title: str) -> str:
    """
    Creates a valid filename based on the given title string. The created filename
    will not conflict with any of the existing files in the specified directory
    :param directory: the directory that the filename should be tailored for
    :param title: the string that the created filename should be based on
    :return: a valid filename that will not conflict with any file in the specified directory
    """
    return prevent_collisions(utils.strings.shorten(remove_invalid(title)),
                              directory)


def sandbox(directory: str) -> Callable:
    """
    Executes function in the specified directory (making that directory if it doesn't already exist)
    then deletes that directory
    """
    def wrapper(function: Callable):
        def makedirs(*args, **kwargs):
            create_directory(directory)
            os.chdir(directory)
            result = function(*args, **kwargs)
            os.chdir("..")
            shutil.rmtree(directory)
            return result
        return makedirs
    return wrapper
