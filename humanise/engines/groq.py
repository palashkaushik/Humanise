import time
from humanise.engines.base import BaseEngine, EngineResult
from humanise.prompts.templates import ANTI_DETECTION_PROMPT


class GroqEngine(BaseEngine):
    name = "groq"

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b"):
        self.api_key = api_key
        self.model = model
        self._rate_limited_until = 0.0

    def available(self) -> bool:
        if not self.api_key:
            return False
        if time.time() < self._rate_limited_until:
            return False
        return True

    def rewrite(self, text: str, temperature: float = 1.0) -> EngineResult:
        return self.rewrite_with_prompt(text, prompt=ANTI_DETECTION_PROMPT, temperature=temperature)

    def rewrite_with_prompt(
        self, text: str, prompt: str, temperature: float = 1.0
    ) -> EngineResult:
        from groq import Groq
        client = Groq(api_key=self.api_key)
        try:
            # Limit output to ~1.5x input length to prevent hallucination
            input_tokens = len(text.split()) * 4  # rough estimate: 1 word ≈ 1.3 tokens
            max_tokens = min(4096, max(512, int(input_tokens * 1.5)))
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Rewrite this differently:\n\n{text}"}
                ],
                temperature=temperature,
                top_p=0.95,
                max_tokens=max_tokens,
            )
            return EngineResult(
                text=response.choices[0].message.content or "",
                engine=self.name,
                tokens_used=response.usage.total_tokens if response.usage else 0,
            )
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                self._rate_limited_until = time.time() + 60
                return EngineResult(text="", engine=self.name, tokens_used=0)
            raise
