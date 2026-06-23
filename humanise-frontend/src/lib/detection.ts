interface DetectionResult {
  total_score: number;
  matches: Record<string, number>;
  pattern_count: number;
  sentence_uniformity: number;
  concerns: string[];
}

interface ReadabilityResult {
  reading_ease: number;
  grade_level: number;
  label: string;
}

interface FullAnalysis {
  human_score: number;
  ai_score: number;
  pattern_count: number;
  patterns: Record<string, number>;
  concerns: string[];
  sentence_uniformity: number;
  burstiness: number;
  perplexity: number;
  readability: ReadabilityResult;
}

const AI_PATTERNS: [string, RegExp][] = [
  ["furthermore_moreover", /\b(furthermore|moreover|additionally|consequently)\b/gi],
  ["in_conclusion", /\bin\s+conclusion\b/gi],
  ["not_only_but_also", /\bnot\s+only\s+.*?\bbut\s+also\b/gi],
  ["it_is_important", /\bit\s+is\s+important\s+to\s+(note|recognize|consider|understand|highlight|emphasize|acknowledge|mention|remember|realize|appreciate)\b/gi],
  ["plays_a_role", /\bplays?\s+a\s+(crucial|key|vital|significant|critical|pivotal|important|essential|fundamental|central|major)\s+role\b/gi],
  ["it_is_worth", /\bit\s+is\s+worth\s+(noting|mentioning|considering|highlighting|emphasizing|exploring|examining|discussing|pointing\s+out)\b/gi],
  ["hedging", /\b(it\s+could\s+be\s+argued|one\s+might\s+consider|it\s+is\s+possible\s+that|it\s+may\s+be\s+that)\b/gi],
  ["three_adjectives", /\b\w+,\s+\w+,\s+and\s+\w+\b/gi],
  ["in_order_to", /\bin\s+order\s+to\b/gi],
  ["delve_into", /\bdelve[s]?\s+(into|deeper)\b/gi],
  ["game_changer", /\bgame[\s-]chang(er|ing)\b/gi],
  ["unprecedented", /\bunprecedented\b/gi],
  ["transformative", /\btransformative\b/gi],
  ["cutting_edge", /\bcutting[\s-]edge\b/gi],
  ["synergy_paradigm", /\b(synerg(y|ies|istic)|paradigm(\s+shift)?)\b/gi],
  ["robust_seamless", /\b(robust|seamless)\s+(solution|integration|platform|system|approach|framework|workflow|experience|interface)\b/gi],
  ["multi_faceted", /\bmulti[\s-]facet(ed)?\b/gi],
  ["harnessing_powering", /\b(harness(ing)?|leverag(ing|e))\s+(the\s+)?power\b/gi],
  ["elevate_transform", /\b(elevat(e|ing)\s+your|transform(ing)?\s+the\s+(way|landscape))\b/gi],
];

