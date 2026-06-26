import re
import random


VERBOSE_REPLACEMENTS = {
    r"\bin order to\b": "to",
    r"\bdue to the fact that\b": "because",
    r"\bat this point in time\b": "now",
    r"\ba large number of\b": "many",
    r"\bthe majority of\b": "most",
    r"\bin the event that\b": "if",
    r"\bwith regard to\b": "about",
    r"\bin spite of the fact that\b": "although",
    r"\bit is important to note that\b": "",
    r"\bit should be noted that\b": "",
    r"\bas a matter of fact\b": "",
    r"\bfor the purpose of\b": "to",
    r"\bwith the exception of\b": "except",
    r"\bin close proximity to\b": "near",
    r"\bat the present time\b": "now",
    r"\bin light of the fact that\b": "because",
    r"\bon the grounds that\b": "because",
    r"\bin the near future\b": "soon",
    r"\ba great deal of\b": "much",
    r"\bhas the ability to\b": "can",
    r"\bis able to\b": "can",
    r"\bwere able to\b": "could",
    r"\bin the case of\b": "for",
    r"\bin a manner that\b": "like",
    r"\bfor the reason that\b": "because",
    r"\bnot only\b": "",
    r"\bbut also\b": "and",
    r"\bin spite of\b": "despite",
    r"\bprior to\b": "before",
    r"\bsubsequent to\b": "after",
    r"\bin the process of\b": "",
    r"\ba number of\b": "several",
    r"\bmajority of\b": "most",
    r"\bthe question as to whether\b": "whether",
    r"\bthere is no doubt that\b": "",
    r"\bit is clear that\b": "",
    r"\bneedless to say\b": "",
    r"\bit is obvious that\b": "",
}


CONCLUSION_PATTERNS = [
    r"^In conclusion,?\s*",
    r"^To conclude,?\s*",
    r"^To summarize,?\s*",
    r"^In summary,?\s*",
    r"^Overall,?\s*",
    r"^All in all,?\s*",
    r"^To wrap up,?\s*",
    r"^In closing,?\s*",
    r"^Ultimately,?\s*",
    r"^Finally,?\s*",
    r"^In the end,?\s*",
    r"^All things considered,?\s*",
    r"^To sum up,?\s*",
    r"\.\s*In conclusion,?\s*",
    r"\.\s*To conclude,?\s*",
    r"\.\s*To summarize,?\s*",
    r"\.\s*In summary,?\s*",
    r"\.\s*Overall,?\s*",
    r"\.\s*All in all,?\s*",
    r"\.\s*To wrap up,?\s*",
    r"\.\s*In closing,?\s*",
]


EVALUATIVE_WORDS = [
    "honestly", "clearly", "notably", "interestingly",
    "remarkably", "surprisingly", "admittedly", "frankly",
    "obviously", "unfortunately", "fortunately", "luckily",
    "unluckily", "predictably", "oddly", "strangely",
]


PASSIVE_PATTERNS = [
    (r"\b(\w+(?:\s+\w+){0,2})\s+was\s+(\w+)\s+by\s+(\w+(?:\s+\w+){0,2})\b", r"\3 \2 \1"),
    (r"\b(\w+(?:\s+\w+){0,2})\s+is\s+(\w+)\s+by\s+(\w+(?:\s+\w+){0,2})\b", r"\3 \2s \1"),
    (r"\b(\w+(?:\s+\w+){0,2})\s+were\s+(\w+)\s+by\s+(\w+(?:\s+\w+){0,2})\b", r"\3 \2 \1"),
    (r"\b(\w+(?:\s+\w+){0,2})\s+are\s+(\w+)\s+by\s+(\w+(?:\s+\w+){0,2})\b", r"\3 \2s \1"),
]


LOGIC_REORDERS = [
    (r"\bThe reason is\b", "What happened is"),
    (r"\bThe result is\b", "What came of it was"),
    (r"\bThe problem is\b", "Here's the problem:"),
    (r"\bThe issue is\b", "Here's the issue:"),
    (r"\bThe answer is\b", "Here's the answer:"),
    (r"\bThe truth is\b", "Honestly,"),
    (r"\bThe fact is\b", "Here's the thing:"),
]


