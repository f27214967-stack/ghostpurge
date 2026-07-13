from typing import List, Type
from ghostpurge.cleaners.base import BaseCleaner

class CleanerRegistry:
    _cleaners: List[Type[BaseCleaner]] = []

    @classmethod
    def register(cls, cleaner_class: Type[BaseCleaner]) -> Type[BaseCleaner]:
        if cleaner_class not in cls._cleaners:
            cls._cleaners.append(cleaner_class)
        return cleaner_class

    @classmethod
    def get_cleaners(cls) -> List[Type[BaseCleaner]]:
        return cls._cleaners
