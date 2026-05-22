from typing import Set

from ..core import AsyncClientBundle, get_response_file_extension


# TODO: this could just work for any filetype, not just images
#  Maybe rename to single_file_parser?
async def single_image_parser(url: str, clients: AsyncClientBundle) -> Set[str]:
    """
    :param response: A web page that has been recognized by this parser
    :returns: A list of all scrapeable urls found in the given webpage
    """
    response = await clients.http.get(url)  # we do this to follow redirects
    if response.status_code == 200 and get_response_file_extension(response) in [
        ".webp",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
    ]:
        return {response.url}
    return set()
