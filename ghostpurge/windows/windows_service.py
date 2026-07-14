import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import os
from pathlib import Path
import sys
import logging

# Add project root to sys.path if run directly
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ghostpurge.main import GhostPurgeDaemon # noqa: E402

class GhostPurgeService(win32serviceutil.ServiceFramework): # type: ignore
    _svc_name_ = "GhostPurge"
    _svc_display_name_ = "GhostPurge Daemon"
    _svc_description_ = "Automated uninstallation leftover cleaner."

    def __init__(self, args: list[str]) -> None:
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.daemon: GhostPurgeDaemon | None = None

    def SvcStop(self) -> None:
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.daemon:
            self.daemon.running = False

    def SvcDoRun(self) -> None:
        # Setup logging specific to the Windows service
        progdata = os.environ.get('ProgramData', 'C:\\ProgramData')
        log_dir = Path(progdata) / 'GhostPurge'
        if not log_dir.exists():
            log_dir.mkdir(parents=True)
        
        log_file = str(log_dir / 'ghostpurge.log')
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger("ghostpurge.windows.service")
        logger.info("GhostPurgeService starting...")

        try:
            config_path = Path(log_dir) / "ghostpurge.yaml"
            if not config_path.exists():
                # Write an empty config if it doesn't exist
                config_path.write_text("daemon:\n  log_file: " + log_file.replace("\\", "\\\\") + "\n")
            
            self.daemon = GhostPurgeDaemon(str(config_path))
            
            # Since the daemon uses a blocking loop, we can run it in a thread 
            # or just call it if it checks self.running properly.
            import threading
            t = threading.Thread(target=self.daemon.run, daemon=True)
            t.start()
            
            # Wait for stop event
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            logger.info("GhostPurgeService stopped.")
            
        except Exception as e:
            logger.error(f"GhostPurgeService crashed: {e}")
            sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(GhostPurgeService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(GhostPurgeService)
