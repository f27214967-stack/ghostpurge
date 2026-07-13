from pathlib import Path
import argparse
import signal
import logging
import time
import os
import glob
from typing import List, Any, Dict, Tuple
from ghostpurge.config import Config
from ghostpurge.utils import setup_logging

# Registries
from ghostpurge.cleaners.registry import CleanerRegistry
from ghostpurge.watchers.base import WatcherRegistry

# Cleaners
import ghostpurge.cleaners.clean_configs  # noqa: F401
import ghostpurge.cleaners.clean_cache  # noqa: F401
import ghostpurge.cleaners.clean_logs  # noqa: F401
import ghostpurge.cleaners.clean_orphans  # noqa: F401
import ghostpurge.cleaners.clean_systemd  # noqa: F401

# Watchers
import ghostpurge.watchers.watcher_dpkg  # noqa: F401
import ghostpurge.watchers.watcher_flatpak  # noqa: F401
import ghostpurge.watchers.watcher_snap  # noqa: F401
import ghostpurge.watchers.watcher_appimage  # noqa: F401
import ghostpurge.watchers.watcher_steam  # noqa: F401
import ghostpurge.watchers.watcher_pip  # noqa: F401
import ghostpurge.watchers.watcher_npm  # noqa: F401

logger = logging.getLogger("ghostpurge.main")

class GhostPurgeDaemon:
    def __init__(self, config_path: str):
        self.config = Config(config_path)
        setup_logging(
            self.config.get("daemon.log_file", "/var/log/ghostpurge.log"),
            self.config.get("daemon.log_level", "INFO")
        )
        self.running = True
        
        self.cleaners = [cls(self.config) for cls in CleanerRegistry.get_cleaners()]
        self.watchers = [cls(self.config, self.handle_uninstall) for cls in WatcherRegistry.get_watchers()]
        
        # File d'attente (pkg, source) -> timestamp
        self.pending_cleans: Dict[Tuple[str, str], float] = {}

    def handle_uninstall(self, package_name: str, source: str) -> None:
        """Queues the event for verification (Debounce)."""
        whitelist: List[str] = self.config.get("whitelist", [])
        if package_name in whitelist:
            logger.info(f"[{source}] Package {package_name} ignored (whitelist).")
            return
            
        # On enregistre l'heure de la détection
        self.pending_cleans[(package_name, source)] = time.time()
        logger.info(f"[{source}] Event intercepted for {package_name}. Anti-update verification (5s)...")

    def _is_package_reinstalled(self, package_name: str, source: str) -> bool:
        """Checks if the package has reappeared on disk."""
        if source == "pip":
            pip_dir = self.config.get("paths.pip_dir", "")
            # Checks if info folder still exists (sign of a completed update)
            pattern1 = os.path.join(pip_dir, f"{package_name}-*.dist-info")
            pattern2 = os.path.join(pip_dir, f"{package_name}-*.egg-info")
            if glob.glob(pattern1) or glob.glob(pattern2):
                return True
        elif source == "npm":
            npm_dir = self.config.get("paths.npm_dir", "")
            if Path(os.path.join(npm_dir, package_name)).exists():
                return True
        return False

    def _process_pending_cleans(self) -> None:
        now = time.time()
        to_clean = []
        for key, ts in list(self.pending_cleans.items()):
            # If 5 seconds have elapsed
            if now - ts >= 5:
                to_clean.append(key)
                del self.pending_cleans[key]
                
        for pkg, src in to_clean:
            if self._is_package_reinstalled(pkg, src):
                logger.info(f"[{src}] CANCELLED: Folder {pkg} reappeared (update confirmed).")
            else:
                self._execute_clean(pkg, src)

    def _execute_clean(self, package_name: str, source: str) -> None:
        logger.info(f"[{source}] Starting cleanup for: {package_name}")
        for cleaner in self.cleaners:
            try:
                cleaner.clean(package_name, source)
            except Exception as e:
                logger.error(f"Error in {cleaner.__class__.__name__}: {e}")
        logger.info(f"[{source}] Finished cleanup for: {package_name}")

    def stop(self, signum: int, frame: Any) -> None:
        logger.info("GhostPurge daemon stop requested...")
        self.running = False

    def run(self) -> None:
        logger.info("Starting GhostPurge (with Anti-Update protection)...")
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        
        for w in self.watchers:
            w.start()
            
        
        try:
            while self.running:
                for w in self.watchers:
                    # Timeout court pour que la boucle tourne régulièrement
                    w.check_events(timeout=1)
                
                # Vérifie la file d'attente à chaque cycle
                self._process_pending_cleans()
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}")
        finally:
            logger.info("GhostPurge daemon stopped gracefully.")

def main() -> None:
    parser = argparse.ArgumentParser(description="GhostPurge Daemon")
    parser.add_argument("--config", default="/etc/ghostpurge/config.yaml", help="Config file")
    args = parser.parse_args()
    
    daemon = GhostPurgeDaemon(args.config)
    daemon.run()

if __name__ == "__main__":
    main()
