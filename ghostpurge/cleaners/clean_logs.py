from pathlib import Path
import logging
import os
import shutil
import glob
from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry

logger = logging.getLogger(__name__)

@CleanerRegistry.register
class LogsCleaner(BaseCleaner):
    def clean(self, package_name: str, source: str) -> None:
        if not self.should_clean(package_name, source, "logs"):
            return

        logger.info(f"[{source}] Cleaning logs for {package_name}...")
        log_dir = self.config.get("paths.log_dir", "/var/log")
        
        target_dir = os.path.join(log_dir, package_name)
        if Path(target_dir).exists() and Path(target_dir).is_dir():
            try:
                shutil.rmtree(target_dir)
                logger.info(f"Dossier de logs supprimé : {target_dir}")
            except Exception as e:
                logger.error(f"Erreur suppression {target_dir}: {e}")

        pattern = os.path.join(log_dir, f"{package_name}*.log*")
        for filepath in glob.glob(pattern):
            try:
                Path(filepath).unlink()
                logger.info(f"Fichier de log supprimé : {filepath}")
            except Exception as e:
                logger.error(f"Erreur suppression {filepath}: {e}")
