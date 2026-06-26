import re
import random

AI_VOCABULARY_SWAPS = {
    r"\butilize(s|d)?\b": r"use\1",
    r"\bfacilitate(s|d)?\b": r"help\1",
    r"\bleverage(s|d)?\b": r"use",
    r"\bdemonstrate(s|d)?\b": r"show\1",
    r"\bcomprehensive\b": "full",
    r"\binnovative\b": "new",
    r"\boptimize\b": "improve",
    r"\bsubsequently\b": "then",
    r"\badditionally\b": "also",
    r"\btherefore\b": "so",
    r"\bfurthermore\b": "plus",
    r"\bnevertheless\b": "still",
    r"\bnonetheless\b": "still",
    r"\bin conclusion\b": "in the end",
    r"\bit is important to note that\b": "",
    r"\bit should be noted that\b": "",
    r"\bit is worth noting that\b": "",
    r"\bit is imperative that\b": "we need to",
    r"\ba comprehensive range of\b": "a range of",
    r"\ba wide variety of\b": "various",
    r"\bin order to\b": "to",
    r"\bin the event that\b": "if",
    r"\bprior to\b": "before",
    r"\bsubsequent to\b": "after",
    r"\bin the context of\b": "in",
    r"\bwith regard to\b": "about",
    r"\bin terms of\b": "in",
    r"\bin the process of\b": "",
    r"\bplays? a (crucial|key|vital|significant|critical|pivotal|important|essential) role\b": "matters",
    r"\bdelve[s]? into\b": "explore",
    r"\bunprecedented\b": "rare",
    r"\btransformative\b": "big",
    r"\bcutting[\s-]edge\b": "new",
    r"\bgame[\s-]chang(er|ing)\b": "breakthrough",
    r"\brobust\b": "strong",
    r"\bseamless\b": "smooth",
    r"\bsynerg(y|ies|istic)\b": "teamwork",
    r"\bparadigm\b": "model",
    r"\bmethodology\b": "method",
    r"\bframework\b": "system",
    r"\blandscape\b": "world",
    r"\bmultifaceted\b": "complex",
    r"\bharness(ing)?\b": "use",
    r"\bempower(s|ed|ing)?\b": "enable\1",
    r"\bfoster(s|ed|ing)?\b": "build\1",
    r"\bnavigate(s|d|ing)?\b": "work through",
    r"\bstreamline(s|d|ing)?\b": "simplify",
    r"\benhance(s|d|ing)?\b": "improve",
    r"\bensure(s|d)?\b": "make sure",
    r"\bestablish(ed|es|ing)?\b": "set up",
    r"\bimpact(s|ed|ing)?\b": "affect",
    r"\bcomponent(s)?\b": "part\1",
    r"\bregarding\b": "about",
    r"\bnevertheless\b": "but",
    r"\bimpactful\b": "big",
    r"\bsubstantial\b": "large",
    r"\bremarkable\b": "notable",
    r"\bextraordinary\b": "unusual",
    r"\bfundamentally\b": "basically",
    r"\bultimately\b": "in the end",
    # Wikipedia AI indicators - significance/legacy patterns
    r"\b(stands|serves)\s+as\s+(a|an|the)\s+(testament|reminder|symbol|example)\b": "is a type of",
    r"\bis\s+a\s+testament\s+to\b": "shows how",
    r"\b(underscores?|highlights?)\s+(its|their|the)\s+(importance|significance|role)\b": "shows that matters",
    r"\breflects?\s+(the|a|its|their)\s+(broader|wider)\b": "matches",
    r"\bsymboliz(e|ing|ed)\s+(its|their|the)\s+(enduring|lasting)\b": "shows that still lasts",
    r"\bcontribut(e|ing|ed)\s+to\s+the\b": "adds to",
    r"\bsetting\s+the\s+stage\s+for\b": "leading to",
    r"\b(mark|marking|shape|shaping)\s+(the|a|an)\s+(beginning|start|dawn|era|age|transition|shift)\b": "starts a",
    r"\bevolving\s+landscape\b": "changing world",
    r"\bfocal\s+point\b": "center",
    r"\bindelible\s+mark\b": "lasting effect",
    r"\bdeeply\s+rooted\b": "old",
    r"\bkey\s+turning\s+point\b": "big change",
    # Promotional language - Wikipedia flags this as superficial
    r"\b(vibrant|rich|profound)\s+(community|culture|heritage|tradition|history|tapestry|mosaic)\b": "nice place",
    r"\bboasts?\s+a\b": "has a",
    r"\bnestled\s+(in|at|within|among)\b": "in",
    r"\bin\s+the\s+heart\s+of\b": "in",
    r"\b(groundbreaking|renowned)\s+(research|discovery|innovation|contribution|work)\b": "new",
    r"\bdiverse\s+array\s+of\b": "many",
    r"\bcommitment\s+to\b": "promise to",
    r"\bnatural\s+beauty\b": "nice scenery",
    r"\b(maintains?\s+an?\s+active|strong|significant)\s+(social\s+media|digital)\s+presence\b": "uses social media",
    # AI-era vocabulary from Wikipedia research
    r"\bdelve[s]?\s+(into|deeper)\b": r"explore \1",
    r"\bgame[\s-]chang(er|ing)\b": "breakthrough",
    r"\bunprecedented\b": "unusual",
    r"\btransformative\b": "big change",
    r"\bcutting[\s-]edge\b": "new",
    r"\bmultifaceted\b": "complex",
    r"\bparadigm\b": "model",
    r"\brobust\b": "strong",
    r"\bseamless\b": "smooth",
    r"\bsynerg(y|ies|istic)\b": "teamwork",
    r"\bnovel\b": "new",
    r"\bmyriad\b": "many",
    r"\bpivotal\b": "key",
    r"\bcomprehensive\b": "full",
}

