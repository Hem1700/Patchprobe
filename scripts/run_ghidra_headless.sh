#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   run_ghidra_headless.sh <ghidra_project_dir> <binary_path> <script_path> <function_name> <output_json> <output_txt> <timeout_sec>

if [[ $# -lt 7 ]]; then
  echo "usage: $0 <ghidra_project_dir> <binary_path> <script_path> <function_name> <output_json> <output_txt> <timeout_sec>" >&2
  exit 2
fi

ghidra_project_dir="$1"
binary_path="$2"
script_path="$3"
function_name="$4"
output_json="$5"
output_txt="$6"
timeout_sec="$7"

mkdir -p "$ghidra_project_dir"
mkdir -p "$(dirname "$output_json")"
mkdir -p "$(dirname "$output_txt")"

analyze_headless_bin=""
if [[ -n "${PATCHDIFF_GHIDRA_ANALYZE_HEADLESS:-}" ]]; then
  analyze_headless_bin="$PATCHDIFF_GHIDRA_ANALYZE_HEADLESS"
elif [[ -n "${GHIDRA_INSTALL_DIR:-}" ]]; then
  analyze_headless_bin="$GHIDRA_INSTALL_DIR/support/analyzeHeadless"
else
  analyze_headless_bin="$(command -v analyzeHeadless || true)"
fi

if [[ -z "$analyze_headless_bin" || ! -x "$analyze_headless_bin" ]]; then
  echo "analyzeHeadless not found (set PATCHDIFF_GHIDRA_ANALYZE_HEADLESS or GHIDRA_INSTALL_DIR)" >&2
  exit 127
fi

project_name="PatchProbeHeadless"
script_dir="$(dirname "$script_path")"
script_name="$(basename "$script_path")"

# Timeout is controlled by the caller (Python subprocess timeout) for portability.
"$analyze_headless_bin" \
  "$ghidra_project_dir" \
  "$project_name" \
  -import "$binary_path" \
  -scriptPath "$script_dir" \
  -postScript "$script_name" "$function_name" "$output_json" "$output_txt" "$timeout_sec" \
  -deleteProject
