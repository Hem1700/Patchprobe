# LLM-Assisted Binary Patch Diffing — Detailed Design Document (Defender-Focused)

> **Goal:** Given two versions of the *same* binary (pre-patch vs post-patch), automatically **match functions**, **diff**, **prioritize high-signal changes**, **selectively decompile**, and produce an **auditable triage report** with LLM-assisted reasoning—focused on **defensive patch validation and prioritization**.

This design is intentionally **non-exploitative**: it does **not** generate payloads, exploits, or weaponization instructions. It’s built for patch verification, vulnerability classification, regression detection, and security review acceleration.

---

## 1) Product definition

### 1.1 Objective
Build a system that, for a pair of binaries `(A=before, B=after)`, will:

1. **Match functions across versions**
2. **Identify high-signal deltas** (security-relevant changes)
3. **Decompile only those deltas** (not entire binaries)
4. **Construct structured before/after artifacts** for LLM analysis
5. **Run multi-round LLM analysis** with guardrails (schema, evidence, policy)
6. **Validate + score** outputs (heuristics + optional static checks)
7. Produce a **defender-oriented report**:
   - likely bug class
   - impact surface & reachability notes (with evidence)
   - recommended validation tests
   - confidence + rationale
   - full provenance/audit log

### 1.2 Non-goals
- No exploit generation, payload creation, or “how to pwn”
- No “1-day exploit” automation
- No scanning arbitrary internet targets
- Default assumes **user-provided or authorized binaries**

### 1.3 Primary users
- AppSec / Product Security: patch validation
- Vulnerability management: rollout prioritization
- Reverse engineers: triage acceleration with audit trails
- Incident response: determine if a patch addresses observed behavior

---

## 2) Research-backed building blocks (what to use and why)

### 2.1 Function matching / diffing backends

#### Option A — Diaphora (IDA-based; mature; SQLite output)
- Strong function matching heuristics; exports to SQLite.
- Good fit for structured scoring and downstream automation.

#### Option B — Open-source-first pipeline (radare2 / ghidra)
- Useful if IDA is not allowed in the environment.
- Expect differences in maturity and correlator quality—design backend abstraction to swap engines.

#### Option C — Ghidra Version Tracking / Program Diff
- Works well in many contexts; also good as a fallback backend.

**Recommendation:** Start with the **most reliable** backend available to you (Diaphora if licensed; otherwise Ghidra/radare2), but implement a **pluggable backend interface** from day one.

---

### 2.2 Decompilation engine: headless + selective
**Key principle:** *Selective decompilation* is required for scale. Decompile only the top-ranked candidate functions and minimal context.

**Ghidra headless** is a strong default because:
- Reliable decompiler API
- Scriptable headless analysis
- Suitable for containerized workers

---

## 3) System architecture

### 3.1 High-level services

**CLI / API**
- `patchdiff` (CLI)
- `patchdiffd` (daemon/API)

**Core pipeline**
1. Ingest Service
2. Binary Normalizer
3. Diff Orchestrator
4. Decompile Service
5. LLM Analysis Service
6. Validation & Scoring
7. Report Generator
8. Artifact Store + Metadata DB

**Supporting**
- Job queue + workers
- Cache layer
- Policy / governance module (authorization & safe mode)

---

## 4) Data flow

Input: `(binary_A, binary_B, metadata)` → Output: `report + artifacts`

1. **Ingest** → compute hashes, detect format/arch
2. **Normalize** → consistent metadata & comparability
3. **Analyze** → function boundaries, strings, call graph
4. **Match + Diff** → function pairs + deltas
5. **Rank** → choose top `N` candidates
6. **Selective Decompile** → only candidate functions + minimal context
7. **Prompt Packet Build** → structured “before/after” bundles
8. **LLM Multi-round Analysis**
9. **Validate + Score** → corroborate claims
10. **Generate Report** → human + machine readable outputs

---

## 5) Component design (deep)

## 5.1 Ingest Service

### Responsibilities
- Accept local files or artifact IDs
- Compute:
  - SHA-256
  - file type (PE/ELF/Mach-O)
  - arch (x86/x64/arm64)
  - build IDs/timestamps where available
- Create an immutable job record

### Interfaces
- CLI: `patchdiff ingest --a path --b path --tag KBxxxx --out job_id`
- API: `POST /jobs` (multipart or object references)

### Storage layout
- Object store:
  - `binaries/{sha256}/raw`
  - `binaries/{sha256}/metadata.json`

---

## 5.2 Binary Normalizer

