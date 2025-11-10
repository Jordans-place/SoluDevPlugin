import json
from pathlib import Path
from time import sleep

from src.auth.anecdotes_auth import AnecdotesAuth
from src.clients.soludev_client import SoluDevClient
from src.common import utils
from src.common.config import config
from src.common.logger import CustomLogger
from src.storage.local_backup import LocalBackup
from src.uploaders.anecdotes_uploader import AnecdotesAuthenticationError, AnecdotesUploader

BACKUP_FILE_NAME: str = config.SERVICE.BACKUP_FILE_NAME
EVIDENCE_NAME_PREFIX: str = config.SERVICE.EVIDENCE_NAME_PREFIX
MAIN_COMPONENT_NAME: str = config.LOGGING.MAIN_COMPONENT_NAME
LOG_FILE_NAME: str = config.LOGGING.COMPONENT_TO_LOG_FILE.get(MAIN_COMPONENT_NAME)
RETRY_DELAY_SECONDS: int = config.SERVICE.RETRY_DELAY_SECONDS
ROLES_FILE_NAME: str = config.SERVICE.ROLES_FILE_NAME
TIMEOUT_SECONDS: int = config.HTTP.TIMEOUT_SECONDS
USERS_FILE_NAME: str = config.SERVICE.USERS_FILE_NAME

SOLUDEV_BASE_URL: str = utils.get_env_variable("SOLUDEV_BASE_URL")
ANECDOTES_API_KEY = utils.get_env_variable("ANECDOTES_API_KEY")
SOLUDEV_API_KEY = utils.get_env_variable('SOLUDEV_API_KEY')
SOLUDEV_USERNAME = utils.get_env_variable('SOLUDEV_USERNAME')
BACKUP_FILE_PATH = utils.get_output_file_path(BACKUP_FILE_NAME)
ROLES_FILE_PATH = utils.get_output_file_path(ROLES_FILE_NAME)
USERS_FILE_PATH = utils.get_output_file_path(USERS_FILE_NAME)

logger = CustomLogger(MAIN_COMPONENT_NAME, LOG_FILE_NAME)


def _get_evidence_name(file_stem: str) -> str:
    return f"{EVIDENCE_NAME_PREFIX}-{file_stem.capitalize()}"


def _save_data_to_file(file_path: Path, data: list[dict]):
    logger.info(f"Saving data to file: {file_path}")

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save data to {file_path}: {e}")
        raise


def upload_with_retry(uploader: AnecdotesUploader, auth: AnecdotesAuth, evidence_name: str, file_path: Path):
    logger.info(f"Uploading file: {file_path} as evidence: {evidence_name}")

    try:
        uploader.upload_file(evidence_name, str(file_path))
        logger.info(f"Successfully uploaded {evidence_name}")
    except AnecdotesAuthenticationError as e:
        logger.warning(f"Authentication failed during upload, refreshing token: {e}")
        auth.refresh_token(uploader._session)
        logger.info(f"Retrying upload for {evidence_name} after token refresh")
        uploader.upload_file(evidence_name, str(file_path))
        logger.info(f"Successfully uploaded {evidence_name} after retry")


def process_and_upload(
        uploader: AnecdotesUploader,
        auth: AnecdotesAuth,
        users: list[dict],
        roles: list[dict],
        backup: LocalBackup):
    _save_data_to_file(USERS_FILE_PATH, users)
    _save_data_to_file(ROLES_FILE_PATH, roles)

    upload_with_retry(uploader, auth, _get_evidence_name(USERS_FILE_PATH.stem), USERS_FILE_PATH)
    upload_with_retry(uploader, auth, _get_evidence_name(ROLES_FILE_PATH.stem), ROLES_FILE_PATH)

    if backup is not None:
        logger.info("Clearing backup after successful upload")
        backup.clear()


def main():
    session = utils.build_session()
    soludev_client = SoluDevClient(SOLUDEV_BASE_URL, SOLUDEV_USERNAME, SOLUDEV_API_KEY, session, TIMEOUT_SECONDS)
    soludev_client.login()

    anecdotes_auth = AnecdotesAuth(api_key=ANECDOTES_API_KEY, session=session)
    anecdotes_auth.apply(session)

    backup = LocalBackup(BACKUP_FILE_PATH)
    uploader = AnecdotesUploader(session=session, service_id="SoluDev")

    success = False
    while not success:
        try:
            backup_data = backup.load()
            if backup_data:
                logger.info("Found backup data, attempting re-upload...")
                users_from_backup = backup_data.get("users", [])
                roles_from_backup = backup_data.get("roles", [])
                process_and_upload(uploader, anecdotes_auth, users_from_backup, roles_from_backup, backup)
                success = True
                continue

            users = [user.model_dump() for user in soludev_client.get_users()]
            roles = [role.model_dump() for role in soludev_client.get_roles()]
            backup.save({"users": users, "roles": roles})
            process_and_upload(uploader, anecdotes_auth, users, roles, backup)
            success = True

        except Exception as e:
            logger.error("Process failed, retrying in 60s...", extra={"error": str(e)})
            sleep(RETRY_DELAY_SECONDS)

    logger.info("Process completed successfully")


if __name__ == "__main__":
    main()
