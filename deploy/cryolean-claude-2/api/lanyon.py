"""Vercel function for the website chat: Claude answers (cryolean/chat.py). Lanyon models need the full CryoLean
server (python -m cryolean serve), so they are reported as skipped here."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
import _chat as chat  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        try:
            b = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except ValueError:
            return self._send(400, {"ok": False, "error": {"code": "BAD_JSON", "message": "request body is not JSON"}})
        q, facts = str(b.get("question", ""))[:2000], str(b.get("facts", ""))[:6000]
        if not q.strip():
            return self._send(400, {"ok": False, "error": {"code": "EMPTY", "message": "empty question"}})
        try:
            data = {"answer": chat.answer(q, facts), "answered_by": "claude", "lanyon": None}
        except chat.ChatUnavailable as e:
            return self._send(503, {"ok": False, "error": {"code": "CHAT_UNAVAILABLE", "message": str(e)}})
        if chat.wants_model(q):
            data["lanyon"] = {"skipped": "Lanyon runs only on the full CryoLean server (python -m cryolean serve)"}
        self._send(200, {"ok": True, "data": data})
