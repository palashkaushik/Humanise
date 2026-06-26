import re
import math

AI_PATTERNS = {
    # Original patterns
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
    "navigate_complex": r"\b(navigat(e|ing|ed)\s+(the\s+)?(complex|intricate|challenging)|steer\s+through|find\s+(one's|their)\s+way)\b",
    "beacon_of": r"\bbeacon\s+of\s+(hope|light|resilience|inspiration|change)\b",
    "tapestry_of": r"\b(tapestry|kaleidoscope|microcosm|melting\s+pot)\s+of\b",
    "journey_of": r"\bjourney\s+of\s+(self[\s-]?discovery|transformation|growth|healing|redemption)\b",
    "dance_of": r"\b(dance|delicate\s+dance|intricate\s+dance)\s+of\s+(light|shadow|life|fate|destiny)\b",
    "eyes_flashed": r"\b(eyes\s+(flashed|sparkled|lit\s+up|narrowed|widened)|smile\s+faltered|face\s+(lit\s+up|fell|dropped)|jaw\s+(clenched|tightened|dropped))\b",
    "heart_pounded": r"\b(heart\s+(pounded|raced|skipped|sank|swelled|soared|hammered|thudded)|chest\s+tightened|gut\s+(twisted|clenched|churned)|pulse\s+(quickened|raced))\b",
    "drowning_in": r"\b(drown(ing|ed)\s+in\s+(their|her|his|its|the)|lost\s+in\s+(their|her|his|its|the)\s+(eyes|gaze|depths)|captivated\s+by)\b",
    "as_they_verb": r"\b[Aa]s\s+they\s+(walked|talked|worked|sat|stood|chatted|laughed|cried|moved|drove|ran|ate|drank|danced|fought|argued|discussed|brainstormed)\b",
    "filled_the_air": r"\b(filled\s+the\s+air|hung\s+in\s+the\s+air|wafted\s+through|permeated\s+the)\b",
    "with_a_nod": r"\bwith\s+a\s+(nod|smile|sigh|shrug|wink|wave|gesture|look|glance|stare)\b",
    "melodious_voice": r"\b(melodious|melodic|singsong|lyrical|lilting|musical)\s+(voice|tone|laugh|blend|mix)\b",
    # Wikipedia AI writing indicators - significance/legacy
    "stands_serves_as": r"\b(stands|serves)\s+as\s+(a|an|the)\s+(testament|reminder|symbol|example|reflection|representation)\b",
    "testament_to": r"\bis\s+a\s+testament\s+to\b",
    "underscores_highlights": r"\b(underscores?|highlights?)\s+(its|their|the|his|her)\s+(importance|significance|role|impact)\b",
    "reflects_broader": r"\breflects?\s+(the|a|its|their)\s+(broader|wider|larger|greater)\b",
    "symbolizing_enduring": r"\bsymboliz(e|ing|ed)\s+(its|their|the)\s+(enduring|lasting|ongoing|continuing)\b",
    "contributing_to_the": r"\bcontribut(e|ing|ed)\s+to\s+the\b",
    "setting_the_stage": r"\bsetting\s+the\s+stage\s+for\b",
    "marking_shaping": r"\b(mark|marking|shape|shaping)\s+(the|a|an)\s+(beginning|start|dawn|era|age|transition|shift)\b",
    "evolving_landscape": r"\bevolving\s+landscape\b",
    "focal_point": r"\bfocal\s+point\b",
    "indelible_mark": r"\bindelible\s+mark\b",
    "deeply_rooted": r"\bdeeply\s+rooted\b",
    "key_turning_point": r"\bkey\s+turning\s+point\b",
    # Promotional language
    "vibrant_rich_profound": r"\b(vibrant|rich|profound)\s+(community|culture|heritage|tradition|history|tapestry|mosaic)\b",
    "boasts_a": r"\bboasts?\s+a\b",
    "nestled_in": r"\bnestled\s+(in|at|within|among)\b",
    "in_the_heart_of": r"\bin\s+the\s+heart\s+of\b",
    "groundbreaking_renowned": r"\b(groundbreaking|renowned)\s+(research|discovery|innovation|contribution|work|achievement)\b",
    "diverse_array": r"\bdiverse\s+array\s+of\b",
    "commitment_to": r"\bcommitment\s+to\b",
    "natural_beauty": r"\bnatural\s+beauty\b",
    "active_social_media": r"\b(maintains?\s+an?\s+active|strong|significant)\s+(social\s+media|digital)\s+presence\b",
    # Superficial analysis
    "highlights_underscores_emphasizes": r"\b(highlight|underscore|emphasize|showcase|exemplify|foster|cultivate|nurture|enhance|enrich|bolster)\w*\b",
    # Negative parallelisms
    "not_just_but_also": r"\bnot\s+just\s+.*?,\s*but\s+also\b",
    "not_x_but_y": r"\bnot\s+\w+,?\s+but\s+\w+\b",
    "x_rather_than_y": r"\b\w+\s+rather\s+than\s+\w+\b",
    # Summary/conclusion
    "in_summary_conclusion": r"\b(in\s+summary|in\s+conclusion|overall|to\s+summarize|to\s+conclude)\b",
    # AI self-reference
    "as_an_ai": r"\bas\s+(an?\s+)?(AI|language\s+model|large\s+language\s+model)\b",
    "it_is_worth_noting": r"\bit\s+(is|was)\s+worth\s+noting\b",
    "worth_noting": r"\bworth\s+noting\b",
    # Copulative replacements (AI avoids simple "is"/"are")
    "suspect_copulatives": r"\b(serves?\s+as|stands?\s+as|marks?\s+as|represents?\s+a|boasts?\s+a|features?\s+a|maintains?\s+a|offers?\s+a|refers?\s+to)\b",
    # Vague attributions
    "vague_attribution": r"\b(industry\s+reports|observers\s+have\s+cited|experts?\s+argue|some\s+critics?\s+argue|several\s+sources|several\s+publications)\b",
    # Outline-like conclusions
    "outline_conclusion": r"\b(despite\s+its.*faces\s+several\s+challenges|despite\s+these\s+challenges|challenges\s+and\s+legacy|future\s+outlook|challenges\s+and\s+future\s+directions)\b",
}

