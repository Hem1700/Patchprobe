from patchprobe.backends.diff.diaphora import _match_symbols, _parse_nm_output
from patchprobe.core.job import BinaryInfo, Job


def _make_job() -> Job:
    return Job(
        job_id="job1",
        created_at="2026-01-01T00:00:00Z",
        tag=None,
        binary_a=BinaryInfo(path="/tmp/a.bin", sha256="a" * 64, file_type="ELF", arch="x64"),
        binary_b=BinaryInfo(path="/tmp/b.bin", sha256="b" * 64, file_type="ELF", arch="x64"),
        config={},
    )


def test_parse_nm_output_extracts_function_symbols() -> None:
    out = "\n".join(
        [
            "0000000000001000 T main",
            "0000000000001020 t helper",
            "0000000000000000 U puts",
            "zzzz invalid line",
        ]
    )
    symbols = _parse_nm_output(out)
    assert len(symbols) == 2
    assert symbols[0].name == "main"
    assert symbols[1].name == "helper"


def test_match_symbols_builds_schema_compatible_pairs() -> None:
    symbols_a = _parse_nm_output("0000000000001000 T _main\n0000000000001100 T helper")
    symbols_b = _parse_nm_output("0000000000002000 T main\n0000000000003000 T helper")
    pairs, diffs = _match_symbols(symbols_a, symbols_b, _make_job())
    assert len(pairs) == 2
    assert len(diffs) == 2
    assert all("func_pair_id" in p for p in pairs)
    assert all(p["status"] == "matched_by_name" for p in pairs)
    assert all("change_summary" in d for d in diffs)
