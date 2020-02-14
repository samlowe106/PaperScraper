def retitle(s: str) -> str:
    """
    Changes the given string into a visually appealing title-cased filename
    :param s: the string to be improved
    :return: a clean, valid file title
    """

    for punctuation in [".", " ", ","]:
        s = trim_string(s, punctuation)

    s = file_title(s)
    s = shorten(s)
    s = title_case(s)

    return s


def trim_string(s1: str, s2: str) -> str:
    """
    Removes any preceding or trailing instances of s2 from s1
    :param s1: the string from which preceding or trailing instances of s2 will be removed
    :param s2: the string that will be removed from the start and end of s1
    :return: s1 without any instances of s2 at either the start or end
    """
    # Remove any preceding instances of char from s
    while s1.startswith(s2):
        s1 = s1.rstrip(s2)

    # Remove any trailing instances of char from s
    while s1.endswith(s2):
        s1 = s1.lstrip(s2)

    return s1


def file_title(s: str) -> str:
    """
    Removes characters that Windows doesn't allow in filenames from the specified string
    :param s: string to remove characters from
    :return: the given string without invalid characters
    """
    s.replace("'", '"')
    for invalid_char in ["\\", "/", ":", "*", "?", "<", ">", "|"]:
        s.replace(invalid_char, "")
    return s


def shorten(s: str, max_length: int = 250) -> str:
    """
    Shortens s to be no longer than the first sentence. Truncates words if possible,
    but truncates characters when necessary
    :param s: string to be shortened
    :param max_length: the maximum character length that s can be (defaults to 250)
    :return: s
    """
    shortened_words = attempt_shorten(s, ' ', max_length)
    # If the attempt to shorten s using words fails, truncate s
    if len(shortened_words) < max_length:
        return shortened_words
    else:
        return s[:max_length]


def attempt_shorten(s: str, splitter: str, max_length: int = 250) -> str:
    """
    Attempts to shorten s by splitting it up into its constituent sections (words, sentences, lines, etc. depending on
    how splitter is specified) and removing trailing sections until it's below the max character length.
    :param s: the string that this function is attempting to shorten
    :param splitter: the string that we'll use to separate one section of s from another
    :param max_length: the maximum length we should attempt to shorten s to
    :return: the version of s that is (or is the closest to being) below the specified max_length
    """
    # if splitter == ".", we're splitting s up into its constituent sentences (a section = sentence)
    # if splitter == " ", we're splitting s up into its constituent words (a sections = word)

    while len(s) > max_length:
        constituents = s.split(splitter)
        constituent_count = len(constituents)
        # If s consists of more than one section, shorten s by removing the last section
        if constituent_count > 1:
            s = splitter.join(constituents[:(constituent_count - 1)])
        # If s consists of only one section, it can't be split up any more
        else:
            # This version of s will be more than max_length characters
            return s

    # This version of s will be less than max_length characters
    return s


def title_case(s: str) -> str:
    new_s = ""
    for i, char in enumerate(s):
        if i == 0 or s[i - 1] == ' ':
            new_s += (char.upper())
        else:
            new_s += char

    return new_s