CONTRACTION_PATTERNS = {
    r"\bit is\b": "it's",
    r"\bdo not\b": "don't",
    r"\bcannot\b": "can't",
    r"\bwill not\b": "won't",
    r"\bthat is\b": "that's",
    r"\bthere is\b": "there's",
    r"\bthey are\b": "they're",
    r"\bwe are\b": "we're",
    r"\byou are\b": "you're",
    r"\bI am\b": "I'm",
    r"\bhe is\b": "he's",
    r"\bshe is\b": "she's",
    r"\bwe have\b": "we've",
    r"\bit has\b": "it's",
    r"\bI have\b": "I've",
    r"\byou have\b": "you've",
    r"\bthey have\b": "they've",
    r"\bwould have\b": "would've",
    r"\bcould have\b": "could've",
    r"\bshould have\b": "should've",
    r"\bwill have\b": "will've",
    r"\bmight have\b": "might've",
    r"\bmust have\b": "must've",
    r"\bdid not\b": "didn't",
    r"\bdoes not\b": "doesn't",
    r"\bhas not\b": "hasn't",
    r"\bhave not\b": "haven't",
    r"\bhad not\b": "hadn't",
    r"\bwas not\b": "wasn't",
    r"\bwere not\b": "weren't",
    r"\bcould not\b": "couldn't",
    r"\bwould not\b": "wouldn't",
    r"\bshould not\b": "shouldn't",
    r"\bis not\b": "isn't",
    r"\bare not\b": "aren't",
}

FILLER_INSERTIONS = [
    "kind of", "sort of", "basically", "honestly", "really",
    "I mean", "you know", "like", "actually", "well",
    "to be fair", "if I'm being honest", "come to think of it",
    "now that I think about it", "the way I see it",
    "for what it's worth", "not gonna lie", "long story short",
]

HEDGING_PHRASES = [
    "more or less", "give or take", "roughly", "approximately",
    "as far as I can tell", "from what I've seen", "in my experience",
    "the way it usually works", "if memory serves",
    "I could be wrong but", "don't quote me on this but",
]

SELF_CORRECTIONS = [
    "Well, almost.", "No wait — actually.", "Or maybe not.",
    "Hard to say.", "It depends.", "At least that's what I think.",
    "But what do I know.", "Take that with a grain of salt.",
    "Though I could be wrong.", "If you want my honest take.",
]

TRANSITION_DISRUPTORS = [
    "But here's the thing — ", "So anyway, ", "Look, ",
    "The thing is, ", "What actually happened was ",
    "Here's what I mean: ", "Let me put it this way — ",
    "The way I see it, ", "From where I stood, ",
]


