import time
from humanise.engines.base import BaseEngine, EngineResult
from humanise.prompts.templates import ANTI_DETECTION_PROMPT


class GeminiEngine(BaseEngine):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self._rate_limited_until = 0.0

    def available(self) -> bool:
        if not self.api_key:
            return False
        if time.time() < self._rate_limited_until:
            return False
        return True

    def rewrite(self, text: str, temperature: float = 0.9) -> EngineResult:
        return self.rewrite_with_prompt(text, prompt=ANTI_DETECTION_PROMPT, temperature=temperature)

    def rewrite_with_prompt(
        self, text: str, prompt: str, temperature: float = 0.9
    ) -> EngineResult:
        from google import genai
        client = genai.Client(api_key=self.api_key)
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=f"{prompt}\n\nRewrite this to sound human:\n\n{text}",
                config={"temperature": temperature}
            )
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                self._rate_limited_until = time.time() + 60
                raise RuntimeError(f"gemini_rate_limited: {e}") from e
            raise
        return EngineResult(
            text=response.text or "",
            engine=self.name,
        )
