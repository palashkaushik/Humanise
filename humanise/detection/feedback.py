import re
import math

AI_PATTERNS = {
    "furthermore_moreover": r"\b(furthermore|moreover|additionally|consequently)\b",
    "in_conclusion": r"\bin\s+conclusion\b",
    "not_only_but_also": r"\bnot\s+only\s+.*?\bbut\s+also\b",
    "it_is_important": r"\bit\s+is\s+important\s+to\s+(note|recognize|consider|understand|highlight|emphasize|acknowledge|mention|remember|realize|appreciate)\b",
    "plays_a_role": r"\bplays?\s+a\s+(crucial|key|vital|significant|critical|pivotal|important|essential|fundamental|central|major)\s+role\b",
    "it_is_worth": r"\bit\s+is\s+worth\s+(noting|mentioning|considering|highlighting|emphasizing|exploring|examining|discussing|pointing\s+out)\b",
    "hedging": r"\b(it\s+could\s+be\s+argued|one\s+might\s+consider|it\s+is\s+possible\s+that|it\s+may\s+be\s+that)\b",
    "three_adjectives": r"\b\w+,\s+\w+,\s+and\s+\w+\b",
    "in_order_to": r"\bin\s+order\s+to\b",
    "delve_into": r"\bdelve[s]?\s+(into|deeper)\b",
    "game_changer": r"\bgame[\s-]chang(er|ing)\b",
    "unprecedented": r"\bunprecedented\b",
    "transformative": r"\btransformative\b",
    "cutting_edge": r"\bcutting[\s-]edge\b",
    "synergy_paradigm": r"\b(synerg(y|ies|istic)|paradigm(\s+shift)?)\b",
    "robust_seamless": r"\b(robust|seamless)\s+(solution|integration|platform|system|approach|framework|workflow|experience|interface)\b",
    "multi_faceted": r"\bmulti[\s-]facet(ed)?\b",
    "harnessing_powering": r"\b(harness(ing)?|leverag(ing|e))\s+(the\s+)?power\b",
    "elevate_transform": r"\b(elevat(e|ing)\s+your|transform(ing)?\s+the\s+(way|landscape))\b",
}

CONVERSATIONAL_AI_PATTERNS = {
    "forced_casual_opener": r"\b(Here's the thing|So I'm|So what|I mean,)\b",
    "parenthetical_honesty": r"\(which,\s*honestly|\(honestly,|\(frankly,",
    "rhetorical_tag": r",\s*(right\?|you know\?|isn't it\?)",
    "over_contracted": r"\b(it's,\s*like,|I'm,\s*like,|he's,\s*like,|she's,\s*like,)",
    "prompt_fragment": r"\b(which,\s*honestly,\s*\w+ me|I'd argue|from what I can tell)\b",
}

SENTENCE_LENGTH_PATTERN = re.compile(r"[.!?]+\s+")

SIGMA_ADJECTIVES = r"\b(innovative|revolutionary|groundbreaking|ground-breaking|disruptive|next-generation|state-of-the-art|best-in-class|world-class|industry-leading|unparalleled|unmatched|unrivaled|superior|exceptional|outstanding|remarkable|extraordinary|incredible|amazing)\b"


def detect_patterns(text: str) -> dict:
    scores = {
        "total_score": 0,
        "matches": {},
        "pattern_count": 0,
        "sentence_uniformity": 0.0,
        "concerns": [],
    }

    for name, pattern in AI_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            scores["matches"][name] = len(matches)
            scores["pattern_count"] += len(matches)
            match_penalty = min(len(matches) * 5, 25)
            scores["total_score"] += match_penalty
            if len(matches) >= 3:
                scores["concerns"].append(f"High frequency of '{name}': {len(matches)} matches")

    for name, pattern in CONVERSATIONAL_AI_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            scores["matches"][name] = len(matches)
            scores["pattern_count"] += len(matches)
            match_penalty = min(len(matches) * 4, 20)
            scores["total_score"] += match_penalty
            if len(matches) >= 2:
                scores["concerns"].append(
                    f"Forced casual pattern '{name}': {len(matches)} matches"
                )

    sigma_matches = re.findall(SIGMA_ADJECTIVES, text, re.IGNORECASE)
    if sigma_matches:
        scores["matches"]["sigma_adjectives"] = len(sigma_matches)
        scores["pattern_count"] += len(sigma_matches)
        scores["total_score"] += min(len(sigma_matches) * 3, 15)

    sentences = [s.strip() for s in SENTENCE_LENGTH_PATTERN.split(text) if s.strip()]
    words_in_text = re.findall(r"\b\w+\b", text)
    if sentences and words_in_text:
        word_counts = [len(s.split()) for s in sentences]
        if len(word_counts) > 2:
            mean_len = sum(word_counts) / len(word_counts)
            diffs = [abs(c - mean_len) for c in word_counts]
            avg_deviation = sum(diffs) / len(diffs)
            uniformity = 1.0 / (avg_deviation + 1.0)
            scores["sentence_uniformity"] = round(uniformity, 3)
            if uniformity > 0.6:
                scores["total_score"] += 15
                scores["concerns"].append(
                    f"Sentence lengths too uniform (uniformity={uniformity:.2f})"
                )

        starter_words = []
        for s in sentences:
            words = s.strip().split()
            if words:
                w = words[0].lower().rstrip(",.!?;:")
                starter_words.append(w)
        if len(starter_words) > 4:
            from collections import Counter
            starter_counts = Counter(starter_words)
            casual_starters = {"so", "and", "but", "here's", "plus", "anyway", "though"}
            casual_hits = sum(starter_counts[w] for w in casual_starters if w in starter_counts)
            starter_ratio = casual_hits / len(starter_words)
            if starter_ratio > 0.3:
                scores["total_score"] += 12
                scores["concerns"].append(
                    f"Repetitive casual sentence starters ({round(starter_ratio*100)}% of sentences)"
                )

            first_person_starters = {"i", "i'm", "i've", "i'd", "i'll", "my", "me"}
            fp_hits = sum(starter_counts[w] for w in first_person_starters if w in starter_counts)
            fp_ratio = fp_hits / len(starter_words)
            if fp_ratio > 0.4:
                penalty = min(int((fp_ratio - 0.4) * 60), 25)
                scores["total_score"] += penalty
                scores["concerns"].append(
                    f"Excessive first-person sentence starters ({round(fp_ratio*100)}% of sentences)"
                )

        contractions = re.findall(r"\b\w+'(?:s|t|ve|ll|re|d|m)\b", text, re.IGNORECASE)
        total_words = len(words_in_text)
        if total_words > 0:
            contraction_ratio = len(contractions) / total_words
            if contraction_ratio > 0.06:
                scores["total_score"] += 10
                scores["concerns"].append(
                    f"Unnaturally high contraction density ({round(contraction_ratio*100)}%)"
                )

    scores["total_score"] = min(scores["total_score"], 100)

    return scores


