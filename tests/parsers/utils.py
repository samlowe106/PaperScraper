import os
import pickle
from datetime import datetime, timedelta
from typing import Dict, Tuple

import httpx

client = httpx.Client()

DAY = timedelta(days=1)

CACHE_PATH = os.path.join("cache")


class Cache:
    """
    Wrapper for httpx client that caches responses using pickle
    By default, cached responses are kept only for 24 hours
    """

    def __init__(self, path=CACHE_PATH, age_limit=DAY):
        self.path = path
        self._cache: Dict[str, Tuple[httpx.Response, datetime.datetime]] = {}
        now = datetime.utcnow()
        with open(CACHE_PATH, "r") as c:
            self._cache = {
                url: tup
                for url, tup in pickle.load(c).items()
                if now - tup[1] < age_limit
            }

    def try_get(self, url: str) -> httpx.Response:
        if url in self._cache.keys():
            return self._cache[url]

        return client.get(url)

    def write(self):
        with open(CACHE_PATH, "w") as c:
            pickle.dump(self._cache, c)
