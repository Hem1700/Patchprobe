# LLM-Assisted Binary Patch Diffing — Implementation Document (CLI-First)

> **Purpose:** This document turns the design into a concrete, implementable plan with explicit modules, data schemas, CLI behavior, workflows, error handling, and test strategy. It is intentionally **defender-focused** and **non-exploitative**.

---

## 0) Scope and constraints

### 0.1 Product scope (explicit)
- **Primary deliverable:** a **CLI tool** that compares two versions of the same binary and generates an **auditable triage report**.
- **Secondary deliverables:** optional local daemon mode, extensible backends (diff, decompile, LLM), machine-readable artifacts, and reproducible outputs.

### 0.2 Non-goals (explicit)
- No exploit or payload generation.
- No remote scanning or unauthorized target analysis.
- No “zero-day” or offensive guidance.

### 0.3 Operating assumptions
- The user provides authorized binaries (pre/ post patch).
- The system may run **fully offline**.
- The system must produce **provenance** for all derived artifacts.

---

## 1) Repository structure

### 1.1 Top-level layout
```
/patchprobe
  /patchprobe
    __init__.py
    cli.py
    config.py
    constants.py
    errors.py
    logging.py
    paths.py

    /core
      pipeline.py
      job.py
      ingest.py
      normalize.py
      diff.py
      rank.py
      decompile.py
      packet.py
      llm.py
      validate.py
      report.py
      artifacts.py

    /backends
      /diff
        base.py
        diaphora.py
        ghidra_diff.py
        radare2.py
      /decompile
        base.py
        ghidra_headless.py
      /llm
        base.py
        local.py
        openai.py

    /models
      schemas.py
      db.py
      migrations

    /storage
      object_store.py
      filesystem_store.py

    /utils
      hashing.py
      filetype.py
      subprocess.py
      jsonschema.py
      retry.py
      time.py
      strings.py

  /scripts
    run_ghidra_headless.sh
    ghidra_decompile.py

  /tests
    /unit
    /integration
    /fixtures

  README.md
  Implementation_Doc.md
  pyproject.toml
```

### 1.2 Notes
- Default language: **Python 3.11+**.
- CLI entrypoint: `patchdiff`.
- Use `pyproject.toml` for packaging (Poetry or Hatch).

---

## 2) CLI specification

### 2.1 CLI entrypoints
- `patchdiff` (main CLI)
- optional `patchdiffd` (daemon / API)

### 2.2 CLI commands and behavior

#### 2.2.1 `patchdiff ingest`
**Purpose:** Register a job and compute metadata.

**Example:**
```
patchdiff ingest --a /path/before.bin --b /path/after.bin --tag KB1234 --out ./jobs/job_001
```

**Options:**
- `--a <path>`: input binary A (pre-patch)
- `--b <path>`: input binary B (post-patch)
- `--tag <string>`: optional tag (e.g., advisory ID)
- `--out <path>`: output job directory
- `--format <json|yaml>`: output metadata format

**Output:**
- Job directory with `job.json`, raw binary references, metadata artifacts

#### 2.2.2 `patchdiff diff`
**Purpose:** Run diff backend to match functions and compute deltas.

**Example:**
```
patchdiff diff --job ./jobs/job_001 --backend diaphora --out ./jobs/job_001
```

**Options:**
- `--job <path>`
- `--backend <diaphora|ghidra|radare2>`
- `--config <path>` optional backend config
- `--out <path>`

**Output:**
- `function_pairs.json`
- `diff_results.json`

#### 2.2.3 `patchdiff rank`
**Purpose:** Rank and select high-signal diffs.

**Example:**
```
patchdiff rank --job ./jobs/job_001 --top 30
```

**Options:**
- `--job <path>`
- `--top <int>`
- `--weights <path>` optional scoring config

**Output:**
- `ranked_candidates.json`

#### 2.2.4 `patchdiff decompile`
**Purpose:** Selectively decompile ranked candidates.

**Example:**
```
patchdiff decompile --job ./jobs/job_001 --top 30
```

**Options:**
- `--job <path>`
- `--top <int>`
- `--timeout <sec>` per function

**Output:**
- `decompile/<func_id>/pseudocode.txt`
- `decompile/<func_id>/metadata.json`

#### 2.2.5 `patchdiff analyze`
**Purpose:** LLM analysis on selected candidates.

