import logging
import threading
import os
from typing import Callable

try:
    import wmi
    import pythoncom
except ImportError:
    wmi = None
    pythoncom = None

from ghostpurge.watchers.base import WatcherRegistry, BaseWatcher
from ghostpurge.config import Config

logger = logging.getLogger("ghostpurge.watchers.watcher_win_wmi")

class WindowsWMIWatcher(BaseWatcher):
    """Monitors Windows uninstalls via WMI (Win32_Product and ProcessStopTrace)"""
    
    def __init__(self, config: Config, callback: Callable[[str, str], None]) -> None:
        super().__init__(config, callback)
        self.threads: list[threading.Thread] = []
        self.running = False

    def start(self) -> None:
        if not wmi or not pythoncom:
            return
        self.running = True
        
        # Thread for Win32_Product uninstall events
        t1 = threading.Thread(target=self._watch_win32_product, daemon=True)
        self.threads.append(t1)
        t1.start()
        
        # Thread for Win32_ProcessStopTrace (e.g., msiexec or unins000.exe exiting)
        t2 = threading.Thread(target=self._watch_processes, daemon=True)
        self.threads.append(t2)
        t2.start()
        
        logger.info("[wmi] Windows WMI watchers started.")

    def _watch_win32_product(self) -> None:
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI()
            # Watch for uninstalls
            watcher = c.watch_for(
                notification_type="Deletion",
                wmi_class="Win32_Product",
                delay_secs=2
            )
            while self.running:
                try:
                    product = watcher(timeout_ms=1000)
                    if product:
                        logger.info(f"[wmi] Win32_Product deletion detected: {product.Name}")
                        self.callback(product.Name, "wmi_product")
                except wmi.x_wmi_timed_out:
                    continue
        except Exception as e:
            logger.error(f"[wmi] Win32_Product watcher error: {e}")
        finally:
            pythoncom.CoUninitialize()

    def _watch_processes(self) -> None:
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI()
            watcher = c.Win32_ProcessStopTrace.watch_for()
            while self.running:
                try:
                    process = watcher(timeout_ms=1000)
                    if process:
                        p_name = process.ProcessName.lower()
                        # Detect common uninstaller processes
                        if p_name in ("unins000.exe", "uninstall.exe") or p_name.startswith("unins"):
                            logger.info(f"[wmi] Uninstaller process stopped: {process.ProcessName}")
                            # We might not know the exact app name from the process name,
                            # but we can trigger a scan or pass the process name
                            self.callback(process.ProcessName, "wmi_process")
                except wmi.x_wmi_timed_out:
                    continue
        except Exception as e:
            logger.error(f"[wmi] Win32_ProcessStopTrace watcher error: {e}")
        finally:
            pythoncom.CoUninitialize()

    def check_events(self, timeout: int = 1) -> None:
        pass

    def stop(self) -> None:
        self.running = False

if os.name == 'nt':
    WatcherRegistry.register(WindowsWMIWatcher)
