from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMConfig:
    model: str
    max_rounds: int


class LLMProvider(Protocol):
    def analyze(self, packet: dict) -> dict:
        ...
