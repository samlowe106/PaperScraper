from os import listdir, makedirs
from os.path import exists
from PIL import Image


def create_directory(dirpath: str) -> None:
    """
    Creates a directory with the specified name if that directory doesn't already exist
    :param dirpath: name of the directory
    :return: None
    """
    if not exists(dirpath):
        makedirs(dirpath)
    return


def convert_to_png(path: str, filename: str) -> str:
    """
    Converts the given image to a .png
    :param path: path that the image is located in
    :param filename: title of the file to be converted
    :return: filename (with new extension)
    """
    new_extension = ".png"
    current_extension = get_extension(filename)
    with Image.open(path + filename + current_extension) as im:
        rgb_im = im.convert('RGB')
        rgb_im.save(path + filename + new_extension)
    return filename + new_extension


def get_extension(filename: str) -> str:
    """
    Gets the extension of the specified file
    :param filename: name of the file (including the extension)
    :return: the file extension
    """
    sections = filename.split('.')
    count = len(sections)
    return sections[len(sections) - 1]


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
