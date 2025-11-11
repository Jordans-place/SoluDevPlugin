import time
import requests
from typing import Optional

from src.common.config import config
from src.common.logger import CustomLogger

ANECDOTES_AUTH_EXCHANGE_URL: str = config.HTTP.ANECDOTES_AUTH_EXCHANGE_URL
JWT_EXPIRY_BUFFER_SECONDS: int = config.SERVICE.JWT_EXPIRY_BUFFER_SECONDS
TIMEOUT_SECONDS: int = config.HTTP.TIMEOUT_SECONDS

AUTH_COMPONENT_NAME: str = config.LOGGING.AUTH_COMPONENT_NAME
LOG_FILE_NAME: str = config.LOGGING.COMPONENT_TO_LOG_FILE.get(AUTH_COMPONENT_NAME)

logger = CustomLogger(component=AUTH_COMPONENT_NAME, log_file=LOG_FILE_NAME)


class AnecdotesAuth:
    def __init__(self, api_key: str, session: requests.Session):
        if not api_key or not api_key.strip():
            logger.error("API key validation failed: empty or whitespace-only key provided")
            raise ValueError("ANECDOTES API key is empty")

        self._api_key = api_key.strip()
        self._session = session
        self._jwt: Optional[str] = None
        self._expiration_ts: int = 0
        self.exchange_url = ANECDOTES_AUTH_EXCHANGE_URL

    def _exchange(self):
        logger.info(f"Attempting to exchange API key for JWT token at {self.exchange_url}")
        try:
            response = self._session.get(
                self.exchange_url,
                headers={"x-anecdotes-api-key": self._api_key},
                timeout=TIMEOUT_SECONDS
            )
            response.raise_for_status()

            jwt_token = response.text.strip().strip('"')
            self._jwt = jwt_token
            self._expiration_ts = int(time.time()) + JWT_EXPIRY_BUFFER_SECONDS
            logger.info(f"JWT token obtained successfully. Expires at timestamp: {self._expiration_ts}")

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout while exchanging API key: {e}")
            raise

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during token exchange: {e.response.status_code} - {e}")
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed during token exchange: {e}")
            raise

    def ensure_jwt(self) -> str:
        current_time = time.time()

        if not self._jwt:
            logger.info("No JWT token found, obtaining new token")
            self._exchange()

        elif current_time >= self._expiration_ts:
            logger.info(f"JWT token expired (current: {current_time}, expiry: {self._expiration_ts}), refreshing token")
            self._exchange()

        else:
            logger.debug(f"Using existing JWT token (expires in {self._expiration_ts - current_time:.0f} seconds)")

        return self._jwt

    def apply(self, session: requests.Session):
        logger.info("Applying authentication headers to session")
        jwt = self.ensure_jwt()
        session.headers.update({
            "Authorization": f"Bearer {jwt}",
            "accept": "application/json",
            "User-Agent": "soludev-plugin/1.0"
        })
        logger.debug("Authentication headers applied successfully")

    def refresh_token(self, session: requests.Session):
        logger.info("Force refreshing JWT token")
        self._exchange()
        self.apply(session)
        logger.info("Token refresh completed and applied to session")
