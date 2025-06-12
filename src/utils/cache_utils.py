# -*- coding: utf-8 -*-
import hashlib
import os
import pickle
import time
from datetime import timedelta
from pathlib import Path
from typing import Any, Union

from cachetools import Cache


class FileCache(Cache):
    def __init__(
        self,
        ttl: Union[int, timedelta] = 86400,
        maxsize: int = 128,
    ):
        super().__init__(maxsize)

        if isinstance(ttl, timedelta):
            self.ttl = ttl.total_seconds()
        else:
            self.ttl = ttl

        self.cache_dir = Path(os.getenv("CACHE_DIR", ".cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: Any) -> Path:
        key_hash = hashlib.md5(str(key).encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.pkl"

    def __getitem__(self, key):
        path = self._get_cache_path(key)
        if not path.exists():
            raise KeyError(key)

        if time.time() - path.stat().st_mtime > self.ttl:
            path.unlink(missing_ok=True)
            raise KeyError(key)

        with open(path, "rb") as f:
            return pickle.load(f)

    def __setitem__(self, key, value):
        path = self._get_cache_path(key)
        with open(path, "wb") as f:
            pickle.dump(value, f)

    def __delitem__(self, key):
        path = self._get_cache_path(key)
        if path.exists():
            path.unlink()

    def clear(self):
        for file in self.cache_dir.glob("*.pkl"):
            file.unlink()
