"""Capability-bound loopback human interface over the same immutable service."""

import hmac
import json
import secrets
import threading
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from epistemics.investigation3.service import InvestigationService, load, status
from epistemics.live.web import Handler as CoreHandler
from epistemics.service import now

ASSETS = Path(__file__).with_name("assets")
COOKIE = "epistemics_investigation3"


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, service, *, collection=False):
        if (
            service.manifest.participant.kind != "human"
            and service.manifest.response_origin != "synthetic"
        ):
            raise ValueError(
                "Browser participation requires a human descriptor or explicit synthetic origin"
            )
        self.service = service
        self.collection = collection
        self.lock = threading.Lock()
        self.ids = (
            [a.assignment_id for a in service.manifest.assignments]
            if collection
            else [service.assignment.assignment_id]
        )
        self.access = secrets.token_urlsafe(32)
        self.session = secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), Handler)

    def target(self, assignment_id):
        current = self.ids.index(self.service.assignment.assignment_id)
        if assignment_id not in self.ids or self.ids.index(assignment_id) > current:
            raise ValueError("Only the current case and accepted earlier cases are accessible")
        return InvestigationService(self.service.directory, assignment_id)

    def advance(self, assignment_id):
        with self.lock:
            service = self.target(assignment_id)
            with service.state() as state:
                if not state["completed_at"]:
                    raise ValueError("Finish the current case before continuing")
                accepted_at = state.get("browser_instructions_accepted_at")
            index = self.ids.index(assignment_id)
            # Retries after a lost response never advance a second time.
            if assignment_id == self.service.assignment.assignment_id and index + 1 < len(self.ids):
                self.service = InvestigationService(service.directory, self.ids[index + 1])
                with self.service.state() as state:
                    state.setdefault("browser_instructions_accepted_at", accepted_at)
            return {"assignment_id": self.service.assignment.assignment_id}


class Handler(CoreHandler):
    def _send(self, status, data, content_type="application/json; charset=utf-8", *, cookie=None):
        if not isinstance(data, bytes):
            data = json.dumps(data, allow_nan=False).encode()
        self.send_response(status)
        for key, value in {
            "Content-Type": content_type,
            "Content-Length": str(len(data)),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        }.items():
            self.send_header(key, value)
        if cookie:
            self.send_header("Set-Cookie", f"{COOKIE}={cookie}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def authorized(self):
        jar = SimpleCookie()
        jar.load(self.headers.get("Cookie", ""))
        value = jar.get(COOKIE)
        return value is not None and hmac.compare_digest(value.value, self.server.session)

    def do_GET(self):
        if not self._guard():
            return
        path = urlsplit(self.path).path
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/app.css": ("app.css", "text/css; charset=utf-8"),
        }
        if path in assets:
            name, mime = assets[path]
            self._send(200, (ASSETS / name).read_bytes(), mime)
            return
        if not self.authorized():
            self._send(403, {"error": "Open the private case link printed by the local evaluator."})
            return
        try:
            if path == "/api/state":
                service = self.server.service
                with service.state() as state:
                    accepted = bool(state.get("browser_instructions_accepted_at"))
                self._send(
                    200,
                    {
                        "protocol": service.describe(),
                        "synthetic": service.manifest.response_origin == "synthetic",
                        "started": accepted,
                        "current": service.get_trial() if accepted else None,
                        "history": service.get_history()["history"] if accepted else [],
                        "assignment_id": service.assignment.assignment_id,
                        "case_number": self.server.ids.index(service.assignment.assignment_id) + 1,
                        "case_count": len(self.server.ids),
                    },
                )
            else:
                self._send(404, {"error": "Not found"})
        except (ValueError, KeyError) as error:
            self._send(409, {"error": str(error)})

    def do_POST(self):
        if not self._guard(mutation=True):
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 32768:
                raise ValueError("Request must contain at most 32 KiB of JSON")
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("JSON object required")
            path = urlsplit(self.path).path
            if path == "/api/open":
                token = data.get("access")
                if not isinstance(token, str) or not hmac.compare_digest(token, self.server.access):
                    self._send(403, {"error": "Invalid private case link"})
                else:
                    self._send(200, {"opened": True}, cookie=self.server.session)
                return
            if not self.authorized():
                self._send(403, {"error": "Open the private case link first"})
                return
            service = self.server.service
            if path == "/api/next":
                self._send(200, self.server.advance(data.get("from_assignment")))
                return
            if path == "/api/begin":
                if data.get("instructions_accepted") is not True:
                    raise ValueError("Please acknowledge the instructions")
                with service.state() as state:
                    state.setdefault("browser_instructions_accepted_at", now())
                self._send(200, {"started": True})
                return
            with service.state() as state:
                if not state.get("browser_instructions_accepted_at"):
                    raise ValueError("Read and acknowledge the instructions first")
            if path == "/api/answers":
                if set(data) != {"trial_id", "answer"}:
                    raise ValueError("Use trial_id and answer only")
                if not isinstance(data["trial_id"], str):
                    raise ValueError("Trial identifier must be a string")
                service = self.server.target(data["trial_id"].rsplit(":", 1)[0])
                self._send(200, service.submit(data["trial_id"], data["answer"]))
            elif path == "/api/finish":
                service = self.server.target(
                    data.get("assignment_id", service.assignment.assignment_id)
                )
                self._send(200, service.finish())
            else:
                self._send(404, {"error": "Not found"})
        except (ValueError, KeyError, TypeError) as error:
            self._send(400, {"error": str(error)})


def serve(directory, assignment, port=8766):
    if not 0 <= port <= 65535:
        raise ValueError("Port must be between 0 and 65535")
    collection = assignment is None
    if collection:
        manifest, _ = load(directory)
        progress = status(directory)
        assignment = next(
            (a["assignment_id"] for a in progress["assignments"] if not a["complete"]),
            manifest.assignments[-1].assignment_id,
        )
    server = LocalServer(port, InvestigationService(directory, assignment), collection=collection)
    print(
        f"Private investigation case: http://127.0.0.1:{server.server_port}/#access={server.access}",
        flush=True,
    )
    print(
        "This private link grants access to the bound human evaluation. Responses stay local.",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
