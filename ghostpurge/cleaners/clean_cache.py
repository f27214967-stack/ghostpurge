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
            if os.path.exists(target) and os.path.isdir(target):
                try:
                    shutil.rmtree(target)
                    logger.info(f"Dossier de cache supprimé : {target}")
                except Exception as e:
                    logger.error(f"Erreur suppression {target}: {e}")
