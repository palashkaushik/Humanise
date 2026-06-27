import time
import re
import random
from typing import Optional, Sequence, Union
from humanise.engines.base import BaseEngine, EngineResult
from humanise.engines.ollama import OllamaEngine
from humanise.engines.gemini import GeminiEngine
from humanise.engines.groq import GroqEngine
from humanise.rules.polish import rule_based_polish, aggressive_polish
from humanise.rules.scramble import scramble
from humanise.rules.humanize_rules import humanize_rules
from humanise.rules.elegant import apply_elegant_rules
from humanise.detection.feedback import detect_patterns, full_analysis
from humanise.prompts.templates import (
    ANTI_DETECTION_PROMPT,
    PASS_1_STRUCTURAL,
    PASS_2_VOCABULARY,
    PASS_3_PUNCTUATION,
    PASS_4_FINGERPRINT,
    FEEDBACK_MULTI_PASS,
)


MULTI_MODEL_ROTATION = [
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "llama-3.3-70b-versatile",
]


def _check_coherence(text: str, original: str) -> str:
    """Detect and fix LLM hallucination / word salad.
    
    When the LLM loses coherence, the output degrades into:
    - Very short fragments (1-2 words)
    - Nonsensical word combinations
    - Repetitive filler patterns
    - Loss of grammatical structure
    
    Returns the original text if the rewrite is incoherent.
    Truncates at the last coherent sentence if degradation is detected.
    """
    if not text or not text.strip():
        return original
    
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    if len(sentences) < 2:
        return original
    
    # Check for incoherence signals
    issues = 0
    
    # 1. Too many very short fragments (1-3 words)
    short_fragments = sum(1 for s in sentences if len(s.split()) <= 3)
    if short_fragments > len(sentences) * 0.4:
        issues += 1
    
    # 2. Sentences that are just filler words
    filler_words = {'and', 'but', 'or', 'so', 'yet', 'also', 'just', 'still', 'now', 'then',
                    'here', 'there', 'where', 'when', 'how', 'why', 'what', 'who', 'which',
                    'that', 'this', 'these', 'those', 'it', 'he', 'she', 'they', 'we', 'you',
                    'I', 'my', 'his', 'her', 'our', 'your', 'its', 'the', 'a', 'an', 'some',
                    'any', 'all', 'no', 'not', 'never', 'always', 'maybe', 'perhaps', 'huh'}
    filler_count = 0
    for s in sentences:
        words = s.lower().split()
        if len(words) <= 2 and all(w.strip('.,!?;:') in filler_words for w in words):
            filler_count += 1
    
    if filler_count > len(sentences) * 0.3:
        issues += 1
    
    # 3. Check for repeated determiners/prepositions
    nonsensical = 0
    for s in sentences:
        words = s.split()
        if len(words) >= 3:
            for i in range(len(words) - 1):
                if words[i].lower() == words[i+1].lower() and words[i].lower() in {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}:
                    nonsensical += 1
                    break
    
    if nonsensical > len(sentences) * 0.2:
        issues += 1
    
    # 4. Check length ratio — if output is >2x input, it's likely hallucinating
    orig_words = len(original.split())
    new_words = len(text.split())
    if new_words > orig_words * 2.0:
        # Truncate to 1.5x input length at the last sentence boundary
        target_words = int(orig_words * 1.5)
        words_so_far = 0
        for i, s in enumerate(sentences):
            words_so_far += len(s.split())
            if words_so_far >= target_words:
                return ' '.join(sentences[:i+1])
        return text
    if new_words < orig_words * 0.5:
        return original
    
    # 5. Check for lowercase sentence starts
    fragment_count = sum(1 for i, s in enumerate(sentences) if i > 0 and s and s[0].islower())
    if fragment_count > len(sentences) * 0.3:
        issues += 1
    
    # 6. Detect late-stage degradation
    third = len(sentences) // 3
    if third >= 2:
        first_third = sentences[:third]
        last_third = sentences[-third:]
        
        first_short = sum(1 for s in first_third if len(s.split()) <= 3)
        last_short = sum(1 for s in last_third if len(s.split()) <= 3)
        
        if last_short > first_short * 2 and last_short > len(last_third) * 0.4:
            issues += 1
    
    # If issues detected, try to salvage by truncating at last good sentence
    if issues >= 1:
        # Walk backwards to find the last "good" sentence
        for i in range(len(sentences) - 1, -1, -1):
            s = sentences[i]
            words = s.split()
            # A good sentence: >= 4 words, starts with capital, not just filler
            if (len(words) >= 4 and 
                s[0].isupper() and
                not all(w.strip('.,!?;:') in filler_words for w in words)):
                truncated = ' '.join(sentences[:i+1])
                # Only use truncation if we kept at least 60% of the text
                if len(truncated.split()) >= orig_words * 0.6:
                    return truncated
        # If no good truncation found, return original
        return original
    
    return text


