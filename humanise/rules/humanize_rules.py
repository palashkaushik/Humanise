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


_SENTENCE_SPLITTERS = [
    (r",\s+and\s+", ". And "),
    (r",\s+but\s+", ". But "),
    (r",\s+so\s+", ". So "),
    (r",\s+because\s+", ". Because "),
    (r",\s+which\s+", ". Which "),
    (r",\s+while\s+", ". While "),
    (r",\s+although\s+", ". Although "),
    (r",\s+however\s+", ". However, "),
    (r"\s+and\s+", ". And "),
    (r"\s+but\s+", ". But "),
    (r"\s+because\s+", ". Because "),
    (r"\s+while\s+", ". While "),
    (r"\s+although\s+", ". Although "),
    (r";\s+", ". "),
    (r":\s+", ": "),
]


_FRAGMENT_INSERTS = [
    "Not bad.", "Kind of wild.", "Go figure.", "Turns out.",
    "Here's the thing.", "Make of that what you will.",
    "Or so I thought.", "That's the thing.", "Honest answer?",
    "No big deal.", "That's what I thought, anyway.",
    "Well, sort of.", "At least that's the theory.",
]


def _force_fragment(text: str, probability: float = 0.5) -> str:
    """Deterministically split long sentences at conjunctions/commas to create variation.
    This is the 'always runs' rewrite that works even without an LLM."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    result = []
    for s in sentences:
        words = s.split()
        if len(words) > 12 and random.random() < probability:
            for pattern, replacement in _SENTENCE_SPLITTERS:
                if re.search(pattern, s):
                    s = re.sub(pattern, replacement, s, count=1)
                    break
            else:
                mid = len(words) // 2
                s1 = " ".join(words[:mid]).rstrip(",;") + "."
                s2 = " ".join(words[mid:])
                if s2 and s2[0].islower():
                    s2 = s2[0].upper() + s2[1:]
                s = f"{s1} {s2}"
        result.append(s)

    out = " ".join(result)

    if random.random() < probability and len(sentences) > 4:
        sentences = re.split(r"(?<=[.!?])\s+", out)
        idx = random.randint(1, max(1, len(sentences) - 2))
        fragment = random.choice(_FRAGMENT_INSERTS)
        sentences.insert(idx, fragment)
        out = " ".join(sentences)

    return out


def _guaranteed_split(text: str, max_words: int = 16) -> str:
    """Final safety net: split ANY sentence over max_words. Non-probabilistic — always runs."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    result = []
    for s in sentences:
        words = s.split()
        if len(words) <= max_words:
            result.append(s)
            continue

        for pattern, replacement in _SENTENCE_SPLITTERS:
            if re.search(pattern, s):
                s = re.sub(pattern, replacement, s, count=1)
                if len(s.split()) <= max_words:
                    result.append(s)
                    break
        else:
            chunks = []
            remaining = words
            while len(remaining) > max_words:
                split_at = max_words
                for i in range(max_words - 1, max(5, max_words - 6), -1):
                    if i < len(remaining) and remaining[i].lower() in (
                        "and", "but", "so", "because", "when", "if", "while",
                        "although", "though", "since", "unless", "where",
                        "after", "before", "until", "that", "which", "who",
                    ):
                        split_at = i
                        break
                chunk = " ".join(remaining[:split_at]).rstrip(",;") + "."
                chunks.append(chunk)
                remaining = remaining[split_at:]
                if remaining and remaining[0].lower() in ("and", "but", "so", "because", "when", "if", "while", "although", "though", "since", "unless", "where", "after", "before", "until"):
                    remaining = remaining[1:]
            if remaining:
                last = " ".join(remaining)
                if last and last[0].islower():
                    last = last[0].upper() + last[1:]
                if not last.endswith((".", "!", "?")):
                    last += "."
                chunks.append(last)
            result.append(" ".join(chunks))
            continue

        if len(s.split()) > max_words:
            words = s.split()
            chunks = []
            while len(words) > max_words:
                mid = len(words) // 2
                chunks.append(" ".join(words[:mid]).rstrip(",;") + ".")
                words = words[mid:]
            if words:
                last = " ".join(words)
                if not last.endswith((".", "!", "?")):
                    last += "."
                chunks.append(last)
            result.append(" ".join(chunks))
        else:
            result.append(s)
    return " ".join(result)


