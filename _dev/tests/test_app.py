import http.client
import importlib.util
import json
import re
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "course_project" / "app" / "app.py"


@pytest.fixture(scope="module")
def server():
    spec = importlib.util.spec_from_file_location("shortly_app", APP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


def call(port, method, path, body=None, raw=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    data = raw if raw is not None else (json.dumps(body) if body is not None else None)
    conn.request(method, path, body=data, headers={"Content-Type": "application/json"} if data else {})
    resp = conn.getresponse()
    text = resp.read().decode("utf-8")
    conn.close()
    return resp.status, dict(resp.getheaders()), text


def test_healthz(server):
    status, headers, text = call(server, "GET", "/healthz")
    assert (status, text) == (200, "ok") and headers["Content-Type"].startswith("text/plain")


def test_create_get_and_redirect(server):
    status, _, text = call(server, "POST", "/api/links", {"url": "https://example.com/a?b=1"})
    created = json.loads(text)
    assert status == 201 and re.fullmatch(r"[A-Za-z0-9]{7}", created["code"])
    assert created["url"] == "https://example.com/a?b=1"
    status, _, text = call(server, "GET", f"/api/links/{created['code']}")
    assert status == 200 and json.loads(text) == created
    status, headers, _ = call(server, "GET", f"/{created['code']}")
    assert status == 302 and headers["Location"] == "https://example.com/a?b=1"


@pytest.mark.parametrize("body, raw", [({}, None), ({"url": "ftp://x.example"}, None), ({"url": "nope"}, None),
                                       ({"url": 5}, None), (None, "{not json")])
def test_bad_requests(server, body, raw):
    status, _, text = call(server, "POST", "/api/links", body, raw)
    assert status == 400 and "error" in json.loads(text)


def test_unknown_paths(server):
    assert call(server, "GET", "/api/links/zzzzzzz")[0] == 404
    assert json.loads(call(server, "GET", "/api/links/zzzzzzz")[2])["error"]
    assert call(server, "GET", "/zzzzzzz")[0] == 404
    assert call(server, "GET", "/a/b/c")[0] == 404
    assert call(server, "POST", "/elsewhere", {"url": "https://example.com"})[0] == 404


def test_file_is_safe_to_paste_into_cloudformation_sub():
    text = APP.read_text(encoding="utf-8")
    assert "${" not in text and "\t" not in text
