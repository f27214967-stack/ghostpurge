import logging
import os

from ghostpurge.cleaners.base import BaseCleaner
from ghostpurge.cleaners.registry import CleanerRegistry
from ghostpurge.config import Config

logger = logging.getLogger("ghostpurge.cleaners.clean_win_tasks")

class CleanWinTasks(BaseCleaner):
    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def clean(self, package_name: str, source: str) -> None:
        if os.name != 'nt':
            return
            
        try:
            import win32com.client
            scheduler = win32com.client.Dispatch('Schedule.Service')
            scheduler.Connect()
            root_folder = scheduler.GetFolder('\\')
            tasks = root_folder.GetTasks(0)
            for task in tasks:
                if package_name.lower() in task.Name.lower():
                    logger.info(f"[clean_win_tasks] Deleting scheduled task: {task.Name}")
                    root_folder.DeleteTask(task.Name, 0)
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"[clean_win_tasks] Error cleaning scheduled tasks: {e}")

if os.name == 'nt':
    CleanerRegistry.register(CleanWinTasks)
