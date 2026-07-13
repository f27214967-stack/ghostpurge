import yaml
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_path: str = "/etc/ghostpurge/config.yaml"):
        self.config_path = Path(config_path)
        self.settings: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Charge le fichier YAML de configuration."""
        if not self.config_path.exists():
            logger.warning(f"File not found: {self.config_path}. Utilisation des valeurs par défaut.")
            self._set_defaults()
            return
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.settings = yaml.safe_load(f) or {}
            logger.info(f"Configuration chargée depuis {self.config_path}")
        except Exception as e:
            logger.error(f"Error reading {self.config_path}: {e}")
            self._set_defaults()

    def _set_defaults(self) -> None:
        self.settings = {
            "mode": "aggressive",
            "whitelist": [],
            "blacklist": [],
            "paths": {
                "log_dir": "/var/log",
                "cache_dir": "/var/cache",
                "config_dir": "/etc",
                "lib_dir": "/var/lib"
            },
            "daemon": {
                "sleep_interval": 5,
                "log_file": "/var/log/ghostpurge.log",
                "log_level": "INFO"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        val = self.settings
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val
