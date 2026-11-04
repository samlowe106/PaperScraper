import mimetypes
import posixpath

import httpx

from .client_bundle import AsyncClientBundle, make_http_client
from .file_manager import UniqueDirectoryFileManager
from .functional import Predicate, afilter, amap, merge
from .host_limiter import HostLimitedTransport, retry_after_seconds


def get_response_file_extension(response: httpx.Response) -> str:
    """
    Gets the extension of the content in the specified response
    :param response: a completed response
    :return: the extension (with its leading dot, e.g. ".jpg") for the response's
    Content-Type, falling back to the url's own extension, or "" if neither helps
    """
    # drop parameters like "; charset=binary" before looking the type up
    mime = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
    # some servers send the nonstandard "image/jpg", which mimetypes doesn't know
    mime = {"image/jpg": "image/jpeg"}.get(mime, mime)
    if extension := mimetypes.guess_extension(mime):
        return extension
    return posixpath.splitext(response.url.path)[1].lower()


__all__ = [
    "AsyncClientBundle",
    "HostLimitedTransport",
    "Predicate",
    "UniqueDirectoryFileManager",
    "afilter",
    "amap",
    "get_response_file_extension",
    "make_http_client",
    "merge",
    "retry_after_seconds",
]
