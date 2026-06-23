import time
from typing import Optional, Sequence, Union
from humanise.engines.base import BaseEngine, EngineResult
from humanise.engines.ollama import OllamaEngine
from humanise.engines.gemini import GeminiEngine
from humanise.engines.groq import GroqEngine
from humanise.rules.polish import rule_based_polish
from humanise.rules.scramble import scramble
from humanise.detection.feedback import detect_patterns, full_analysis


MULTI_MODEL_ROTATION = [
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
    "openai/gpt-oss-20b",
]


STRENGTH_CONFIG = {
    "light": {
        "temperature": 0.8,
        "passes": 1,
        "rule_polish": True,
        "target_score": 60,
        "max_feedback_iterations": 1,
    },
    "medium": {
        "temperature": 0.9,
        "passes": 1,
        "rule_polish": True,
        "target_score": 75,
        "max_feedback_iterations": 1,
    },
    "aggressive": {
        "temperature": 1.0,
        "passes": 2,
        "rule_polish": True,
        "scramble": True,
        "target_score": 85,
        "max_feedback_iterations": 2,
    },
    "ninja": {
        "temperature": 1.1,
        "passes": 3,
        "rule_polish": True,
        "scramble": True,
        "target_score": 95,
        "max_feedback_iterations": 3,
    },
}


class Humanise:
    def __init__(
        self,
        ollama_model: str = "llama3.1:8b",
        ollama_url: str = "http://localhost:11434",
        gemini_key: Optional[str] = None,
        gemini_model: str = "gemini-2.5-flash",
        groq_key: Optional[str] = None,
        groq_models: Optional[Sequence[str]] = None,
        single_groq_model: bool = False,
    ):
        self.engines: list[BaseEngine] = []
        self._add_engine(OllamaEngine(base_url=ollama_url, model=ollama_model))
        if gemini_key:
            self._add_engine(GeminiEngine(api_key=gemini_key, model=gemini_model))
        if groq_key:
            if single_groq_model or not groq_models:
                models = [groq_models[0]] if groq_models else ["llama-3.3-70b-versatile"]
            else:
                models = groq_models
            for model in models:
                self._add_engine(GroqEngine(api_key=groq_key, model=model))

    def _add_engine(self, engine: BaseEngine):
        if engine.available():
            self.engines.append(engine)

    def _rotate_engine(self, pass_num: int, total: int) -> Optional[BaseEngine]:
        if not self.engines:
            return None
        return self.engines[pass_num % len(self.engines)]

    def _engine_count(self) -> int:
        return len(self.engines)

    def analyze(self, text: str) -> dict:
        return full_analysis(text)

    def _rewrite_pass(
        self, text: str, temperature: float, pass_num: int, total_passes: int
    ) -> str:
        engine = self._rotate_engine(pass_num, total_passes)
        if engine is None:
            return text
        try:
            engine_result = engine.rewrite(text, temperature=temperature)
            if engine_result.text.strip():
                return engine_result.text
        except Exception:
            return text
        return text

    def humanize(self, text: str, strength: str = "medium") -> str:
        config = STRENGTH_CONFIG.get(strength, STRENGTH_CONFIG["medium"])
        passes = config["passes"]
        temperature = config["temperature"]

        if not self.engines:
            return rule_based_polish(text)

        result = text
        for i in range(passes):
            result = self._rewrite_pass(result, temperature, i, passes)

        if config["rule_polish"]:
            result = rule_based_polish(result)

        if config.get("scramble"):
            result = scramble(result, strength=strength)

        return result

    def humanize_with_report(self, text: str, strength: str = "medium") -> dict:
        config = STRENGTH_CONFIG.get(strength, STRENGTH_CONFIG["medium"])
        before = full_analysis(text)
        start_time = time.perf_counter()

        result = self.humanize(text, strength)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000)
        after = full_analysis(result)

        fixes = {}
        for pattern_name in before.get("patterns", {}):
            if pattern_name in after.get("patterns", {}):
                removed = before["patterns"][pattern_name] - after["patterns"][pattern_name]
                if removed > 0:
                    fixes[pattern_name] = removed
            else:
                fixes[pattern_name] = before["patterns"][pattern_name]

        improvement = round(after["human_score"] - before["human_score"], 1)

        return {
            "text": result,
            "before": before,
            "after": after,
            "improvement": improvement,
            "fixes": fixes,
            "strength": strength,
            "engines_used": self._engine_count(),
            "elapsed_ms": elapsed_ms,
        }

    def humanize_with_feedback(
        self, text: str, strength: str = "medium", max_iterations: int | None = None
    ) -> str:
        config = STRENGTH_CONFIG.get(strength, STRENGTH_CONFIG["medium"])
        max_iter = max_iterations or config["max_feedback_iterations"]
        target = config["target_score"]
        result = text

        for i in range(max_iter):
            result = self.humanize(result, strength="aggressive" if i > 0 else strength)
            analysis = full_analysis(result)
            if analysis["human_score"] >= target:
                break

        return result

    def detect(self, text: str) -> dict:
        return detect_patterns(text)
