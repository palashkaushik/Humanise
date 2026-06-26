import time
import random
from typing import Optional, Sequence, Union
from humanise.engines.base import BaseEngine, EngineResult
from humanise.engines.ollama import OllamaEngine
from humanise.engines.gemini import GeminiEngine
from humanise.engines.groq import GroqEngine
from humanise.rules.polish import rule_based_polish, aggressive_polish
from humanise.rules.scramble import scramble
from humanise.detection.feedback import detect_patterns, full_analysis
from humanise.prompts.templates import (
    PASS_1_STRUCTURAL,
    PASS_2_VOCABULARY,
    PASS_3_PUNCTUATION,
    PASS_4_FINGERPRINT,
    FEEDBACK_MULTI_PASS,
)


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
        "passes": 2,
        "rule_polish": True,
        "target_score": 75,
        "max_feedback_iterations": 2,
    },
    "aggressive": {
        "temperature": 1.0,
        "passes": 3,
        "rule_polish": True,
        "scramble": True,
        "target_score": 85,
        "max_feedback_iterations": 3,
    },
    "ninja": {
        "temperature": 1.1,
        "passes": 4,
        "rule_polish": True,
        "scramble": True,
        "target_score": 95,
        "max_feedback_iterations": 4,
    },
}

PASS_PROMPTS = [
    PASS_1_STRUCTURAL,
    PASS_2_VOCABULARY,
    PASS_3_PUNCTUATION,
    PASS_4_FINGERPRINT,
]


