from typing import Set

import httpx


# TODO: this could just work for any filetype, not just images
#  Maybe rename to single_file_parser?
async def single_image_parser(url: str, client: httpx.AsyncClient) -> Set[str]:
    """
    :param response: A web page that has been recognized by this parser
    :returns: A list of all scrapeable urls found in the given webpage
    """
    response = await client.get(url)
    if response.status_code == 200 and get_response_file_extension(response) in [
        ".webp",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
    ]:
        return {response.url}
    return set()


def get_response_file_extension(response: httpx.Response) -> str:
    """
    Gets the extension of the content in the specified response
    :param r: valid request object
    :return: the filetype of the content stored in that request, in lowercase
    """
    return "." + response.headers["Content-type"].split("/")[1].lower()
