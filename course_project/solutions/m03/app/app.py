"""shortly - a tiny URL shortener (standard library only, runs on Python 3.9+).

Links live in a dict in memory, so they vanish when the process restarts and each server
has its own copy. Milestone M05 moves them into a database.

    PORT=8000 python3 app.py
"""
import json
import os
import random
import string
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

LINKS = {}
ALPHABET = string.ascii_letters + string.digits


def new_code():
    while True:
        code = "".join(random.choice(ALPHABET) for _ in range(7))
        if code not in LINKS:
            return code


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json", headers=None):
        data = (json.dumps(body) if content_type == "application/json" else body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/healthz":
            self.reply(200, "ok", "text/plain")
        elif path.startswith("/api/links/"):
            code = path[len("/api/links/"):]
            if code in LINKS:
                self.reply(200, {"code": code, "url": LINKS[code]})
            else:
                self.reply(404, {"error": "unknown code"})
        elif path.count("/") == 1 and path[1:] in LINKS:
            self.reply(302, "", "text/plain", {"Location": LINKS[path[1:]]})
        else:
            self.reply(404, "not found", "text/plain")

    def do_POST(self):
        if self.path.split("?")[0] != "/api/links":
            return self.reply(404, "not found", "text/plain")
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            url = body["url"]
            parts = urlparse(url if isinstance(url, str) else "")
            if parts.scheme not in ("http", "https") or not parts.netloc:
                raise ValueError("url must start with http:// or https://")
        except (ValueError, KeyError, TypeError) as exc:
            return self.reply(400, {"error": "send JSON like {\"url\": \"https://example.com\"}: %s" % exc})
        code = new_code()
        LINKS[code] = url
        self.reply(201, {"code": code, "url": url})

    def log_message(self, format, *args):
        print("%s %s" % (self.command, self.path))


def main():
    port = int(os.environ.get("PORT", "8000"))
    print("shortly listening on port %d" % port)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
