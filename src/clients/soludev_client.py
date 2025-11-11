import requests

from src.common.config import config
from src.common.logger import CustomLogger
from src.common.models import User, Role

SOLUDEV_CLIENT_NAME: str = config.LOGGING.SOLUDEV_CLIENT_NAME
LOG_FILE_NAME: str = config.LOGGING.COMPONENT_TO_LOG_FILE.get(SOLUDEV_CLIENT_NAME)

logger = CustomLogger(component=SOLUDEV_CLIENT_NAME, log_file=LOG_FILE_NAME)


class SoluDevClient:
    def __init__(self, base_url: str, username: str, api_key: str, session: requests.Session, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.credentials = {"username": username, "api_key": api_key}
        self.session = session
        self.timeout = timeout

    def login(self):
        logger.info(f"Attempting login to {self.base_url}/login")

        try:
            response = self.session.post(f"{self.base_url}/login", json=self.credentials, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")

            if not token:
                logger.error("Login failed: token missing in response")
                raise RuntimeError("SoluDev login failed: missing 'token'")

            self.session.headers.update({"Authorization": f"Bearer {token}"})
            logger.info("SoluDev login successful")

        except requests.exceptions.Timeout as e:
            logger.error(f"Login request timed out: {e}")
            raise

        except requests.exceptions.HTTPError as e:
            logger.error(f"Login HTTP error: {e.response.status_code} - {e}")
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {e}")
            raise

    def get_users(self) -> list[User]:
        logger.info("Start fetching users")
        page = 1
        users: list[dict] = []

        while True:
            response = self.session.get(f"{self.base_url}/users", params={"page": page}, timeout=self.timeout)
            response.raise_for_status()
            json_data = response.json()
            users_batch = json_data.get("users", [])
            users.extend(users_batch)
            logger.info("Fetched users page", page=page, count=len(users_batch), total=len(users))

            pagination = json_data.get("pagination", {})

            if not pagination or not pagination.get("has_next", False):
                break

            page += 1

        return [User(**user) for user in users]

    def get_roles(self) -> list[Role]:
        response = self.session.get(f"{self.base_url}/roles", timeout=self.timeout)
        response.raise_for_status()
        json_data = response.json()
        roles = json_data.get("roles", [])
        logger.info("Fetched roles", count=len(roles))
        return [Role(**role) for role in roles]
