# LLM-Assisted Binary Patch Diffing — Implementation Document (CLI-First, Very Detailed)

> **Purpose:** This document turns the design into concrete engineering work with explicit modules, data schemas, CLI contracts, stage I/O, error codes, and test strategy. The system is **defender-focused** and **non-exploitative**.

---

## 0) Summary and guiding principles

### 0.1 Deliverable summary
- A **CLI tool** named `patchdiff` that compares two versions of the same binary and generates an **auditable triage report**.
- A **reproducible pipeline** with stable artifacts for each stage.
- A **pluggable architecture** for diffing, decompilation, and LLM analysis.

### 0.2 Core invariants
- Raw binaries are **never modified**.
- Every derived artifact is **hash-addressed** and **traceable** to inputs.
- All LLM outputs must be **structured JSON** and **evidence-backed**.
- Safety policy prohibits exploit guidance and operationalization.

### 0.3 Non-goals
- No offensive exploit generation.
- No remote target scanning.
- No ingestion of untrusted binaries without explicit user authorization.

---

## 1) Terminology and data types

### 1.1 Terminology
- **Binary A**: Pre-patch binary.
- **Binary B**: Post-patch binary.
- **Function pair**: A matched function between A and B.
- **Candidate**: A function pair selected for decompilation and LLM analysis.
- **Artifact**: Any output file produced by a pipeline stage.

### 1.2 Standard fields
All artifacts share a common metadata envelope:
```json
{
  "artifact_id": "uuid",
  "artifact_type": "string",
  "created_at": "ISO-8601",
  "tool_version": "string",
  "inputs": {
    "binary_a_sha256": "...",
    "binary_b_sha256": "...",
    "upstream_artifact_hashes": ["..."]
  }
}
```

---

## 2) Repository structure

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
      migrations/

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

  /specs
    /schemas
      artifact.schema.json
      job.schema.json
      function_pair.schema.json
      diff_result.schema.json
      ranked_candidate.schema.json
      decompile_artifact.schema.json
      llm_output.schema.json
      validation_result.schema.json
      report.schema.json
      config.schema.json

  /tests
    /unit
    /integration
    /fixtures

  README.md
  Implementation_Doc.md
  pyproject.toml
```

---

## 3) CLI specification (contract-level detail)

### 3.1 Command: `patchdiff ingest`
**Purpose:** Create a job record and compute initial binary metadata.

**Inputs:**
- `--a <path>`: binary A (required)
- `--b <path>`: binary B (required)
- `--tag <string>`: optional advisory/tag
- `--out <path>`: job directory (required)

**Outputs:**
- `<job>/job.json`
- `<job>/artifacts/ingest/metadata_a.json`
- `<job>/artifacts/ingest/metadata_b.json`

**Exit codes:**
- `0`: success
- `10`: invalid CLI args
- `20`: file not found
- `30`: hash/metadata failure

### 3.2 Command: `patchdiff diff`
**Purpose:** Run diff backend to match functions and compute deltas.

**Inputs:**
- `--job <path>`
- `--backend <diaphora|ghidra|radare2>`

**Outputs:**
- `<job>/artifacts/diff/function_pairs.json`
- `<job>/artifacts/diff/diff_results.json`

### 3.3 Command: `patchdiff rank`
**Purpose:** Score and select high-signal candidates.

**Inputs:**
- `--job <path>`
- `--top <int>`

**Outputs:**
- `<job>/artifacts/rank/ranked_candidates.json`

### 3.4 Command: `patchdiff decompile`
**Purpose:** Decompile top candidates only.

**Inputs:**
- `--job <path>`
- `--top <int>`
- `--timeout <sec>`

**Outputs:**
- `<job>/artifacts/decompile/<func_id>/pseudocode.txt`
- `<job>/artifacts/decompile/<func_id>/metadata.json`

### 3.5 Command: `patchdiff analyze`
**Purpose:** Run LLM analysis.

**Inputs:**
- `--job <path>`
- `--provider <local|openai>`
- `--model <name>`
- `--max-rounds <int>`

**Outputs:**
- `<job>/artifacts/analysis/<func_id>/llm.json`

### 3.6 Command: `patchdiff validate`
**Purpose:** Validate LLM output against evidence.

**Outputs:**
- `<job>/artifacts/validation/<func_id>/validation.json`

### 3.7 Command: `patchdiff report`
**Purpose:** Generate final report.

**Inputs:**
- `--format <markdown|html|json>`

**Outputs:**
- `<job>/report.md` or `<job>/report.json`

### 3.8 Command: `patchdiff run`
**Purpose:** Run the entire pipeline end-to-end.

---

## 4) Configuration details

### 4.1 Config file location
- Default: `~/.config/patchdiff/config.yaml`
- Override: `--config <path>`

### 4.2 Config schema
A full JSON schema exists at `specs/schemas/config.schema.json`.

### 4.3 Config precedence
1. CLI flags
2. Job-local overrides (`<job>/job_config.json`)
3. User config file
4. Built-in defaults

---

## 5) Job directory layout

```
<job>/
  job.json
  job_config.json
  artifacts/
    ingest/
    normalize/
    diff/
    rank/
    decompile/
    analysis/
    validation/
    report/
  report.md
  logs/
    job.log
