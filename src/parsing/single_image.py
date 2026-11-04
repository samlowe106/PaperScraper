from ..core import AsyncClientBundle, get_response_file_extension

IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif"}


# TODO: this could just work for any filetype, not just images
#  Maybe rename to single_file_parser?
async def single_image_parser(url: str, clients: AsyncClientBundle) -> list[str]:
    """
    :param url: a url that may point directly at an image (possibly via redirects)
    :returns: the final url of the image, or [] if it isn't one
    """
    assert clients.http is not None, "bundle must be entered (async with) first"
    # stream so only the headers are read; the body is downloaded later, once
    async with clients.http.stream("GET", url) as response:
        if (
            response.status_code == 200
            and get_response_file_extension(response) in IMAGE_EXTENSIONS
        ):
            # response.url is an httpx.URL; the rest of the pipeline expects str
            return [str(response.url)]
    return []
