# Humanise

Free, open-source tool to make AI-generated text read like a human wrote it.

```
humanise humanize --text "AI-generated text here" --strength aggressive
```

## Principles

- **Free by default** — zero API cost with Ollama. Optional cloud engines for quality.
- **Genuine humanization, not detector-proofing** — rewrites at structural level, not token swaps.
- **Multi-engine fingerprint mixing** — different LLMs produce different statistical signatures.
- **Detection-aware but not detection-chasing** — internal scoring for quality, not an arms race.

## Quick Start

```bash
# Install
pip install humanise

# Humanize text with Ollama (free, local)
humanise humanize --text "AI text here" --strength medium

# From a file
humanise humanize --file draft.txt --output final.txt

# With detection feedback loop (rewrite until it passes)
humanise humanize --file draft.txt --feedback

# Rule-based polish only (no LLM needed)
humanise rules --file draft.txt
```

Requires Python 3.10+ and [Ollama](https://ollama.com) for the default backend. Pull a model:

```bash
ollama pull llama3.1:8b
```

## Engines

| Engine | Cost | Limit | Speed |
|--------|------|-------|-------|
| Ollama | $0 | Unlimited | Local GPU |
| Gemini | $0 | 1500 req/day | Fast |
| Groq | $0 | 30 req/min | Very fast |

Set environment variables for cloud engines:

```powershell
$env:GEMINI_API_KEY = "your-key"      # https://aistudio.google.com/apikey
$env:GROQ_API_KEY = "your-key"        # https://console.groq.com
```

## How It Works

```
Input → [Prompt Engine] → [LLM Rewriters] → [Rule Polish] → [Detection Check] → Output
```

1. **Prompt Engine** — anti-detection template with burstiness, perplexity, structural disruption rules
2. **LLM Rewriters** — multi-pass through different engines (Ollama → Groq → Gemini) to mix statistical fingerprints
3. **Rule Polish** — regex-based post-processing: 40+ AI vocabulary swaps, contraction injection
4. **Detection Check** — 19 pattern detectors score the output; feedback loop re-rewrites flagged sections

## Commands

```bash
# Humanize
humanise humanize -t "text" -s light|medium|aggressive|ninja
humanise humanize -f draft.txt -o result.txt --feedback

# Detect AI patterns
humanise detect -t "text to analyze"
humanise detect -f essay.txt

# Rule-based polish (no LLM, instant)
humanise rules -t "text"
humanise rules -f draft.txt
```

## Detection Patterns Tracked

The detection module scores text against 19 known AI markers:

- **Vocabulary**: "furthermore", "moreover", "delve into", "unprecedented", "transformative", "game-changer", "cutting-edge", "synergy", "robust solution", "multi-faceted"
- **Structure**: "plays a crucial role", "not only X but also Y", "in order to", hedging patterns
- **Style**: "it is important to note", "it is worth noting", three-adjective lists ("X, Y, and Z")
- **Rhythm**: Sentence length uniformity (low burstiness = high AI signal)
- **Marketing**: "innovative", "revolutionary", "groundbreaking", "next-generation" and other sigma adjectives

## Architecture

```
humanise/
├── prompts/templates.py    # Anti-detection prompts, tone profiles, self-check
├── engines/
│   ├── base.py             # BaseEngine, EngineResult dataclass
│   ├── ollama.py           # Local Ollama backend (free, unlimited)
│   ├── gemini.py           # Google Gemini backend (1.5K/day free)
│   └── groq.py             # Groq backend (30/min free)
├── rules/polish.py         # 40 AI vocab swaps + 30 contraction patterns
├── detection/feedback.py   # 19 pattern detectors + sentence uniformity
├── pipeline.py             # Multi-pass orchestration with engine rotation
└── cli.py                  # CLI entry point
```

## License

MIT