CONVERSATIONAL_AI_PATTERNS = {
    "forced_casual_opener": r"\b(Here's the thing|So I'm|So what|I mean,)\b",
    "parenthetical_honesty": r"\(which,\s*honestly|\(honestly,|\(frankly,",
    "rhetorical_tag": r",\s*(right\?|you know\?|isn't it\?)",
    "over_contracted": r"\b(it's,\s*like,|I'm,\s*like,|he's,\s*like,|she's,\s*like,)",
    "prompt_fragment": r"\b(which,\s*honestly,\s*\w+ me|I'd argue|from what I can tell)\b",
    "i_hope_this_helps": r"\bI\s+hope\s+this\s+helps\b",
    "of_course_certainly": r"\b(Of\s+course|Certainly|You're\s+absolutely\s+right)\b",
    "would_you_like": r"\b(Would\s+you\s+like|Is\s+there\s+anything\s+else|Let\s+me\s+know)\b",
    "if_you_have_concerns": r"\bIf\s+you\s+have\s+(any\s+)?(concerns|suggestions|questions|feedback)\b",
    "i_am_committed": r"\b(I\s+am|We\s+are)\s+committed\s+to\b",
    "i_assure_you": r"\bI\s+assure\s+you\b",
    "my_intention_is": r"\b(my\s+intention|my\s+goal|my\s+objective)\s+is\b",
    "ensure_article_adheres": r"\bensure\s+(the\s+)?(article|content|text)\s+(adheres|aligns|meets|conforms)\b",
}

