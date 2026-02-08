# PatchProbe Task List

**Decisions First**
- [ ] Pick MVP diff backend: `diaphora` (IDA) or `ghidra` (Version Tracking)
- [ ] Decide default LLM mode: `local-only` vs `hosted-allowed` with explicit opt-in
- [ ] Set MVP report verbosity and top-N default

**Project Wiring**
- [ ] Confirm package name and install flow (`pip install -e .`) and verify `patchdiff` entrypoint
- [ ] Add `Makefile` or `scripts/` helpers for common tasks (run, test, lint)
- [ ] Add `CHANGELOG.md` and versioning policy

**Config and CLI**
- [ ] Implement environment variable overrides: `PATCHDIFF_CONFIG`, `PATCHDIFF_LOG_LEVEL`, `PATCHDIFF_OFFLINE`
- [ ] Add config schema validation on startup (`specs/schemas/config.schema.json`)
- [ ] Expand CLI help text with examples per command
- [ ] Add CLI error mapping to exit codes with explicit error details

**Artifact Framework**
- [ ] Implement central `write_artifact(...)` that writes envelope + payload and validates schema
- [ ] Add artifact hashing of payload for reproducibility
- [ ] Add `artifact_index.json` per job recording created artifacts with timestamps and hashes

**Ingest Stage**
- [ ] Validate binary paths and file sizes early; record errors with code 20/30
- [ ] Expand file type detection for Mach-O CPU subtypes and ELF archs
- [ ] Record build IDs where available (ELF `.note.gnu.build-id`, PE debug directory)
- [ ] Write full ingest artifacts with schema validation

**Normalize Stage**
- [ ] Extract section tables, import/export info, symbol presence, debug info status
- [ ] Add signature and certificate detection for PE
- [ ] Persist `normalized_metadata.json` and per-binary normalization summaries

**Diff Stage**
- [ ] Implement chosen backend end-to-end
- [ ] Implement headless analysis orchestration
- [ ] Parse backend output to `function_pairs.json` and `diff_results.json`
- [ ] Implement stable `func_id` generation
- [ ] Add backend execution logs and timeout handling
- [ ] Write diff artifacts with schema validation

**Ranking Engine**
- [ ] Implement feature extraction from `diff_results` and normalized metadata
- [ ] Add CFG complexity deltas and branch deltas
- [ ] Add string-signal extraction (error/invalid/bounds)
- [ ] Apply weighted scoring and produce ranked candidates with reasons
- [ ] Persist `ranked_candidates.json` with schema validation

**Decompile Stage**
- [ ] Implement Ghidra headless orchestration
- [ ] Add project creation and import
- [ ] Implement function selection and decompilation
- [ ] Export pseudo-C and metadata
- [ ] Add per-function timeouts and fallback to assembly
- [ ] Persist `decompile/<func_id>/metadata.json` and `pseudocode.txt`

**Packet Builder**
- [ ] Build structured prompt packets with strict JSON envelope
- [ ] Include before/after pseudocode, diff summary, and metadata
- [ ] Validate packets against `llm_output.schema.json` requirements

**LLM Analysis**
- [ ] Implement local provider integration (llama.cpp or equivalent)
- [ ] Implement hosted provider with explicit opt-in and redaction support
- [ ] Enforce strict JSON output and safety policy checks
- [ ] Add multi-round analysis option and store per-round outputs

**Validation Engine**
- [ ] Structural checks: verify snippets exist in pseudo-C and diff markers
- [ ] Heuristic checks: new bounds checks, null checks, integer widening
- [ ] Compute validation score and merge with LLM confidence + match score

**Report Generation**
- [ ] Build Markdown report with required sections and ranked candidates
- [ ] Add JSON report for integration consumers
- [ ] Optional HTML report with lightweight template

**Storage and Cache**
- [ ] Implement object store abstraction with filesystem backend
- [ ] Add caching for repeated diff/decompile outputs by binary hash

**Logging and Audit**
- [ ] Job-scoped JSON logs with `job_id`, `stage`, `event`
- [ ] Audit log entries for every stage including input/output hashes

**Testing**
- [ ] Unit tests for hashing, file type detection, config loading
- [ ] Integration tests with known patch pairs (fixtures)
- [ ] Schema validation tests for every artifact type

**CI and Quality**
- [ ] Add linting (`ruff` or `flake8`) and formatting (`black` or `ruff format`)
- [ ] Add `pytest` CI workflow
- [ ] Add `pre-commit` hooks (optional)
