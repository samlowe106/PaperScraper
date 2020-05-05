import app.strhelpers
import app.urlhelpers
import json
from praw.models import Submission
from typing import Dict, List, Tuple

# Represents a tuple in the form (URL (str), whether the URL was correctly downloaded (bool))
URLTuple = Tuple[str, bool]


def is_skippable(post: Submission) -> bool:
    """
    Determines if a given reddit post can be skipped or not
    :param post: a reddit post object
    :return: True if the given post is a comment, selfpost, or links to another reddit post, else False
    """
    return (not hasattr(post, 'title')) or post.is_self or "https://reddit.com/" in post.url


def sanitize_post(post: Submission, titlecase: bool = False) -> Submission:
    """
    Fixes post's title and finds post's urls
    :param post: a post object
    :return: the same post with additional new_title and recognized_urls fields
    """
    post.new_title = strhelpers.retitle(post.title)
    if titlecase:
        post.new_title = strhelpers.title_case(post.new_title)
    
    # recognized_urls is a List[URLTuple] which lists all the urls associated with the post and whether
    #  that url was downloaded or not
    post.recognized_urls = []
    for url in urlhelpers.find_urls(post.url):
        post.recognized_urls.append(url, False) # False because no posts have been downloaded yet
    
    return post


def is_parsed(url_tuples: List[URLTuple]) -> bool:
    """
    Determines if every url in the list was parsed correctly
    :param url_tuples: list of tuples
    :return: True if the second element of each tuple in the list is True, else False
    """
    return count_parsed(url_tuples) == len(url_tuples)


def count_parsed(tup_list: List[URLTuple]) -> int:
    """
    Counts the number of urls that were parsed
    :param tup_list: a list of url tuples
    :return: number of tuples in the list who were correctly parsed
    """
    count = 0
    for _, parsed in tup_list:
        if parsed:
            count += 1
    return count


def log_post(post: Submission, file: str) -> None:
    """
    Writes the given post's title and url to the specified file
    :param post: reddit post object
    :param file: log file path
    :return: None
    """

    post_dict = {
        "title"           : post.title,
        "id"              : post.id,
        "url"             : post.url,
        "recognized_urls" : post.recognized_urls
    }

    with open(file, "a", encoding="utf-8") as logfile:
        json.dump(post_dict, logfile)

    return


def print_post(index: int, post: Submission) -> None:
    """
    Prints out information about the specified post
    :param index: the index number of the post
    :param post: Reddit post to be printed
    :return: None
    """
    print("\n{0}. {1}".format(index, post.old_title))
    print("   r/" + str(post.subreddit))
    print("   " + post.url)
    print("   Saved {0} / {1} image(s).".format(count_parsed(post.recognized_urls), len(post.recognized_urls)))
    return