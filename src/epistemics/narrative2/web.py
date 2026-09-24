"""Loopback human adapter, using the same accepted-answer service as MCP."""

import hmac
import json
import secrets
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from epistemics.live.web import Handler as CoreHandler
from epistemics.narrative2.service import NarrativeService, load, save

ASSETS = Path(__file__).with_name("assets")


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, directory, port=0):
        self.directory = Path(directory)
        self.manifest, _ = load(directory)
        if (
            self.manifest.participant.kind != "human"
            and self.manifest.response_origin != "synthetic"
        ):
            raise ValueError("Browser requires a human participant or explicit synthetic origin")
        self.access = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        super().__init__(("127.0.0.1", port), Handler)

    def current(self):
        for i, a in enumerate(self.manifest.assignments):
            service = NarrativeService(self.directory, a.assignment_id)
            with service.state() as state:
                if state["completed_at"] is None:
                    return i, service
        return len(self.manifest.assignments), None


class Handler(CoreHandler):
    def authorized(self):
        return hmac.compare_digest(
            self.headers.get("Authorization", ""), "Bearer " + self.server.access
        )

    def do_GET(self):
        if not self._guard():
            return
        path = urlsplit(self.path).path
        if path in ("/", "/app.js", "/app.css"):
            name = "index.html" if path == "/" else path[1:]
            mime = {"index.html": "text/html", "app.js": "text/javascript", "app.css": "text/css"}[
                name
            ]
            self._send(200, (ASSETS / name).read_bytes(), mime + "; charset=utf-8")
            return
        if not self.authorized():
            self._send(403, {"error": "Use the private link supplied by the evaluator."})
            return
        if path != "/api/state":
            self._send(404, {"error": "Not found"})
            return
        try:
            with self.server.lock:
                i, service = self.server.current()
                accepted = (self.server.directory / "browser-consent").exists()
                self._send(
                    200,
                    {
                        "complete": service is None,
                        "started": accepted,
                        "case_number": i + 1 if service else i,
                        "case_count": len(self.server.manifest.assignments),
                        "assignment_id": service.assignment.assignment_id if service else None,
                        "protocol": service.describe() if service else None,
                        "current": service.get_trial() if service and accepted else None,
                        "history": service.get_history()["history"] if service and accepted else [],
                        "synthetic": self.server.manifest.response_origin == "synthetic",
                    },
                )
        except ValueError as e:
            self._error(e)

    def do_POST(self):
        if not self._guard(mutation=True):
            return
        if not self.authorized():
            self._send(403, {"error": "Use the private link supplied by the evaluator."})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 16384:
                raise ValueError("Invalid request size")
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError("Expected a JSON object")
            path = urlsplit(self.path).path
            with self.server.lock:
                if path == "/api/begin":
                    if body.get("instructions_accepted") is not True:
                        raise ValueError("Accept the instructions before beginning")
                    save(self.server.directory / "browser-consent", b"Instructions accepted\n")
                    self._send(200, {"started": True})
                    return
                if path not in ("/api/answers", "/api/finish"):
                    self._send(404, {"error": "Not found"})
                    return
                if not (self.server.directory / "browser-consent").exists():
                    raise ValueError("Accept the instructions before beginning")
                current, _ = self.server.current()
                ids = [a.assignment_id for a in self.server.manifest.assignments]
                target = body.get("assignment_id")
                if target not in ids or ids.index(target) > current:
                    raise ValueError("Only current or accepted earlier cases are accessible")
                service = NarrativeService(self.server.directory, target)
                result = (
                    service.submit(body["trial_id"], body["answer"])
                    if path == "/api/answers"
                    else service.finish()
                )
                self._send(200, result)
        except (ValueError, KeyError) as e:
            self._error(e)


def serve(directory, port):
    server = LocalServer(directory, port)
    print(f"http://127.0.0.1:{server.server_port}/#access={server.access}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
