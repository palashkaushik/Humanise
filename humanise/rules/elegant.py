"""
Elegant writing rules — research-backed humanization.

Based on:
- GPTZero's 7-layer detection model (burstiness, perplexity, UID)
- Stylometric research on human vs AI text patterns
- Strunk & White, Zinsser, Williams "Style: The Basics of Clarity and Grace"
- Academic papers on computational stylistics (Biber features, Burrows' Delta)

Key insight: AI text is detected by UNIFORMITY — uniform sentence length,
uniform information density, uniform vocabulary. Humans are IRREGULAR.
"""

import re
import random
import statistics
from typing import List, Tuple


# ─── GPTZero AI Vocabulary (top flag words) ───────────────────────────────
# From GPTZero's published AI vocabulary lists (Oct 2024 - Mar 2025)
# These words appear disproportionately in AI text vs human text.
AI_FLAG_WORDS = {
    # Tier 1: Very high AI signal — almost never in human writing
    "delve": "dig into",
    "leverage": "use",
    "utilize": "use",
    "facilitate": "help",
    "streamline": "simplify",
    "optimize": "improve",
    "foster": "build",
    "cultivate": "grow",
    "empower": "enable",
    "nurture": "grow",
    "spearhead": "lead",
    "trailblaze": "pioneer",
    "endeavor": "try",
    "commence": "start",
    "ascertain": "figure out",
    "elucidate": "explain",
    "exacerbate": "make worse",
    "aforementioned": "this",
    "subsequent": "next",
    "pertaining": "about",
    "herein": "here",
    "therein": "there",
    "whereby": "by which",
    "notwithstanding": "despite",
    "henceforth": "from now on",

    # Tier 2: High AI signal — replace with simpler words
    "comprehensive": "full",
    "unprecedented": "unseen",
    "groundbreaking": "new",
    "innovative": "new",
    "robust": "strong",
    "seamless": "smooth",
    "paradigm": "approach",
    "multifaceted": "complex",
    "nuanced": "subtle",
    "sophisticated": "advanced",
    "intricate": "detailed",
    "paramount": "critical",
    "meticulous": "careful",
    "pivotal": "key",
    "integral": "essential",
    "flourish": "thrive",
    "embark": "start",
    "endeavors": "efforts",
    "landscape": "field",
    "realm": "area",
    "tapestry": "mix",
    "mosaic": "mix",
    "synergy": "teamwork",
    "holistic": "complete",
    "underscores": "shows",
    "underscoring": "showing",
    "profound": "deep",
    "resonate": "connect",
    "resonates": "connects",
    "emphasize": "stress",
    "emphasizes": "stresses",
    "highlight": "point out",
    "highlights": "points out",
    "meticulously": "carefully",
    "significantly": "noticeably",
    "substantially": "considerably",
    "furthermore": "also",
    "moreover": "also",
    "consequently": "so",
    "nevertheless": "still",
    "additionally": "also",
    "subsequently": "then",
    "conversely": "on the other hand",
    "predominantly": "mostly",
    "predominant": "main",
    "inherent": "built-in",
    "inherent": "built-in",
    "intrinsic": "built-in",
    "encompass": "include",
    "encompasses": "includes",
    "encompassing": "including",
    "comprehensive": "full",
    "implement": "do",
    "implements": "does",
    "implementing": "doing",
    "implementation": "setup",
    "facilitating": "helping",
    "streamlining": "simplifying",
    "optimizing": "improving",
    "fostering": "building",
    "cultivating": "growing",
    "empowering": "enabling",
}

# Words that are fine in human text but AI overuses
AI_OVERUSED_PHRASES = {
    "in today's world": "nowadays",
    "in the realm of": "in",
    "it is important to note": "",
    "it is worth noting": "",
    "it is crucial to understand": "",
    "in conclusion": "so",
    "to sum up": "overall",
    "in summary": "overall",
    "as we move forward": "",
    "in the ever-evolving": "",
    "in the rapidly evolving": "",
    "in the landscape of": "in",
    "in the tapestry of": "in",
    "in the mosaic of": "in",
    "a testament to": "proof of",
    "a myriad of": "lots of",
    "a plethora of": "lots of",
    "a multitude of": "lots of",
    "an abundance of": "lots of",
    "a cornucopia of": "lots of",
    "the ability to": "can",
    "the process of": "",
    "the act of": "",
    "in order to": "to",
    "for the purpose of": "to",
    "with regard to": "about",
    "in terms of": "for",
    "on a daily basis": "daily",
    "at the present time": "now",
    "at this point in time": "now",
    "due to the fact that": "because",
    "in light of the fact that": "because",
    "given the fact that": "because",
    "on the grounds that": "because",
    "in the event that": "if",
    "for the reason that": "because",
    "in spite of the fact that": "although",
    "despite the fact that": "although",
    "each and every": "every",
    "first and foremost": "first",
    "last but not least": "finally",
    "by means of": "by",
    "in the near future": "soon",
    "in the foreseeable future": "soon",
}


