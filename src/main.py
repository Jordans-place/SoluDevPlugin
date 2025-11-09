import json

from src.Anecdotes_auth import AnecdotesAuth
from src.common import utils
from src.common.logger import CustomLogger
from time import sleep
from pathlib import Path

from src.common.models import User, Role
from src.local_backup import LocalBackup
from src.soludev_client import SoluDevClient
from src.uploader import AnecdotesUploader

logger = CustomLogger("MAIN", "logs/soludev_plugin.log")




def main():
    session = utils.build_session()
    soludev_client = SoluDevClient(BASE_URL, SOLUDEV_USERNAME, SOLUDEV_API_KEY, session, TIMEOUT_SECONDS)
    soludev_client.login()

    anecdotes_auth = AnecdotesAuth(api_key=ANECDOTES_API_KEY, session=session)
    anecdotes_auth.apply(session)

    backup = LocalBackup(BACKUP_FILE_NAME)
    uploader = AnecdotesUploader(session=session, service_id="SoluDev")

    while True:
        try:
            data = backup.load()
            if data:
                logger.info("Found backup data, attempting re-upload...")

                users_as_array = data.get("users", [])
                roles_as_array = data.get("roles", [])

                USERS_FILE.write_text(json.dumps(users_as_array, indent=2, ensure_ascii=False), encoding="utf-8")
                ROLES_FILE.write_text(json.dumps(roles_as_array, indent=2, ensure_ascii=False), encoding="utf-8")

                _upload_with_refresh(uploader, anecdotes_auth, USERS_FILE)
                _upload_with_refresh(uploader, anecdotes_auth, ROLES_FILE)

                backup.clear()
                break

            users: list[User] = soludev_client.get_users()
            roles: list[Role] = soludev_client.get_roles()

            users_arr = [u.model_dump() for u in users]
            roles_arr = [r.model_dump() for r in roles]

            USERS_FILE.write_text(json.dumps(users_arr, indent=2, ensure_ascii=False), encoding="utf-8")
            ROLES_FILE.write_text(json.dumps(roles_arr, indent=2, ensure_ascii=False), encoding="utf-8")

            backup.save({"users": users_arr, "roles": roles_arr})

            _upload_with_refresh(uploader, anecdotes_auth, USERS_FILE)
            _upload_with_refresh(uploader, anecdotes_auth, ROLES_FILE)

            backup.clear()
            break

        except Exception as e:
            logger.error("Process failed, retrying in 60s...", extra={"error": str(e)})
            sleep(60)


if __name__ == "__main__":
    main()
