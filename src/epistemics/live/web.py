"""Loopback-only human adapter. Static assets and public session routes are allowlisted."""

import hashlib
import json
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, ValidationError

from epistemics.live.service import LiveService, SessionConflict, UnknownSession
from epistemics.models import Model
from epistemics.participants import EvaluationConditions, HumanParticipant
from epistemics.passport.models import read_passport
from epistemics.passport.render import render_html, render_markdown

ASSETS = Path(__file__).with_name("assets")
COOKIE = "epistemics_core_session"


class HumanStart(Model):
    request_id: str = Field(min_length=16, max_length=128)
    subject_id: str = Field(default="", max_length=256)
    instructions_accepted: bool = Field(strict=True)
    tools: list[str] | None = None
    assistance: list[str] | None = None


class Submission(Model):
    trial_id: str = Field(max_length=64)
    answer: dict


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, service, *, synthetic=False):
        self.service = service
        self.synthetic = synthetic
        super().__init__(("127.0.0.1", port), Handler)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        # Session IDs, answers and private data do not enter access logs.
        return

    def _send(
        self,
        status,
        data,
        content_type="application/json; charset=utf-8",
        *,
        cookie=None,
        filename=None,
    ):
        if not isinstance(data, bytes):
            data = json.dumps(data, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        )
        if cookie is not None:
            self.send_header(
                "Set-Cookie",
                f"{COOKIE}={cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000",
            )
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass  # State/receipts persist; a reconnect can retry idempotently.

    def _guard(self, *, mutation=False):
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host") not in allowed_hosts:
            self._send(403, {"error": "This local service requires its loopback host"})
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin not in {f"http://{host}" for host in allowed_hosts}:
            self._send(403, {"error": "Cross-origin requests are not accepted"})
            return False
        if mutation and (
            self.headers.get("X-Epistemics-Request") != "1"
            or self.headers.get_content_type() != "application/json"
        ):
            self._send(403, {"error": "Use the same-origin JSON client"})
            return False
        return True

    def _session_id(self):
        jar = SimpleCookie()
        jar.load(self.headers.get("Cookie", ""))
        item = jar.get(COOKIE)
        if item is None or len(item.value) > 64:
            raise UnknownSession("No session in this browser")
        return item.value

    def _error(self, error):
        if isinstance(error, UnknownSession):
            self._send(404, {"error": str(error)})
        elif isinstance(error, SessionConflict):
            self._send(409, {"error": str(error)})
        elif isinstance(error, ValidationError):
            self._send(
                400,
                {
                    "error": "; ".join(
                        ".".join(map(str, item["loc"])) + ": " + item["msg"]
                        for item in error.errors(include_input=False, include_context=False)
                    )
                },
            )
        else:
            self._send(400, {"error": str(error)})

    def do_GET(self):
        if not self._guard():
            return
        path = urlsplit(self.path).path
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/app.css": ("app.css", "text/css; charset=utf-8"),
        }
        try:
            if path in assets:
                filename, mime = assets[path]
                self._send(200, (ASSETS / filename).read_bytes(), mime)
            elif path == "/api/protocol":
                self._send(
                    200, self.server.service.describe() | {"synthetic_demo": self.server.synthetic}
                )
            elif path == "/api/session":
                try:
                    current = self.server.service.get_trial(self._session_id())
                except UnknownSession:
                    self._send(200, {"session": None})
                else:
                    self._send(200, {"session": current})
            elif path == "/passport":
                raw = self.server.service.passport_bytes(self._session_id())
                self._send(
                    200, render_html(read_passport(raw)).encode(), "text/html; charset=utf-8"
                )
            elif path in {
                "/download/report.json",
                "/download/passport.json",
                "/download/passport.md",
            }:
                session_id = self._session_id()
                if path.endswith("/report.json"):
                    raw = self.server.service.report_bytes(session_id)
                else:
                    raw = self.server.service.passport_bytes(session_id)
                if path.endswith(".md"):
                    raw = render_markdown(read_passport(raw)).encode()
                self._send(
                    200,
                    raw,
                    "text/markdown; charset=utf-8"
                    if path.endswith(".md")
                    else "application/json; charset=utf-8",
                    filename=path.rsplit("/", 1)[1],
                )
            else:
                self._send(404, {"error": "Not found"})
        except (ValueError, KeyError) as error:
            self._error(error)

    def do_POST(self):
        if not self._guard(mutation=True):
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 32768:
                raise ValueError("Request must contain at most 32 KiB of JSON")
            data = json.loads(self.rfile.read(size))
            path = urlsplit(self.path).path
            if path == "/api/sessions":
                request = HumanStart.model_validate(data)
                subject = (
                    request.subject_id.strip()
                    or "human:" + hashlib.sha256(request.request_id.encode()).hexdigest()[:12]
                )
                participant = HumanParticipant(subject_id=subject)
                result = self.server.service.start(
                    participant,
                    request_id=request.request_id,
                    conditions=EvaluationConditions(
                        interface="browser", tools=request.tools, assistance=request.assistance
                    ),
                    instructions_accepted=request.instructions_accepted,
                    response_origin="synthetic" if self.server.synthetic else "human",
                )
                self._send(201, result, cookie=result["session_id"])
            elif path == "/api/answers":
                request = Submission.model_validate(data)
                self._send(
                    200,
                    self.server.service.submit(
                        self._session_id(), request.trial_id, request.answer
                    ),
                )
            else:
                self._send(404, {"error": "Not found"})
        except (ValueError, KeyError) as error:
            self._error(error)


def serve(port=8765, database=".epistemics/live.sqlite3", *, synthetic=False):
    server = LocalServer(port, LiveService(database), synthetic=synthetic)
    print(f"Epistemics core: http://127.0.0.1:{server.server_port}", flush=True)
    if synthetic:
        print(
            "SYNTHETIC DEMO: every response collected by this server is labeled synthetic.",
            flush=True,
        )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
