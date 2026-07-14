import logging
import os
from contextlib import suppress

from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry
from ghostpurge.config import Config

logger = logging.getLogger("ghostpurge.cleaners.clean_win_services")

class CleanWinServices(BaseCleaner):
    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def clean(self, package_name: str, source: str) -> None:
        if os.name != 'nt':
            return
            
        try:
            import wmi
            c = wmi.WMI()
            for service in c.Win32_Service(Name=package_name):
                logger.info(f"[clean_win_services] Stopping and deleting orphaned service: {service.Name}")
                with suppress(Exception):
                    service.StopService()
                service.Delete()
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"[clean_win_services] Error cleaning services: {e}")

if os.name == 'nt':
    CleanerRegistry.register(CleanWinServices)
