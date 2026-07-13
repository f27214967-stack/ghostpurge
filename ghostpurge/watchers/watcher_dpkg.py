from typing import Callable
from ghostpurge.config import Config
import logging
import re
from ghostpurge.watchers.base import BaseWatcher, WatcherRegistry
from inotify_simple import INotify, flags

logger = logging.getLogger(__name__)

@WatcherRegistry.register
class DpkgWatcher(BaseWatcher):
    def __init__(self, config: Config, callback: Callable[[str, str], None]) -> None:
        super().__init__(config, callback)
        self.watch_file = "/var/log/dpkg.log"
        self.inotify = INotify()
        self.mask = flags.MODIFY
        self.remove_pattern = re.compile(r" remove (\S+) ")
        self.recent_removals: set[str] = set()

    def start(self) -> None:
        try:
            self.inotify.add_watch(self.watch_file, self.mask)
            logger.info(f"Watching DPKG on {self.watch_file}")
        except Exception as e:
            logger.error(f"Erreur watch DPKG: {e}")

    def check_events(self, timeout: int) -> None:
        try:
            events = self.inotify.read(timeout=timeout * 1000)
            if events:
                self._check_log()
        except Exception:
            pass
        self.recent_removals.clear()

    def _check_log(self) -> None:
        try:
            with open(self.watch_file, 'r') as f:
                lines = f.readlines()[-10:]
                for line in lines:
                    match = self.remove_pattern.search(line)
                    if match:
                        pkg = match.group(1).split(':')[0]
                        if pkg not in self.recent_removals:
                            self.recent_removals.add(pkg)
                            self.callback(pkg, "apt")
        except Exception:
            pass