STRENGTH_CONFIG = {
    "light": {
        "temperature": 1.2,
        "passes": 1,
        "rule_polish": True,
        "target_score": 60,
        "max_feedback_iterations": 1,
    },
    "medium": {
        "temperature": 1.5,
        "passes": 1,
        "rule_polish": True,
        "target_score": 75,
        "max_feedback_iterations": 2,
    },
    "aggressive": {
        "temperature": 1.8,
        "passes": 1,
        "rule_polish": True,
        "scramble": True,
        "target_score": 85,
        "max_feedback_iterations": 3,
    },
    "ninja": {
        "temperature": 2.0,
        "passes": 1,
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
                models = [groq_models[0]] if groq_models else ["openai/gpt-oss-20b"]
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

        available_engines = [e for e in self.engines if e.available()]
        if not available_engines:
            return None

        if len(available_engines) == 1:
            return available_engines[0]

        candidates = [e for e in available_engines if e.name != last]
        if not candidates:
            candidates = available_engines

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

        if not self.engines:
            result = rule_based_polish(text)
            result = apply_elegant_rules(result, strength=strength)
            return result

        fingerprint = EngineFingerprint()

        # Single high-temperature LLM pass — the LLM does the heavy lifting
        engine = self._select_engine(0, 1, fingerprint)
        if engine is None:
            result = text
        else:
            try:
                pass_result = engine.rewrite_with_prompt(
                    text,
                    prompt=ANTI_DETECTION_PROMPT,
                    temperature=config["temperature"],
                )
                result = pass_result.text if pass_result.text.strip() else text
                # Check for LLM hallucination / word salad
                result = _check_coherence(result, text)
                if pass_result.text.strip():
                    fingerprint.record(engine.name, "rewrite")
            except Exception:
                result = text

        # Light post-processing: only AI word removal + typo fixing
        # The LLM already handles structure, rhythm, and tone
        result = apply_elegant_rules(result, strength=strength)

        # If no engines available, use rule-based only
        if not fingerprint.engines_used:
            result = rule_based_polish(text)
            result = apply_elegant_rules(result, strength=strength)

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

        # Light post-processing: only AI word removal + typo fixing
        result = apply_elegant_rules(result, strength=strength)

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
        default_iters = {
            "light": 4,
            "medium": 6,
            "aggressive": 8,
            "ninja": 10,
        }
        max_iter = max_iterations or default_iters.get(strength, config["max_feedback_iterations"] * 2)
        target = config["target_score"]
        result = text
        fingerprint = EngineFingerprint()

        best_result = result
        best_score = full_analysis(result)["human_score"]
        stable_count = 0

        for i in range(max_iter):
            # Single high-temperature LLM pass per iteration
            iteration_temp = min(2.0, config["temperature"] + (i * 0.1))

            engine = self._select_engine(i, max_iter, fingerprint)
            if engine:
                try:
                    pass_result = engine.rewrite_with_prompt(
                        result,
                        prompt=ANTI_DETECTION_PROMPT,
                        temperature=iteration_temp,
                    )
                    if pass_result.text.strip():
                        result = pass_result.text
                        # Check for LLM hallucination / word salad
                        result = _check_coherence(result, text)
                        fingerprint.record(engine.name, "rewrite")
                except Exception:
                    pass

            # Apply light post-processing
            result = apply_elegant_rules(result, strength=strength)

            # Check score
            analysis = full_analysis(result)
            current_score = analysis["human_score"]

            if current_score > best_score:
                best_score = current_score
                best_result = result
                stable_count = 0
            else:
                stable_count += 1

            if current_score >= target and stable_count >= 1:
                return best_result

            # If stuck, try feedback prompt
            if stable_count >= 2 and i < max_iter - 1:
                concerns = analysis.get("concerns", [])
                feedback_prompt = self._build_specific_feedback_prompt(
                    concerns=concerns,
                    analysis=analysis,
                    iteration=i,
                    fingerprint=fingerprint,
                )
                engine = self._select_engine(
                    fingerprint.pass_count,
                    fingerprint.pass_count + 2,
                    fingerprint,
                )
                if engine:
                    try:
                        fb_result = engine.rewrite_with_prompt(
                            result,
                            prompt=feedback_prompt,
                            temperature=min(2.0, iteration_temp + 0.2),
                        )
                        if fb_result and fb_result.text.strip():
                            result = fb_result.text
                            fingerprint.record(engine.name, "feedback")
                            stable_count = 0
                    except AttributeError:
                        pass

        result = apply_elegant_rules(result, strength=strength)
        current_score = full_analysis(result)["human_score"]
        if current_score > best_score:
            best_score = current_score
            best_result = result

        return best_result

    def _build_specific_feedback_prompt(
        self,
        concerns: list,
        analysis: dict,
        iteration: int,
        fingerprint: EngineFingerprint,
    ) -> str:
        last_engine = fingerprint.last_engine() or "unknown"
        passes_completed = fingerprint.pass_count

        # Build a specific, actionable feedback prompt
        concerns_text = "\n".join(f"- {c}" for c in concerns[:8]) if concerns else "- General AI patterns detected"

        # Add specific stats
        stats_lines = []
        if analysis.get("burstiness", 0) < 0.4:
            stats_lines.append(f"- Burstiness is LOW ({analysis['burstiness']:.2f}) — sentence lengths are too uniform. Create EXTREME variance: fragments next to run-ons.")
        if analysis.get("perplexity", 0) < 60:
            stats_lines.append(f"- Perplexity is LOW ({analysis['perplexity']:.0f}) — word choices are too predictable. Use UNUSUAL pairings.")
        if analysis.get("sentence_uniformity", 0) > 0.5:
            stats_lines.append(f"- Sentence uniformity is HIGH ({analysis['sentence_uniformity']:.2f}) — break up the rhythm.")
        if analysis.get("pattern_count", 0) > 3:
            stats_lines.append(f"- {analysis['pattern_count']} AI patterns detected — replace with totally different structures.")

        stats_text = "\n".join(stats_lines) if stats_lines else ""

        return f"""You are rewriting to pass AI detection. This is iteration {iteration + 1}. Previous attempts were flagged.

FLAGGED ISSUES:
{concerns_text}

{f"STATISTICAL SIGNALS:" + chr(10) + stats_text if stats_text else ""}

YOU MUST:
1. REWRITE EVERY SENTENCE — don't just edit a few. The whole text needs to feel like a different person wrote it.
2. USE UNUSUAL WORD COMBINATIONS — replace predictable phrases with surprising ones.
3. VARY SENTENCE LENGTHS EXTREMELY — mix 2-word fragments with 30-word flowing sentences.
4. ADD SPECIFIC DETAILS — brand names, prices, years, weird comparisons.
5. USE DIFFERENT SENTENCE STARTERS — vary: prepositions, adverbs, fragments, questions.
6. WRITE IN YOUR ENGINE'S NATURAL STYLE — you are "{last_engine}". Don't copy other engines' patterns.
7. BREAK THE FOURTH WALL OCCASIONALLY — "Look, " "Here's the thing, " "Honestly? " "Turns out. "

CRITICAL: Average sentence length MUST be under 22 words. Use contractions. Add at least 3 em dashes. Include at least 2 rhetorical questions per 300 words.

Return ONLY the rewritten text. No explanations, no headers, no meta-commentary.

Text to rewrite:

"""

    def humanize_best_of(
        self, text: str, strength: str = "medium", candidates: int = 2
    ) -> dict:
        config = STRENGTH_CONFIG.get(strength, STRENGTH_CONFIG["medium"])
        temperature = config["temperature"]

        best_text, best_engine, comparison = self._best_of_n(
            text, temperature, 0, 1, n=candidates
        )

        best_text = apply_elegant_rules(best_text, strength=strength)

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