const CONVERSATIONAL_AI_PATTERNS: [string, RegExp][] = [
  ["forced_casual_opener", /\b(Here's the thing|So I'm|So what|I mean,)\b/gi],
  ["parenthetical_honesty", /\(which,\s*honestly|\(honestly,|\(frankly,/gi],
  ["rhetorical_tag", /,\s*(right\?|you know\?|isn't it\?)/gi],
  ["over_contracted", /\b(it's,\s*like,|I'm,\s*like,|he's,\s*like,|she's,\s*like,)/gi],
  ["prompt_fragment", /\b(which,\s*honestly,\s*\w+ me|I'd argue|from what I can tell)\b/gi],
];

const SIGMA_ADJECTIVES = /\b(innovative|revolutionary|groundbreaking|ground-breaking|disruptive|next-generation|state-of-the-art|best-in-class|world-class|industry-leading|unparalleled|unmatched|unrivaled|superior|exceptional|outstanding|remarkable|extraordinary|incredible|amazing)\b/gi;

const SENTENCE_SPLIT = /[.!?]+\s+/;

function countMatches(pattern: RegExp, text: string): { count: number; groups?: string[] } {
  const matches = [...text.matchAll(pattern)];
  return { count: matches.length };
}

export function detectPatterns(text: string): DetectionResult {
  const result: DetectionResult = {
    total_score: 0,
    matches: {},
    pattern_count: 0,
    sentence_uniformity: 0,
    concerns: [],
  };

  for (const [name, pattern] of AI_PATTERNS) {
    const matches = [...text.matchAll(pattern)];
    if (matches.length > 0) {
      result.matches[name] = matches.length;
      result.pattern_count += matches.length;
      const penalty = Math.min(matches.length * 5, 25);
      result.total_score += penalty;
      if (matches.length >= 3) {
        result.concerns.push(`High frequency of '${name}': ${matches.length} matches`);
      }
    }
  }

  for (const [name, pattern] of CONVERSATIONAL_AI_PATTERNS) {
    const matches = [...text.matchAll(pattern)];
    if (matches.length > 0) {
      result.matches[name] = matches.length;
      result.pattern_count += matches.length;
      const penalty = Math.min(matches.length * 4, 20);
      result.total_score += penalty;
      if (matches.length >= 2) {
        result.concerns.push(`Forced casual pattern '${name}': ${matches.length} matches`);
      }
    }
  }

  const sigmaMatches = [...text.matchAll(SIGMA_ADJECTIVES)];
  if (sigmaMatches.length > 0) {
    result.matches["sigma_adjectives"] = sigmaMatches.length;
    result.pattern_count += sigmaMatches.length;
    result.total_score += Math.min(sigmaMatches.length * 3, 15);
  }

  const wordsInText = text.match(/\b\w+\b/g) || [];
  const sentences = text.split(SENTENCE_SPLIT).map(s => s.trim()).filter(Boolean);

  if (sentences.length > 0 && wordsInText.length > 0) {
    const wordCounts = sentences.map(s => s.split(/\s+/).length);
    if (wordCounts.length > 2) {
      const meanLen = wordCounts.reduce((a, b) => a + b, 0) / wordCounts.length;
      const diffs = wordCounts.map(c => Math.abs(c - meanLen));
      const avgDeviation = diffs.reduce((a, b) => a + b, 0) / diffs.length;
      const uniformity = 1 / (avgDeviation + 1);
      result.sentence_uniformity = Math.round(uniformity * 1000) / 1000;
      if (uniformity > 0.6) {
        result.total_score += 15;
        result.concerns.push(`Sentence lengths too uniform (uniformity=${uniformity.toFixed(2)})`);
      }
    }

    const starterWords: string[] = [];
    for (const s of sentences) {
      const words = s.trim().split(/\s+/);
      if (words.length > 0) {
        starterWords.push(words[0].toLowerCase().replace(/[,.!?;:]$/, ""));
      }
    }
    if (starterWords.length > 4) {
      const freq: Record<string, number> = {};
      for (const w of starterWords) freq[w] = (freq[w] || 0) + 1;

      const casualStarters = new Set(["so", "and", "but", "here's", "plus", "anyway", "though"]);
      let casualHits = 0;
      for (const w of casualStarters) if (freq[w]) casualHits += freq[w];
      const starterRatio = casualHits / starterWords.length;
      if (starterRatio > 0.3) {
        result.total_score += 12;
        result.concerns.push(`Repetitive casual sentence starters (${Math.round(starterRatio * 100)}% of sentences)`);
      }

      const firstPersonStarters = new Set(["i", "i'm", "i've", "i'd", "i'll", "my", "me"]);
      let fpHits = 0;
      for (const w of firstPersonStarters) if (freq[w]) fpHits += freq[w];
      const fpRatio = fpHits / starterWords.length;
      if (fpRatio > 0.4) {
        const penalty = Math.min(Math.floor((fpRatio - 0.4) * 60), 25);
        result.total_score += penalty;
        result.concerns.push(`Excessive first-person sentence starters (${Math.round(fpRatio * 100)}% of sentences)`);
      }
    }

    const contractions = text.match(/\b\w+'(?:s|t|ve|ll|re|d|m)\b/gi);
    if (contractions && wordsInText.length > 0) {
      const contractionRatio = contractions.length / wordsInText.length;
      if (contractionRatio > 0.06) {
        result.total_score += 10;
        result.concerns.push(`Unnaturally high contraction density (${Math.round(contractionRatio * 100)}%)`);
      }
    }
  }

  result.total_score = Math.min(result.total_score, 100);
  return result;
}

function countSyllables(word: string): number {
  const w = word.toLowerCase();
  if (w.length <= 2) return 1;
  let count = 0;
  const vowels = "aeiouy";
  if (vowels.includes(w[0])) count++;
  for (let i = 1; i < w.length; i++) {
    if (vowels.includes(w[i]) && !vowels.includes(w[i - 1])) count++;
  }
  if (w.endsWith("e")) count--;
  if (w.endsWith("le") && w.length > 2 && !vowels.includes(w[w.length - 3])) count++;
  if (w.endsWith("ed") && w.length > 3 && !vowels.includes(w[w.length - 3])) count++;
  return Math.max(count, 1);
}

export function fleschKincaid(text: string): ReadabilityResult {
  const sentences = text.split(SENTENCE_SPLIT).map(s => s.trim()).filter(Boolean);
  const words = text.match(/\b\w+\b/g) || [];
  if (sentences.length === 0 || words.length === 0) {
    return { reading_ease: 0, grade_level: 0, label: "N/A" };
  }

  const numSentences = Math.max(sentences.length, 1);
  const numWords = words.length;
  const numSyllables = words.reduce((sum, w) => sum + countSyllables(w), 0);

  let readingEase = 206.835 - 1.015 * (numWords / numSentences) - 84.6 * (numSyllables / numWords);
  readingEase = Math.round(Math.max(0, Math.min(120, readingEase)) * 10) / 10;

  let gradeLevel = 0.39 * (numWords / numSentences) + 11.8 * (numSyllables / numWords) - 15.59;
  gradeLevel = Math.round(Math.max(0, Math.min(18, gradeLevel)) * 10) / 10;

  let label: string;
  if (readingEase >= 90) label = "Very Easy";
  else if (readingEase >= 80) label = "Easy";
  else if (readingEase >= 70) label = "Fairly Easy";
  else if (readingEase >= 60) label = "Standard";
  else if (readingEase >= 50) label = "Fairly Difficult";
  else if (readingEase >= 30) label = "Difficult";
  else label = "Very Difficult";

  return { reading_ease: readingEase, grade_level: gradeLevel, label };
}

export function computeBurstiness(text: string): number {
  const sentences = text.split(SENTENCE_SPLIT).map(s => s.trim()).filter(Boolean);
  if (sentences.length < 3) return 0;
  const wordCounts = sentences.map(s => s.split(/\s+/).length);
  const meanLen = wordCounts.reduce((a, b) => a + b, 0) / wordCounts.length;
  if (meanLen === 0) return 0;
  const variance = wordCounts.reduce((sum, c) => sum + (c - meanLen) ** 2, 0) / wordCounts.length;
  const stdDev = Math.sqrt(variance);
  const burstiness = stdDev / meanLen;
  return Math.round(Math.min(burstiness, 2) * 1000) / 1000;
}

export function computePerplexity(text: string): number {
  const words = text.match(/\b\w+\b/g)?.map(w => w.toLowerCase()) || [];
  if (words.length < 4) return 0;

  const bigrams: Map<string, number> = new Map();
  const unigrams: Map<string, number> = new Map();
  for (let i = 0; i < words.length - 1; i++) {
    const bg = `${words[i]}|${words[i + 1]}`;
    bigrams.set(bg, (bigrams.get(bg) || 0) + 1);
    unigrams.set(words[i], (unigrams.get(words[i]) || 0) + 1);
  }
  unigrams.set(words[words.length - 1], (unigrams.get(words[words.length - 1]) || 0) + 1);

  const vocabSize = unigrams.size;
  if (vocabSize === 0) return 0;

  let logProbSum = 0;
  for (let i = 0; i < words.length - 1; i++) {
    const bgCount = bigrams.get(`${words[i]}|${words[i + 1]}`) || 0;
    const ugCount = unigrams.get(words[i]) || 0;
    const prob = (bgCount + 1) / (ugCount + vocabSize);
    logProbSum += Math.log(Math.max(prob, 1e-10));
  }

  const perplexity = Math.exp(-logProbSum / Math.max(words.length - 1, 1));
  return Math.round(perplexity * 10) / 10;
}

export function computeHumanScore(detectionScore: number, burstiness: number, perplexity: number): number {
  let baseScore = 100 - detectionScore;
  if (burstiness > 0.6) baseScore += 5;
  else if (burstiness < 0.2) baseScore -= 10;
  if (perplexity > 150) baseScore += 5;
  else if (perplexity < 50 && perplexity > 0) baseScore -= 10;
  return Math.round(Math.max(0, Math.min(100, baseScore)) * 10) / 10;
}

export function fullAnalysis(text: string): FullAnalysis {
  const detection = detectPatterns(text);
  const readability = fleschKincaid(text);
  const burstiness = computeBurstiness(text);
  const perplexity = computePerplexity(text);
  const humanScore = computeHumanScore(detection.total_score, burstiness, perplexity);

  return {
    human_score: humanScore,
    ai_score: detection.total_score,
    pattern_count: detection.pattern_count,
    patterns: detection.matches,
    concerns: detection.concerns,
    sentence_uniformity: detection.sentence_uniformity,
    burstiness,
    perplexity,
    readability,
  };
}
