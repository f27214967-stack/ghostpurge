from ghostpurge.config import Config
from ghostpurge.watchers.watcher_dpkg import DpkgWatcher

def test_config_defaults() -> None:
    config = Config("dummy.yaml")
    assert config.get("mode") == "aggressive"
    assert isinstance(config.get("whitelist"), list)

def test_dpkg_watcher() -> None:
    config = Config("dummy.yaml")
    watcher = DpkgWatcher(config, lambda p, s: None)
    assert watcher.watch_file == "/var/log/dpkg.log"
