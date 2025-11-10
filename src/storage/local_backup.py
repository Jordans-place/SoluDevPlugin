import json
from json import JSONDecodeError
from pathlib import Path

from src.common.config import config
from src.common.logger import CustomLogger

BACKUP_COMPONENT_NAME: str = config.LOGGING.BACKUP_COMPONENT_NAME
LOG_FILE_NAME: str = config.LOGGING.COMPONENT_TO_LOG_FILE.get(BACKUP_COMPONENT_NAME)

logger = CustomLogger(component=BACKUP_COMPONENT_NAME, log_file=LOG_FILE_NAME)


class LocalBackup:
    def __init__(self, backup_path: Path):
        self.path = backup_path

    def save(self, data: dict):
        logger.info(f"Attempting to save backup to {self.path}")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            logger.info(f"Backup saved successfully to {self.path}")

        except IOError as error:
            logger.error(f"IO error while saving backup to {self.path}: {error}")
            raise RuntimeError(f"Failed to save backup: {error}") from error
        except TypeError as error:
            logger.error(f"Data serialization error while saving backup: {error}")
            raise RuntimeError(f"Failed to save backup: {error}") from error

    def load(self) -> dict:
        logger.info(f"Attempting to load backup from {self.path}")

        if not self.path.exists():
            logger.info(f"Backup file does not exist at {self.path}, returning empty dict")
            return {}
        try:
            with open(self.path, encoding="utf-8") as file:
                data = json.load(file)

            logger.info(f"Backup loaded successfully from {self.path}")
            return data

        except JSONDecodeError as error:
            logger.error(f"JSON decode error while loading backup from {self.path}: {error}")
            return {}
        except IOError as error:
            logger.error(f"IO error while loading backup from {self.path}: {error}")
            return {}

    def clear(self):
        logger.info(f"Attempting to clear backup at {self.path}")

        if not self.path.exists():
            return
        try:
            self.path.unlink()
        except IOError as error:
            logger.error(f"IO error while clearing backup at {self.path}: {error}")
            raise RuntimeError(f"Failed to clear backup: {error}") from error
