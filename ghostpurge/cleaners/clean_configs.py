from pathlib import Path
import logging
import os
import shutil
from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry
from ghostpurge.utils import run_command

logger = logging.getLogger(__name__)

@CleanerRegistry.register
class ConfigCleaner(BaseCleaner):
    def clean(self, package_name: str, source: str) -> None:
        if not self.should_clean(package_name, source, "config"):
            return

        logger.info(f"[{source}] Checking configs for {package_name}...")
        
        if source == "apt":
            code, stdout, _ = run_command(["dpkg", "-l", package_name])
            if code == 0:
                lines = stdout.strip().split('\n')
                if len(lines) > 5 and lines[5].startswith('rc'):
                    logger.info(f"Purge dpkg pour {package_name}...")
                    run_command(["dpkg", "--purge", package_name])

        # Purge dans ~/.config (commun à platpak, snap, appimage, etc.)
        user_config = os.path.expanduser(f"~/.config/{package_name}")
        if Path(user_config).exists() and Path(user_config).is_dir():
            try:
                shutil.rmtree(user_config)
                logger.info(f"Dossier de config utilisateur supprimé : {user_config}")
            except Exception as e:
                logger.error(f"Erreur suppression config {user_config}: {e}")
