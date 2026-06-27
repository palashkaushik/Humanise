import re
import random

SYNONYM_DB = {
    "important": ["critical", "key", "central", "vital", "serious", "big", "the kind that matters", "the one you remember"],
    "significant": ["meaningful", "notable", "sizable", "real", "genuine", "hard to miss"],
    "however": ["but", "though", "still", "yet", "that said", "then again"],
    "therefore": ["so", "thus", "as a result", "which means", "that's why"],
    "additionally": ["also", "plus", "on top of that", "and", "then there's"],
    "consequently": ["so", "as a result", "which leads to", "meaning", "and now"],
    "substantial": ["large", "big", "sizable", "decent", "real", "no small thing"],
    "demonstrate": ["show", "point to", "make clear", "reveal", "prove"],
    "implement": ["build", "put in place", "set up", "roll out", "get going"],
    "leverage": ["use", "draw on", "tap into", "put to work", "make use of"],
    "optimize": ["improve", "tune", "sharpen", "tighten up", "refine", "make better"],
    "facilitate": ["help", "enable", "make possible", "ease", "speed up"],
    "utilize": ["use", "apply", "employ", "put to work", "make use of"],
    "comprehensive": ["full", "complete", "thorough", "in-depth", "no stone unturned"],
    "robust": ["strong", "solid", "reliable", "tough", "capable", "built to last"],
    "seamless": ["smooth", "clean", "effortless", "natural", "no hiccups"],
    "innovative": ["new", "fresh", "creative", "novel", "different", "something else"],
    "paradigm": ["model", "pattern", "way of thinking", "approach"],
    "methodology": ["approach", "method", "way", "process", "how we did it"],
    "framework": ["structure", "system", "setup", "skeleton"],
    "landscape": ["scene", "world", "space", "field", "playing field"],
    "synergy": ["collaboration", "combined effect", "teamwork", "working together"],
    "crucial": ["vital", "key", "critical", "central", "make-or-break"],
    "ensure": ["make sure", "guarantee", "lock in", "secure", "nail down"],
    "enhance": ["boost", "improve", "strengthen", "build up", "level up"],
    "navigate": ["steer through", "work through", "find a way through", "muddle through"],
    "unprecedented": ["never seen before", "unheard of", "new ground", "first time for everything"],
    "transformative": ["life-changing", "redefining", "remaking", "big"],
    "fundamentally": ["at its core", "really", "basically", "when you strip it down"],
    "ultimately": ["in the end", "finally", "when it comes down to it", "at the end of the day"],
    "nevertheless": ["still", "even so", "regardless", "that said"],
    "regarding": ["about", "on", "around", "concerning", "when it comes to"],
    "impact": ["effect", "influence", "fallout", "result", "what happened because of it"],
    "component": ["piece", "part", "element", "layer", "building block"],
    "streamline": ["simplify", "speed up", "cut through", "clean up"],
    "foster": ["encourage", "build", "nurture", "spark", "grow"],
    "empower": ["enable", "equip", "give the tools to", "set free"],
    "established": ["set up", "built", "put in place", "created", "started"],
    "remarkable": ["notable", "impressive", "striking", "hard to ignore", "standout"],
    "extraordinary": ["unusual", "rare", "out of the ordinary", "something else", "wild"],
    "substantial": ["large", "big", "decent", "real", "significant", "no small amount"],
    # GPTZero-flagged: purple prose vocabulary
    "tenebrous": ["dark", "shadowy", "dim", "gloomy"],
    "ethereal": ["faint", "delicate", "light", "soft"],
    "unearthly": ["strange", "odd", "weird", "eerie"],
    "guttural": ["rough", "harsh", "gravelly", "raspy"],
    "pronouncement": ["voice", "words", "statement"],
    "celestial": ["sky", "starry", "heavenly"],
    "cosmic": ["huge", "massive", "enormous", "universal"],
    # GPTZero-flagged: body reaction cliches
    "clenched": ["tight", "gripped", "curled", "balled"],
    "quickened": ["sped up", "got faster", "raced"],
    "tingled": ["prickled", "went numb", "buzzed"],
    "crawled": ["crept", "moved", "shifted"],
}

DELETABLE_PHRASES = [
    "it should be noted that", "it is worth noting that",
    "it is important to note that", "needless to say",
    "it goes without saying that", "in order to",
    "in the context of", "with regard to",
    "in terms of", "in the process of",
    "it is imperative that", "it is essential to note",
    "it goes without saying", "it bears mentioning",
    "it is worth highlighting", "it should be emphasized",
]

