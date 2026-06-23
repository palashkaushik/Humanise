# Humanise — AI Writing Humanization Tool

A free, open-source tool to make AI-generated text read like a human wrote it.

## Architecture

```
Input → [Prompt Engine] → [LLM Rewriters] → [Rule Polish] → [Detection Check] → Output
         templates.py     ollama/gemini/groq  rules/polish.py  detection/feedback.py
```

- **prompts/templates.py** — anti-detection prompt templates with burstiness, perplexity, structural disruption rules
- **engines/** — LLM backends: Ollama (local, free), Gemini (1.5K/day free), Groq (30/min free)
- **rules/polish.py** — regex-based post-processing: AI vocabulary swaps, contraction injection
- **detection/feedback.py** — pattern detection: 19 AI markers, sentence uniformity scoring
- **pipeline.py** — orchestration: multi-pass rewriting with engine rotation, feedback loop

## Principles

1. **Free by default** — zero API cost with Ollama. Optional cloud engines for quality.
2. **Genuine humanization, not detector-proofing** — rewrites at structural level, not token swaps
3. **Multi-engine fingerprint mixing** — different LLMs produce different statistical signatures
4. **Detection-aware but not detection-chasing** — internal scoring for quality, not an arms race

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
