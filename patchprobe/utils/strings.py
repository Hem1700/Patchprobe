from __future__ import annotations


def safe_truncate(s: str, limit: int = 2000) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + "..."
