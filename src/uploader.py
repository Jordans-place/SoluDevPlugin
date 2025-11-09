import requests
import json
from pathlib import Path
from src.common.logger import CustomLogger
from src.common.config import config

ANECDOTES_UPLOADER_NAME: str = config.LOGGING.ANECDOTES_UPLOADER_NAME
LOG_FILE_NAME: str = config.LOGGING.COMPONENT_TO_LOG_FILE.get(ANECDOTES_UPLOADER_NAME)
ANECDOTES_UPLOADER_BASE_URL: str = config.HTTP.ANECDOTES_UPLOADER_BASE_URL
OUT_DIR_PATH: str = config.SERVICE.OUT_DIR_PATH
OUT_DIR = Path(OUT_DIR_PATH)
EVIDENCE_IDS_FILE_NAME: str = config.SERVICE.EVIDENCE_IDS_FILE_NAME
EVIDENCE_IDS_FILE_PATH: Path = OUT_DIR / EVIDENCE_IDS_FILE_NAME



logger = CustomLogger(ANECDOTES_UPLOADER_NAME, LOG_FILE_NAME)


class AnecdotesUploader:
    def __init__(self, session: requests.Session, service_id: str = "SoluDev"):
        self.service_id = service_id
        self._session = session
        self.evidence_ids_file = EVIDENCE_IDS_FILE_PATH
        self._ensure_store()
        self.anecdotes_uploader_base_url = ANECDOTES_UPLOADER_BASE_URL

    def _ensure_store(self):
        self.evidence_ids_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.evidence_ids_file.exists():
            self.evidence_ids_file.write_text(json.dumps({}, indent=4))

    def _load_evidence_ids(self) -> dict:
        return json.loads(self.evidence_ids_file.read_text())

    def _save_evidence_id(self, name: str, evidence_id: str):
        data = self._load_evidence_ids()
        data[name] = evidence_id
        self.evidence_ids_file.write_text(json.dumps(data, indent=4))

    def _create_collection(self, evidence_name: str, empty_state: str):
        files = {
            "service_id": (None, self.service_id),
            "evidence_name": (None, evidence_name),
            "evidence_help": (None, f"Auto-collected {evidence_name} from SoluDev."),
            "empty_state": (None, empty_state),
            "is_uar": (None, "false"),
            "is_sot": (None, "false"),
        }
        resp = self._session.post(f"{self.anecdotes_uploader_base_url}/create", files=files, timeout=20)
        if resp.status_code != 201:
            raise RuntimeError(f"create failed: {resp.status_code} - {resp.text}")
        return resp.json().get("evidence_id")

    def _get_or_create_evidence_id(self, name: str, empty_state: str) -> str:
        store = self._load_evidence_ids()
        if name in store:
            return store[name]

        evidence_id = self._create_collection(name, empty_state)
        self._save_evidence_id(name, evidence_id)
        return evidence_id

    def upload_file(self, evidence_name: str, file_path: str):
        evidence_id = self._get_or_create_evidence_id(
            evidence_name, f"No data found in {evidence_name}."
        )

        with open(file_path, "rb") as fp:
            files = {"evidence_file": (Path(file_path).name, fp, "application/json")}
            resp = self._session.post(f"{self.anecdotes_uploader_base_url}/{evidence_id}/attach", files=files, timeout=30)

        if resp.status_code == 401:
            raise PermissionError("401 from Anecdotes")
        if resp.status_code != 201:
            raise RuntimeError(f"attach failed: {resp.status_code} - {resp.text}")

        return True