AI_STARTER_PATTERNS = [
    (r"^(In today's world,?\s*)", ""),
    (r"^(In this article,?\s*)", ""),
    (r"^(In this guide,?\s*)", ""),
    (r"^(In this post,?\s*)", ""),
    (r"^(When it comes to\s+)", ""),
    (r"^(It is worth noting that\s+)", ""),
    (r"^(It goes without saying that\s+)", ""),
    (r"^(As we move forward,?\s*)", ""),
    (r"^(With the advent of\s+)", ""),
    (r"^(In the realm of\s+)", ""),
    (r"^(The world of\s+)", ""),
    (r"^(One of the most\s+)", ""),
    (r"^(It's no secret that\s+)", ""),
    (r"^(There's no denying that\s+)", ""),
]

FRAGMENTS_TO_INJECT = [
    "Not bad.", "Kind of wild.", "That's the thing.",
    "Honestly? It works.", "Go figure.", "Strange but true.",
    "Or so I thought.", "Turns out.", "Here's the kicker.",
    "And just like that.", "No big deal.", "Well, sort of.",
    "That happened.", "Make of that what you will.",
    "At least that's the theory.", "If you say so.",
]

TRANSITIONS_TO_ADD = [
    "But then again — ", "So anyway, ", "The thing is, ",
    "Look, ", "Here's what happened: ", "What I mean is, ",
    "The way I see it, ", "From where I'm standing, ",
    "If I'm being honest, ", "Not gonna lie, ",
    "Come to think of it, ", "Now that I mention it, ",
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


def _remove_ai_starters(text: str) -> str:
    for pattern, replacement in AI_STARTER_PATTERNS:
        text = re.sub(pattern, replacement, text, count=1)
    return text


def _vary_sentence_lengths(paragraph: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    if len(sentences) < 2:
        return paragraph

    result = []
    for s in sentences:
        words = s.split()
        if len(words) > 16:
            # Split long sentences into 2-3 chunks at natural break points
            # Prefer splitting at conjunctions (and, but, so, because, when, if)
            conjunction_pattern = re.compile(
                r"\s+(and|but|so|because|when|if|while|although|though|since|unless|where|after|before|until)\s+",
                re.IGNORECASE,
            )
            parts = conjunction_pattern.split(" ".join(words))
            if len(parts) > 2:
                # Reconstruct: parts come in pairs [before, conj, after, conj, after...]
                chunks = []
                i = 0
                current_chunk = []
                while i < len(parts):
                    current_chunk.append(parts[i])
                    i += 1
                    if i < len(parts) and parts[i].lower() in ("and", "but", "so", "because", "when", "if", "while", "although", "though", "since", "unless", "where", "after", "before", "until"):
                        # Check if current chunk is long enough to split here
                        if len(current_chunk) >= 10:
                            chunks.append(" ".join(current_chunk).rstrip(",;") + ".")
                            current_chunk = [parts[i], parts[i + 1]] if i + 1 < len(parts) else []
                            i += 2
                        else:
                            current_chunk.append(parts[i])
                            if i + 1 < len(parts):
                                current_chunk.append(parts[i + 1])
                            i += 2
                    i += 1
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                # Cap chunk length at 15 words
                final_chunks = []
                for chunk in chunks:
                    chunk_words = chunk.split()
                    while len(chunk_words) > 15:
                        mid = len(chunk_words) // 2
                        part1 = " ".join(chunk_words[:mid]).rstrip(",;") + "."
                        part2 = " ".join(chunk_words[mid:])
                        if part2 and part2[0].islower():
                            part2 = part2[0].upper() + part2[1:]
                        final_chunks.append(part1)
                        chunk_words = part2.split()
                    if chunk_words:
                        final_chunks.append(" ".join(chunk_words))
                result.extend(final_chunks)
            else:
                # No conjunctions found — split at midpoint
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
        else:
            result.append(s)

    return " ".join(result)


def _insert_fragments(paragraph: str, count: int) -> str:
    if count <= 0 or len(paragraph) < 60:
        return paragraph

    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    if len(sentences) < 3:
        return paragraph

    for _ in range(count):
        if len(sentences) > 3:
            idx = random.randint(1, len(sentences) - 2)
            fragment = random.choice(FRAGMENTS_TO_INJECT)
            sentences.insert(idx, fragment)

    return " ".join(sentences)


def _add_hedging_and_transitions(paragraph: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    if len(sentences) < 4:
        return paragraph

    if random.random() < 0.25 and len(sentences) > 2:
        idx = random.randint(1, len(sentences) - 1)
        transition = random.choice(TRANSITIONS_TO_ADD)
        sentences[idx] = f"{transition}{sentences[idx][0].lower()}{sentences[idx][1:]}" if len(sentences[idx]) > 1 else sentences[idx]

    return " ".join(sentences)


def _add_typos(text: str, probability: float = 0.02) -> str:
    typo_map = {
        "the ": ["teh ", "hte "],
        "their ": ["theri ", "thier "],
        "your ": ["you're "],
        "its ": ["it's "],
        "than ": ["then "],
        "then ": ["than "],
        "your ": ["youre "],
        "were ": ["we're "],
        "its ": ["ist "],
    }

    words = text.split()
    for i in range(len(words)):
        for correct, typos in typo_map.items():
            if words[i].lower() == correct.strip() and random.random() < probability:
                words[i] = random.choice(typos)
                break

    return " ".join(words)


def _add_colloquialisms(text: str, probability: float = 0.15) -> str:
    colloquialisms = [
        ("a lot", "a ton"),
        ("very", "really"),
        ("quite", "pretty"),
        ("seems to be", "looks like"),
        ("appears to be", "seems like"),
        ("it is clear that", "you can tell that"),
        ("it is evident that", "obviously"),
        ("in my opinion", "I think"),
        ("for the most part", "mostly"),
        ("at this point", "now"),
        ("in the future", "later"),
        ("in the past", "before"),
        ("as a result", "so"),
        ("due to the fact that", "because"),
        ("in spite of", "despite"),
        ("at the end of the day", "ultimately"),
        ("the fact that", "that"),
        ("in order to", "to"),
        ("on a regular basis", "regularly"),
        ("at the present time", "now"),
]

    for original, replacement in colloquialisms:
        pattern = re.compile(re.escape(original), re.IGNORECASE)
        text = pattern.sub(
            lambda m, r=replacement: r if random.random() < probability else m.group(0),
            text,
        )

    return text


def _shuffle_sentence_order(text: str, probability: float = 0.1) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) < 5:
        return text

    for i in range(len(sentences) - 1):
        if random.random() < probability:
            sentences[i], sentences[i + 1] = sentences[i + 1], sentences[i]

    return " ".join(sentences)


def scramble(text: str, strength: str = "medium") -> str:
    config = {
        "light": {"synonym_prob": 0.2, "fragment_count": 0, "vary_sentences": False,
                  "typo_prob": 0.0, "colloquial_prob": 0.1, "shuffle_prob": 0.0},
        "medium": {"synonym_prob": 0.4, "fragment_count": 1, "vary_sentences": True,
                   "typo_prob": 0.01, "colloquial_prob": 0.2, "shuffle_prob": 0.05},
        "aggressive": {"synonym_prob": 0.6, "fragment_count": 2, "vary_sentences": True,
                       "typo_prob": 0.02, "colloquial_prob": 0.3, "shuffle_prob": 0.1},
        "ninja": {"synonym_prob": 0.75, "fragment_count": 3, "vary_sentences": True,
                  "typo_prob": 0.03, "colloquial_prob": 0.4, "shuffle_prob": 0.15},
    }
    cfg = config.get(strength, config["medium"])

    text = _remove_filler(text)
    text = _remove_ai_starters(text)
    text = _scramble_synonyms(text, cfg["synonym_prob"])
    text = _add_colloquialisms(text, cfg["colloquial_prob"])

    if cfg["typo_prob"] > 0:
        text = _add_typos(text, cfg["typo_prob"])

    paragraphs = re.split(r"\n\s*\n", text)
    processed = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if cfg["vary_sentences"]:
            para = _vary_sentence_lengths(para)
        para = _insert_fragments(para, cfg["fragment_count"])
        para = _add_hedging_and_transitions(para)
        processed.append(para)

    text = "\n\n".join(processed)

    if cfg["shuffle_prob"] > 0:
        text = _shuffle_sentence_order(text, cfg["shuffle_prob"])

    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\s+,", ",", text)

    return text.strip()
