# -*- coding: utf-8 -*-
import hashlib
import os
import pickle
import time
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Union

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
        prefix = key.split("__")[0]
        return self.cache_dir / f"{prefix}.pkl"

    def __getitem__(self, key):
        path = self._get_cache_path(key)
        if not path.exists():
            raise KeyError(key)

        if time.time() - path.stat().st_mtime > self.ttl:
            path.unlink(missing_ok=True)
            raise KeyError(key)

        with open(path, "rb") as f:
            obj: Dict[str, Any] = pickle.load(f)

        if "__" in key:
            _code = key.split("__")[1]
            if _code not in obj:
                raise KeyError(key)
            return obj[_code]

        return obj

    def __setitem__(self, key, value):
        path = self._get_cache_path(key)

        if "__" in key:
            cache_data = {}
            if path.exists():
                with open(path, "rb") as f:
                    cache_data = pickle.load(f)

            cache_data[key.split("__")[1]] = value
        else:
            cache_data = value

        with open(path, "wb") as f:
            pickle.dump(cache_data, f)

    def __delitem__(self, key):
        path = self._get_cache_path(key)
        if path.exists():
            path.unlink()

    def clear(self):
        for file in self.cache_dir.glob("*.pkl"):
            file.unlink()
