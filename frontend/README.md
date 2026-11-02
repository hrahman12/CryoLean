# CryoLean frontend

One three-card WebGL website, with Live checker and Demos · recorded runs tabs.

The canonical catalog currently contains 20 industries, 204 experiment profiles
and 220 configurations. `npm run build` regenerates the read-only fallback
catalog from CryoLeanAPI; a connected browser loads the current backend catalog.
No compatibility outcomes are embedded in that fallback catalog.

Run the complete website and backend:

```powershell
pip install -r requirements.txt
npm ci --prefix frontend
npm run build
python -m cryolean serve --port 8000
```

Open http://127.0.0.1:8000. The Lean binary must be built as described in the root
README. A busy port can be replaced with any available port.

For Vite development, run the backend separately and set CRYOLEAN_DEV_API to its
origin before `npm run dev`. The default development backend is port 8000.
PyWebView remains supported through the same canonical client.

After confirming requirements, a live check calls the real Lean checker. A
separate automatic Z3 search exposes only complete candidates that have already
passed Lean. Apply Fix rechecks the server-held exact candidate and verifies its
input hash before applying it. The original result remains available. Neither
repair generation nor explanations need an external AI service.

Recorded playback uses the same ConfiguratorCards, viewer and explanation
components. Its artifacts are actual engine runs from
`scripts/record_frontend_demos.py`, explicitly labeled historical. Recorded
verdicts never enter the live setup reducer. The four README workflows include
the 14 T UNKNOWN diagnostic, the 39-line repair, the two/three probe-arm
comparison, and the validated 23-hour campaign.

All 204 profiles have apparatus descriptors. There are 39 instrument geometry
families and 41 experiment mechanisms, with source construction notes for 60
featured configurations. These are illustrative procedural models, not certified
CAD. Unpublished dimensions remain unknown. Source geometry is presentation
metadata and never becomes a verification specification.

See DEPLOYMENT.md, TEST_REPORT.md and INTEGRATION_AUDIT.md.
