from humanise.engines.base import BaseEngine, EngineResult
from humanise.prompts.templates import ANTI_DETECTION_PROMPT


class GroqEngine(BaseEngine):
    name = "groq"

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model

    def available(self) -> bool:
        return bool(self.api_key)

    def rewrite(self, text: str, temperature: float = 1.0) -> EngineResult:
        return self.rewrite_with_prompt(text, prompt=ANTI_DETECTION_PROMPT, temperature=temperature)

    def rewrite_with_prompt(
        self, text: str, prompt: str, temperature: float = 1.0
    ) -> EngineResult:
        from groq import Groq
        client = Groq(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Rewrite this differently:\n\n{text}"}
            ],
            temperature=temperature,
            max_tokens=4096,
        )
        return EngineResult(
            text=response.choices[0].message.content or "",
            engine=self.name,
            tokens_used=response.usage.total_tokens if response.usage else 0,
        )
