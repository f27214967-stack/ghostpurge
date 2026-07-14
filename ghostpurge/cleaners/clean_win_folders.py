import logging
import os
from pathlib import Path
import shutil
from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry
from ghostpurge.config import Config

logger = logging.getLogger("ghostpurge.cleaners.clean_win_folders")

class CleanWinFolders(BaseCleaner):
    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def clean(self, package_name: str, source: str) -> None:
        if os.name != 'nt':
            return
        
        paths_to_check = []
        appdata = os.environ.get('APPDATA', '')
        localappdata = os.environ.get('LOCALAPPDATA', '')
        progdata = os.environ.get('ProgramData', '')
        
        if appdata:
            paths_to_check.append(os.path.join(appdata, package_name))
        if localappdata:
            paths_to_check.append(os.path.join(localappdata, package_name))
        if progdata:
            paths_to_check.append(os.path.join(progdata, package_name))
        
        for p in paths_to_check:
            if Path(p).exists():
                try:
                    shutil.rmtree(p)
                    logger.info(f"[clean_win_folders] Removed orphaned folder: {p}")
                except Exception as e:
                    logger.error(f"[clean_win_folders] Failed to remove {p}: {e}")

if os.name == 'nt':
    CleanerRegistry.register(CleanWinFolders)
