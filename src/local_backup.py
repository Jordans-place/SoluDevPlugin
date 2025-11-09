import json
from pathlib import Path


class LocalBackup:
    def __init__(self, backup_path: Path):
        self.path = backup_path

    def save(self, data: dict):
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def load(self) -> dict:
        if not self.path.exists():
            return {}

        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

    def clear(self):
        if self.path.exists():
            self.path.unlink()
