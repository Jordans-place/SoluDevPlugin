import time
import requests

from src.common.config import config
from src.common.logger import CustomLogger

ANECDOTES_AUTH_EXCHANGE_URL: str = config.HTTP.ANECDOTES_AUTH_EXCHANGE_URL
AUTH_TIMEOUT_SECONDS: int = 20
JWT_EXPIRY_BUFFER_SECONDS: int = 55 * 60

AUTH_COMPONENT_NAME: str = "ANECDOTES_AUTH"
logger = CustomLogger(component=AUTH_COMPONENT_NAME, log_file="logs/anecdotes_auth.log")


class AnecdotesAuth:
    def __init__(self, api_key: str, session: requests.Session):
        if not api_key or not api_key.strip():
            raise ValueError("ANECDOTES API key is empty")
        self._api_key = api_key.strip()
        self._session = session
        self._jwt = None
        self._exp_ts = 0
        self.exchange_url = ANECDOTES_AUTH_EXCHANGE_URL

    def _exchange(self):
        response = self._session.get(
            self.exchange_url,
            headers={"x-anecdotes-api-key": self._api_key},
            timeout=AUTH_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        jwt_token = response.text.strip().strip('"')
        self._jwt = jwt_token
        self._exp_ts = int(time.time()) + JWT_EXPIRY_BUFFER_SECONDS

    def ensure_jwt(self):
        if not self._jwt or time.time() >= self._exp_ts:
            self._exchange()
        return self._jwt

    def apply(self, session: requests.Session):
        jwt = self.ensure_jwt()
        session.headers.update({
            "Authorization": f"Bearer {jwt}",
            "accept": "application/json",
            "User-Agent": "soludev-plugin/1.0"
        })

    def refresh_token(self, session: requests.Session):
        self._exchange()
        self.apply(session)

