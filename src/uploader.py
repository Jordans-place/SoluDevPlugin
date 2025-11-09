import requests
import json
from pathlib import Path
from src.common.logger import CustomLogger

logger = CustomLogger("UPLOADER", "logs/soludev_plugin.log")


class AnecdotesUploader:
    BASE_URL = "https://gateway.anecdotes.ai/evidence/v1/evidence"

    def __init__(self, token: str, service_id: str = "SoluDev"):
        self.service_id = service_id
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
        self.evidence_ids_file = Path("./out/evidence_ids.json")
        self._ensure_store()

    def _ensure_store(self):
        self.evidence_ids_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.evidence_ids_file.exists():
            self.evidence_ids_file.write_text(json.dumps({}, indent=2))

    def _load_evidence_ids(self) -> dict:
        return json.loads(self.evidence_ids_file.read_text())

    def _save_evidence_id(self, name: str, evidence_id: str):
        data = self._load_evidence_ids()
        data[name] = evidence_id
        self.evidence_ids_file.write_text(json.dumps(data, indent=2))

    def _create_collection(self, evidence_name: str, empty_state: str):
        files = {
            "service_id": (None, self.service_id),
            "evidence_name": (None, evidence_name),
            "evidence_help": (None, f"Auto‑collected {evidence_name} from SoluDev."),
            "empty_state": (None, empty_state),
            "is_uar": (None, "false"),
            "is_sot": (None, "false"),
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
        }

        response = requests.post(
            f"{self.BASE_URL}/create",
            headers=headers,
            files=files,
            timeout=10
        )

        if not response.ok:
            logger.error("Failed to create evidence collection",
                         extra={"status": response.status_code, "msg": response.text})
            raise Exception(f"create failed: {response.text}")

        evidence_id = response.json().get("evidence_id")
        logger.info(f"Created evidence collection: {evidence_name}", evidence_id=evidence_id)
        return evidence_id

    def _get_or_create_evidence_id(self, name: str, empty_state: str) -> str:
        store = self._load_evidence_ids()
        if name in store:
            return store[name]

        evidence_id = self._create_collection(name, empty_state)
        self._save_evidence_id(name, evidence_id)
        return evidence_id

    def upload_file(self, evidence_name: str, file_path: str):
        evidence_id = self._get_or_create_evidence_id(
            name=evidence_name,
            empty_state=f"No data found in {evidence_name}."
        )

        files = {"evidence_file": open(file_path, "rb")}

        response = requests.post(f"{self.BASE_URL}/{evidence_id}/attach", headers=self.headers, files=files, timeout=20)

        if not response.ok:
            logger.error("Upload failed", extra={"status": response.status_code, "msg": response.text})
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")

        logger.info("Upload successful", evidence=evidence_name, evidence_id=evidence_id)
