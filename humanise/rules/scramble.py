import re
import random

SYNONYM_DB = {
    "important": ["critical", "key", "central", "vital", "serious", "big"],
    "significant": ["meaningful", "notable", "sizable", "real", "genuine"],
    "however": ["but", "though", "still", "yet", "that said"],
    "therefore": ["so", "thus", "as a result", "which means"],
    "additionally": ["also", "plus", "on top of that", "and"],
    "consequently": ["so", "as a result", "which leads to", "meaning"],
    "substantial": ["large", "big", "sizable", "decent", "real"],
    "demonstrate": ["show", "point to", "make clear", "reveal"],
    "implement": ["build", "put in place", "set up", "roll out"],
    "leverage": ["use", "draw on", "tap into", "put to work"],
    "optimize": ["improve", "tune", "sharpen", "tighten up", "refine"],
    "facilitate": ["help", "enable", "make possible", "ease"],
    "utilize": ["use", "apply", "employ", "put to work"],
    "comprehensive": ["full", "complete", "thorough", "in-depth"],
    "robust": ["strong", "solid", "reliable", "tough", "capable"],
    "seamless": ["smooth", "clean", "effortless", "natural"],
    "innovative": ["new", "fresh", "creative", "novel", "different"],
    "paradigm": ["model", "pattern", "way of thinking"],
    "methodology": ["approach", "method", "way", "process"],
    "framework": ["structure", "system", "setup"],
    "landscape": ["scene", "world", "space", "field"],
    "synergy": ["collaboration", "combined effect", "teamwork"],
    "crucial": ["vital", "key", "critical", "central"],
    "ensure": ["make sure", "guarantee", "lock in", "secure"],
    "enhance": ["boost", "improve", "strengthen", "build up"],
    "navigate": ["steer through", "work through", "find a way through"],
    "unprecedented": ["never seen before", "unheard of", "new ground"],
    "transformative": ["life-changing", "redefining", "remaking"],
    "fundamentally": ["at its core", "really", "basically"],
    "ultimately": ["in the end", "finally", "when it comes down to it"],
    "nevertheless": ["still", "even so", "regardless"],
    "regarding": ["about", "on", "around", "concerning"],
    "impact": ["effect", "influence", "fallout", "result"],
    "component": ["piece", "part", "element", "layer"],
    "streamline": ["simplify", "speed up", "cut through"],
    "foster": ["encourage", "build", "nurture", "spark"],
    "empower": ["enable", "equip", "give the tools to"],
    "established": ["set up", "built", "put in place", "created"],
}

DELETABLE_PHRASES = [
    "it should be noted that", "it is worth noting that",
    "it is important to note that", "needless to say",
    "it goes without saying that", "in order to",
    "in the context of", "with regard to",
    "in terms of", "in the process of",
]


def _scramble_synonyms(text: str, probability: float) -> str:
    for word, alternatives in sorted(SYNONYM_DB.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        text = pattern.sub(
            lambda m, pool=alternatives, p=probability: (
                random.choice(pool) if random.random() < p else m.group(0)
            ),
            text,
        )
    return text


def _remove_filler(text: str) -> str:
    for phrase in DELETABLE_PHRASES:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        text = pattern.sub("", text)
    return text


def _vary_sentence_lengths(paragraph: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    if len(sentences) < 3:
        return paragraph

    result = []
    i = 0
    while i < len(sentences):
        s = sentences[i]
        words = s.split()
        if len(words) > 22 and i + 1 < len(sentences):
            mid = len(words) // 2
            s1 = " ".join(words[:mid]).rstrip(",;")
            if not s1.endswith((".", "!", "?")):
                s1 += "."
            s2 = " ".join(words[mid:])
            if s2 and s2[0].islower():
                s2 = s2[0].upper() + s2[1:]
            if not s2.endswith((".", "!", "?")):
                s2 += "."
            result.append(s1)
            result.append(s2)
            i += 1
        elif len(words) <= 6 and i + 1 < len(sentences):
            next_words = sentences[i + 1].split()
            if next_words and len(next_words) <= 8:
                next_words[0] = next_words[0].lower()
                combined = s.rstrip(".") + " and " + " ".join(next_words)
                if not combined.endswith((".", "!", "?")):
                    combined += "."
                result.append(combined)
                i += 2
                continue
            result.append(s)
            i += 1
        else:
            result.append(s)
            i += 1

    return " ".join(result)


def _insert_noise(paragraph: str, count: int) -> str:
    if count <= 0:
        return paragraph
    noises = ["I think.", "Honestly.", "Really.", "No, seriously.",
              "Here's what I mean.", "Let me put it this way.",
              "You know what I mean?", "Think about it."]
    for _ in range(count):
        if len(paragraph) > 40:
            noise = random.choice(noises)
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            if len(sentences) > 2:
                idx = random.randint(1, len(sentences) - 1)
                sentences.insert(idx, noise)
                paragraph = " ".join(sentences)
    return paragraph


def scramble(text: str, strength: str = "medium") -> str:
    config = {
        "light": {"synonym_prob": 0.15, "noise_count": 0, "vary_sentences": False},
        "medium": {"synonym_prob": 0.3, "noise_count": 0, "vary_sentences": True},
        "aggressive": {"synonym_prob": 0.5, "noise_count": 0, "vary_sentences": True},
        "ninja": {"synonym_prob": 0.65, "noise_count": 0, "vary_sentences": True},
    }
    cfg = config.get(strength, config["medium"])

    text = _remove_filler(text)
    text = _scramble_synonyms(text, cfg["synonym_prob"])

    paragraphs = re.split(r"\n\s*\n", text)
    processed = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if cfg["vary_sentences"]:
            para = _vary_sentence_lengths(para)
        para = _insert_noise(para, cfg["noise_count"])
        processed.append(para)

    text = "\n\n".join(processed)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\s+,", ",", text)

    return text.strip()
