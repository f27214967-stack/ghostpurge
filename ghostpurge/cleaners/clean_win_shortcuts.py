import logging
import os
from pathlib import Path

from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry
from ghostpurge.config import Config

logger = logging.getLogger("ghostpurge.cleaners.clean_win_shortcuts")

class CleanWinShortcuts(BaseCleaner):
    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def clean(self, package_name: str, source: str) -> None:
        if os.name != 'nt':
            return
            
        desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        start_menu = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
        
        for path in (desktop, start_menu):
            if not Path(path).exists():
                continue
            self._clean_directory_shortcuts(path, package_name)

    def _clean_directory_shortcuts(self, path: str, package_name: str) -> None:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.lnk') and package_name.lower() in file.lower():
                    lnk_path = Path(os.path.join(root, file))
                    try:
                        lnk_path.unlink()
                        logger.info(f"[clean_win_shortcuts] Removed ghost shortcut: {lnk_path}")
                    except Exception as e:
                        logger.error(f"[clean_win_shortcuts] Failed to remove shortcut {lnk_path}: {e}")

if os.name == 'nt':
    CleanerRegistry.register(CleanWinShortcuts)