**Example:**
```
patchdiff analyze --job ./jobs/job_001 --provider local --model llama3
```

**Options:**
- `--job <path>`
- `--provider <local|openai>`
- `--model <name>`
- `--max-rounds <int>`
- `--offline` force local only

**Output:**
- `analysis/<func_id>/llm.json`

#### 2.2.6 `patchdiff validate`
**Purpose:** Validate LLM output against evidence.

**Example:**
```
patchdiff validate --job ./jobs/job_001
```

**Output:**
- `validation/<func_id>/validation.json`

#### 2.2.7 `patchdiff report`
**Purpose:** Generate final report.

**Example:**
```
patchdiff report --job ./jobs/job_001 --format markdown
```

**Output:**
- `report.md` or `report.html` or `report.json`

#### 2.2.8 `patchdiff run`
**Purpose:** End-to-end pipeline in one command.

**Example:**
```
patchdiff run --a before.bin --b after.bin --top 30
```

---

## 3) Configuration

### 3.1 Config file
- Default path: `~/.config/patchdiff/config.yaml`
- User override: `--config <path>`

### 3.2 Example config
```yaml
storage:
  type: filesystem
  root: ~/.patchdiff

backends:
  diff: diaphora
  decompile: ghidra
  llm: local

ranking:
  top_n: 30
  weights:
    cfg_change: 0.3
    new_guard: 0.2
    string_signal: 0.1

llm:
  provider: local
  model: llama3
  max_rounds: 3

report:
  format: markdown
```

### 3.3 Config precedence
1. CLI flags
2. Job-local `job_config.json`
3. User config file
4. Defaults

---

## 4) Core pipeline (end-to-end)

### 4.1 Pipeline orchestration
Implement a `Pipeline` class that runs these stages with idempotent artifacts:
1. Ingest
2. Normalize
3. Diff
4. Rank
5. Decompile
6. LLM analysis
7. Validation
8. Report

Each stage:
- Reads inputs from job directory or object store
- Writes outputs to a stable path
- Produces `artifact.json` with metadata and hashes

### 4.2 Stage contracts
- Each stage must produce JSON artifacts with **strict schemas**.
- All artifacts must have:
  - `artifact_id`
  - `created_at`
  - `tool_version`
  - `inputs` (hashes of upstream artifacts)

---

## 5) Data models and schemas

### 5.1 Job schema
```json
{
  "job_id": "...",
  "tag": "KB1234",
  "created_at": "2026-02-08T12:00:00Z",
  "binary_a": {"sha256": "...", "path": "..."},
  "binary_b": {"sha256": "...", "path": "..."},
  "config": {"diff_backend": "diaphora"}
}
```

### 5.2 Function pair schema
```json
{
  "func_pair_id": "...",
  "func_id_a": "...",
  "func_id_b": "...",
  "match_score": 0.92,
  "evidence": ["hash match", "cfg similarity"],
  "status": "matched"
}
```

### 5.3 Diff result schema
```json
{
  "func_pair_id": "...",
  "change_summary": {
    "basic_blocks_added": 2,
    "basic_blocks_removed": 1,
    "branches_added": 1
  },
  "severity_hint": 0.7
}
```

### 5.4 Ranked candidate schema
```json
{
  "func_pair_id": "...",
  "rank": 3,
  "score": 0.86,
  "top_signals": [
    {"signal": "added_guard_clause", "evidence": "new early return"}
  ]
}
```

### 5.5 LLM output schema
```json
{
  "bug_class": "integer overflow / truncation",
  "confidence": 0.72,
  "evidence": [
    {"type": "before", "snippet": "...", "location": "func.c:123"}
  ],
  "reachability_notes": ["Called by handler X"],
  "recommended_validation": ["Test len == max+1"],
  "safety": {"no_exploit_steps": true}
}
```

---

## 6) Diff backend implementation

### 6.1 Backend interface
```python
class DiffBackend(Protocol):
    def analyze(self, binary_path: str, out_dir: str) -> AnalysisArtifact: ...
    def match(self, a_analysis: AnalysisArtifact, b_analysis: AnalysisArtifact) -> list[FunctionPair]: ...
    def diff(self, pairs: list[FunctionPair]) -> list[DiffResult]: ...
```

### 6.2 Diaphora backend (IDA)
- Execute IDA headless script to generate SQLite.
- Parse SQLite into `FunctionPair` objects.
- Extract CFG, strings, hashes, and match score.

