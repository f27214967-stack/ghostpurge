import logging
import os
import typing
try:
    import winreg
except ImportError:
    winreg = typing.Any # type: ignore

from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry
from ghostpurge.config import Config

logger = logging.getLogger("ghostpurge.cleaners.clean_win_registry")

class CleanWinRegistry(BaseCleaner):
    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def clean(self, package_name: str, source: str) -> None:
        if os.name != 'nt' or not winreg:
            return
            
        keys_to_check = [
            (winreg.HKEY_CURRENT_USER, rf"Software\{package_name}"), # type: ignore[attr-defined, unused-ignore]
            (winreg.HKEY_LOCAL_MACHINE, rf"Software\{package_name}"), # type: ignore[attr-defined, unused-ignore]
            (winreg.HKEY_LOCAL_MACHINE, rf"Software\WOW6432Node\{package_name}") # type: ignore[attr-defined, unused-ignore]
        ]
        for hkey, subkey in keys_to_check:
            try:
                winreg.DeleteKey(hkey, subkey) # type: ignore[attr-defined, unused-ignore]
                logger.info(f"[clean_win_registry] Removed registry key: {subkey}")
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.error(f"[clean_win_registry] Failed to remove registry key {subkey}: {e}")

if os.name == 'nt':
    CleanerRegistry.register(CleanWinRegistry)
