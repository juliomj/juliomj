from cachetools import TTLCache


class QueryCache:
    def __init__(self, ttl_seconds: int, maxsize: int = 2048) -> None:
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)

    def get(self, key: str):
        return self._cache.get(key)

    def set(self, key: str, value) -> None:
        self._cache[key] = value
