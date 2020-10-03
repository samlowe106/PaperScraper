from app.helpers.parsers.imgur import ImgurParser
from app.helpers.parsers.single_image import SingleImageParser
from typing import List
from requests.models import Response


parser_list = [SingleImageParser(), ImgurParser()]

def find_urls(r: Response) -> List[str]:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """
    
    for parser in parser_list:
        if parser.recognizes(r):
            return parser.parse(r)

    return []