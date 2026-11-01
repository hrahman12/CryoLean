// Development / test only. Inside the desktop app, PyWebView injects window.pywebview.api.
// In a normal browser (npm run dev, Playwright) this installs the same API surface, forwarding each
// call to scripts/dev_bridge.py, which runs the real CryoLeanAPI (Lean + Z3 + SQLite) on localhost.
// The envelope ({ok, data} / {ok:false, error}) is passed through unchanged; nothing is computed here.

export function installDevBridgeIfRequested() {
  if (window.pywebview?.api) return null;
  const params = new URLSearchParams(window.location.search);
  let base = params.get("bridge");
  if (!base && import.meta.env.DEV) base = import.meta.env.VITE_BRIDGE_URL || "http://127.0.0.1:8765";
  if (!base) return null;
  base = base.replace(/\/$/, "");
  const api = new Proxy(
    {},
    {
      get(_t, method) {
        if (typeof method !== "string" || method === "then") return undefined;
        return async (...args) => {
          try {
            const res = await fetch(`${base}/rpc/${method}`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ args }),
            });
            return await res.json();
          } catch (e) {
            return { ok: false, error: { code: "bridge_unreachable", message: `Development bridge not reachable at ${base}: ${e.message}`, verdict: null } };
          }
        };
      },
    },
  );
  window.pywebview = { api };
  window.dispatchEvent(new Event("pywebviewready"));
  return base;
}
