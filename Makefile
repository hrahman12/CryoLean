# CryoLean: one-command install and run (macOS and Linux).
#
#   make install && make run
#
# install: Python venv + requirements, Lean toolchain (elan) + `lake build` of the checker,
#          the SQLite catalog, and the React GUI (frontend/dist).
# run:     opens the desktop app (PyWebView window, the GUI talks to the local Python/Lean backend).
#
# Windows: use the PowerShell steps in README.md (Setup on Windows).

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Paths are relative to the repository root (run make from there), so folders with spaces work.
VENV     := .venv
PY       := $(VENV)/bin/python
PIP      := $(PY) -m pip
UNAME_S  := $(shell uname -s)
ELAN_BIN := $(HOME)/.elan/bin
export PATH := $(ELAN_BIN):/opt/homebrew/bin:/usr/local/bin:$(PATH)

# First Python >= 3.11 found on PATH (macOS ships 3.9 as python3, so look for newer ones first).
PYTHON_SYS := $(shell for p in python3.13 python3.12 python3.11 python3; do \
	  if command -v $$p >/dev/null 2>&1 && $$p -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then command -v $$p; break; fi; done)

FRONTEND_DIST := frontend/dist/index.html
LEAN_BIN      := lean/.lake/build/bin/cryolean
DB            := data/cryolean.db

.PHONY: help install run deps python lean db frontend dev test test-e2e clean

help:
	@echo "CryoLean"
	@echo "  make install    install everything (Python venv, Lean checker, catalog DB, GUI)"
	@echo "  make run        open the CryoLean desktop app"
	@echo "  make dev        GUI with hot reload in a browser (dev bridge on :8765 + Vite on :5173)"
	@echo "  make test       backend tests (fast) + GUI end-to-end tests against the real backend"
	@echo "  make clean      remove build outputs (venv, Lean build, DB, frontend dist and node_modules)"

# ---------------------------------------------------------------- install
install: deps python lean db frontend
	@echo ""
	@echo "CryoLean is installed. Start it with:  make run"

deps:
ifeq ($(UNAME_S),Darwin)
	@if [ -z "$(PYTHON_SYS)" ] || ! command -v npm >/dev/null 2>&1; then \
	  if ! command -v brew >/dev/null 2>&1; then \
	    echo "Python >= 3.11 and Node.js are required. Install Homebrew (https://brew.sh) or install them manually, then re-run make install."; exit 1; \
	  fi; \
	fi
	@if [ -z "$(PYTHON_SYS)" ]; then echo "Installing Python 3.12 with Homebrew"; brew install python@3.12; fi
	@if ! command -v npm >/dev/null 2>&1; then echo "Installing Node.js with Homebrew"; brew install node; fi
else
	@if [ -z "$(PYTHON_SYS)" ]; then echo "Python >= 3.11 is required (e.g. sudo apt install python3.12 python3.12-venv)."; exit 1; fi
	@command -v npm >/dev/null 2>&1 || { echo "Node.js (npm) is required: https://nodejs.org or your package manager."; exit 1; }
endif
	@if ! command -v elan >/dev/null 2>&1; then \
	  echo "Installing elan (Lean toolchain manager)"; \
	  curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none; \
	fi
	@echo "Prerequisites OK"

python: $(PY)
$(PY):
	@PYBIN="$(PYTHON_SYS)"; [ -n "$$PYBIN" ] || PYBIN="$$(command -v python3.12 || command -v python3)"; \
	  echo "Creating virtual environment with $$PYBIN"; "$$PYBIN" -m venv "$(VENV)"
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -r requirements.txt --quiet
	@echo "Python dependencies installed"

lean: $(LEAN_BIN)
$(LEAN_BIN):
	@echo "Building the Lean checker (first build downloads Lean $$(cat lean/lean-toolchain | cut -d: -f2); this can take a few minutes)"
	cd lean && lake build

db: $(DB)
$(DB): $(PY)
	$(PY) -m cryolean build-db

frontend: $(FRONTEND_DIST)
$(FRONTEND_DIST): $(wildcard frontend/src/*.* frontend/src/*/*.*) frontend/package.json frontend/package-lock.json docs/codex/cryolean-client.js
	cd frontend && npm ci --no-audit --no-fund && npm run build

# ---------------------------------------------------------------- run
run:
	@[ -x "$(PY)" ] && [ -f "$(LEAN_BIN)" ] && [ -f "$(DB)" ] && [ -f "$(FRONTEND_DIST)" ] || { echo "Not installed yet. Run: make install"; exit 1; }
	$(PY) -m cryolean.desktop --frontend "$(FRONTEND_DIST)"

# ---------------------------------------------------------------- development
dev: $(PY)
	@echo "GUI: http://127.0.0.1:5173   (uses the real backend through scripts/dev_bridge.py)"
	@trap 'kill 0' EXIT; $(PY) scripts/dev_bridge.py --port 8765 & cd frontend && npx vite --host 127.0.0.1

test: $(PY)
	$(PY) -m pytest -m "not slow" -q
	$(MAKE) test-e2e

test-e2e: $(FRONTEND_DIST)
	cd frontend && npx playwright install chromium && CRYOLEAN_PYTHON="$(abspath $(PY))" npx playwright test

clean:
	rm -rf "$(VENV)" lean/.lake/build frontend/dist frontend/node_modules frontend/test-results "$(DB)"
