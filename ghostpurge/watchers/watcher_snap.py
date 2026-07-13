from contextlib import suppress
from pathlib import Path
from typing import Callable
from ghostpurge.config import Config
import logging
from ghostpurge.watchers.base import BaseWatcher, WatcherRegistry
from inotify_simple import INotify, flags

logger = logging.getLogger(__name__)

@WatcherRegistry.register
class SnapWatcher(BaseWatcher):
    def __init__(self, config: Config, callback: Callable[[str, str], None]) -> None:
        super().__init__(config, callback)
        self.watch_dir = self.config.get("paths.snap_dir", "/var/lib/snapd/snaps")
        self.inotify = INotify()
        self.mask = flags.DELETE | flags.MOVED_FROM

    def start(self) -> None:
        if not Path(self.watch_dir).exists():
            return
        try:
            self.inotify.add_watch(self.watch_dir, self.mask)
            logger.info(f"Watching Snap on {self.watch_dir}")
        except Exception as e:
            logger.error(f"Error watching Snap: {e}")

    def check_events(self, timeout: int) -> None:
        with suppress(Exception):
            for event in self.inotify.read(timeout=timeout * 1000):
                pkg = event.name.split('_')[0] if event.name else ""
                if pkg:
                    self.callback(pkg, "snap")
