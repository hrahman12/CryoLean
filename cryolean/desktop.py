"""Desktop host: opens the Codex-built frontend in a native window and exposes CryoLeanAPI to it.

    pip install pywebview
    python -m cryolean.desktop --frontend frontend\\dist\\index.html

This file contains no GUI of its own; it only connects the separately developed frontend to the local
Python backend (window.pywebview.api.*). Without --frontend it opens a minimal status page.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bridge import CryoLeanAPI

STATUS_PAGE = """<!doctype html><meta charset="utf-8"><title>CryoLean backend</title>
<body style="font-family:system-ui;margin:2rem"><h1>CryoLean backend is running</h1>
<p>Point <code>--frontend</code> at the Codex frontend build (frontend/dist/index.html) to load the user interface.</p><pre id="s">checking Lean…</pre>
<script>window.addEventListener('pywebviewready', async () => {
  const r = await window.pywebview.api.get_lean_status();
  document.getElementById('s').textContent = JSON.stringify(r.ok ? r.data : r.error, null, 2);
});</script></body>"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CryoLean desktop host (PyWebView)")
    ap.add_argument("--frontend", help="path or URL of the Codex frontend entry page (frontend/dist/index.html)")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)
    try:
        import webview
    except ImportError:
        print("PyWebView is not installed: pip install pywebview")
        return 1
    frontend = a.frontend
    if frontend and "://" not in frontend:
        # PyWebView resolves relative paths against the entry script, not the working directory
        p = Path(frontend).expanduser().resolve()
        if not p.is_file():
            print(f"Frontend not found at {p}. Build it first: npm ci --prefix frontend && npm run build --prefix frontend")
            return 1
        frontend = str(p)
    api = CryoLeanAPI()
    # "Save report" in the GUI downloads a PDF/JSON file; PyWebView blocks downloads unless this is on.
    webview.settings["ALLOW_DOWNLOADS"] = True
    if frontend:
        webview.create_window("CryoLean", frontend, js_api=api, width=1360, height=900, min_size=(960, 640))
    else:
        webview.create_window("CryoLean", html=STATUS_PAGE, js_api=api, width=900, height=700)
    # Serve local files over PyWebView's built-in HTTP server so the built frontend (ES modules) loads
    # from absolute and relative paths alike, on macOS (WebKit) and Windows (WebView2).
    webview.start(debug=a.debug, http_server=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
