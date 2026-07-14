import logging
import threading
import os
import ctypes
from typing import Callable, Set

from ghostpurge.watchers.base import WatcherRegistry, BaseWatcher
from ghostpurge.config import Config

logger = logging.getLogger("ghostpurge.windows.watcher_registry")

if os.name == 'nt':
    import ctypes.wintypes
    advapi32 = ctypes.windll.advapi32
    kernel32 = ctypes.windll.kernel32

    # Constants
    HKEY_LOCAL_MACHINE = 0x80000002
    HKEY_CURRENT_USER = 0x80000001
    KEY_READ = 0x20019
    KEY_NOTIFY = 0x0010
    REG_NOTIFY_CHANGE_NAME = 1
    REG_NOTIFY_CHANGE_LAST_SET = 4
    WAIT_OBJECT_0 = 0
    WAIT_TIMEOUT = 258

class WindowsRegistryWatcher(BaseWatcher):
    """Monitors Windows Registry for uninstalls using native ctypes API"""
    
    def __init__(self, config: Config, callback: Callable[[str, str], None]) -> None:
        super().__init__(config, callback)
        self.keys_to_watch: list[tuple[int, str]] = []
        if os.name == 'nt':
            self.keys_to_watch = [
                (HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
                (HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
        self.threads: list[threading.Thread] = []
        self.running = False
        self.stop_event = None

    def start(self) -> None:
        if os.name != 'nt':
            return
            
        self.running = True
        self.stop_event = kernel32.CreateEventW(None, True, False, None)
        
        for hkey, subkey in self.keys_to_watch:
            t = threading.Thread(target=self._watch_key, args=(hkey, subkey), daemon=True)
            self.threads.append(t)
            t.start()
        logger.info("[registry] Windows Registry ctypes watcher started.")

    def _get_subkeys(self, hkey_root: int, subkey_path: str) -> set[str]:
        subkeys: set[str] = set()
        hkey = ctypes.wintypes.HKEY()
        res = advapi32.RegOpenKeyExW(hkey_root, subkey_path, 0, KEY_READ, ctypes.byref(hkey))
        if res != 0:
            return subkeys
            
        index = 0
        buf_len = ctypes.wintypes.DWORD(256)
        name_buf = ctypes.create_unicode_buffer(256)
        
        while True:
            buf_len.value = 256
            ret = advapi32.RegEnumKeyExW(hkey, index, name_buf, ctypes.byref(buf_len), None, None, None, None)
            if ret != 0:
                break
            subkeys.add(name_buf.value)
            index += 1
            
        advapi32.RegCloseKey(hkey)
        return subkeys

    def _watch_key(self, hkey_root: int, subkey_path: str) -> None:
        hkey = ctypes.wintypes.HKEY()
        res = advapi32.RegOpenKeyExW(hkey_root, subkey_path, 0, KEY_NOTIFY | KEY_READ, ctypes.byref(hkey))
        if res != 0:
            logger.error(f"[registry] Failed to open key {subkey_path} (Err: {res})")
            return

        change_event = kernel32.CreateEventW(None, True, False, None)
        events = (ctypes.wintypes.HANDLE * 2)(change_event, self.stop_event)
        
        current_keys = self._get_subkeys(hkey_root, subkey_path)

        while self.running:
            kernel32.ResetEvent(change_event)
            filter_flags = REG_NOTIFY_CHANGE_NAME | REG_NOTIFY_CHANGE_LAST_SET
            ret = advapi32.RegNotifyChangeKeyValue(hkey, True, filter_flags, change_event, True)
            if ret != 0:
                logger.error(f"[registry] RegNotifyChangeKeyValue failed: {ret}")
                break

            wait_res = kernel32.WaitForMultipleObjects(2, events, False, 0xFFFFFFFF)
            
            if wait_res == WAIT_OBJECT_0:
                new_keys = self._get_subkeys(hkey_root, subkey_path)
                removed = current_keys - new_keys
                for r in removed:
                    logger.info(f"[registry] Uninstalled package detected: {r}")
                    self.callback(r, "registry")
                current_keys = new_keys
            elif wait_res == WAIT_OBJECT_0 + 1:
                break
                
        advapi32.RegCloseKey(hkey)
        kernel32.CloseHandle(change_event)

    def check_events(self, timeout: int = 1) -> None:
        pass

    def stop(self) -> None:
        self.running = False
        if os.name == 'nt' and self.stop_event:
            kernel32.SetEvent(self.stop_event)

if os.name == 'nt':
    WatcherRegistry.register(WindowsRegistryWatcher)
