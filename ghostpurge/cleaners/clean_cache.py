from pathlib import Path
import logging
import os
import shutil
from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry

logger = logging.getLogger(__name__)

@CleanerRegistry.register
class CacheCleaner(BaseCleaner):
    def clean(self, package_name: str, source: str) -> None:
        if not self.should_clean(package_name, source, "cache"):
            return

        logger.info(f"[{source}] Cleaning cache for {package_name}...")
        
        paths_to_check = [
            os.path.join(self.config.get("paths.cache_dir", "/var/cache"), package_name),
            os.path.expanduser(f"~/.cache/{package_name}")
        ]

        for target in paths_to_check:
            self._clean_target(target)

    def _clean_target(self, target: str) -> None:
        if Path(target).exists() and Path(target).is_dir():
            try:
                shutil.rmtree(target)
                logger.info(f"Cache folder deleted : {target}")
            except Exception as e:
                logger.error(f"Error deleting {target}: {e}")