### Why it matters
Diff noise increases when comparing:
- different alignments or rebasing
- different symbol presence
- signatures/certs embedded
- packers/wrappers

### Actions (derived artifacts)
- Extract section table, import/export info, debug presence
- Optionally strip/record signature blocks (without altering raw input)
- Produce `normalized_metadata.json`

**Rule:** Keep raw binaries immutable; normalization artifacts are derived and reproducible.

---

## 5.3 Diff Orchestrator

### Backend abstraction
Define a unified interface:

```
DiffBackend
  - analyze(binary) -> AnalysisArtifact
  - match(a_analysis, b_analysis) -> FunctionPairs
  - diff(function_pairs) -> DiffResults
```

### Output schema (core)
**function_pairs**
- `job_id`
- `func_id_a`, `func_id_b`
- `match_score`
- `evidence` (hashes, CFG similarity, string xrefs)
- `status` (matched/ambiguous/unmatched)

**diff_results**
- `job_id`
- `func_pair_id`
- `change_summary` (counts + feature deltas)
- `asm_delta` (optional)
- `pseudocode_delta` (filled after decompile)
- `severity_hint` (heuristic rank)

---

## 5.4 Candidate Selection / Prioritization Engine

### Goal
Reduce thousands of diffs to ~10–50 high-signal candidates.

### Signals (ranking features)

**Structural**
- CFG complexity changed significantly
- new branches/guards added/removed
- new error paths introduced or removed
- added calls to validation helpers

**Semantic-ish (from pseudo if available)**
- new bounds checks
- integer widening/casts
- added null checks
- changed alloc/free pairing patterns

**Textual**
- changed strings: “invalid”, “bounds”, “overflow”, “assert”, “error”
- format string changes

**Surface / Reachability**
- modified externally reachable entrypoints (exports, handlers, RPC stubs, parsers)
- changed parameters for public-facing functions

### Scoring model
Start with transparent linear scoring:

`score = Σ(w_i * signal_i)`

Add:
- normalization/caps to avoid runaway scoring
- correlation confidence weighting (`match_score`)

### Output
Ranked list with human-readable reasoning:

```json
{
  "func_pair_id": "...",
  "rank": 3,
  "score": 0.86,
  "top_signals": [
    {"signal":"added_guard_clause", "evidence":"new early return if len > max"},
    {"signal":"new_integer_widening", "evidence":"(int)->(size_t)"}
  ]
}
```

---

## 5.5 Decompile Service (headless + selective)

### Worker model
- One worker = one headless analysis environment
- Treat concurrency as **process-level**, not thread-level
- Per-function timeouts (60–120s) and fallbacks

### Inputs
- `binary_sha`
- `target_functions` (addresses or stable IDs)
- `context_policy` (how much to include)

### Outputs (per function)
- prototype/signature
- raw decompiled pseudo-C
- callers/callees list
- strings/xrefs used by the function
- (optional) line mapping / token index for evidence anchoring

### Failure handling
- If decompile fails: return assembly + metadata and mark `decompile_status=failed`.

---

## 5.6 Prompt Packet Builder (structured LLM inputs)

### Why structured packets
- Removes ambiguity for the model
- Enables deterministic parsing and validation
- Allows evidence-based reasoning over real diff artifacts

### Packet format (strict JSON envelope)
```json
{
  "job_id": "...",
  "binary_a": {"sha256":"...", "version":"..."},
  "binary_b": {"sha256":"...", "version":"..."},
  "function": {
    "name_a": "...",
    "name_b": "...",
    "prototype_a": "...",
    "prototype_b": "...",
    "callers_a": ["..."],
    "callers_b": ["..."]
  },
  "diff": {
    "pseudocode_a": "...",
    "pseudocode_b": "...",
    "notes": ["..."]
  },
  "questions": [
    "What is the most likely bug class fixed here?",
    "What evidence supports that?",
    "What are the preconditions for reaching this code?",
    "List defensive validation test cases that exercise the fixed path."
  ],
  "required_output_schema": { "...": "..." }
}
```

---

## 5.7 LLM Analysis Service (multi-round + guardrails)

### Provider abstraction
Support pluggable providers:
- local model (privacy/sensitive binaries)
- hosted API (speed)

### Core guardrails
1. Strict output schema (JSON)
2. Evidence requirement: cite specific before/after snippets
3. Uncertainty allowed: “unknown/insufficient evidence”
4. Safety policy enforcement: refuse exploit operationalization prompts

### Multi-round pattern
- **Round 1:** classify & summarize the change
- **Round 2:** adversarial critique (counter-hypotheses)
- **Round 3:** consistency check against diff
- **Round 4:** final structured verdict (confidence + validation checklist)

