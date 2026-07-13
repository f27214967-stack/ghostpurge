from abc import ABC, abstractmethod
from ghostpurge.config import Config

class BaseCleaner(ABC):
    def __init__(self, config: Config):
        self.config = config

    @abstractmethod
    def clean(self, package_name: str, source: str) -> None:
        pass

    def should_clean(self, package_name: str, source: str, artifact: str) -> bool:
        if not package_name or package_name.strip() == "":
            return False
            
        mode = self.config.get("mode", "aggressive")
        blacklist = self.config.get("blacklist", [])
        
        if package_name in blacklist:
            return True
            
        if mode == "hyper-aggressive":
            return True
            
        if mode == "conservative":
            return artifact in ["config", "cache"]
            
        # mode aggressive (default)
        return True
