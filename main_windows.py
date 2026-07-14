import sys
import os
import argparse

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load Windows modules so they register themselves

# Load Windows modules so they register themselves
import ghostpurge.windows.watcher_registry # noqa: F401
import ghostpurge.windows.watcher_wmi # noqa: F401
import ghostpurge.windows.watcher_filesystem # noqa: F401
import ghostpurge.windows.cleaner_windows # noqa: F401

from ghostpurge.main import GhostPurgeDaemon
from ghostpurge.windows.windows_service import GhostPurgeService

def handle_service_command(args: argparse.Namespace) -> None:
    svc_args = ["windows_service.py"]
    if args.install:
        svc_args.append("install")
    if args.remove:
        svc_args.append("remove")
    if args.start:
        svc_args.append("start")
    if args.stop:
        svc_args.append("stop")
        
    sys.argv = svc_args
    import win32serviceutil
    win32serviceutil.HandleCommandLine(GhostPurgeService)

def handle_console(args: argparse.Namespace) -> None:
    progdata = os.environ.get('ProgramData', 'C:\\ProgramData')
    config_path = args.config or os.path.join(progdata, 'GhostPurge', 'ghostpurge.yaml')
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            log_p = os.path.join(progdata, 'GhostPurge', 'ghostpurge.log').replace("\\", "\\\\")
            f.write(f"daemon:\n  log_file: {log_p}\n")
    daemon = GhostPurgeDaemon(config_path)
    daemon.run()

def main() -> None:
    parser = argparse.ArgumentParser(description="GhostPurge Windows")
    parser.add_argument("--install", action="store_true", help="Install the Windows Service")
    parser.add_argument("--remove", action="store_true", help="Remove the Windows Service")
    parser.add_argument("--start", action="store_true", help="Start the Windows Service")
    parser.add_argument("--stop", action="store_true", help="Stop the Windows Service")
    parser.add_argument("--console", action="store_true", help="Run in console (debug)")
    parser.add_argument("--config", default=None, help="Path to config file")

    args = parser.parse_args()

    if args.install or args.remove or args.start or args.stop:
        handle_service_command(args)
        return

    if args.console:
        handle_console(args)
        return

    parser.print_help()

if __name__ == "__main__":
    main()
