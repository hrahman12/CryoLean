"""Shared fixtures. Real-data tests use the real SQLite catalog built from data/ and the real Lean binary.
Tests that write (registration, promotion, modifications) use a temporary copy of the database.
Synthetic fixtures are explicitly marked as such in the tests that use them."""
import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryolean import config, db  # noqa: E402


@pytest.fixture(scope="session")
def built_db(tmp_path_factory):
    p = tmp_path_factory.mktemp("db") / "cryolean.db"
    db.build_database(db_path=p)
    return p


@pytest.fixture(scope="session")
def lean_available():
    if not config.lean_binary_path().exists():
        pytest.fail(f"Lean checker binary missing at {config.lean_binary_path()}; run `lake build` in lean/")
    return True


@pytest.fixture(scope="session")
def api(built_db, lean_available):
    from cryolean.bridge import CryoLeanAPI
    return CryoLeanAPI(str(built_db))


@pytest.fixture()
def fresh_api(built_db, tmp_path, lean_available):
    from cryolean.bridge import CryoLeanAPI
    p = tmp_path / "copy.db"
    shutil.copy(built_db, p)
    return CryoLeanAPI(str(p))


def data(env):
    assert env["ok"], env.get("error")
    return env["data"]


def check(api, exp, cfg, **kw):
    kw.setdefault("confirmed", True)
    return data(api.check_compatibility(exp, cfg, **kw))


def outcome(result, key):
    for c in result["checks"]:
        if key in c["keys"] or "/".join(c["keys"]) == key:
            return c["outcome"]
    for c in result["coupled_checks"]:
        if c["model"] == key or c["id"].startswith(key):
            return c["outcome"]
    raise KeyError(key)
