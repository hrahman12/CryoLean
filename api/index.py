"""Hosted entrypoint; same FastAPI / CryoLeanAPI / Lean / Z3 as local runs."""
import os
import gzip
import hashlib
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("CRYOLEAN_DB", "/tmp/cryolean-hosted.db")
os.environ.setdefault("CRYOLEAN_AI_PROVIDER", "lexical")
digest=(ROOT / 'lean/bin/cryolean.sha256').read_text().strip()
binary=Path(tempfile.gettempdir())/f'cryolean-{digest[:16]}'
if not binary.exists():
    target=binary.with_name(binary.name+f'.{os.getpid()}.tmp')
    with gzip.open(ROOT/'lean/bin/cryolean.gz','rb') as source, target.open('wb') as output:
        shutil.copyfileobj(source,output)
    if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
        raise RuntimeError('Hosted Lean binary integrity check failed')
    target.chmod(0o755)
    os.replace(target,binary)
os.environ.setdefault("CRYOLEAN_LEAN_BIN", str(binary))
from cryolean.server import app
