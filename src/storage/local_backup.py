import json
from pathlib import Path


class LocalBackup:
    def __init__(self, backup_path: Path):
        self.path = backup_path

    def save(self, data: dict) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
        except (IOError, TypeError) as error:
            raise RuntimeError(f"Failed to save backup: {error}") from error

    def load(self) -> dict:
        if not self.path.exists():
            return {}

        try:
            with open(self.path, encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as _error:
            return {}

    def clear(self) -> None:
        if self.path.exists():
            try:
                self.path.unlink()
            except IOError as error:
                raise RuntimeError(f"Failed to clear backup: {error}") from error