class EngineFingerprint:
    """Tracks which engines and styles have been used to ensure diversity."""

    def __init__(self):
        self.engines_used: list[str] = []
        self.styles_used: list[str] = []
        self.pass_count: int = 0

    def record(self, engine_name: str, style: str):
        self.engines_used.append(engine_name)
        self.styles_used.append(style)
        self.pass_count += 1

    def get_diversity_score(self) -> float:
        if not self.engines_used:
            return 0.0
        unique_engines = len(set(self.engines_used))
        unique_styles = len(set(self.styles_used))
        engine_diversity = unique_engines / len(self.engines_used)
        style_diversity = unique_styles / len(self.styles_used)
        return (engine_diversity + style_diversity) / 2

    def last_engine(self) -> Optional[str]:
        return self.engines_used[-1] if self.engines_used else None

    def summary(self) -> dict:
        return {
            "passes": self.pass_count,
            "engines": self.engines_used,
            "styles": self.styles_used,
            "diversity_score": self.get_diversity_score(),
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

    def _select_engine(
        self, pass_num: int, total_passes: int, fingerprint: EngineFingerprint
    ) -> Optional[BaseEngine]:
        if not self.engines:
            return None

        last = fingerprint.last_engine()

        if len(self.engines) == 1:
            return self.engines[0]

        candidates = [e for e in self.engines if e.name != last]
        if not candidates:
            candidates = self.engines

        weights = []
        for engine in candidates:
            w = 1.0
            if engine.name == last:
                w *= 0.2
            if pass_num == 0 and engine.name == "ollama":
                w *= 1.3
            elif pass_num == total_passes - 1 and engine.name == "groq":
                w *= 1.2
            weights.append(w)

        total = sum(weights)
        weights = [w / total for w in weights]
        return random.choices(candidates, weights=weights, k=1)[0]

    def _get_pass_prompt(self, pass_num: int) -> str:
        idx = pass_num % len(PASS_PROMPTS)
        return PASS_PROMPTS[idx]

    def _get_pass_style(self, pass_num: int) -> str:
        styles = ["structural", "vocabulary", "punctuation", "fingerprint"]
        return styles[pass_num % len(styles)]

    def _engine_count(self) -> int:
        return len(self.engines)

    def analyze(self, text: str) -> dict:
        return full_analysis(text)

    def _rewrite_pass(
        self,
        text: str,
        temperature: float,
        pass_num: int,
        total_passes: int,
        fingerprint: EngineFingerprint,
    ) -> str:
        engine = self._select_engine(pass_num, total_passes, fingerprint)
        if engine is None:
            return text

        prompt = self._get_pass_prompt(pass_num)
        style = self._get_pass_style(pass_num)

        try:
            engine_result = engine.rewrite_with_prompt(
                text, prompt=prompt, temperature=temperature
            )
            if engine_result.text.strip():
                fingerprint.record(engine.name, style)
                return engine_result.text
        except AttributeError:
            try:
                engine_result = engine.rewrite(text, temperature=temperature)
                if engine_result.text.strip():
                    fingerprint.record(engine.name, style)
                    return engine_result.text
            except Exception:
                return text
        except Exception:
            return text

        return text

    def _best_of_n(
        self, text: str, temperature: float, pass_num: int, total_passes: int, n: int = 2
    ) -> tuple[str, str, str]:
        if len(self.engines) < 2 or n < 2:
            engine = self._select_engine(pass_num, total_passes, EngineFingerprint())
            if engine is None:
                return text, "none", "none"
            try:
                result = engine.rewrite(text, temperature=temperature)
                return result.text, engine.name, engine.name
            except Exception:
                return text, "none", "none"

        candidates = []
        engines_tried = []
        available = list(self.engines)
        random.shuffle(available)

        for engine in available[:n]:
            try:
                result = engine.rewrite(text, temperature=temperature)
                if result.text.strip():
                    candidates.append((result.text, engine.name))
                    engines_tried.append(engine.name)
            except Exception:
                continue

        if not candidates:
            return text, "none", "none"

        scored = []
        for text_candidate, engine_name in candidates:
            analysis = full_analysis(text_candidate)
            scored.append((analysis["human_score"], text_candidate, engine_name))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_text, best_engine = scored[0]

        if len(scored) > 1:
            second_text = scored[1][1]
            return best_text, best_engine, f"beat:{scored[1][2]}({scored[1][0]:.0f})"

        return best_text, best_engine, "solo"

    def humanize(self, text: str, strength: str = "medium") -> str:
        config = STRENGTH_CONFIG.get(strength, STRENGTH_CONFIG["medium"])
        passes = config["passes"]
        temperature = config["temperature"]

        if not self.engines:
            return rule_based_polish(text)

        fingerprint = EngineFingerprint()
        result = text

        for i in range(passes):
            result = self._rewrite_pass(result, temperature, i, passes, fingerprint)

        if config["rule_polish"]:
            result = rule_based_polish(result)

        if config.get("scramble"):
            result = scramble(result, strength=strength)

        return result

    def humanize_with_report(self, text: str, strength: str = "medium") -> dict:
        config = STRENGTH_CONFIG.get(strength, STRENGTH_CONFIG["medium"])
        before = full_analysis(text)
        start_time = time.perf_counter()

        fingerprint = EngineFingerprint()
        result = text
        passes = config["passes"]
        temperature = config["temperature"]

        pass_results = []
        for i in range(passes):
            pre_pass = result
            result = self._rewrite_pass(result, temperature, i, passes, fingerprint)
            post_pass = full_analysis(result)
            pass_results.append({
                "pass": i + 1,
                "style": self._get_pass_style(i),
                "engine": fingerprint.engines_used[-1] if fingerprint.engines_used else "none",
                "score_before": full_analysis(pre_pass)["human_score"],
                "score_after": post_pass["human_score"],
            })

        if config["rule_polish"]:
            result = rule_based_polish(result)

        if config.get("scramble"):
            result = scramble(result, strength=strength)

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
            "engines_used": fingerprint.summary(),
            "pass_results": pass_results,
            "elapsed_ms": elapsed_ms,
        }

    def humanize_with_feedback(
        self, text: str, strength: str = "medium", max_iterations: int | None = None
    ) -> str:
        config = STRENGTH_CONFIG.get(strength, STRENGTH_CONFIG["medium"])
        max_iter = max_iterations or config["max_feedback_iterations"]
        target = config["target_score"]
        result = text

        fingerprint = EngineFingerprint()

        for i in range(max_iter):
            pass_strength = "aggressive" if i > 0 else strength
            pass_config = STRENGTH_CONFIG.get(pass_strength, STRENGTH_CONFIG["medium"])

            for p in range(pass_config["passes"]):
                result = self._rewrite_pass(
                    result,
                    pass_config["temperature"],
                    p,
                    pass_config["passes"],
                    fingerprint,
                )

            analysis = full_analysis(result)
            if analysis["human_score"] >= target:
                break

            if i < max_iter - 1:
                analysis_text = full_analysis(result)
                concerns = analysis_text.get("concerns", [])
                if concerns:
                    last_engine = fingerprint.last_engine() or "unknown"
                    feedback_prompt = FEEDBACK_MULTI_PASS.format(
                        flagged_issues="\n".join(f"- {c}" for c in concerns[:5]),
                        passes_completed=fingerprint.pass_count,
                        engines_used=", ".join(fingerprint.engines_used),
                        pass_number=fingerprint.pass_count + 1,
                        engine_name=last_engine,
                    )
                    engine = self._select_engine(
                        fingerprint.pass_count,
                        fingerprint.pass_count + 2,
                        fingerprint,
                    )
                    if engine:
                        try:
                            result = engine.rewrite_with_prompt(
                                result,
                                prompt=feedback_prompt,
                                temperature=pass_config["temperature"],
                            )
                            if result and result.text.strip():
                                result = result.text
                                fingerprint.record(engine.name, "feedback")
                        except AttributeError:
                            pass

        if config["rule_polish"]:
            result = rule_based_polish(result)
        if config.get("scramble"):
            result = scramble(result, strength=strength)

        return result

    def humanize_best_of(
        self, text: str, strength: str = "medium", candidates: int = 2
    ) -> dict:
        config = STRENGTH_CONFIG.get(strength, STRENGTH_CONFIG["medium"])
        temperature = config["temperature"]

        best_text, best_engine, comparison = self._best_of_n(
            text, temperature, 0, 1, n=candidates
        )

        if config["rule_polish"]:
            best_text = rule_based_polish(best_text)
        if config.get("scramble"):
            best_text = scramble(best_text, strength=strength)

        before = full_analysis(text)
        after = full_analysis(best_text)

        return {
            "text": best_text,
            "engine": best_engine,
            "comparison": comparison,
            "before": before,
            "after": after,
            "improvement": round(after["human_score"] - before["human_score"], 1),
        }

    def detect(self, text: str) -> dict:
        return detect_patterns(text)