def _inject_function_words(text: str, probability: float = 0.3) -> str:
    """Add function words (the, a, is, was, of, and, to, in, for, with) to lower AI signal.
    Detectors flag low function-word ratio as AI."""
    sentences = re.split(r"(?<=[.!?])\s+", text)

    for i in range(len(sentences)):
        s = sentences[i]
        words = s.split()
        if len(words) < 3:
            continue

        for j in range(len(words)):
            if random.random() > probability:
                continue
            w = words[j].lower()
            if w in ("jumps", "runs", "walks", "sits", "stands", "looks", "sprints", "hops", "skips"):
                if j == 0 or words[j-1].lower() in ("the", "a", "an", "was", "is", "were", "are"):
                    continue
                if w.endswith("s"):
                    verb = w[:-1] + "ing"
                    words[j] = f"was {verb}"
                break
            if w in ("goes", "comes", "feels", "seems", "appears"):
                if j == 0 or words[j-1].lower() in ("the", "a", "an", "was", "is", "were", "are"):
                    continue
                if w == "goes":
                    words[j] = "was going"
                elif w == "comes":
                    words[j] = "was coming"
                elif w == "feels":
                    words[j] = "was feeling"
                elif w == "seems":
                    words[j] = "was seeming"
                elif w == "appears":
                    words[j] = "was appearing"
                break
        sentences[i] = " ".join(words)

    return " ".join(sentences)


