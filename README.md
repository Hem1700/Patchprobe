# PatchProbe

CLI-first tool for defender-focused binary patch diffing with LLM-assisted triage.

## Quickstart
- `python3 -m venv .venv`
- `. .venv/bin/activate`
- `python -m pip install -e .`
- `python -m pytest -q`

## Getting Test Binaries
- This repo does not ship sample `.bin` files.
- You can create quick local test binaries by compiling two tiny C programs (before/after):

```bash
cat > before.c <<'EOF'
#include <stdio.h>
int main(void) { puts("before"); return 0; }
EOF

cat > after.c <<'EOF'
#include <stdio.h>
int main(void) { puts("after"); return 0; }
EOF

cc -O2 -o before before.c
cc -O2 -o after after.c
```

## Commands
- `patchdiff ingest --a <before> --b <after> --out <job_dir>`
- `patchdiff normalize --job <job_dir>`
- `patchdiff diff --job <job_dir> --backend diaphora`
- `patchdiff rank --job <job_dir> --top 30`
- `patchdiff decompile --job <job_dir> --top 30 --timeout 90`
- `patchdiff analyze --job <job_dir> --provider local --model llama3 --max-rounds 2`
- `patchdiff validate --job <job_dir>`
- `patchdiff report --job <job_dir> --format markdown`
- `patchdiff run --a <before> --b <after> --out <job_dir> --format json`

## Run PatchProbe / Patchdiff
- After install, run via console entrypoint:

```bash
patchdiff run --a ./before --b ./after --out ./job_001 --format json
```

- Or run via module path:

```bash
python -m patchprobe.cli run --a ./before --b ./after --out ./job_001 --format json
```

## Artifacts
- Stage outputs are written under `<job_dir>/artifacts/`.
- Every stage also writes envelope artifacts with hashes and schema checks.
- Job-level indexes/logs:
  - `<job_dir>/artifact_index.json`
  - `<job_dir>/audit.jsonl`

See `Implementation_Doc.md` for detailed architecture and contracts.
