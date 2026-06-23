const AI_VOCABULARY_SWAPS: [RegExp, string][] = [
  [/\butilize(s|d)?\b/gi, "use$1"],
  [/\bfacilitate(s|d)?\b/gi, "help$1"],
  [/\bleverage(s|d)?\b/gi, "$1"],
  [/\bdemonstrate(s|d)?\b/gi, "show$1"],
  [/\bcomprehensive\b/gi, "full"],
  [/\binnovative\b/gi, "new"],
  [/\boptimize\b/gi, "improve"],
  [/\bsubsequently\b/gi, "then"],
  [/\badditionally\b/gi, "also"],
  [/\btherefore\b/gi, "so"],
  [/\bfurthermore\b/gi, "plus"],
  [/\bhowever\b/gi, "but"],
  [/\bnevertheless\b/gi, "still"],
  [/\bnonetheless\b/gi, "still"],
  [/\bin conclusion\b/gi, "in the end"],
  [/\bit is important to note that\b/gi, "the key thing is"],
  [/\bit should be noted that\b/gi, "note that"],
  [/\bit is worth noting that\b/gi, ""],
  [/\bit is imperative that\b/gi, "we need to"],
  [/\ba comprehensive range of\b/gi, "a range of"],
  [/\ba wide variety of\b/gi, "various"],
  [/\bin order to\b/gi, "to"],
  [/\bin the event that\b/gi, "if"],
  [/\bprior to\b/gi, "before"],
  [/\bsubsequent to\b/gi, "after"],
  [/\bin the context of\b/gi, "in"],
  [/\bwith regard to\b/gi, "about"],
  [/\bin terms of\b/gi, "in"],
  [/\bin the process of\b/gi, ""],
  [/\bplays? a (crucial|key|vital|significant|critical|pivotal|important) role\b/gi, "matters"],
];

const CONTRACTION_PATTERNS: [RegExp, string][] = [
  [/\bit is\b/gi, "it's"],
  [/\bdo not\b/gi, "don't"],
  [/\bcannot\b/gi, "can't"],
  [/\bwill not\b/gi, "won't"],
  [/\bthat is\b/gi, "that's"],
  [/\bthere is\b/gi, "there's"],
  [/\bthey are\b/gi, "they're"],
  [/\bwe are\b/gi, "we're"],
  [/\byou are\b/gi, "you're"],
  [/\bI am\b/gi, "I'm"],
  [/\bhe is\b/gi, "he's"],
  [/\bshe is\b/gi, "she's"],
  [/\bit would\b/gi, "it'd"],
  [/\bwe have\b/gi, "we've"],
  [/\bit has\b/gi, "it's"],
  [/\bI have\b/gi, "I've"],
  [/\byou have\b/gi, "you've"],
  [/\bthey have\b/gi, "they've"],
  [/\bwould have\b/gi, "would've"],
  [/\bcould have\b/gi, "could've"],
  [/\bshould have\b/gi, "should've"],
  [/\bwill have\b/gi, "will've"],
  [/\bmight have\b/gi, "might've"],
  [/\bmust have\b/gi, "must've"],
  [/\bdid not\b/gi, "didn't"],
  [/\bdoes not\b/gi, "doesn't"],
  [/\bhas not\b/gi, "hasn't"],
  [/\bhave not\b/gi, "haven't"],
  [/\bhad not\b/gi, "hadn't"],
  [/\bwas not\b/gi, "wasn't"],
  [/\bwere not\b/gi, "weren't"],
  [/\bcould not\b/gi, "couldn't"],
  [/\bwould not\b/gi, "wouldn't"],
  [/\bshould not\b/gi, "shouldn't"],
  [/\bmight not\b/gi, "mightn't"],
  [/\bmust not\b/gi, "mustn't"],
  [/\bis not\b/gi, "isn't"],
  [/\bare not\b/gi, "aren't"],
];

const SYNONYM_DB: Record<string, string[]> = {
  important: ["critical", "key", "central", "vital", "serious", "big"],
  significant: ["meaningful", "notable", "sizable", "real", "genuine"],
  however: ["but", "though", "still", "yet", "that said"],
  therefore: ["so", "thus", "as a result", "which means"],
  additionally: ["also", "plus", "on top of that", "and"],
  consequently: ["so", "as a result", "which leads to", "meaning"],
  substantial: ["large", "big", "sizable", "decent", "real"],
  demonstrate: ["show", "point to", "make clear", "reveal"],
  implement: ["build", "put in place", "set up", "roll out"],
  leverage: ["use", "draw on", "tap into", "put to work"],
  optimize: ["improve", "tune", "sharpen", "tighten up", "refine"],
  facilitate: ["help", "enable", "make possible", "ease"],
  utilize: ["use", "apply", "employ", "put to work"],
  comprehensive: ["full", "complete", "thorough", "in-depth"],
  robust: ["strong", "solid", "reliable", "tough", "capable"],
  seamless: ["smooth", "clean", "effortless", "natural"],
  innovative: ["new", "fresh", "creative", "novel", "different"],
  paradigm: ["model", "pattern", "way of thinking"],
  methodology: ["approach", "method", "way", "process"],
  framework: ["structure", "system", "setup"],
  landscape: ["scene", "world", "space", "field"],
  synergy: ["collaboration", "combined effect", "teamwork"],
  crucial: ["vital", "key", "critical", "central"],
  ensure: ["make sure", "guarantee", "lock in", "secure"],
  enhance: ["boost", "improve", "strengthen", "build up"],
  navigate: ["steer through", "work through", "find a way through"],
  unprecedented: ["never seen before", "unheard of", "new ground"],
  transformative: ["life-changing", "redefining", "remaking"],
  fundamentally: ["at its core", "really", "basically"],
  ultimately: ["in the end", "finally", "when it comes down to it"],
  nevertheless: ["still", "even so", "regardless"],
  regarding: ["about", "on", "around", "concerning"],
  impact: ["effect", "influence", "fallout", "result"],
  component: ["piece", "part", "element", "layer"],
  streamline: ["simplify", "speed up", "cut through"],
  foster: ["encourage", "build", "nurture", "spark"],
  empower: ["enable", "equip", "give the tools to"],
  established: ["set up", "built", "put in place", "created"],
};

