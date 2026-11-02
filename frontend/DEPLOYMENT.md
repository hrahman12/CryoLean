# Real hosted backend deployment

Public URL: https://frontend-pied-five-58.vercel.app/

The production deployment includes FastAPI, the canonical CryoLeanAPI, Z3, the
source-backed catalog and a Linux build of the actual Lean 4.35.0 checker.
Anonymous requests were tested against /api/health, /api/check and /api/bridge,
including the complete FAIL -> verified repair -> fresh PASS loop.

## Reproduce

Build the Linux checker and its actual kernel audit first, using Linux or WSL:

```powershell
wsl -d Ubuntu -- bash /mnt/c/Users/Rahma/CryoLean/scripts/build_linux_backend.sh
npm run deploy
```

On Linux use `bash scripts/build_linux_backend.sh`. The script downloads the
pinned official Lean release, compiles the unchanged project, runs its real
selftest and audits 48 theorems. Only standard axioms are accepted.

`npm run deploy` regenerates the frontend catalog/assets, builds React, packages
Vercel Build Output API v3 static assets and a real Python function, then deploys
the prebuilt artifact. It requires an authenticated Vercel CLI project.

Configure CRYOLEAN_RECEIPT_KEY once as a secret production environment variable.
It is already configured on this project. Do not put its value in source files.
It signs bounded result receipts so cold instances can restore an authentic
record. Apply Fix always executes Lean again; a signed receipt is not a proof.

The compiled ELF exceeds Vercel's individual upload limit, so the package stores
it as gzip and an SHA-256 digest. Cold initialization verifies and extracts the
identical binary into /tmp, then executes it. The binary's actual hash is used
by the source hash and theorem audit. The runtime bundle is approximately
122.5 MiB, without the full Lean toolchain, local DB, credentials or AI packages.

Requests use the same-origin /api/bridge allowlist. Trusted catalog registration,
Gatekeeper execution and inline equipment modification are not public web
operations. Exact input/catalog fingerprints and checker hashes reject stale
repairs. Temporary hosted result state is carried by authenticated receipts.

An unavailable or failing backend returns an error with no verdict. The live
button is disabled while disconnected. There is no recorded-result fallback
for live checks.

Run `python scripts/test_hosted_backend.py` to repeat the anonymous smoke test.
Local generated results are in frontend/test-results/hosted.json (ignored).
Final verified production deployment: dpl_3DbtKZcuShsqGUuCzQxj8xhPDTtV. The public alias was tested anonymously after deployment; all seven hosted checks passed.
