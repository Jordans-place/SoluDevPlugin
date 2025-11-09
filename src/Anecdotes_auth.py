import time
import requests

class AnecdotesAuth:
    EXCHANGE_URL = "https://gateway.anecdotes.ai/identity/v1/apikey/exchange"

    def __init__(self, api_key: str, session: requests.Session | None = None):
        if not api_key or not api_key.strip():
            raise ValueError("ANECDOTES API key is empty")
        self._api_key = api_key.strip()
        self._s = session or requests.Session()
        self._jwt = None
        self._exp_ts = 0

    def _exchange(self):
        resp = self._s.get(self.EXCHANGE_URL, headers={"x-anecdotes-api-key": self._api_key}, timeout=20)
        resp.raise_for_status()
        jwt_token = resp.text.strip().strip('"')
        self._jwt = jwt_token
        self._exp_ts = int(time.time()) + (55 * 60)

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

    def refresh_on_401(self, session: requests.Session):
        self._exchange()
        self.apply(session)