def _count_syllables(word: str) -> int:
    word = word.lower()
    if len(word) <= 2:
        return 1
    count = 0
    vowels = "aeiouy"
    if word[0] in vowels:
        count += 1
    for i in range(1, len(word)):
        if word[i] in vowels and word[i - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
        count += 1
    if word.endswith("ed") and len(word) > 3 and word[-3] not in vowels:
        count += 1
    return max(count, 1)


def flesch_kincaid(text: str) -> dict:
    sentences = [s.strip() for s in SENTENCE_LENGTH_PATTERN.split(text) if s.strip()]
    words = re.findall(r"\b\w+\b", text)
    if not sentences or not words:
        return {"reading_ease": 0.0, "grade_level": 0.0, "label": "N/A"}

    num_sentences = max(len(sentences), 1)
    num_words = len(words)
    num_syllables = sum(_count_syllables(w) for w in words)

    reading_ease = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)
    reading_ease = round(max(0.0, min(120.0, reading_ease)), 1)

    grade_level = 0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59
    grade_level = round(max(0.0, min(18.0, grade_level)), 1)

    if reading_ease >= 90:
        label = "Very Easy"
    elif reading_ease >= 80:
        label = "Easy"
    elif reading_ease >= 70:
        label = "Fairly Easy"
    elif reading_ease >= 60:
        label = "Standard"
    elif reading_ease >= 50:
        label = "Fairly Difficult"
    elif reading_ease >= 30:
        label = "Difficult"
    else:
        label = "Very Difficult"

    return {"reading_ease": reading_ease, "grade_level": grade_level, "label": label}


def compute_burstiness(text: str) -> float:
    sentences = [s.strip() for s in SENTENCE_LENGTH_PATTERN.split(text) if s.strip()]
    if len(sentences) < 3:
        return 0.0
    word_counts = [len(s.split()) for s in sentences]
    mean_len = sum(word_counts) / len(word_counts)
    if mean_len == 0:
        return 0.0
    variance = sum((c - mean_len) ** 2 for c in word_counts) / len(word_counts)
    std_dev = math.sqrt(variance)
    burstiness = std_dev / mean_len
    return round(min(burstiness, 2.0), 3)


def compute_perplexity(text: str) -> float:
    words = re.findall(r"\b\w+\b", text.lower())
    if len(words) < 4:
        return 0.0

    bigrams = {}
    unigrams = {}
    for i in range(len(words) - 1):
        bg = (words[i], words[i + 1])
        bigrams[bg] = bigrams.get(bg, 0) + 1
        unigrams[words[i]] = unigrams.get(words[i], 0) + 1
    unigrams[words[-1]] = unigrams.get(words[-1], 0) + 1

    vocab_size = len(unigrams)
    if vocab_size == 0:
        return 0.0

    log_prob_sum = 0.0
    for i in range(len(words) - 1):
        bg_count = bigrams.get((words[i], words[i + 1]), 0)
        ug_count = unigrams.get(words[i], 0)
        prob = (bg_count + 1) / (ug_count + vocab_size)
        log_prob_sum += math.log(max(prob, 1e-10))

    perplexity = math.exp(-log_prob_sum / max(len(words) - 1, 1))
    return round(perplexity, 1)


def compute_human_score(detection_score: float, burstiness: float, perplexity: float) -> float:
    base_score = 100.0 - detection_score

    if burstiness > 0.6:
        base_score += 5.0
    elif burstiness < 0.2:
        base_score -= 10.0

    if perplexity > 150:
        base_score += 5.0
    elif perplexity < 50 and perplexity > 0:
        base_score -= 10.0

    return round(max(0.0, min(100.0, base_score)), 1)


def full_analysis(text: str) -> dict:
    detection = detect_patterns(text)
    readability = flesch_kincaid(text)
    burstiness = compute_burstiness(text)
    perplexity = compute_perplexity(text)
    human_score = compute_human_score(
        detection["total_score"], burstiness, perplexity
    )

    return {
        "human_score": human_score,
        "ai_score": detection["total_score"],
        "pattern_count": detection["pattern_count"],
        "patterns": detection["matches"],
        "concerns": detection["concerns"],
        "sentence_uniformity": detection["sentence_uniformity"],
        "burstiness": burstiness,
        "perplexity": perplexity,
        "readability": readability,
    }
