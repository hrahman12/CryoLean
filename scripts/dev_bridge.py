"""Development bridge: exposes the real CryoLeanAPI over HTTP on localhost so the GUI can run in a normal
browser (npm run dev) and in Playwright end-to-end tests.

The desktop app does NOT use this: there, PyWebView injects window.pywebview.api directly.
This file adds no logic. It forwards POST /rpc/<method> {"args": [...]} to CryoLeanAPI.<method>(*args) and
returns the bridge's own envelope unchanged ({"ok": true, "data": ...} or {"ok": false, "error": ...}).

    python scripts/dev_bridge.py [--port 8765]
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cryolean.bridge import CryoLeanAPI  # noqa: E402

API = CryoLeanAPI()
LOCK = threading.Lock()   # the desktop host calls the API one request at a time; keep the same here
PUBLIC = {n for n in dir(API) if not n.startswith("_") and callable(getattr(API, n))}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):  # noqa: N802 - CORS preflight from the Vite dev server
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            return self._send(200, {"ok": True, "methods": sorted(PUBLIC)})
        self._send(404, {"ok": False, "error": {"code": "not_found", "message": self.path, "verdict": None}})

    def do_POST(self):  # noqa: N802
        if not self.path.startswith("/rpc/"):
            return self._send(404, {"ok": False, "error": {"code": "not_found", "message": self.path, "verdict": None}})
        method = self.path[len("/rpc/"):]
        if method not in PUBLIC:
            return self._send(404, {"ok": False, "error": {"code": "not_found", "message": f"unknown method {method}", "verdict": None}})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            args = body.get("args") or []
        except (ValueError, AttributeError) as e:
            return self._send(400, {"ok": False, "error": {"code": "invalid_input", "message": str(e), "verdict": None}})
        try:
            with LOCK:
                env = getattr(API, method)(*args)
        except Exception as e:  # noqa: BLE001 - report like the bridge does; never invent a verdict
            env = {"ok": False, "error": {"code": "internal_error", "message": str(e), "verdict": None}}
        self._send(200, env)

    def log_message(self, fmt, *a):  # quieter console: one line per call
        sys.stderr.write("dev_bridge: " + (fmt % a) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CryoLean development bridge (localhost only)")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args(argv)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"CryoLean dev bridge on http://127.0.0.1:{a.port}  ({len(PUBLIC)} methods)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
