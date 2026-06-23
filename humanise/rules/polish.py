import re

AI_VOCABULARY_SWAPS = {
    r"\butilize(s|d)?\b": r"use\1",
    r"\bfacilitate(s|d)?\b": r"help\1",
    r"\bleverage(s|d)?\b": r"\1",
    r"\bdemonstrate(s|d)?\b": r"show\1",
    r"\bcomprehensive\b": "full",
    r"\binnovative\b": "new",
    r"\boptimize\b": "improve",
    r"\bsubsequently\b": "then",
    r"\badditionally\b": "also",
    r"\btherefore\b": "so",
    r"\bfurthermore\b": "plus",
    r"\bhowever\b": "but",
    r"\bnevertheless\b": "still",
    r"\bnonetheless\b": "still",
    r"\bin conclusion\b": "in the end",
    r"\bit is important to note that\b": "the key thing is",
    r"\bit should be noted that\b": "note that",
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
    r"\bplays? a (crucial|key|vital|significant|critical|pivotal|important) role\b": "matters",
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
    r"\bit would\b": "it'd",
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
    r"\bmight not\b": "mightn't",
    r"\bmust not\b": "mustn't",
    r"\bis not\b": "isn't",
    r"\bare not\b": "aren't",
}


def rule_based_polish(text: str, vocabulary: bool = True, contractions: bool = True) -> str:
    if vocabulary:
        for pattern, replacement in AI_VOCABULARY_SWAPS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    if contractions:
        for pattern, replacement in CONTRACTION_PATTERNS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()
