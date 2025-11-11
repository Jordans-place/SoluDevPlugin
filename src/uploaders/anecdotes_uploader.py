import json
import requests
from http import HTTPStatus
from pathlib import Path

from src.common import utils
from src.common.config import config
from src.common.exceptions import AnecdotesAuthenticationError
from src.common.logger import CustomLogger


ANECDOTES_UPLOADER_BASE_URL: str = config.HTTP.ANECDOTES_UPLOADER_BASE_URL
ANECDOTES_UPLOADER_NAME: str = config.LOGGING.ANECDOTES_UPLOADER_NAME
EVIDENCE_IDS_FILE_NAME: str = config.SERVICE.EVIDENCE_IDS_FILE_NAME
EVIDENCE_IDS_FILE_PATH: Path = utils.get_output_file_path(EVIDENCE_IDS_FILE_NAME)
LOG_FILE_NAME: str = config.LOGGING.COMPONENT_TO_LOG_FILE.get(ANECDOTES_UPLOADER_NAME)
TIMEOUT_SECONDS: int = config.HTTP.TIMEOUT_SECONDS

logger = CustomLogger(ANECDOTES_UPLOADER_NAME, LOG_FILE_NAME)


class AnecdotesUploader:
    def __init__(self, session: requests.Session):
        self.session = session
        self.evidence_ids_file = EVIDENCE_IDS_FILE_PATH
        self.base_url = ANECDOTES_UPLOADER_BASE_URL
        self._initialize_evidence_store()

    def _initialize_evidence_store(self):
        self.evidence_ids_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.evidence_ids_file.exists():
            self.evidence_ids_file.write_text(json.dumps({}, indent=4))

    def _load_evidence_ids(self) -> dict:
        try:
            evidence_ids = json.loads(self.evidence_ids_file.read_text())
            return evidence_ids
        except (json.JSONDecodeError, IOError) as error:
            logger.error(f"Failed to load evidence IDs: {error}")
            return {}

    def _save_evidence_id(self, name: str, evidence_id: str):
        data = self._load_evidence_ids()
        data[name] = evidence_id
        try:
            with open(self.evidence_ids_file, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
        except IOError as error:
            logger.error(f"Failed to save evidence ID: {error}")
            raise

    def _create_collection(self, evidence_name: str, empty_state: str) -> str:
        collection = {
            "service_id": (None, 'SoluDev'),
            "evidence_name": (None, evidence_name),
            "evidence_help": (None, f"Auto-collected {evidence_name} from SoluDev."),
            "empty_state": (None, empty_state),
            "is_uar": (None, "false"),
            "is_sot": (None, "false"),
        }
        response = self.session.post( f"{self.base_url}/create", files=collection, timeout=TIMEOUT_SECONDS)

        if response.status_code != HTTPStatus.CREATED:
            raise RuntimeError(f"create failed: {response.status_code} - {response.text}")

        evidence_id = response.json().get("evidence_id")

        if not evidence_id:
            raise RuntimeError("create failed: missing 'evidence_id' in response")

        return evidence_id

    def _get_or_create_evidence_id(self, evidence_name: str, empty_state: str) -> str:
        evidence_ids = self._load_evidence_ids()

        if evidence_name in evidence_ids:
            return evidence_ids[evidence_name]

        evidence_id = self._create_collection(evidence_name, empty_state)
        self._save_evidence_id(evidence_name, evidence_id)
        return evidence_id

    def upload_file(self, evidence_name: str, file_path: str) -> bool:
        evidence_id: str = self._get_or_create_evidence_id(evidence_name, f"No data found in {evidence_name}")

        try:
            with open(file_path, "rb") as file_handle:
                files = {"evidence_file": (Path(file_path).name, file_handle, "application/json")}
                response = self.session.post(f"{self.base_url}/{evidence_id}/attach",files=files,timeout=TIMEOUT_SECONDS)

            if response.status_code == HTTPStatus.UNAUTHORIZED:
                raise AnecdotesAuthenticationError("401 from Anecdotes")

            if response.status_code != HTTPStatus.CREATED:
                raise RuntimeError(f"attach failed: {response.status_code} - {response.text}")

            return True
        except IOError as error:
            logger.error(f"Failed to read file {file_path}: {error}")
            raise
