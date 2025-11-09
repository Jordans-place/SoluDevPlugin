import logging
import os
from typing import Any


class ComponentFormatter(logging.Formatter):
    def __init__(self, component: str):
        super().__init__(fmt='%(asctime)s - ' + component + ' - %(name)s - %(levelname)s - %(message)s')


class CustomLogger(logging.Logger):
    def __init__(self, component: str, log_file: str, name: str = 'logger', level: int = logging.INFO):
        super().__init__(name, level)

        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', log_file))
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(level)

        formatter = ComponentFormatter(component)
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        self.addHandler(console_handler)
        self.addHandler(file_handler)

    def log_with_metadata(self, level: int, message: str, **metadata: Any):
        if metadata:
            message += f' | Metadata: {metadata}'
        self.log(level, message)

    def debug(self, message: str, **metadata: Any):
        self.log_with_metadata(logging.DEBUG, message, **metadata)

    def info(self, message: str, **metadata: Any):
        self.log_with_metadata(logging.INFO, message, **metadata)

    def warning(self, message: str, **metadata: Any):
        self.log_with_metadata(logging.WARNING, message, **metadata)

    def error(self, message: str, **metadata: Any):
        self.log_with_metadata(logging.ERROR, message, **metadata)
