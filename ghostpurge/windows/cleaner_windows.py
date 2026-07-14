import logging
import os
import shutil

try:
    import winreg
except ImportError:
    winreg = None

from ghostpurge.cleaners.registry import CleanerRegistry

logger = logging.getLogger("ghostpurge.windows.cleaner_windows")

class WindowsCleaner:
    def __init__(self, config):
        self.config = config

    def clean(self, package_name: str, source: str) -> None:
        if os.name != 'nt':
            return
            
        logger.info(f"Starting Windows cleanup for {package_name}")
        self._clean_folders(package_name)
        self._clean_registry(package_name)
        self._clean_services(package_name)
        self._clean_tasks(package_name)
        self._clean_shortcuts(package_name)

    def _clean_folders(self, package_name: str):
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
            if os.path.exists(p):
                try:
                    shutil.rmtree(p)
                    logger.info(f"[cleaner] Removed orphaned folder: {p}")
                except Exception as e:
                    logger.error(f"[cleaner] Failed to remove {p}: {e}")

    def _clean_registry(self, package_name: str):
        if not winreg:
            return
        keys_to_check = [
            (winreg.HKEY_CURRENT_USER, rf"Software\{package_name}"),
            (winreg.HKEY_LOCAL_MACHINE, rf"Software\{package_name}"),
            (winreg.HKEY_LOCAL_MACHINE, rf"Software\WOW6432Node\{package_name}")
        ]
        for hkey, subkey in keys_to_check:
            try:
                # To delete a key with subkeys, we need to recursively delete it or use SHDeleteKey.
                # Simplified for demonstration.
                winreg.DeleteKey(hkey, subkey)
                logger.info(f"[cleaner] Removed registry key: {subkey}")
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.error(f"[cleaner] Failed to remove registry key {subkey}: {e}")

    def _clean_services(self, package_name: str):
        # Using sc query or wmi to find and delete services matching package_name
        try:
            import wmi
            c = wmi.WMI()
            for service in c.Win32_Service(Name=package_name):
                logger.info(f"[cleaner] Stopping and deleting orphaned service: {service.Name}")
                try:
                    service.StopService()
                except Exception:
                    pass
                service.Delete()
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"[cleaner] Error cleaning services: {e}")

    def _clean_tasks(self, package_name: str):
        try:
            import win32com.client
            scheduler = win32com.client.Dispatch('Schedule.Service')
            scheduler.Connect()
            root_folder = scheduler.GetFolder('\\')
            tasks = root_folder.GetTasks(0)
            for task in tasks:
                if package_name.lower() in task.Name.lower():
                    logger.info(f"[cleaner] Deleting scheduled task: {task.Name}")
                    root_folder.DeleteTask(task.Name, 0)
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"[cleaner] Error cleaning scheduled tasks: {e}")

    def _clean_shortcuts(self, package_name: str):
        desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        start_menu = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
        
        for path in [desktop, start_menu]:
            if not os.path.exists(path):
                continue
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.lnk') and package_name.lower() in file.lower():
                        lnk_path = os.path.join(root, file)
                        try:
                            os.remove(lnk_path)
                            logger.info(f"[cleaner] Removed ghost shortcut: {lnk_path}")
                        except Exception as e:
                            logger.error(f"[cleaner] Failed to remove shortcut {lnk_path}: {e}")

if os.name == 'nt':
    CleanerRegistry.register(WindowsCleaner)
