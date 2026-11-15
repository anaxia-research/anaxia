"""Local HTTP interface for the research graph."""

import hmac
import json
import re
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .papers import ALLOWED, export
from .spec import normalize
from .strategies import catalog

STATIC = Path(__file__).with_name("static")
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8"),
          "/app.js": ("app.js", "application/javascript; charset=utf-8")}
HEX = r"[a-f0-9]{32}"
ID = re.compile(rf"/api/missions/({HEX})(?:/(control|export|events))?\Z")
DOWNLOAD = re.compile(rf"/files/({HEX})/({HEX})/([a-z.]+)\Z")


def make_server(store, runner, port, exports):
    exports = Path(exports)
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            return

        def respond(self, data, mime="application/json; charset=utf-8", status=200):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; script-src 'self'; style-src 'self'; "
                             "object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(data)

        def authorize_host(self):
            hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if self.headers.get("Host") not in hosts:
                self.respond({"error": "Open ann on its loopback address."}, status=403)
                return False
            return True

        def do_GET(self):
            if not self.authorize_host():
                return
            try:
                self.get()
            except KeyError:
                self.respond({"error": "Resource not found."}, status=404)
            except ValueError as error:
                self.respond({"error": str(error)}, status=400)
            except OSError:
                self.respond({"error": "Could not read the requested file."}, status=500)

        def get(self):
            url = urlsplit(self.path)
            path = url.path
            if path in ASSETS:
                name, mime = ASSETS[path]
                return self.respond((STATIC / name).read_bytes(), mime)
            if path == "/api/health":
                return self.respond({"status": "ready", "csrf_token": token})
            if path == "/api/strategies":
                return self.respond(catalog())
            if path == "/api/missions":
                return self.respond({"missions": store.missions()})
            match = ID.fullmatch(path)
            query = parse_qs(url.query, max_num_fields=8)
            if match:
                mid, route = match.groups()
                if route == "events":
                    return self.respond({"events": store.events(mid, max(0, int(query.get("since", [0])[0])))})
                if route is None:
                    offset = min(10_000, max(0, int(query.get("offset", [0])[0])))
                    limit = min(2048, max(1, int(query.get("limit", [512])[0])))
                    return self.respond(store.snapshot(mid, offset, limit))
            match = DOWNLOAD.fullmatch(path)
            if match and match[3] in ALLOWED:
                mid, bundle, name = match.groups()
                file = exports / mid / bundle / name
                if not file.is_file():
                    raise KeyError(name)
                mime = {"main.pdf": "application/pdf", "mission.zip": "application/zip",
                        "evidence.json": "application/json"}.get(name, "text/plain; charset=utf-8")
                return self.respond(file.read_bytes(), mime)
            raise KeyError(path)

        def do_POST(self):
            if not self.authorize_host():
                return
            provided = self.headers.get("X-ANN-Token", "")
            origin = self.headers.get("Origin")
            if (not provided.isascii() or not hmac.compare_digest(provided, token)
                    or (origin is not None and origin != "http://" + self.headers["Host"])):
                return self.respond({"error": "Refresh the ann page before making changes."}, status=403)
            try:
                size = int(self.headers.get("Content-Length", -1))
                if not 0 < size <= 48_000 or self.headers.get_content_type() != "application/json":
                    raise ValueError("Send a bounded JSON object")
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise ValueError("Send a JSON object")
                self.post(body)
            except KeyError:
                self.respond({"error": "Mission or action not found."}, status=404)
            except (ValueError, TypeError, RecursionError) as error:
                self.respond({"error": str(error)}, status=400)
            except OSError:
                self.respond({"error": "Could not write to the research workspace."}, status=500)

        def post(self, body):
            if self.path == "/api/missions":
                mission = store.create(normalize(body))
                return self.respond({"mission": mission}, status=201)
            match = ID.fullmatch(self.path)
            if not match:
                raise KeyError(self.path)
            mid, route = match.groups()
            if route == "control":
                action = body.get("action")
                if action not in ("start", "resume", "pause", "cancel"):
                    raise ValueError("Unknown mission action")
                mission = runner.start(mid, action) if action in ("start", "resume") else store.control(mid, action)
                return self.respond({"mission": mission})
            if route == "export":
                if set(body) - {"pdf"} or type(body.get("pdf", False)) is not bool:
                    raise ValueError("Export accepts only a boolean PDF option")
                mission = store.mission(mid)
                bundle = export(mission, store.results(mid), exports / mid, pdf=body.get("pdf", False))
                name = Path(bundle["directory"]).name
                files = [dict(name=file, url=f"/files/{mid}/{name}/{file}") for file in bundle["files"]]
                return self.respond({"files": files, "status": bundle["status"]})
            raise KeyError(route)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