def rule_based_polish(text: str, vocabulary: bool = True, contractions: bool = True) -> str:
    if vocabulary:
        for pattern, replacement in AI_VOCABULARY_SWAPS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    if contractions:
        for pattern, replacement in CONTRACTION_PATTERNS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def aggressive_polish(text: str) -> str:
    text = rule_based_polish(text)

    text = _inject_em_dashes(text)
    text = _add_filler_words(text)
    text = _add_hedging(text)
    text = _add_self_corrections(text)
    text = _disrupt_transitions(text)
    text = _vary_punctuation(text)
    text = _add_rhetorical_questions(text)

    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\s+;", ";", text)
    text = re.sub(r"\s+-\s+", " - ", text)

    return text.strip()


def _inject_em_dashes(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) < 3:
        return text

    target = max(1, len(sentences) // 5)
    indices = random.sample(range(len(sentences)), min(target, len(sentences)))

    for idx in indices:
        s = sentences[idx]
        if " — " in s or "—" in s:
            continue
        words = s.split()
        if len(words) > 8:
            mid = random.randint(3, len(words) - 3)
            part1 = " ".join(words[:mid])
            part2 = " ".join(words[mid:])
            sentences[idx] = f"{part1} — {part2}"

    return " ".join(sentences)


def _add_filler_words(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) < 4:
        return text

    count = max(1, len(sentences) // 8)
    indices = random.sample(range(len(sentences)), min(count, len(sentences)))

    for idx in indices:
        s = sentences[idx]
        if random.random() < 0.3:
            filler = random.choice(FILLER_INSERTIONS)
            if s.lower().startswith(("the ", "a ", "an ", "it ", "this ", "that ")):
                words = s.split()
                sentences[idx] = f"{words[0]} {filler} {', '.join(words[1:])}" if len(words) > 1 else s
            else:
                sentences[idx] = f"{filler}, {s[0].lower()}{s[1:]}" if s else s

    return " ".join(sentences)


def _add_hedging(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) < 5:
        return text

    count = max(1, len(sentences) // 10)
    indices = random.sample(range(len(sentences)), min(count, len(sentences)))

    for idx in indices:
        s = sentences[idx]
        if s.strip().endswith("?"):
            continue
        hedge = random.choice(HEDGING_PHRASES)
        sentences[idx] = f"{hedge}, {s[0].lower()}{s[1:]}" if s else s

    return " ".join(sentences)


def _add_self_corrections(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) < 6:
        return text

    count = max(1, len(sentences) // 12)
    indices = random.sample(range(len(sentences)), min(count, len(sentences)))

    for idx in indices:
        s = sentences[idx]
        correction = random.choice(SELF_CORRECTIONS)
        sentences[idx] = f"{s.rstrip()} {correction}"

    return " ".join(sentences)


def _disrupt_transitions(text: str) -> str:
    paragraphs = re.split(r"\n\s*\n", text)
    result = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        sentences = re.split(r"(?<=[.!?])\s+", para)
        if len(sentences) > 1 and random.random() < 0.3:
            transition = random.choice(TRANSITION_DISRUPTORS)
            sentences[1] = f"{transition}{sentences[1][0].lower()}{sentences[1][1:]}" if len(sentences[1]) > 1 else sentences[1]
        result.append(" ".join(sentences))

    return "\n\n".join(result)


def _vary_punctuation(text: str) -> str:
    text = re.sub(r",\s*which\b", "; which", text)
    text = re.sub(r",\s*and\b", "; and", text, count=1)
    text = re.sub(r"\bso\b", lambda m: random.choice(["so", "So"]), text, count=1, flags=re.IGNORECASE)
    return text


def _add_rhetorical_questions(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) < 8:
        return text

    count = max(1, len(sentences) // 15)
    indices = random.sample(range(len(sentences)), min(count, len(sentences)))

    questions = [
        "Right?", "Isn't it?", "Or was it?", "Who knows?",
        "Makes you think, doesn't it?", "At least that's how I remember it.",
        "What else would you call it?", "Am I wrong?",
    ]

    for idx in indices:
        q = random.choice(questions)
        sentences[idx] = f"{sentences[idx].rstrip('.')} {q}"

    return " ".join(sentences)
