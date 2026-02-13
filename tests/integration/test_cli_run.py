from pathlib import Path

from patchprobe.cli import main


def test_cli_run_end_to_end_creates_expected_outputs(monkeypatch, tmp_path: Path) -> None:
    a = tmp_path / "before.bin"
    b = tmp_path / "after.bin"
    a.write_bytes(b"\x7fELF" + b"\x00" * 96)
    b.write_bytes(b"\x7fELF" + b"\x01" * 96)
    job_dir = tmp_path / "job"

    monkeypatch.setattr(
        "sys.argv",
        [
            "patchdiff",
            "run",
            "--a",
            str(a),
            "--b",
            str(b),
            "--out",
            str(job_dir),
            "--format",
            "json",
            "--max-rounds",
            "2",
        ],
    )
    main()

    assert (job_dir / "job.json").exists()
    assert (job_dir / "artifact_index.json").exists()
    assert (job_dir / "artifacts" / "normalize" / "normalized_metadata.json").exists()
    assert (job_dir / "artifacts" / "analysis" / "round_outputs.json").exists()
    assert (job_dir / "report.json").exists()