_LOCAL_SYNONYMS = {
    "important": "key",
    "prioritizes": "leans toward",
    "clarify": "spell out",
    "specificity": "the details",
    "nuanced": "tricky",
    "convey": "get across",
    "sophistication": "fancy-sounding",
    "detailed": "thorough",
    "technical": "tech",
    "advanced": "fancy",
    "precise": "exact",
    "imperative": "needed",
    "essential": "must-have",
    "critical": "key",
    "substantive": "real",
    "meticulous": "careful",
    "elaborate": "go into",
    "synthesize": "pull together",
    "pragmatic": "practical",
    "utilitarian": "useful",
    "facilitate": "help",
    "elucidate": "explain",
    "commensurate": "on par with",
    "spontaneity": "life",
    "emotional depth": "feeling",
    "significant": "real",
    "good": "solid",
    "bad": "rough",
    "big": "huge",
    "small": "tiny",
    "happy": "stoked",
    "sad": "bummed",
    "fast": "quick",
    "slow": "sluggish",
    "many": "tons of",
    "few": "not many",
    "often": "a lot",
    "always": "every single time",
    "never": "not once",
    "very": "really",
    "really": "honestly",
    "great": "awesome",
    "nice": "pretty solid",
    "thing": "deal",
    "things": "stuff",
    "think": "figure",
    "said": "was like",
    "told": "let know",
    "went": "headed",
    "got": "grabbed",
    "make": "put together",
    "use": "work with",
    "show": "put on display",
    "help": "a hand",
    "need": "could use",
    "want": "are after",
    "like": "are into",
    "know": "get",
    "see": "catch",
    "look": "check out",
    "find": "track down",
    "give": "hand over",
    "take": "grab",
    "come": "show up",
    "go": "head out",
    "tell": "let in on",
    "ask": "put the question to",
    "try": "give it a shot",
    "start": "kick off",
    "stop": "wrap up",
    "keep": "hang on to",
    "hold": "cling to",
    "put": "stick",
    "turn": "spin",
    "move": "shift",
    "run": "dash",
    "walk": "stroll",
    "sit": "park yourself",
    "stand": "be on your feet",
    "talk": "chat",
    "speak": "yap",
    "write": "jot down",
    "read": "go through",
    "open": "pop open",
    "close": "shut",
    "build": "put up",
    "break": "snap",
    "fix": "patch up",
    "change": "switch up",
    "grow": "balloon",
    "shrink": "contract",
    "rise": "climb",
    "fall": "tumble",
    "push": "shove",
    "pull": "yank",
    "carry": "haul",
    "bring": "tote",
    "leave": "bail out",
    "stay": "hang around",
    "wait": "hold up",
    "follow": "tail",
    "lead": "head up",
    "win": "take it",
    "lose": "drop it",
    "play": "fool around with",
    "work": "put in the time",
    "live": "hang your hat",
    "die": "kick the bucket",
    "feel": "sense",
    "seem": "come across",
    "appear": "show up",
    "happen": "go down",
    "become": "turn into",
    "remain": "stick around",
    "include": "cover",
    "contain": "hold",
    "provide": "hand over",
    "offer": "put on the table",
    "allow": "let",
    "enable": "make possible",
    "require": "call for",
    "suggest": "put out there",
    "explain": "lay out",
    "describe": "paint a picture of",
    "develop": "build out",
    "create": "put together",
    "produce": "turn out",
    "perform": "do",
    "achieve": "pull off",
    "succeed": "make it",
    "fail": "fall flat",
    "improve": "step up",
    "increase": "ramp up",
    "decrease": "dial back",
    "reduce": "trim",
    "add": "toss in",
    "remove": "yank out",
    "include": "cover",
    "exclude": "cut out",
    "consider": "think over",
    "decide": "call it",
    "choose": "pick",
    "select": "single out",
    "prefer": "lean toward",
    "expect": "figure on",
    "remember": "recall",
    "forget": "blank on",
    "realize": "catch on",
    "understand": "get",
    "believe": "buy",
    "doubt": "not buy",
    "wonder": "be curious about",
    "imagine": "picture",
    "suppose": "figure",
    "assume": "take it",
    "admit": "own up",
    "deny": "shot down",
    "refuse": "turn down",
    "accept": "take",
    "agree": "be on board",
    "disagree": "not buy it",
    "argue": "go back and forth",
    "discuss": "talk over",
    "mention": "bring up",
    "notice": "pick up on",
    "recognize": "place",
    "identify": "pin down",
    "discover": "stumble on",
    "reveal": "let slip",
    "hide": "keep under wraps",
    "expose": "lay bare",
    "protect": "watch out for",
    "defend": "stand up for",
    "attack": "go after",
    "support": "back",
    "oppose": "be against",
    "resist": "push back",
    "avoid": "steer clear of",
    "prevent": "put a stop to",
    "allow": "green-light",
    "forbid": "shut down",
    "encourage": "give a push to",
    "discourage": "talk out of",
    "influence": "sway",
    "affect": "hit",
    "impact": "blow",
    "cause": "set off",
    "result": "pan out",
}


def _local_synonym_swap(text: str, probability: float = 0.4) -> str:
    """Replace common words with local synonyms — works without any API."""
    words = re.findall(r"\b[\w']+\b", text)
    word_set = set(w.lower() for w in words)

    def _has_substring_overlap(phrase: str) -> bool:
        phrase_words = set(phrase.lower().split())
        return any(w in word_set for w in phrase_words if w != phrase.lower())

    available = [w for w in _LOCAL_SYNONYMS if w in word_set]
    if not available:
        return text

    out = text
    for word in available:
        replacement = _LOCAL_SYNONYMS[word]
        if _has_substring_overlap(replacement):
            continue
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        matches = list(pattern.finditer(out))
        if not matches:
            continue
        for m in matches:
            if random.random() < probability:
                original = m.group(0)
                if original[0].isupper():
                    replacement_cap = replacement[0].upper() + replacement[1:]
                else:
                    replacement_cap = replacement
                out = out[:m.start()] + replacement_cap + out[m.end():]
                word_set.add(replacement.lower())
                break
    return out


def _conciseness_pass(text: str) -> str:
    for pattern, replacement in VERBOSE_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\s+,", ",", text)
    return text.strip()


def _active_voice_pass(text: str, probability: float = 0.5) -> str:
    """Disabled — regex-based active/passive conversion produces broken output.
    Kept as a no-op for API compatibility."""
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
            if len(s.split()) > 10:
                continue
            word = random.choice(EVALUATIVE_WORDS)
            sentences[i] = f"{word.capitalize()}, {s[0].lower()}{s[1:]}" if len(s) > 1 else s
    return " ".join(sentences)


