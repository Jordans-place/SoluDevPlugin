import requests

from src.common.logger import CustomLogger
from src.common.models import User, Role

logger = CustomLogger(component='SOLUDEV_CLIENT', log_file='logs/soludev_plugin.log')


class SoluDevClient:
    def __init__(self, base_url: str, username: str, api_key: str, session: requests.Session, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.credentials = {"username": username, "api_key": api_key}
        self.session = session
        self.timeout = timeout

    def login(self):
        response = self.session.post(f"{self.base_url}/login", json=self.credentials, timeout=self.timeout)
        response.raise_for_status()
        token = response.json().get("token")

        if not token:
            raise RuntimeError("SoluDev login failed: missing 'token'")

        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("SoluDev login successful")

    def get_users(self) -> list[User]:
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
