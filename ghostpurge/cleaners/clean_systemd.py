from pathlib import Path
import logging
from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry
from ghostpurge.utils import run_command

logger = logging.getLogger(__name__)

@CleanerRegistry.register
class SystemdCleaner(BaseCleaner):
    def clean(self, package_name: str, source: str) -> None:
        if not self.should_clean(package_name, source, "config"):
            return

        logger.info(f"[{source}] Checking systemd services for {package_name}...")
        
        service_file = f"/etc/systemd/system/{package_name}.service"
        if Path(service_file).exists():
            try:
                Path(service_file).unlink()
                run_command(["systemctl", "daemon-reload"])
                logger.info(f"Service {package_name} supprimé.")
            except Exception as e:
                logger.error(f"Error deleting {service_file}: {e}")
