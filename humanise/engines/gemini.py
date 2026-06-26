from humanise.engines.base import BaseEngine, EngineResult
from humanise.prompts.templates import ANTI_DETECTION_PROMPT


class GeminiEngine(BaseEngine):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

    def available(self) -> bool:
        return bool(self.api_key)

    def rewrite(self, text: str, temperature: float = 0.9) -> EngineResult:
        return self.rewrite_with_prompt(text, prompt=ANTI_DETECTION_PROMPT, temperature=temperature)

    def rewrite_with_prompt(
        self, text: str, prompt: str, temperature: float = 0.9
    ) -> EngineResult:
        from google import genai
        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=f"{prompt}\n\nRewrite this to sound human:\n\n{text}",
            config={"temperature": temperature}
        )
        return EngineResult(
            text=response.text or "",
            engine=self.name,
        )
