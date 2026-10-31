import copy
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from backend import config  # noqa: E402
from backend.api import app  # noqa: E402
from backend.catalog import Catalog  # noqa: E402
from backend.research_pipeline import ResearchPipeline  # noqa: E402
from backend.sessions import SessionStore  # noqa: E402


@pytest.fixture(scope="session")
def lean_available():
    if not config.lean_binary_path().exists():
        pytest.fail(f"Lean checker binary missing at {config.lean_binary_path()}; run `lake build` in lean/")
    return True


@pytest.fixture(scope="session")
def catalog():
    return Catalog()


@pytest.fixture()
def client(lean_available):
    return TestClient(app)


@pytest.fixture()
def tmp_client(tmp_path, lean_available):
    """A client whose catalog lives in a temporary copy of data/ (for registration / promotion tests)."""
    data = tmp_path / "data"
    shutil.copytree(ROOT / "data", data, ignore=shutil.ignore_patterns("candidates", "research_requests", "registry"))
    old = (app.state.catalog, app.state.pipeline, app.state.sessions, app.state.matcher)
    cat = Catalog(data)
    app.state.catalog = cat
    app.state.pipeline = ResearchPipeline(cat, data / "research_requests", data / "candidates")
    app.state.sessions = SessionStore()
    app.state.matcher = None
    try:
        yield TestClient(app), cat, data
    finally:
        app.state.catalog, app.state.pipeline, app.state.sessions, app.state.matcher = old


def verify(client, experiment_id, configuration_id, confirmed=True, **kw):
    r = client.post("/verify", json={"experiment_id": experiment_id, "configuration_id": configuration_id,
                                     "confirmed": confirmed, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def outcome(result, key):
    return next(c["outcome"] for c in result["checks"] if c["key"] == key)