```

---

## 6) Artifact schemas (authoritative)

Each artifact type has a JSON Schema definition in `specs/schemas/`.

| Artifact | File | Purpose |
|---------|------|---------|
| Job | `job.schema.json` | job metadata and binary hashes |
| Function pairs | `function_pair.schema.json` | matched function pairs |
| Diff results | `diff_result.schema.json` | delta summary |
| Ranked candidates | `ranked_candidate.schema.json` | top-N selection |
| Decompile artifact | `decompile_artifact.schema.json` | pseudo-C + metadata |
| LLM output | `llm_output.schema.json` | structured analysis |
| Validation result | `validation_result.schema.json` | validation checks |
| Report | `report.schema.json` | report structure |

---

## 7) Stage-by-stage implementation details

### 7.1 Ingest
**Inputs:** binary file paths
**Steps:**
1. Verify file existence.
2. Compute SHA-256.
3. Detect file type (PE/ELF/Mach-O).
4. Detect arch (x86/x64/arm64).
5. Write `job.json` + metadata artifacts.

### 7.2 Normalize
**Goal:** reduce diff noise without altering originals.
**Outputs:** `normalized_metadata.json` for each binary.

### 7.3 Diff
**Goal:** produce stable function pairs and diff summaries.
**Backend interface:** defined in `patchprobe/backends/diff/base.py`.

### 7.4 Rank
**Goal:** compute score per function pair.
**Model:** weighted sum of signals * match confidence.

### 7.5 Decompile
**Goal:** decompile only top-N candidates.
**Backend interface:** defined in `patchprobe/backends/decompile/base.py`.

### 7.6 LLM Analysis
**Goal:** produce structured, evidence-backed analysis.
**Safety:** enforce JSON schema and disallow exploit steps.

### 7.7 Validate
**Goal:** verify LLM claims match actual diff evidence.

### 7.8 Report
**Goal:** compile final results in Markdown/JSON.

---

## 8) Error codes

| Code | Meaning |
|------|---------|
| 10 | CLI argument error |
| 20 | File not found |
| 30 | Hash/metadata failure |
| 40 | Diff backend failure |
| 50 | Decompile failure |
| 60 | LLM failure |
| 70 | Validation failure |
| 80 | Report generation failure |

---

## 9) Logging

- JSON structured logs.
- Each log entry includes `job_id`, `stage`, `event`, `level`.
- Logs stored in `<job>/logs/job.log`.

---

## 10) Determinism and reproducibility

- Each artifact includes input hashes and tool version.
- Pipeline stages are idempotent.
- Re-run should not change outputs unless inputs differ.

---

## 11) Testing

### 11.1 Unit tests
- Hashing, filetype detection, config parsing.

### 11.2 Integration tests
- Known patch pairs with expected ranked candidates.

### 11.3 Regression tests
- Schema validation across versions.

---

## 12) Implementation roadmap

### Phase 0
- CLI skeleton
- Ingest
- Single diff backend
- Ranking
- JSON report

### Phase 1
- Selective decompile
- LLM single-round
- Validation

### Phase 2
- Multi-backend
- Multi-round LLM
- HTML report

---

## 13) Open decisions

- Primary diff backend for MVP (Diaphora vs Ghidra).
- Local-only mode default for LLM.
- Initial report verbosity level.


---

## 14) Detailed interfaces (authoritative)

### 14.1 Diff backend interface
```python
class DiffBackend(Protocol):
    def run(self, job: Job, job_dir: str) -> None:
        """
        Inputs:
          - job: Job object with binary metadata
          - job_dir: job root directory
        Outputs:
          - writes function_pairs.json
          - writes diff_results.json
        Failure:
          - raise DiffBackendError on hard failure
        """