TEMPORAL_STAGING = r"\b(for\s+a\s+(moment|brief\s+moment|fleeting\s+moment)\b|suddenly,\s+the\s+world|time\s+seemed\s+to|the\s+world\s+around\s+(them|him|her|us)\s+(seemed|felt|appeared)\s+to)"

EMOTIONAL_BEATS = r"\b(surge\s+of|wave\s+of|rush\s+of|flood\s+of|tingle\s+of|pang\s+of|flash\s+of|hint\s+of|trace\s+of)\s+(emotion|feeling|sympathy|empathy|excitement|regret|sadness|joy|anger|fear|hope|longing|nostalgia|determination|energy|electricity|warmth|recognition)\b"

NARRATIVE_FRAMING = r"\b(little\s+did\s+(they|he|she|I|we)\s+know|had\s+a\s+feeling\s+that|it\s+was\s+the\s+(start|beginning)\s+of\s+something|couldn['']t\s+shake\s+the\s+feeling|felt\s+a\s+(thrill|chill|shiver)\s+(run|go)\s+(down|through|up)\s+(their|his|her|my)\s+spine)\b"

DIALOGUE_ATTRIBUTION = r"\b(she\s+said,\s+her\s+voice|he\s+said,\s+his\s+voice|she\s+whispered,\s+her\s+voice|he\s+whispered,\s+his\s+voice|(s|)he\s+said,\s+(their|his|her)\s+voice\s+(barely\s+above\s+a\s+whisper|trembling|shaking|breaking|cracking|quivering|filled\s+with))\b"

SENTENCE_LENGTH_PATTERN = re.compile(r"[.!?]+\s+")

SIGMA_ADJECTIVES = r"\b(innovative|revolutionary|groundbreaking|ground-breaking|disruptive|next-generation|state-of-the-art|best-in-class|world-class|industry-leading|unparalleled|unmatched|unrivaled|superior|exceptional|outstanding|remarkable|extraordinary|incredible|amazing)\b"


