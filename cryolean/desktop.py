"""Desktop host: opens the Antigravity-built frontend in a native window and exposes CryoLeanAPI to it.

    pip install pywebview
    python -m cryolean.desktop --frontend path\\to\\antigravity\\dist\\index.html

This file contains no GUI of its own; it only connects the separately developed frontend to the local
Python backend (window.pywebview.api.*). Without --frontend it opens a minimal status page.
"""
from __future__ import annotations

import argparse
import sys

from .bridge import CryoLeanAPI

STATUS_PAGE = """<!doctype html><meta charset="utf-8"><title>CryoLean backend</title>
<body style="font-family:system-ui;margin:2rem"><h1>CryoLean backend is running</h1>
<p>Point <code>--frontend</code> at the Antigravity build to load the user interface.</p><pre id="s">checking Lean…</pre>
<script>window.addEventListener('pywebviewready', async () => {
  const r = await window.pywebview.api.get_lean_status();
  document.getElementById('s').textContent = JSON.stringify(r.ok ? r.data : r.error, null, 2);
});</script></body>"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CryoLean desktop host (PyWebView)")
    ap.add_argument("--frontend", help="path or URL of the Antigravity frontend entry page (index.html)")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)
    try:
        import webview
    except ImportError:
        print("PyWebView is not installed: pip install pywebview")
        return 1
    api = CryoLeanAPI()
    if a.frontend:
        webview.create_window("CryoLean", a.frontend, js_api=api, width=1280, height=840)
    else:
        webview.create_window("CryoLean", html=STATUS_PAGE, js_api=api, width=900, height=700)
    webview.start(debug=a.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
