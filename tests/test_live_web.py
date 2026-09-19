import hashlib
import http.cookiejar
import json
import threading
from contextlib import contextmanager
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

import pytest
from test_live import response

from epistemics.live.service import LiveService
from epistemics.live.web import LocalServer
from epistemics.passport.build import verify_derivation
from epistemics.passport.models import read_passport


@contextmanager
def running_server(tmp_path, *, synthetic=False):
    server = LocalServer(0, LiveService(tmp_path / "web.db"), synthetic=synthetic)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class BrowserClient:
    def __init__(self, base):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.client = build_opener(HTTPCookieProcessor(self.jar))

    def request(self, path, data=None, headers=None):
        body = None if data is None else json.dumps(data).encode()
        default = (
            {}
            if body is None
            else {"Content-Type": "application/json", "X-Epistemics-Request": "1"}
        )
        request = Request(self.base + path, data=body, headers=default | (headers or {}))
        try:
            result = self.client.open(request, timeout=10)
        except HTTPError as error:
            result = error
        with result:
            return result.status, result.headers, result.read()

    def json(self, path, data=None):
        code, _, raw = self.request(path, data)
        assert code in {200, 201}, raw
        return json.loads(raw)


def test_full_browser_http_flow_resume_downloads_and_isolation(tmp_path):
    with running_server(tmp_path, synthetic=True) as base:
        client = BrowserClient(base)
        assert client.json("/api/session") == {"session": None}
        protocol = client.json("/api/protocol")
        assert protocol["total_trials"] == 34 and protocol["synthetic_demo"]
        request = {
            "request_id": "browser-start-id-001",
            "instructions_accepted": True,
            "tools": [],
            "assistance": [],
        }
        sid = client.json("/api/sessions", request)["session_id"]
        assert client.json("/api/sessions", request)["session_id"] == sid
        assert "HttpOnly" in next(iter(client.jar))._rest
        assert client.request("/download/report.json")[0] == 409
        for index in range(34):
            current = client.json("/api/session")["session"]
            assert current["answered"] == index
            assert current["context"]["participant"]["kind"] == "human"
            assert current["context"]["conditions"]["interface"] == "browser"
            assert current["context"]["response_origin"] == "synthetic"
            trial = current["trial"]
            submission = {"trial_id": trial["trial_id"], "answer": response(trial)}
            receipt = client.json("/api/answers", submission)
            assert client.json("/api/answers", submission) == receipt
        assert client.json("/api/session")["session"]["complete"]
        raw = client.request("/download/report.json")[2]
        passport_bytes = client.request("/download/passport.json")[2]
        passport = read_passport(passport_bytes)
        assert passport.source.sha256 == hashlib.sha256(raw).hexdigest()
        verify_derivation(passport, raw)
        assert client.request("/download/report.json")[2] == raw
        html = client.request("/passport")
        assert html[0] == 200 and b"SYNTHETIC" in html[2]
        assert b"passport/0.2.0" in html[2]
        assert client.request("/download/passport.md")[0] == 200
        stranger = BrowserClient(base)
        assert stranger.json("/api/session") == {"session": None}
        assert stranger.request("/passport")[0] == 404
        assert stranger.request("/download/report.json")[0] == 404


def test_http_guard_and_allowlist(tmp_path):
    with running_server(tmp_path) as base:
        client = BrowserClient(base)
        for path in ["/", "/app.js", "/app.css"]:
            code, headers, raw = client.request(path)
            assert code == 200 and raw
            assert headers["Cache-Control"] == "no-store"
            assert "script-src 'self'" in headers["Content-Security-Policy"]
        for path in [
            "/.epistemics/live.sqlite3",
            "/../service.py",
            "/api/sessions",
            "/assets/../../web.py",
        ]:
            assert client.request(path)[0] == 404
        assert client.request("/api/protocol", headers={"Host": "attacker.example"})[0] == 403
        assert (
            client.request("/api/protocol", headers={"Origin": "https://attacker.example"})[0]
            == 403
        )
        payload = {"request_id": "browser-start-id-002", "instructions_accepted": True}
        assert client.request("/api/sessions", payload, {"X-Epistemics-Request": ""})[0] == 403
        assert client.request("/api/sessions", payload, {"Origin": "null"})[0] == 403
        for extra in [
            {"seed": 7},
            {"response_origin": "agent"},
            {"instructions_accepted": False},
            {"instructions_accepted": "true"},
            {"configuration": {}},
        ]:
            assert client.request("/api/sessions", payload | extra)[0] == 400
        client.json("/api/sessions", payload)
        session = client.json("/api/session")["session"]
        assert session["context"]["response_origin"] == "human"  # No answers submitted.
        assert session["context"]["conditions"]["tools"] is None
        assert "configuration" not in session["context"]["participant"]
        assert (
            client.request(
                "/api/answers", {"trial_id": "core-00", "answer": {"target_probability": 2}}
            )[0]
            == 400
        )
        assert client.json("/api/session")["session"]["answered"] == 0


@pytest.mark.parametrize(
    "body",
    [b"{broken", b"[]", b"null", b"x" * 32769],
    ids=["invalid-json", "array", "null", "oversize"],
)
def test_malformed_requests_do_not_break_server(tmp_path, body):
    with running_server(tmp_path) as base:
        client = BrowserClient(base)
        request = Request(
            base + "/api/sessions",
            data=body,
            headers={"Content-Type": "application/json", "X-Epistemics-Request": "1"},
        )
        with pytest.raises(HTTPError) as error:
            client.client.open(request, timeout=5)
        assert error.value.code == 400
        assert client.json("/api/session") == {"session": None}