def detect_patterns(text: str) -> dict:
    scores = {
        "total_score": 0,
        "matches": {},
        "pattern_count": 0,
        "sentence_uniformity": 0.0,
        "burstiness_score": 0.0,
        "perplexity_score": 0.0,
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
                scores["concerns"].append(f"Forced casual pattern '{name}': {len(matches)} matches")

    sigma_matches = re.findall(SIGMA_ADJECTIVES, text, re.IGNORECASE)
    if sigma_matches:
        scores["matches"]["sigma_adjectives"] = len(sigma_matches)
        scores["pattern_count"] += len(sigma_matches)
        scores["total_score"] += min(len(sigma_matches) * 3, 15)

    for name, pattern in [
        ("temporal_staging", TEMPORAL_STAGING),
        ("emotional_beats", EMOTIONAL_BEATS),
        ("narrative_framing", NARRATIVE_FRAMING),
        ("dialogue_attribution", DIALOGUE_ATTRIBUTION),
    ]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            scores["matches"][name] = len(matches)
            scores["pattern_count"] += len(matches)
            scores["total_score"] += min(len(matches) * 3, 15)
            if len(matches) >= 1:
                scores["concerns"].append(f"Formulaic '{name}': {len(matches)} matches")

    sentences = [s.strip() for s in SENTENCE_LENGTH_PATTERN.split(text) if s.strip()]
    words_in_text = re.findall(r"\b\w+\b", text)

    if sentences and words_in_text:
        word_counts = [len(s.split()) for s in sentences]
        if len(word_counts) > 3:
            mean_len = sum(word_counts) / len(word_counts)
            diffs = [abs(c - mean_len) for c in word_counts]
            avg_deviation = sum(diffs) / len(diffs)
            uniformity = 1.0 / (avg_deviation + 1.0)
            scores["sentence_uniformity"] = round(uniformity, 3)

            if uniformity > 0.6:
                scores["total_score"] += 15
                scores["concerns"].append(f"Sentence lengths too uniform (uniformity={uniformity:.2f})")

            burstiness = std_dev / mean_len if (mean_len := sum(word_counts) / len(word_counts)) > 0 and (variance := sum((c - mean_len) ** 2 for c in word_counts) / len(word_counts)) > 0 and (std_dev := math.sqrt(variance)) > 0 else 0
            burstiness = min(burstiness, 2.0)

            if burstiness < 0.25:
                scores["total_score"] += 8
                scores["burntiness_score"] = 8
                scores["concerns"].append(f"Very low burstiness ({burstiness:.2f}) — statistically unlikely for human text")
            elif burstiness < 0.4:
                scores["total_score"] += 4
                scores["burntiness_score"] = 4

        starter_words = []
        for s in sentences:
            words = s.strip().split()
            if words:
                w = words[0].lower().rstrip(",.!?;:")
                starter_words.append(w)
        if len(starter_words) > 5:
            from collections import Counter
            starter_counts = Counter(starter_words)

            common_starters = {"the", "a", "an", "he", "she", "it", "they", "as", "with", "rocky", "rani"}
            starter_variety = len([c for c in starter_counts if starter_counts[c] >= 2])
            if starter_variety >= 3:
                scores["total_score"] += 10
                scores["concerns"].append(f"Repetitive sentence starters ({starter_variety} words used 2+ times)")

            casual_starters = {"so", "and", "but", "here's", "plus", "anyway", "though"}
            casual_hits = sum(starter_counts[w] for w in casual_starters if w in starter_counts)
            starter_ratio = casual_hits / len(starter_words)
            if starter_ratio > 0.3:
                scores["total_score"] += 12
                scores["concerns"].append(f"Repetitive casual sentence starters ({round(starter_ratio*100)}%)")

            first_person_starters = {"i", "i'm", "i've", "i'd", "i'll", "my", "me"}
            fp_hits = sum(starter_counts[w] for w in first_person_starters if w in starter_counts)
            fp_ratio = fp_hits / len(starter_words)
            if fp_ratio > 0.4:
                penalty = min(int((fp_ratio - 0.4) * 60), 25)
                scores["total_score"] += penalty
                scores["concerns"].append(f"Excessive first-person sentence starters ({round(fp_ratio*100)}% of sentences)")

        contractions = re.findall(r"\b\w+'(?:s|t|ve|ll|re|d|m)\b", text, re.IGNORECASE)
        total_words = len(words_in_text)
        if total_words > 0:
            contraction_ratio = len(contractions) / total_words
            if contraction_ratio > 0.06:
                scores["total_score"] += 10
                scores["concerns"].append(f"Unnaturally high contraction density ({round(contraction_ratio*100)}%)")

    bigrams_found = {}
    unigrams_found = {}
    words_lower = [w.lower() for w in words_in_text]
    for i in range(len(words_lower) - 1):
        bg = (words_lower[i], words_lower[i + 1])
        bigrams_found[bg] = bigrams_found.get(bg, 0) + 1
        unigrams_found[words_lower[i]] = unigrams_found.get(words_lower[i], 0) + 1
    unigrams_found[words_lower[-1]] = unigrams_found.get(words_lower[-1], 0) + 1

    if len(words_lower) >= 4 and len(unigrams_found) > 0:
        log_prob_sum = 0.0
        vocab = len(unigrams_found)
        for i in range(len(words_lower) - 1):
            bg_count = bigrams_found.get((words_lower[i], words_lower[i + 1]), 0)
            ug_count = unigrams_found.get(words_lower[i], 0)
            prob = (bg_count + 1) / (ug_count + vocab)
            log_prob_sum += math.log(max(prob, 1e-10))
        perplexity = math.exp(-log_prob_sum / max(len(words_lower) - 1, 1))

        if perplexity < 30 and perplexity > 0:
            scores["total_score"] += 10
            scores["perplexity_score"] = 10
            scores["concerns"].append(f"Very low perplexity ({perplexity:.0f}) — text is too predictable, strong AI signal")
        elif perplexity < 60 and perplexity > 0:
            scores["total_score"] += 5
            scores["perplexity_score"] = 5

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
