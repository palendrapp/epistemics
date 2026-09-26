"""Shared clarified protocol in a private human browser; original sessions are untouched."""

import secrets
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from epistemics.source_learning.web import Handler as BaseHandler
from epistemics.source_selective.service import VerificationService

ASSETS = Path(__file__).with_name("assets")


class Handler(BaseHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", "/app.js", "/app.css"):
            if not self._guard():
                return
            name = "index.html" if path == "/" else path[1:]
            mime = {"index.html": "text/html", "app.js": "text/javascript", "app.css": "text/css"}[
                name
            ]
            self._send(200, (ASSETS / name).read_bytes(), mime + "; charset=utf-8")
        else:
            super().do_GET()


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, directory, port=0):
        self.service = VerificationService(directory)
        m = self.service.manifest
        if m.participant.kind != "human" and m.response_origin != "synthetic":
            raise ValueError(
                "Browser requires human/synthetic participation and structured presentation"
            )
        self.access = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        super().__init__(("127.0.0.1", port), Handler)


def serve(directory, port):
    server = LocalServer(directory, port)
    print(f"http://127.0.0.1:{server.server_port}/#access={server.access}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
