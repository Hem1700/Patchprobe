from __future__ import annotations

import subprocess
from typing import Sequence


def run_command(cmd: Sequence[str], timeout: int | None = None, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, timeout=timeout, cwd=cwd, check=False, capture_output=True, text=True)
