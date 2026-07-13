from typing import Callable
from ghostpurge.config import Config
import logging
import os
from ghostpurge.watchers.base import BaseWatcher, WatcherRegistry
from inotify_simple import INotify, flags

logger = logging.getLogger(__name__)

@WatcherRegistry.register
class PipWatcher(BaseWatcher):
    def __init__(self, config: Config, callback: Callable[[str, str], None]) -> None:
        super().__init__(config, callback)
        self.watch_dir = self.config.get("paths.pip_dir", "/home/user/.local/lib/python3.11/site-packages")
        self.inotify = INotify()
        self.mask = flags.DELETE | flags.MOVED_FROM

    def start(self) -> None:
        if not os.path.exists(self.watch_dir):
            return
        try:
            self.inotify.add_watch(self.watch_dir, self.mask)
            logger.info(f"Watching Pip on {self.watch_dir}")
        except Exception as e:
            logger.error(f"Erreur watch Pip: {e}")

    def check_events(self, timeout: int) -> None:
        try:
            for event in self.inotify.read(timeout=timeout * 1000):
                if event.name and event.name.endswith(".dist-info"):
                    pkg = event.name.split('-')[0]
                    self.callback(pkg, "pip")
        except Exception:
            pass