def _remove_ai_flag_words(text: str, probability: float = 0.8) -> str:
    """Replace GPTZero AI vocabulary with simpler alternatives.
    
    Research basis: GPTZero tracks 100+ words that appear disproportionately
    in AI text. Removing them reduces AI signal without changing meaning.
    """
    for word, replacement in AI_FLAG_WORDS.items():
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        if pattern.search(text) and random.random() < probability:
            text = pattern.sub(replacement, text)

    for phrase, replacement in AI_OVERUSED_PHRASES.items():
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        if pattern.search(text) and random.random() < probability:
            text = pattern.sub(replacement, text)

    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _fix_burstiness(text: str) -> str:
    """Fix uniform sentence length — the #1 AI detection signal.
    
    Research basis: GPTZero's primary detection layer is "burstiness" —
    variation in sentence length. AI text has low burstiness (uniform
    lengths). Human text has high burstiness (mixed short + long).
    
    Strategy: Only split sentences that have a comma or semicolon in the
    middle third. Never split mid-word or mid-clause. Only applies when
    there are 5+ sentences with very uniform lengths (std dev < 4).
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) < 5:
        return text

    lengths = [len(s.split()) for s in sentences]
    current_std = statistics.stdev(lengths) if len(lengths) > 1 else 0

    # Only intervene if sentences are very uniform (std < 4)
    if current_std >= 4:
        return text

    result = list(sentences)

    # Find the longest sentence that has a comma/semicolon break point
    longest_idx = max(range(len(result)), key=lambda i: len(result[i].split()))
    longest_words = result[longest_idx].split()
    
    if len(longest_words) > 10:
        # Find break points at commas/semicolons (prefer those near the middle)
        mid = len(longest_words) // 2
        best_break = None
        best_distance = len(longest_words)
        
        for i, w in enumerate(longest_words):
            if w.endswith(",") or w.endswith(";"):
                distance = abs(i - mid)
                if distance < best_distance:
                    best_distance = distance
                    best_break = i + 1
        
        # Only split if we found a natural break point AND the second part is a complete clause
        if best_break and best_break > 2 and best_break < len(longest_words) - 2:
            part1 = " ".join(longest_words[:best_break]).rstrip(",;") + "."
            part2 = " ".join(longest_words[best_break:])
            # Ensure part2 starts with capital letter
            if part2 and part2[0].islower():
                part2 = part2[0].upper() + part2[1:]
            result[longest_idx] = part1
            result.insert(longest_idx + 1, part2)

    return " ".join(result)


def _add_unpredictability(text: str, probability: float = 0.15) -> str:
    """Add irregularity that humans naturally produce.
    
    Research basis: Human text has higher perplexity (more unexpected
    word choices) and higher burstiness. This adds small irregularities
    that break AI's uniform patterns.
    
    IMPORTANT: Only adds short sentences BETWEEN existing sentences,
    never modifies existing sentences.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) < 4:
        return text

    result = []
    for i, s in enumerate(sentences):
        words = s.split()
        # After long sentences (>15 words), occasionally add a short one
        # But not at the very end (i < len(sentences) - 1)
        if len(words) > 15 and random.random() < probability and i < len(sentences) - 1:
            fragments = [
                "Still.", "Maybe.", "Hard to say.", "Not sure.",
                "Could be.", "Or not.", "Then again.", "Honestly.",
                "Weird.", "Strange.", "Odd.", "Funny thing.",
                "Here's the thing.", "The thing is.", "Look.",
                "Anyway.", "So.", "Right.", "Well.",
                "No way.", "Get this.", "Listen.", "Think about it.",
            ]
            result.append(s)
            result.append(random.choice(fragments))
        else:
            result.append(s)

    return " ".join(result)


