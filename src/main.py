import json

from src.Anecdotes_auth import AnecdotesAuth
from src.common import utils
from src.common.logger import CustomLogger
from time import sleep
from pathlib import Path

from src.local_backup import LocalBackup
from src.soludev_client import SoluDevClient
from src.uploader import AnecdotesUploader
from src.common.config import config


SOLUDEV_BASE_URL: str = config.HTTP.SOLUDEV_BASE_URL
TIMEOUT_SECONDS: int = config.HTTP.TIMEOUT_SECONDS
SOLUDEV_USERNAME = utils.get_env_variable('SOLUDEV_USERNAME')
SOLUDEV_API_KEY = utils.get_env_variable('SOLUDEV_API_KEY')
ANECDOTES_API_KEY = utils.get_env_variable("ANECDOTES_API_KEY")

BACKUP_FILE_NAME: str = config.SERVICE.BACKUP_FILE_NAME
OUT_DIR_PATH: str = config.SERVICE.OUT_DIR_PATH
USERS_FILE_NAME: str = config.SERVICE.USERS_FILE_NAME
ROLES_FILE_NAME: str = config.SERVICE.ROLES_FILE_NAME
OUT_DIR = Path(OUT_DIR_PATH)
OUT_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_FILE_PATH: Path = OUT_DIR / BACKUP_FILE_NAME
USERS_FILE_PATH: Path = OUT_DIR / USERS_FILE_NAME
ROLES_FILE_PATH: Path = OUT_DIR / ROLES_FILE_NAME
MAIN_COMPONENT_NAME: str = config.LOGGING.MAIN_COMPONENT_NAME
LOG_FILE_NAME: str = config.LOGGING.COMPONENT_TO_LOG_FILE.get(MAIN_COMPONENT_NAME)

logger = CustomLogger(MAIN_COMPONENT_NAME, LOG_FILE_NAME)


def process_and_upload(uploader: AnecdotesUploader, auth: AnecdotesAuth, users: list[dict], roles: list[dict], backup: LocalBackup = None):
    USERS_FILE_PATH.write_text(json.dumps(users, indent=4, ensure_ascii=False), encoding="utf-8")
    ROLES_FILE_PATH.write_text(json.dumps(roles, indent=4, ensure_ascii=False), encoding="utf-8")

    for file_path in [USERS_FILE_PATH, ROLES_FILE_PATH]:
        try:
            uploader.upload_file("SoluDev " + file_path.stem.capitalize(), str(file_path))
        except PermissionError:
            auth.refresh_on_401(uploader._session)
            uploader.upload_file("SoluDev " + file_path.stem.capitalize(), str(file_path))

    if backup is not None:
        backup.clear()


def main():
    session = utils.build_session()
    soludev_client = SoluDevClient(SOLUDEV_BASE_URL, SOLUDEV_USERNAME, SOLUDEV_API_KEY, session, TIMEOUT_SECONDS)
    soludev_client.login()

    anecdotes_auth = AnecdotesAuth(api_key=ANECDOTES_API_KEY, session=session)
    anecdotes_auth.apply(session)

    backup = LocalBackup(BACKUP_FILE_PATH)
    uploader = AnecdotesUploader(session=session, service_id="SoluDev")

    while True:
        try:
            backup_data = backup.load()
            if backup_data:
                logger.info("Found backup data, attempting re-upload...")
                users_from_backup = backup_data.get("users", [])
                roles_from_backup = backup_data.get("roles", [])
                process_and_upload(uploader, anecdotes_auth, users_from_backup, roles_from_backup, backup)
                break

            users = [user.model_dump() for user in soludev_client.get_users()]
            roles_arr = [role.model_dump() for role in soludev_client.get_roles()]
            backup.save({"users": users, "roles": roles_arr})
            process_and_upload(uploader, anecdotes_auth, users, roles_arr, backup)
            break

        except Exception as e:
            logger.error("Process failed, retrying in 60s...", extra={"error": str(e)})
            sleep(60)


if __name__ == "__main__":
    main()
