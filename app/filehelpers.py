from os import listdir, makedirs
from os.path import exists, splitext
from PIL import Image
from typing import Tuple
import ntpath


def create_directory(dirpath: str) -> None:
    """
    Creates a directory with the specified name if that directory doesn't already exist
    :param dirpath: name of the directory
    :return: None
    """
    if not exists(dirpath):
        makedirs(dirpath)
    return


def convert_to_png(filepath: str) -> str:
    """
    Converts the given image to a .png
    :param path: path that the image is located in
    :param filename: title of the file to be converted
    :return: filename (with new extension)
    """
    new_ext = ".png"
    root = ntpath.splitext(filepath)[0]
    new_path = root + new_ext
    with Image.open(filepath) as im:
        rgb_im = im.convert('RGB')
        rgb_im.save(new_path)
    return new_path


def get_extension(url: str) -> str:
    """
    Gets the extension from the given filepath or url
    :param url: a direct link to an image
    :return: the directly-linked image's extension
    """
    # split removes query strings from urls
    return ntpath.splitext(url.split('?')[0])


def save_image(image, path: str, title: str, extension: str) -> str:
    """
    Saves the specified image to the specified path with the specified title and file extension
    :param image: the image to be saved
    :param path: the path the image should be saved to
    :param title: the title the image file should have
    :param extension: the file extension
    :return: final filename (with extension)
    """
    # Set up the output path
    create_directory(path)

    # Start a loop (prevents this file from overwriting another with the same name by adding (i) before the extension)
    for i in range(len(listdir(path)) + 1):

        # Insert a number in the filename to prevent conflicts
        if i > 0:
            file_title = "{0} ({1})".format(title, i)
        else:
            file_title = title

        # If no files share the same name, write the file
        if (file_title + extension) not in listdir(path):

            # Write the file
            with open(path + file_title + extension, "wb") as File:
                for chunk in image.iter_content(4096):
                    File.write(chunk)

            # Return the final filename (with extension)
            return file_title + extension
