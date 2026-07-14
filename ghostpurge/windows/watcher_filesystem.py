import logging
import threading
import os
from typing import Callable

try:
    import win32file
    import win32con
except ImportError:
    win32file = None
    win32con = None

from ghostpurge.watchers.base import WatcherRegistry

logger = logging.getLogger("ghostpurge.windows.watcher_filesystem")

class WindowsFilesystemWatcher:
    """Monitors Windows Filesystem for uninstalls"""
    
    def __init__(self, config, callback: Callable[[str, str], None]):
        self.config = config
        self.callback = callback
        self.threads = []
        self.running = False
        self.paths_to_watch = []
        
        if os.name == 'nt':
            prog_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            prog_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
            appdata = os.environ.get('APPDATA', '')
            localappdata = os.environ.get('LOCALAPPDATA', '')
            
            for p in [prog_files, prog_files_x86, appdata, localappdata]:
                if p and os.path.exists(p):
                    self.paths_to_watch.append(p)

    def start(self):
        if not win32file:
            return
        self.running = True
        for path in self.paths_to_watch:
            t = threading.Thread(target=self._watch_path, args=(path,), daemon=True)
            self.threads.append(t)
            t.start()
        logger.info("[fs] Windows Filesystem watchers started.")

    def _watch_path(self, path: str):
        ACTIONS = { # noqa: F841
            1: "Created",
            2: "Deleted",
            3: "Updated",
            4: "Renamed from",
            5: "Renamed to"
        }
        
        FILE_LIST_DIRECTORY = 0x0001
        try:
            hDir = win32file.CreateFile(
                path,
                FILE_LIST_DIRECTORY,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_FLAG_BACKUP_SEMANTICS,
                None
            )
        except Exception as e:
            logger.error(f"[fs] Failed to open handle for {path}: {e}")
            return

        while self.running:
            try:
                results = win32file.ReadDirectoryChangesW(
                    hDir,
                    1024,
                    False, # Don't watch full subtree, too expensive. Just top-level folders.
                    win32con.FILE_NOTIFY_CHANGE_DIR_NAME,
                    None,
                    None
                )
                for action, file in results:
                    if action == 2: # Deleted
                        logger.info(f"[fs] Folder deleted in {path}: {file}")
                        self.callback(file, "filesystem")
            except Exception as e:
                logger.error(f"[fs] Error watching {path}: {e}")
                break

    def check_events(self, timeout: int = 1):
        pass

    def stop(self):
        self.running = False

if os.name == 'nt':
    WatcherRegistry.register(WindowsFilesystemWatcher)