```

### 14.2 Decompile backend interface
```python
class DecompileBackend(Protocol):
    def run(self, job: Job, job_dir: str, top_n: int | None, timeout: int) -> None:
        """
        Inputs:
          - job: Job object
          - job_dir: job root directory
          - top_n: optional override
          - timeout: per-function timeout
        Outputs:
          - writes decompile artifacts under artifacts/decompile/
        """
```

### 14.3 LLM provider interface
```python
class LLMProvider(Protocol):
    def analyze(self, packet: dict) -> dict:
        """
        Input: prompt packet (strict JSON)
        Output: structured JSON per llm_output.schema.json
        """
```

### 14.4 Storage interface
```python
class ObjectStore(Protocol):
    def write_bytes(self, rel_path: str, data: bytes) -> str: ...
    def read_bytes(self, rel_path: str) -> bytes: ...
```

---

## 15) Detailed error handling

### 15.1 Error object shape
Errors should be logged and returned with:
```json
{
  "error": {
    "code": 40,
    "type": "DiffBackendError",
    "message": "diff backend failed",
    "details": {"backend": "diaphora"}
  }
}
```

### 15.2 Exit code mapping
- `10`: CLI argument parsing failure
- `20`: file not found
- `30`: ingest failure
- `40`: diff backend failure
- `50`: decompile failure
- `60`: LLM analysis failure
- `70`: validation failure
- `80`: report failure

---

## 16) CLI contract (full options)

### 16.1 Global flags
- `--config <path>`: config path
- `--log-level <LEVEL>`: DEBUG/INFO/WARN/ERROR

### 16.2 Command flag matrix

| Command | Required flags | Optional flags |
|---------|----------------|----------------|
| ingest | `--a` `--b` `--out` | `--tag` |
| diff | `--job` | `--backend` |
| rank | `--job` | `--top` |
| decompile | `--job` | `--top` `--timeout` |
| analyze | `--job` | `--provider` `--model` `--max-rounds` |
| validate | `--job` | none |
| report | `--job` | `--format` |
| run | `--a` `--b` `--out` | `--tag` `--backend` `--top` `--timeout` `--provider` `--model` `--max-rounds` `--format` |

---

## 17) Stage I/O contracts (explicit)

### 17.1 Ingest outputs
- `artifacts/ingest/metadata_a.json`
- `artifacts/ingest/metadata_b.json`

Required fields:
- `path`, `sha256`, `file_type`, `arch`, `created_at`

### 17.2 Diff outputs
- `artifacts/diff/function_pairs.json` list of `FunctionPair`
- `artifacts/diff/diff_results.json` list of `DiffResult`

### 17.3 Rank outputs
- `artifacts/rank/ranked_candidates.json`

### 17.4 Decompile outputs
- `artifacts/decompile/<func_id>/pseudocode.txt`
- `artifacts/decompile/<func_id>/metadata.json`

### 17.5 Analysis outputs
- `artifacts/analysis/llm.json`

### 17.6 Validation outputs
- `artifacts/validation/validation.json`

### 17.7 Report outputs
- `report.md` or `report.json`

---

## 18) Ranking features (definitions)

### 18.1 Structural
- `cfg_nodes_delta`: absolute delta in CFG nodes
- `branches_added`: count of newly introduced branches
- `branches_removed`: count of removed branches

### 18.2 Semantic-ish
- `new_bounds_check`: newly introduced bounds comparison
- `new_null_check`: newly introduced pointer check
- `integer_widening`: type widening in arithmetic or indexing

### 18.3 Textual
- `string_error_signal`: new strings containing "error", "invalid", "bounds"

---

## 19) Environment variables

- `PATCHDIFF_CONFIG`: override config file path
- `PATCHDIFF_LOG_LEVEL`: override log level
- `PATCHDIFF_OFFLINE`: force local LLM only

---

## 20) Artifact validation strategy

- Validate every artifact against its JSON schema on write.
- Fail fast if schema validation fails.

---

## 21) Safety policy enforcement

- LLM analysis prompts always include a policy note: no exploit steps.
- Any output containing exploit instructions is rejected by validation.

---

## 22) Implementation checklist

- [ ] CLI scaffolding (argparse)
- [ ] Ingest metadata
- [ ] Schema validation
- [ ] Diff backend integration
- [ ] Ranking engine
- [ ] Selective decompilation
- [ ] LLM analysis integration
- [ ] Validation checks
- [ ] Report generation

