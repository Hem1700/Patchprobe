# Changelog

## 0.1.0
- Added end-to-end CLI pipeline with `ingest`, `normalize`, `diff`, `rank`, `decompile`, `analyze`, `validate`, `report`, and `run`.
- Added artifact envelope framework with schema validation, payload hashing, and `artifact_index.json`.
- Added normalization metadata extraction for PE/ELF and binary deltas.
- Added symbol-based diff backend (`diaphora` path via `nm`) with stable function IDs.
- Added weighted ranking engine and candidate scoring.
- Added decompile stage candidate expansion and headless Ghidra runner integration with fallback behavior.
- Added packet-driven LLM analysis, multi-round output support, and schema-compatible outputs.
- Added validation checks (evidence grounding, safety, bug-class alignment) with per-candidate validation scoring.
- Added blended report generation for Markdown/JSON outputs.
- Added audit log entries per stage in `audit.jsonl`.
- Added unit and integration tests and CI-ready project tooling.
