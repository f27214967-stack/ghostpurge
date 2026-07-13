from contextlib import suppress
from pathlib import Path
from typing import Callable
from ghostpurge.config import Config
import logging
from ghostpurge.watchers.base import BaseWatcher, WatcherRegistry
from inotify_simple import INotify, flags

logger = logging.getLogger(__name__)

@WatcherRegistry.register
class SteamWatcher(BaseWatcher):
    def __init__(self, config: Config, callback: Callable[[str, str], None]) -> None:
        super().__init__(config, callback)
        self.watch_dir = self.config.get("paths.steam_dir", "/home/user/.steam/steam/steamapps/common")
        self.inotify = INotify()
        self.mask = flags.DELETE | flags.MOVED_FROM

    def start(self) -> None:
        if not Path(self.watch_dir).exists():
            return
        try:
            self.inotify.add_watch(self.watch_dir, self.mask)
            logger.info(f"Watching Steam on {self.watch_dir}")
        except Exception as e:
            logger.error(f"Error watching Steam: {e}")

    def check_events(self, timeout: int) -> None:
        with suppress(Exception):
            for event in self.inotify.read(timeout=timeout * 1000):
                if event.name:
                    self.callback(event.name, "steam")
