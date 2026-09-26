"""Private loopback browser using the same service and answer validation as MCP."""

import hmac
import json
import secrets
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from epistemics.live.web import Handler as CoreHandler
from epistemics.source_learning.service import SourceLearningService
from epistemics.source_learning.storage import save

ASSETS = Path(__file__).with_name("assets")


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, directory, port=0):
        self.service = SourceLearningService(directory)
        m = self.service.manifest
        if m.participant.kind != "human" and m.response_origin != "synthetic":
            raise ValueError("Browser requires a human participant or explicit synthetic origin")
        self.access = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        super().__init__(("127.0.0.1", port), Handler)


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
                service = self.server.service
                started = (service.directory / "browser-consent").exists()
                self._send(
                    200,
                    {
                        "started": started,
                        "protocol": service.describe(),
                        "current": service.get_trial() if started else None,
                        "history": service.get_history()["history"] if started else [],
                    },
                )
        except ValueError as error:
            self._error(error)

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
                service = self.server.service
                if path == "/api/begin":
                    if body != {"instructions_accepted": True}:
                        raise ValueError("Accept the instructions before beginning")
                    save(service.directory / "browser-consent", b"Instructions accepted\n")
                    self._send(200, {"started": True})
                    return
                if path not in ("/api/answers", "/api/finish"):
                    self._send(404, {"error": "Not found"})
                    return
                if not (service.directory / "browser-consent").exists():
                    raise ValueError("Accept the instructions before beginning")
                if path == "/api/answers":
                    if set(body) != {"trial_id", "answer"}:
                        raise ValueError("Provide trial_id and answer only")
                    result = service.submit(body["trial_id"], body["answer"])
                else:
                    if body:
                        raise ValueError("Finish takes an empty request")
                    result = service.finish()
                self._send(200, result)
        except (ValueError, KeyError) as error:
            self._error(error)


def serve(directory, port):
    server = LocalServer(directory, port)
    print(f"http://127.0.0.1:{server.server_port}/#access={server.access}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