def _break_triplets(text: str, probability: float = 0.7) -> str:
    pattern = re.compile(
        r"\b(\w+(?:\s+\w+){0,2}),\s+(\w+(?:\s+\w+){0,2}),\s+and\s+(\w+(?:\s+\w+){0,2})\b"
    )
    def replace(m):
        if random.random() > probability:
            return m.group(0)
        x, y, z = m.group(1), m.group(2), m.group(3)
        y_cap = y[0].upper() + y[1:] if y else y
        z_cap = z[0].upper() + z[1:] if z else z
        return f"{x}. {y_cap}. And {z_cap}."
    return pattern.sub(replace, text)


def _vary_paragraph_lengths(text: str, split_prob: float = 0.4, merge_prob: float = 0.3) -> str:
    paragraphs = re.split(r"\n\s*\n", text)
    result = []
    i = 0
    while i < len(paragraphs):
        para = paragraphs[i].strip()
        if not para:
            i += 1
            continue
        sentences = re.split(r"(?<=[.!?])\s+", para)
        if len(sentences) > 5 and random.random() < split_prob:
            mid = len(sentences) // 2
            result.append(" ".join(sentences[:mid]))
            result.append(" ".join(sentences[mid:]))
        elif len(sentences) <= 2 and i + 1 < len(paragraphs) and random.random() < merge_prob:
            next_para = paragraphs[i + 1].strip()
            if next_para:
                result.append(para + " " + next_para)
                i += 2
                continue
            result.append(para)
        else:
            result.append(para)
        i += 1
    return "\n\n".join(result)


def _conciseness_pass(text: str) -> str:
    for pattern, replacement in VERBOSE_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\s+,", ",", text)
    return text.strip()


def _active_voice_pass(text: str, probability: float = 0.5) -> str:
    def try_replace(match):
        if random.random() > probability:
            return match.group(0)
        return match.expand(match.re.pattern.replace("\\w+(?:\\s+\\w+){0,2}", "").replace("\\b", "").replace("(?", "(?P<"))
    for pattern, replacement in PASSIVE_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _reorder_sentence_logic(text: str, probability: float = 0.3) -> str:
    def maybe_replace(m):
        if random.random() > probability:
            return m.group(0)
        return m.expand(replacement)
    for pattern, replacement in LOGIC_REORDERS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _inject_subjectivity(text: str, probability: float = 0.08) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) < 3:
        return text
    for i in range(len(sentences)):
        if random.random() < probability:
            s = sentences[i]
            if not s:
                continue
            starts_eval = any(s.lower().startswith(w) for w in EVALUATIVE_WORDS)
            if starts_eval:
                continue
            word = random.choice(EVALUATIVE_WORDS)
            sentences[i] = f"{word.capitalize()}, {s[0].lower()}{s[1:]}" if len(s) > 1 else s
    return " ".join(sentences)


def _strip_conclusions(text: str) -> str:
    for pattern in CONCLUSION_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def humanize_rules(text: str, strength: str = "medium") -> str:
    config = {
        "light": {
            "conciseness": True,
            "strip_conclusions": True,
            "active_voice": False,
            "triplets": False,
            "subjectivity": 0.03,
            "paragraphs": (0.1, 0.1),
            "logic_reorder": 0.1,
        },
        "medium": {
            "conciseness": True,
            "strip_conclusions": True,
            "active_voice": True,
            "triplets": True,
            "subjectivity": 0.06,
            "paragraphs": (0.25, 0.2),
            "logic_reorder": 0.2,
        },
        "aggressive": {
            "conciseness": True,
            "strip_conclusions": True,
            "active_voice": True,
            "triplets": True,
            "subjectivity": 0.08,
            "paragraphs": (0.4, 0.3),
            "logic_reorder": 0.3,
        },
        "ninja": {
            "conciseness": True,
            "strip_conclusions": True,
            "active_voice": True,
            "triplets": True,
            "subjectivity": 0.1,
            "paragraphs": (0.5, 0.4),
            "logic_reorder": 0.4,
        },
    }
    cfg = config.get(strength, config["medium"])

    if cfg["strip_conclusions"]:
        text = _strip_conclusions(text)
    if cfg["conciseness"]:
        text = _conciseness_pass(text)
    if cfg["active_voice"]:
        text = _active_voice_pass(text, probability=0.4 if strength in ("aggressive", "ninja") else 0.25)
    if cfg["triplets"]:
        text = _break_triplets(text, probability=0.7 if strength in ("aggressive", "ninja") else 0.5)
    split_p, merge_p = cfg["paragraphs"]
    text = _vary_paragraph_lengths(text, split_prob=split_p, merge_prob=merge_p)
    text = _reorder_sentence_logic(text, probability=cfg["logic_reorder"])
    text = _inject_subjectivity(text, probability=cfg["subjectivity"])

    return text
