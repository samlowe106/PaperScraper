def retitle(s: str, title: bool = False) -> str:
    """
    Strips certain punctuation from the start and end of the given string,
    and optionally titlecases it
    :param s: the string to be improved
    :param title: True if the string should be in title case
    :return: a string without certain punctuation at the start or end
    """

    for punctuation in [".", " ", ","]:
        s = trim_string(s, punctuation)

    if title:
        s = title_case(s)

    return s


def trim_string(s1: str, s2: str) -> str:
    """
    Removes any preceding or trailing instances of s2 from s1
    :param s1: the string from which preceding or trailing instances of s2 will be removed
    :param s2: the string that will be removed from the start and end of s1
    :return: s1 without any instances of s2 at either the start or end
    """
    if s2: # ensure termination
        while s1.startswith(s2):
            s1 = s1.lstrip(s2)

        while s1.endswith(s2):
            s1 = s1.rstrip(s2)

    return s1


def shorten(s: str, max_length: int = 250) -> str:
    """
    Shortens s to be shorter than the specified maximum length, truncating at a
    word if possible. Appends an ellipsis if possible.
    :param s: string to be shortened
    :param max_length: the maximum character length that s can be (defaults to 250)
    :return: s
    :raises IndexError: if max_length is less than 0
    """
    if len(s) <= max_length:
        return s

    while len(s := s.rsplit(' ', 1)[0]) + 3 > max_length and ' ' in s:
        # Second condition ensures that there's more than one word, and that the loop terminates
        pass

    return s + '...'


def title_case(s: str) -> str:
    """
    Capitalizes the first character and all characters immediately after spaces in the given string
    (the string.title() method additionally capitalizes characters after punctuation)
    :param s: the string to be title-cased
    :return: s in title case
    """
    # Using ''.join() is faster than using += to accumulate a string
    # https://google.github.io/styleguide/pyguide.html#310-strings

    return "".join([char.upper() if (i == 0 or s[i - 1] == ' ')
                   else char for i, char in enumerate(s)])