### Example output schema
```json
{
  "bug_class": "integer overflow / truncation",
  "confidence": 0.72,
  "evidence": [
    {"type":"before", "snippet":"...", "location":"func.c:123-140"},
    {"type":"after",  "snippet":"...", "location":"func.c:128-150"}
  ],
  "reachability_notes": [
    "Called by handler X (confirmed by callgraph evidence)"
  ],
  "recommended_validation": [
    "Test case where len == max+1",
    "Boundary tests for negative/large values"
  ],
  "safety": {
    "no_exploit_steps": true
  }
}
```

---

## 5.8 Validation & Scoring

### Validation types

**A) Structural validation**
- Model referenced snippets that exist
- Claims about “new check added” correspond to actual diff markers
- Function pair match is not ambiguous

**B) Heuristic corroboration**
- If “bounds check added”: confirm new conditional branch and compare against bound
- If “null check added”: confirm new pointer check patterns

**C) Optional static checks**
- Confirm new early returns exist
- Confirm variable constraints precede memory accesses

### Final confidence score
Combine:
- backend match confidence
- candidate selection score
- LLM confidence (bounded)
- validation pass rate

---

## 5.9 Report Generator

### Output formats
- Human-readable: HTML/PDF/Markdown
- Machine-readable: JSON for integrations

### Report sections
1. Job metadata (hashes, versions, tool versions)
2. Ranked candidate changes
3. For each candidate:
   - function identity + match confidence
   - evidence diff (before/after)
   - likely bug class
   - reachability notes (with proof)
   - defensive validation checklist
   - confidence + rationale
4. Audit log (what ran, inputs, outputs)

---

## 6) Storage, schemas, provenance

### Stores
- Object store: binaries, diff DBs, decompile outputs, reports
- Postgres: jobs, metadata, candidate rankings, validation outcomes
- Optional: vector index for historical “fix pattern” similarity

### Provenance (reproducibility)
- tool versions
- configs
- deterministic seeds where possible
- artifact hashes for every derived output

---

## 7) Security, safety, governance

### Authorization & scope controls
- Users attest they are authorized to analyze binaries
- Default local-only operation for sensitive data
- Disable “fetch arbitrary remote targets” by default

### Abuse prevention
- No exploit modules
- Policy checks block weaponization outputs
- Optional redaction mode for sensitive symbols/strings

### Data handling
- encrypt at rest
- strict access logs
- retention policies
- “no external LLM” mode for strict environments

---

## 8) Implementation plan (stack + infra)

### Suggested stack
- Python: orchestration + services
- Workers: containerized stages
- Queue: Redis + RQ/Celery (or Temporal for higher reliability)
- DB: Postgres
- Object store: S3-compatible (MinIO for local dev)
- UI: optional; start with CLI

### Containers
- `worker-diff` (diff backend)
- `worker-decompile` (headless decompile)
- `worker-llm` (LLM provider wrapper)
- `worker-report` (rendering + export)

### Performance targets
- Ingest/metadata: seconds
- Diff: minutes (binary size dependent)
- Decompile: seconds–minutes for top candidates
- LLM: minutes per batch

---

## 9) Testing & evaluation

### Correctness tests
- Open-source patch pairs with known ground truth
- Regression suite: function matching edge cases

### Robustness tests
- stripped vs symbol-rich
- compiler changes
- LTO/PGO
- rebasing / section layout changes

### Metrics
- Precision@K: top-K candidates that are truly security-relevant
- Time-to-triage: job start → first actionable candidate
- Hallucination rate: model claims failing validation

---

## 10) Roadmap

### Phase 0 — MVP (end-to-end)
- CLI for two binaries
- Diff backend + top-N candidate selection
- selective decompile candidates
- single-round strict-JSON LLM analysis
- JSON report output

### Phase 1 — Validation + multi-round + HTML report
- multi-round analysis + cross-check
- validation engine + combined confidence score
- HTML report + audit logs

### Phase 2 — Multi-backend + scale
- add alternate diff backends
- caching + artifact reuse across jobs
- bulk job processing

### Phase 3 — Enterprise readiness
- RBAC
- compliance logging
- hardened local-only mode
- ticketing integrations

---

## 11) Next deliverables (repo-ready spec pack)
If you want, the next step is to generate:
1. OpenAPI spec for `/jobs`, `/artifacts`, `/reports`
2. Postgres schema migrations
3. Worker I/O JSON schemas
4. CLI command spec
5. Folder structure + Dockerfiles
6. Initial scoring rubric and normalization rules

