from dataclasses import dataclass, field


@dataclass
class EngineResult:
    text: str
    engine: str
    tokens_used: int = 0
    latency_ms: float = 0.0


class BaseEngine:
    name: str = "base"

    def rewrite(self, text: str, temperature: float = 1.0) -> EngineResult:
        raise NotImplementedError

    def rewrite_with_prompt(
        self, text: str, prompt: str, temperature: float = 1.0
    ) -> EngineResult:
        return self.rewrite(text, temperature=temperature)

    def available(self) -> bool:
        return False
