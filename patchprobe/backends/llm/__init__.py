from .base import LLMProvider
from .local import LocalProvider
from .openai import OpenAIProvider


def get_provider(name: str, model: str, max_rounds: int) -> LLMProvider:
    name = name.lower()
    if name == "local":
        return LocalProvider(model=model, max_rounds=max_rounds)
    if name == "openai":
        return OpenAIProvider(model=model, max_rounds=max_rounds)
    raise ValueError(f"Unknown LLM provider: {name}")
