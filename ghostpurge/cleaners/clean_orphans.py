import logging
from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry
import subprocess

logger = logging.getLogger(__name__)

@CleanerRegistry.register
class OrphanCleaner(BaseCleaner):
    def clean(self, package_name: str, source: str) -> None:
        if not self.should_clean(package_name, source, "orphans"):
            return

        logger.info(f"[{source}] Searching for orphans after {package_name}...")
        
        if source == "apt":
            env = {"DEBIAN_FRONTEND": "noninteractive"}
            cmd = ["apt-get", "autoremove", "-y", "--purge"]
            try:
                subprocess.run(cmd, capture_output=True, text=True, env=env)
                logger.info("APT orphans cleanup finished.")
            except Exception as e:
                logger.error(f"Erreur autoremove: {e}")
                
        elif source == "flatpak":
            try:
                subprocess.run(["flatpak", "uninstall", "--unused", "-y"], capture_output=True)
                logger.info("Nettoyage Flatpak orphelins terminé.")
            except Exception as e:
                logger.error(f"Erreur flatpak unused: {e}")
