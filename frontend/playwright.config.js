// End-to-end tests of the GUI against the REAL backend (Lean checker, Z3, SQLite catalog).
// Starts scripts/dev_bridge.py (the CryoLeanAPI over localhost) and a static preview of frontend/dist.
// Prerequisites: `make install` (or: venv + requirements, `lake build`, `python -m cryolean build-db`, `npm run build`).
import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const venvPy = process.platform === "win32" ? path.join(root, ".venv", "Scripts", "python.exe") : path.join(root, ".venv", "bin", "python");
const python = process.env.CRYOLEAN_PYTHON || (existsSync(venvPy) ? venvPy : "python3");

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 60_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:4173",
    viewport: { width: 1360, height: 900 },
    acceptDownloads: true,
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `"${python}" "${path.join(root, "scripts", "dev_bridge.py")}" --port 8765`,
      url: "http://127.0.0.1:8765/health",
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: "npx vite preview --port 4173 --strictPort --host 127.0.0.1",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
});
