"""Signed, bounded result receipts for stateless hosted instances.

Receipts preserve a real server-produced record across cold starts. They never
substitute for a Lean run when checking or applying a repair. The existing
fingerprint checks reject changed catalogs; the signature rejects client edits.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import zlib

from . import db

_LOCAL_KEY = secrets.token_bytes(32)


def _key():
    value = os.environ.get("CRYOLEAN_RECEIPT_KEY")
    if os.environ.get("VERCEL") and not value:
        raise RuntimeError("CRYOLEAN_RECEIPT_KEY must be configured for hosted result receipts")
    return value.encode() if value else _LOCAL_KEY


def issue(api, result_id):
    con = api._catalog.connect()
    try:
        row = con.execute("SELECT fingerprint,doc FROM results WHERE id=?", (result_id,)).fetchone()
    finally:
        con.close()
    if not row:
        return None
    payload = json.dumps({"id": result_id, "exp": int(time.time()) + 86400,
                          "fingerprint": row[0], "doc": json.loads(row[1])}, separators=(",", ":")).encode()
    if len(payload) > 8_000_000:
        raise ValueError("Result receipt exceeds the supported size; run a smaller comparison")
    packed = base64.urlsafe_b64encode(zlib.compress(payload, 6)).decode()
    return packed + "." + hmac.new(_key(), packed.encode(), hashlib.sha256).hexdigest()


def restore(api, result_id, receipt):
    if not isinstance(receipt, str) or len(receipt) > 1_000_000:
        raise ValueError("Invalid result receipt")
    packed, signature = receipt.rsplit(".", 1)
    expected = hmac.new(_key(), packed.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Result receipt signature is invalid; run a fresh check")
    decoder = zlib.decompressobj()
    payload = decoder.decompress(base64.urlsafe_b64decode(packed), 8_000_001)
    if len(payload) > 8_000_000 or not decoder.eof:
        raise ValueError("Invalid result receipt size")
    data = json.loads(payload)
    if data["id"] != result_id or data["exp"] < time.time():
        raise ValueError("Result receipt expired or does not belong to this result; check again")
    doc = data["doc"]
    con = api._catalog.connect()
    try:
        with con:
            con.execute("INSERT OR REPLACE INTO results VALUES (?,?,?,?)",
                        (result_id, data["fingerprint"], doc["result"]["checked_at"], db.dumps(doc)))
    finally:
        con.close()
    api._details(result_id)
