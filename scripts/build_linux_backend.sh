#!/usr/bin/env bash
# Build the same trusted Lean sources for the Linux hosted runtime.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
scratch="$repo/.tools/linux-backend"
mkdir -p "$scratch"
version="$(sed -n 's/.*:v//p' "$repo/lean/lean-toolchain" | tr -d '\r')"
if [ ! -x "$scratch/lean-$version-linux/bin/lake" ]; then
  curl -fL --retry 3 "https://github.com/leanprover/lean4/releases/download/v$version/lean-$version-linux.tar.zst" -o "$scratch/toolchain.tar.zst"
  tar --zstd -xf "$scratch/toolchain.tar.zst" -C "$scratch"
fi
export PATH="$scratch/lean-$version-linux/bin:$PATH"
mkdir -p "$scratch/project/CryoLean"
cp "$repo/lean/"*.lean "$repo/lean/lakefile.toml" "$repo/lean/lean-toolchain" "$scratch/project/"
cp "$repo/lean/CryoLean/"*.lean "$scratch/project/CryoLean/"
cd "$scratch/project"
lake build
.lake/build/bin/cryolean selftest
ldd .lake/build/bin/cryolean || true
cp .lake/build/bin/cryolean "$scratch/cryolean"
lake env lean Audit.lean > "$scratch/axioms.txt"
python3 - "$scratch" <<'PY'
import hashlib, json, re, sys
from pathlib import Path
p = Path(sys.argv[1]); project = p / 'project'
h = hashlib.sha256()
for f in sorted((project/'CryoLean').glob('*.lean'))+[project/'Main.lean']:
    h.update(f.name.encode()); h.update(f.read_bytes())
h.update((p/'cryolean').read_bytes())
theorems={}
for line in (p/'axioms.txt').read_text().splitlines():
    m=re.match(r"'CryoLean\.([^']+)' (depends on axioms: \[(.*)\]|does not depend on any axioms)",line.strip())
    if m: theorems[m[1]]=[a.strip() for a in (m[3] or '').split(',') if a.strip()]
standard={'propext','Classical.choice','Quot.sound'}
assert len(theorems)>=48 and all(set(a)<=standard for a in theorems.values())
(p/'audit-axioms.json').write_text(json.dumps({'source_hash':h.hexdigest(),'standard_axioms':sorted(standard),'theorems':theorems,'all_standard':True,'count':len(theorems)},indent=2))
print('Linux kernel audit:',len(theorems),'theorems, standard axioms only')
PY
printf 'Linux checker ready: %s\n' "$scratch/cryolean"
