import requests

from src.common import utils
from src.common.logger import CustomLogger
from time import sleep

from src.common.models import User, Role
from src.local_backup import LocalBackup
from src.soludev_client import SoluDevClient
from src.uploader import AnecdotesUploader

logger = CustomLogger("MAIN", "logs/soludev_plugin.log")




def main():
    session = utils.build_session()
    soludev_client = SoluDevClient(BASE_URL, SOLUDEV_USERNAME, SOLUDEV_API_KEY, session, TIMEOUT_SECONDS)
    backup = LocalBackup(BACKUP_FILE_NAME)
    anacdots_uploader = AnecdotesUploader(token=ANECDOTES_TOKEN)
    soludev_client.login()

    while True:
        try:
            data = backup.load()
            if data:
                logger.info("Found backup data, attempting re-upload...")
                anacdots_uploader.upload_file("SoluDev Users List", "./out/users.json")
                anacdots_uploader.upload_file("SoluDev Roles List", "./out/roles.json")
                backup.clear()
                break

            users: list[User] = soludev_client.get_users()
            roles: list[Role] = soludev_client.get_roles()

            payload = {
                "users": [u.model_dump() for u in users],
                "roles": [r.model_dump() for r in roles],
            }

            backup.save(payload)
            anacdots_uploader.upload_file("SoluDev Users List", "./out/users.json")
            anacdots_uploader.upload_file("SoluDev Roles List", "./out/roles.json")
            backup.clear()
            break

        except Exception as e:
            logger.error("Process failed, retrying in 60s...", extra={"error": str(e)})
            sleep(60)


if __name__ == "__main__":
    main()
