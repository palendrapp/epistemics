"""Workers AI REST client for Clef.

Credentials come from the environment (CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN), set by the
user in the shell or in a gitignored .env file at the repository root; a variable already set in
the shell wins. They are never logged, stored or written into a record, and error messages never
include them.
"""

import json
import os
import time
import urllib.error
import urllib.request

ENDPOINT = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
TRANSIENT = {408, 409, 425, 429, 500, 502, 503, 504}
VARIABLES = ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN")


class ClefError(RuntimeError):
    pass


def load_env_file(path=".env", names=VARIABLES):
    """Set the named variables from a KEY=VALUE file (optional `export`, optional quotes) where the
    environment does not already have them. Returns the names it set, never the values."""
    try:
        lines = open(path).read().splitlines()
    except FileNotFoundError:
        return []
    found = []
    for line in lines:
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or key not in names or os.environ.get(key):
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        if value:
            os.environ[key] = value
            found.append(key)
    return found


class Client:
    def __init__(self, account, token, timeout=120, retries=5, backoff=2.0, opener=None):
        self._account = account
        self._token = token
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self._open = opener or urllib.request.urlopen

    @classmethod
    def from_env(cls, **kwargs):
        account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        token = os.environ.get("CLOUDFLARE_API_TOKEN")
        if not account or not token:
            raise ClefError(
                "Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN in this shell or in .env (a "
                "token with the Workers AI Read and Edit permissions)."
            )
        return cls(account, token, **kwargs)

    def _scrub(self, text):
        return str(text).replace(self._token, "[token]").replace(self._account, "[account]")

    def run(self, model, body):
        """POST one request; returns (parsed JSON response, elapsed seconds, attempts)."""
        url = ENDPOINT.format(account=self._account, model=model)
        data = json.dumps(body, ensure_ascii=False).encode()
        headers = {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}
        last = None
        for attempt in range(1, self.retries + 1):
            request = urllib.request.Request(url, data=data, headers=headers, method="POST")
            start = time.monotonic()
            try:
                with self._open(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode())
                return payload, time.monotonic() - start, attempt
            except urllib.error.HTTPError as error:
                detail = error.read().decode(errors="replace")[:500]
                last = f"HTTP {error.code}: {self._scrub(detail)}"
                if error.code not in TRANSIENT:
                    raise ClefError(last) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                last = self._scrub(repr(error))
            if attempt < self.retries:
                time.sleep(self.backoff * 2 ** (attempt - 1))
        raise ClefError(f"Gave up after {self.retries} attempts: {last}")
