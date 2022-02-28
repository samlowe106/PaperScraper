def retitle(string: str, title: bool = False) -> str:
    """
    Strips certain punctuation from the start and end of the given string,
    and optionally titlecases it
    :param s: the string to be improved
    :param title: True if the string should be in title case
    :return: a string without certain punctuation at the start or end
    """

    for punctuation in [".", " ", ","]:
        string = trim_string(string, punctuation)

    return title_case(string) if title else string


def trim_string(string1: str, string2: str) -> str:
    """
    Removes any preceding or trailing instances of s2 from s1
    :param s1: the string from which preceding or trailing instances of s2 will be removed
    :param s2: the string that will be removed from the start and end of s1
    :return: s1 without any instances of s2 at either the start or end
    """
    if string2: # loops won't terminate if string2 is empty
        while string1.startswith(string2):
            string1 = string1.lstrip(string2)

        while string1.endswith(string2):
            string1 = string1.rstrip(string2)

    return string1


def shorten(string: str, max_length: int = 250) -> str:
    """
    Shortens s to be shorter than the specified maximum length, truncating at a
    word if possible. Appends an ellipsis if possible.
    :param s: string to be shortened
    :param max_length: the maximum character length that s can be (defaults to 250)
    :return: s
    :raises IndexError: if max_length is less than 0
    """
    if len(string) <= max_length:
        return string

    #TODO: refactor, shouldn't have mutation in while condition
    while len(string := string.rsplit(' ', 1)[0]) + 3 > max_length and ' ' in string:
        # Second condition ensures that there's more than one word, and that the loop terminates
        pass

    # truncating at a word failed, just truncate at a character
    if len(string) > max_length:
        string = string[:(max_length - 3)]

    return string + '...'


def title_case(string: str) -> str:
    """
    Capitalizes the first character and all characters immediately after spaces in the given string
    (the string.title() method additionally capitalizes characters after punctuation)
    :param s: the string to be title-cased
    :return: s in title case
    """
    return "".join([char.upper() if (i == 0 or string[i - 1] == ' ')
                   else char for i, char in enumerate(string)])


def remove_invalid(string: str) -> str:
    """
    Removes characters that Windows doesn't allow in filenames from the specified string
    :param s: string to remove characters from
    :return: the given string without invalid characters
    """
    string = string.replace('"', "'")
    for invalid_char in ["\\", "/", ":", "*", "?", "<", ">", "|"]:
        string = string.replace(invalid_char, "")
    return string


def file_title(title: str) -> str:
    """
    Creates a valid, aesthetically pleasing filename based on the given title string
    :param title: the string that the created filename should be based on
    :return: a valid filename
    """
    return shorten(retitle(remove_invalid(title)))
