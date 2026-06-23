import requests
from humanise.engines.base import BaseEngine, EngineResult
from humanise.prompts.templates import ANTI_DETECTION_PROMPT


class OllamaEngine(BaseEngine):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.base_url = base_url
        self.model = model

    def available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def rewrite(self, text: str, temperature: float = 1.1) -> EngineResult:
        r = requests.post(f"{self.base_url}/api/generate", json={
            "model": self.model,
            "system": ANTI_DETECTION_PROMPT,
            "prompt": f"Rewrite this to sound human:\n\n{text}",
            "stream": False,
            "options": {"temperature": temperature, "top_p": 0.95}
        })
        data = r.json()
        return EngineResult(
            text=data.get("response", ""),
            engine=self.name,
            tokens_used=data.get("eval_count", 0),
        )