const DELETABLE_PHRASES = [
  "it should be noted that",
  "it is worth noting that",
  "it is important to note that",
  "needless to say",
  "it goes without saying that",
  "in order to",
  "in the context of",
  "with regard to",
  "in terms of",
  "in the process of",
];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function scrambleSynonyms(text: string, probability: number): string {
  const keys = Object.keys(SYNONYM_DB).sort((a, b) => b.length - a.length);
  for (const word of keys) {
    const alternatives = SYNONYM_DB[word];
    const pattern = new RegExp(`\\b${word}\\b`, "gi");
    text = text.replace(pattern, (match) => {
      if (Math.random() < probability) {
        return pick(alternatives);
      }
      return match;
    });
  }
  return text;
}

function removeFiller(text: string): string {
  for (const phrase of DELETABLE_PHRASES) {
    text = text.replace(new RegExp(phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi"), "");
  }
  return text;
}

function varySentenceLengths(paragraph: string): string {
  const sentences = paragraph.split(/(?<=[.!?])\s+/);
  if (sentences.length < 3) return paragraph;

  const result: string[] = [];
  let i = 0;
  while (i < sentences.length) {
    const s = sentences[i];
    const words = s.split(/\s+/);
    if (words.length > 22 && i + 1 < sentences.length) {
      const mid = Math.floor(words.length / 2);
      let s1 = words.slice(0, mid).join(" ").replace(/[,;]$/, "");
      if (!/[.!?]$/.test(s1)) s1 += ".";
      let s2 = words.slice(mid).join(" ");
      if (s2 && s2[0] === s2[0].toLowerCase()) {
        s2 = s2[0].toUpperCase() + s2.slice(1);
      }
      if (!/[.!?]$/.test(s2)) s2 += ".";
      result.push(s1, s2);
      i++;
    } else if (words.length <= 6 && i + 1 < sentences.length) {
      const nextWords = sentences[i + 1].split(/\s+/);
      if (nextWords.length && nextWords.length <= 8) {
        nextWords[0] = nextWords[0].toLowerCase();
        let combined = s.replace(/\.$/, "") + " and " + nextWords.join(" ");
        if (!/[.!?]$/.test(combined)) combined += ".";
        result.push(combined);
        i += 2;
        continue;
      }
      result.push(s);
      i++;
    } else {
      result.push(s);
      i++;
    }
  }
  return result.join(" ");
}

function insertNoise(paragraph: string, count: number): string {
  if (count <= 0) return paragraph;
  const noises = [
    "I think.",
    "Honestly.",
    "Really.",
    "No, seriously.",
    "Here's what I mean.",
    "Let me put it this way.",
    "You know what I mean?",
    "Think about it.",
  ];
  for (let n = 0; n < count; n++) {
    if (paragraph.length > 40) {
      const noise = pick(noises);
      const sentences = paragraph.split(/(?<=[.!?])\s+/);
      if (sentences.length > 2) {
        const idx = 1 + Math.floor(Math.random() * (sentences.length - 1));
        sentences.splice(idx, 0, noise);
        paragraph = sentences.join(" ");
      }
    }
  }
  return paragraph;
}

export function ruleBasedPolish(
  text: string,
  opts: { vocabulary?: boolean; contractions?: boolean } = {}
): string {
  const { vocabulary = true, contractions = true } = opts;
  if (vocabulary) {
    for (const [pattern, replacement] of AI_VOCABULARY_SWAPS) {
      text = text.replace(pattern, replacement);
    }
  }
  if (contractions) {
    for (const [pattern, replacement] of CONTRACTION_PATTERNS) {
      text = text.replace(pattern, replacement);
    }
  }
  text = text.replace(/\s{2,}/g, " ");
  return text.trim();
}

export function scramble(text: string, strength: string = "medium"): string {
  const configs: Record<string, { synonymProb: number; noiseCount: number; varySentences: boolean }> = {
    light: { synonymProb: 0.15, noiseCount: 0, varySentences: false },
    medium: { synonymProb: 0.3, noiseCount: 0, varySentences: true },
    aggressive: { synonymProb: 0.5, noiseCount: 0, varySentences: true },
    ninja: { synonymProb: 0.65, noiseCount: 0, varySentences: true },
  };
  const cfg = configs[strength] || configs.medium;

  text = removeFiller(text);
  text = scrambleSynonyms(text, cfg.synonymProb);

  const paragraphs = text.split(/\n\s*\n/);
  const processed: string[] = [];
  for (const para of paragraphs) {
    let p = para.trim();
    if (!p) continue;
    if (cfg.varySentences) {
      p = varySentenceLengths(p);
    }
    p = insertNoise(p, cfg.noiseCount);
    processed.push(p);
  }

  text = processed.join("\n\n");
  text = text.replace(/\s{2,}/g, " ");
  text = text.replace(/\s+\./g, ".");
  text = text.replace(/\s+,/g, ",");
  return text.trim();
}
