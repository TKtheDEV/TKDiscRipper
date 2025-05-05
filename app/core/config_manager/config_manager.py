import yaml
import os
import platform
from pathlib import Path


class ConfigManager:
    def __init__(self, config_path=None):
        self.config_path = Path(config_path) if config_path else self._default_config_path()
        self.config_data = {}
        self._load()

    def _default_config_path(self):
        root = Path.home() if platform.system() != "Windows" else Path(os.environ["USERPROFILE"])
        return root / "TKDR" / "config" / "TKDiscRipper.conf"

    def _load(self):
        if self.config_path.exists():
            with self.config_path.open("r") as f:
                self.config_data = yaml.safe_load(f) or {}

    def reload(self):
        self._load()

    def get(self, path, fallback=None):
        entry = self._resolve_entry(path)
        return entry.get("value", fallback) if entry else fallback

    def get_description(self, path):
        entry = self._resolve_entry(path)
        return entry.get("description") if entry else None

    def get_type(self, path):
        entry = self._resolve_entry(path)
        return entry.get("type") if entry else None

    def get_path(self, path, fallback=None):
        val = self.get(path, fallback)
        return Path(os.path.expanduser(val)).resolve() if val else None

    def set(self, path, value):
        section, key = path.split(".", 1)
        if section in self.config_data and key in self.config_data[section]:
            self.config_data[section][key]["value"] = value
            with self.config_path.open("w") as f:
                yaml.dump(self.config_data, f)
        else:
            raise KeyError(f"Config path '{path}' not found")

    def _resolve_entry(self, path):
        try:
            section, key = path.split(".", 1)
            return self.config_data.get(section, {}).get(key)
        except ValueError:
            return None

    def all(self):
        return self.config_data