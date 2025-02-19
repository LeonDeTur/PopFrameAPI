import pickle
from pathlib import Path
from typing import Any

from idustorage import Cacheable


class CacheablePickleObject(Cacheable):
    def __init__(self, to_cache: Any):
        self.object = to_cache

    def to_file(self, path: Path, name: str, ext: str, date: str, *args) -> str:
        filepath = f"{date}_{name}"
        for arg in args:
            filepath += f"_{arg}"
        filepath += ext
        try:
            with open(path / filepath, "wb") as fout:
                pickle.dump(self.object, fout)
        except Exception as error:
            print(error)
        return filepath
