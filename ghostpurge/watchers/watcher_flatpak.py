from typing import Callable
from ghostpurge.config import Config
import logging
import os
from ghostpurge.watchers.base import BaseWatcher, WatcherRegistry
from inotify_simple import INotify, flags

logger = logging.getLogger(__name__)

@WatcherRegistry.register
class FlatpakWatcher(BaseWatcher):
    def __init__(self, config: Config, callback: Callable[[str, str], None]) -> None:
        super().__init__(config, callback)
        self.watch_dir = self.config.get("paths.flatpak_dir", "/var/lib/flatpak/app")
        self.inotify = INotify()
        self.mask = flags.DELETE | flags.MOVED_FROM

    def start(self) -> None:
        if not os.path.exists(self.watch_dir):
            return
        try:
            self.inotify.add_watch(self.watch_dir, self.mask)
            logger.info(f"Watching Flatpak on {self.watch_dir}")
        except Exception as e:
            logger.error(f"Erreur watch Flatpak: {e}")

    def check_events(self, timeout: int) -> None:
        try:
            for event in self.inotify.read(timeout=timeout * 1000):
                pkg = event.name
                if pkg:
                    self.callback(pkg, "flatpak")
        except Exception:
            pass