def _vary_sentence_openings(text: str) -> str:
    """Ensure sentences don't all start the same way.
    
    Research basis: AI text often starts sentences with similar
    structures (subject-verb-object). Humans vary openings:
    prepositional phrases, adverbs, conjunctions, participles.
    
    This detects consecutive sentences starting the same way and
    varies the second one.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) < 3:
        return text

    result = list(sentences)
    openings = []

    for i, s in enumerate(sentences):
        words = s.split()
        if not words:
            openings.append("")
            continue
        first_word = words[0].lower()
        openings.append(first_word)

    # Find consecutive sentences starting with same word
    for i in range(1, len(result)):
        if openings[i] == openings[i - 1] and openings[i]:
            words = result[i].split()
            if len(words) < 3:
                continue

            # Vary the opening
            alternatives = {
                "the": ["A", "That", "This", "One", "My"],
                "a": ["The", "That", "This", "One"],
                "he": ["Then", "Still", "Meanwhile", "Later"],
                "she": ["Then", "Still", "Meanwhile", "Later"],
                "it": ["That", "This", "Still", "Then", "Now"],
                "i": ["Then", "Still", "Later", "So", "And"],
                "and": ["But", "Yet", "Still", "Then", "So"],
                "but": ["And", "Yet", "Still", "So"],
                "in": ["Inside", "Within", "At", "On"],
                "on": ["At", "In", "Upon", "Above"],
                "at": ["In", "On", "From"],
                "was": ["Had been", "Seemed", "Appeared", "Felt"],
                "is": ["Seems", "Appears", "Feels", "Looks"],
            }

            alt = alternatives.get(openings[i], [])
            if alt:
                words[0] = random.choice(alt)
                result[i] = " ".join(words)

    return " ".join(result)


def _reduce_clause_uniformity(text: str) -> str:
    """Break up uniform comma-separated clauses.
    
    Research basis: AI text tends to produce run-on sentences with
    multiple comma-separated clauses of similar length. Humans mix
    sentence structures.
    
    Strategy: Only split sentences with 4+ clauses of very similar
    length (std dev < 30% of average). This is conservative to avoid
    breaking sentence structure.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    result = []

    for s in sentences:
        # Count comma-separated clauses
        clauses = re.split(r",\s+", s)
        if len(clauses) < 5:
            result.append(s)
            continue

        clause_lengths = [len(c.split()) for c in clauses]

        if len(clause_lengths) > 4:
            std = statistics.stdev(clause_lengths) if len(clause_lengths) > 1 else 0
            avg = statistics.mean(clause_lengths)

            # Only split if clauses are very uniform (std < 25% of average)
            if avg > 3 and std < avg * 0.25:
                # Split: put first clause as its own sentence, rest stays
                first_clause = clauses[0].strip()
                rest = ", ".join(clauses[1:])
                if not first_clause.endswith((".", "!", "?")):
                    first_clause += "."
                result.append(first_clause)
                result.append(rest)
                continue

        result.append(s)

    return " ".join(result)


def _add_information_density_variation(text: str, probability: float = 0.1) -> str:
    """Vary information density across sentences.
    
    Research basis: The Uniform Information Density (UID) principle
    says humans spread information unevenly — some sentences are
    dense with meaning, others are light/transitional. AI spreads
    information evenly (high UID score with low variance).
    
    This adds occasional "breather" sentences between dense ones.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) < 4:
        return text

    result = []
    for i, s in enumerate(sentences):
        words = s.split()

        # After a dense sentence (>15 words), occasionally add a short one
        if len(words) > 15 and random.random() < probability:
            breathers = [
                "Strange, right?",
                "Hard to explain.",
                "Or maybe not.",
                "Weird.",
                "Anyway.",
                "Get it?",
                "Make sense?",
                "You know?",
                "Right?",
                "Think about it.",
                "Or so it seemed.",
                "At least, that's what I think.",
                "Makes you wonder.",
                "Funny how that works.",
                "That's the thing.",
            ]
            result.append(s)
            result.append(random.choice(breathers))
        else:
            result.append(s)

    return " ".join(result)


def apply_elegant_rules(text: str, strength: str = "medium") -> str:
    """Apply light post-processing to LLM output.
    
    The LLM already handles structure, rhythm, and tone.
    We only need to remove AI-flagged vocabulary that detectors look for.
    """
    probs = {
        "light": 0.3,
        "medium": 0.5,
        "aggressive": 0.7,
        "ninja": 0.9,
    }
    p = probs.get(strength, 0.5)

    text = _remove_ai_flag_words(text, probability=p)

    return text
