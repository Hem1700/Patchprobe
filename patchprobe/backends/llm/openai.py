from __future__ import annotations

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str, max_rounds: int) -> None:
        self.model = model
        self.max_rounds = max_rounds

    def analyze(self, packet: dict) -> dict:
        # Placeholder: implement hosted provider calls.
        return {"status": "not_implemented", "model": self.model}
