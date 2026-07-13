from abc import ABC, abstractmethod
from typing import Callable, List, Type
from ghostpurge.config import Config

class BaseWatcher(ABC):
    def __init__(self, config: Config, callback: Callable[[str, str], None]):
        self.config = config
        self.callback = callback

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def check_events(self, timeout: int) -> None:
        pass

class WatcherRegistry:
    _watchers: List[Type[BaseWatcher]] = []

    @classmethod
    def register(cls, watcher_class: Type[BaseWatcher]) -> Type[BaseWatcher]:
        if watcher_class not in cls._watchers:
            cls._watchers.append(watcher_class)
        return watcher_class

    @classmethod
    def get_watchers(cls) -> List[Type[BaseWatcher]]:
        return cls._watchers
