from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
import os
import requests

from .config import config

OUT_DIR_PATH: str = config.SERVICE.OUT_DIR_PATH
MIN_POOL_CONNECTIONS: int = config.HTTP.MIN_POOL_CONNECTIONS
MAX_POOL_CONNECTIONS: int = config.HTTP.MAX_POOL_CONNECTIONS

load_dotenv()


def get_env_variable(variable_name: str) -> str:
    value = os.getenv(variable_name)
    if not value:
        raise ValueError(f"Environment variable {variable_name} is missing")
    return value

def get_output_file_path(filename: str) -> Path:
    out_dir = Path(OUT_DIR_PATH)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / filename

def build_session(total_retries: int = 5, backoff_factor: float = 0.5) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=MIN_POOL_CONNECTIONS, pool_maxsize=MAX_POOL_CONNECTIONS)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