### 6.3 Ghidra backend
- Use Ghidra Version Tracking.
- Export results to JSON.
- Map to unified schema.

### 6.4 Radare2 backend
- Use `radiff2` for function matching.
- Parse textual output into structured data.

### 6.5 Backend output normalization
- Convert all backends into common model.
- Normalize function IDs to stable `func_id` using:
  - `binary_sha256` + `function_start_address` + `symbol_name`

---

## 7) Candidate ranking

### 7.1 Features
- CFG complexity delta
- New/removed branches
- New error paths
- String change signals
- Reachability (exports, handlers)
- Match confidence

### 7.2 Scoring
```python
score = sum(weight[signal] * value(signal))
score *= match_score
```

### 7.3 Ranking output
- Provide top N candidates with reasoning.
- Include raw signal values for auditability.

---

## 8) Decompile service

### 8.1 Interface
```python
class DecompileBackend(Protocol):
    def decompile(self, binary_path: str, func_ids: list[str], out_dir: str) -> list[DecompileArtifact]: ...
```

### 8.2 Ghidra headless
- Use `analyzeHeadless` with custom script.
- For each func address:
  - Decompile and export pseudo-C
  - Extract prototype, callers, callees

### 8.3 Failure handling
- On timeout or failure:
  - fallback to assembly extraction
  - record `decompile_status = failed`

---

## 9) Prompt packet builder

### 9.1 Responsibilities
- Build strict JSON packets for LLM input.
- Include before/after pseudocode, metadata, and questions.

### 9.2 Packet structure
- `binary_a` and `binary_b` metadata
- `function` metadata
- `diff` (pseudo + notes)
- `required_output_schema`

---

## 10) LLM analysis service

### 10.1 Provider interface
```python
class LLMProvider(Protocol):
    def analyze(self, packet: dict, config: LLMConfig) -> dict: ...
```

### 10.2 Local provider
- Use llama.cpp or similar local inference.
- Strict JSON output enforced.

### 10.3 Hosted provider
- Use OpenAI or other provider (optional).
- Enforce system prompt to block exploit output.

### 10.4 Multi-round analysis
- Round 1: classification
- Round 2: critique
- Round 3: reconciliation
- Round 4: final verdict

---

## 11) Validation engine

### 11.1 Structural checks
- Ensure references exist in pseudocode.
- Ensure claimed changes match diff markers.

### 11.2 Heuristic checks
- Bounds check added?
- Null check added?
- Integer widening?

### 11.3 Scoring
Combine:
- LLM confidence
- validation pass rate
- match confidence

---

## 12) Report generation

### 12.1 Formats
- Markdown (default)
- HTML (optional)
- JSON (machine)

### 12.2 Required sections
- Job metadata
- Ranked candidates
- Evidence diff
- Bug class + confidence
- Validation checklist
- Audit log

---

## 13) Logging and observability

### 13.1 Logging structure
- JSON logs for machine parsing
- Log levels: DEBUG, INFO, WARN, ERROR

### 13.2 Job audit log
- Every stage must log input hash and output hash
- Record tool versions and configs

---

## 14) Security considerations

- Local-only mode by default
- Redaction option for sensitive strings
- Enforce explicit user confirmation for hosted LLM

---

## 15) Testing strategy

### 15.1 Unit tests
- Hashing, config parsing, schema validation

### 15.2 Integration tests
- Known patch pairs
- Verify rank ordering

### 15.3 Regression tests
- Ensure stability of schemas
- Ensure non-exploit guardrails

---

## 16) Release packaging

- Package as `patchdiff`
- Provide Homebrew formula (optional)
- Provide Docker image for reproducible environment

---

## 17) Implementation roadmap

### Phase 0
- CLI skeleton
- Ingest + metadata
- Diff backend (single)
- Rank + report (JSON)

### Phase 1
- Selective decompile
- LLM analysis (single-round)
- Validation engine

### Phase 2
- Multi-backend support
- Multi-round LLM
- HTML report

### Phase 3
- Daemon/API
- RBAC + audit logs

---

## 18) Open questions

- Which diff backend will be primary (IDA/Diaphora vs Ghidra)?
- Do you want local-only by default, or allow hosted LLM by default?
- What level of report detail is needed for initial MVP?

