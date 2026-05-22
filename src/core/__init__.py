import httpx

from .client_bundle import AsyncClientBundle
from .file_manager import DownloadsExtensions, UniqueDirectoryFileManager
from .functional import Predicate, afilter, amap, merge


def get_response_file_extension(response: httpx.Response) -> str:
    """
    Gets the extension of the content in the specified response
    :param r: valid request object
    :return: the filetype of the content stored in that request, in lowercase
    """
    return "." + response.headers["Content-type"].split("/")[1].lower()


__all__ = [
    "AsyncClientBundle",
    "DownloadsExtensions",
    "UniqueDirectoryFileManager",
    "Predicate",
    "afilter",
    "amap",
    "merge",
    "get_response_file_extension",
]