def _strip_conclusions(text: str) -> str:
    for pattern in CONCLUSION_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _break_perfect_grammar(text: str, probability: float = 0.3) -> str:
    """Break AI's grammatically perfect text by starting sentences with conjunctions
    and adding fragments. GPTZero flags text that 'lacks creative deviations.'"""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) < 4:
        return text

    result = []
    for i, s in enumerate(sentences):
        words = s.split()
        if len(words) < 3:
            result.append(s)
            continue

        if random.random() < probability and i > 0:
            # Start with a conjunction
            conj = random.choice(["And ", "But ", "So ", "Yet ", "Still "])
            result.append(f"{conj}{s[0].lower()}{s[1:]}")
        elif random.random() < probability * 0.5 and len(words) > 10:
            # Break into a fragment + full sentence
            mid = len(words) // 2
            frag = " ".join(words[:mid]).rstrip(",;") + "."
            rest = " ".join(words[mid:])
            if rest and rest[0].islower():
                rest = rest[0].upper() + rest[1:]
            result.append(frag)
            result.append(rest)
        else:
            result.append(s)

    return " ".join(result)


def _add_informal_openers(text: str, probability: float = 0.15) -> str:
    """Add informal sentence openers to break the 'too precise' pattern."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) < 5:
        return text

    openers = [
        "Honestly, ", "Look, ", "Thing is, ", "Mind you, ",
        "Turns out, ", "Weirdly, ", "Surprisingly, ", "Oddly, ",
        "To be fair, ", "In fairness, ", "Funny thing is, ",
    ]

    result = []
    for i, s in enumerate(sentences):
        if random.random() < probability and i > 0 and not s.startswith(("I ", "He ", "She ", "It ", "The ", "A ")):
            opener = random.choice(openers)
            result.append(f"{opener}{s[0].lower()}{s[1:]}")
        else:
            result.append(s)

    return " ".join(result)


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
            "force_fragment": 0.3,
            "local_synonyms": 0.3,
            "grammar_break": 0.2,
            "informal_openers": 0.1,
        },
        "medium": {
            "conciseness": True,
            "strip_conclusions": True,
            "active_voice": True,
            "triplets": True,
            "subjectivity": 0.06,
            "paragraphs": (0.25, 0.2),
            "logic_reorder": 0.2,
            "force_fragment": 0.5,
            "local_synonyms": 0.4,
            "grammar_break": 0.3,
            "informal_openers": 0.15,
        },
        "aggressive": {
            "conciseness": True,
            "strip_conclusions": True,
            "active_voice": True,
            "triplets": True,
            "subjectivity": 0.08,
            "paragraphs": (0.4, 0.3),
            "logic_reorder": 0.3,
            "force_fragment": 0.7,
            "local_synonyms": 0.5,
            "grammar_break": 0.4,
            "informal_openers": 0.2,
        },
        "ninja": {
            "conciseness": True,
            "strip_conclusions": True,
            "active_voice": True,
            "triplets": True,
            "subjectivity": 0.1,
            "paragraphs": (0.5, 0.4),
            "logic_reorder": 0.4,
            "force_fragment": 0.85,
            "local_synonyms": 0.6,
            "grammar_break": 0.5,
            "informal_openers": 0.25,
        },
    }
    cfg = config.get(strength, config["medium"])

    # GPTZero: break perfect grammar first
    text = _break_perfect_grammar(text, probability=cfg.get("grammar_break", 0.3))
    text = _add_informal_openers(text, probability=cfg.get("informal_openers", 0.15))

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
    text = _force_fragment(text, probability=cfg["force_fragment"])
    text = _local_synonym_swap(text, probability=cfg["local_synonyms"])
    text = _reorder_sentence_logic(text, probability=cfg["logic_reorder"])
    text = _inject_subjectivity(text, probability=cfg["subjectivity"])
    text = _inject_function_words(text, probability=0.3)

    max_words = {"light": 18, "medium": 16, "aggressive": 14, "ninja": 12}.get(strength, 16)
    text = _guaranteed_split(text, max_words=max_words)

    return text
