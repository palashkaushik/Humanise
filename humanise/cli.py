import sys
import os
import argparse
import json
from humanise.pipeline import Humanise, MULTI_MODEL_ROTATION
from humanise.rules.polish import rule_based_polish
from humanise.rules.scramble import scramble


def _get_key(flag_value: str | None, env_var: str) -> str | None:
    if flag_value:
        return flag_value
    return os.environ.get(env_var) or None


def _format_score(analysis: dict, label: str = "") -> str:
    lines = []
    if label:
        lines.append(f"  {label}:")
    lines.append(f"    Human Score: {analysis['human_score']}%  |  "
                 f"AI Score: {analysis['ai_score']}  |  "
                 f"Burstiness: {analysis['burstiness']}  |  "
                 f"Perplexity: {analysis['perplexity']}")
    readability = analysis["readability"]
    lines.append(f"    Readability: Grade {readability['grade_level']}  |  "
                 f"Reading Ease {readability['reading_ease']} ({readability['label']})")
    return "\n".join(lines)


def _format_fixes(fixes: dict) -> str:
    if not fixes:
        return "  (no pattern fixes applied)"
    lines = ["  Fixes applied:"]
    for name, count in sorted(fixes.items(), key=lambda x: -x[1]):
        lines.append(f"    - {name}: {count} removed")
    return "\n".join(lines)


def _print_score_report(report: dict):
    engines = report['engines_used']
    if isinstance(engines, dict):
        engines_str = f"{engines['passes']} passes, {len(set(engines['engines']))} engines"
    else:
        engines_str = str(engines)

    print()
    print("=" * 52)
    print("  HUMANISE SCORE REPORT")
    print("=" * 52)
    print(f"  Strength: {report['strength']}  |  "
          f"Engines: {engines_str}  |  "
          f"Time: {report['elapsed_ms']}ms")
    print("-" * 52)
    print(f"  Human Score: {report['before']['human_score']}%  ->  "
          f"{report['after']['human_score']}%  "
          f"({'+' if report['improvement'] >= 0 else ''}{report['improvement']}%)")
    print(f"  AI Score:    {report['before']['ai_score']}    ->  "
          f"{report['after']['ai_score']}")
    print(f"  Burstiness:  {report['before']['burstiness']}  ->  "
          f"{report['after']['burstiness']}")
    print(f"  Perplexity:  {report['before']['perplexity']}  ->  "
          f"{report['after']['perplexity']}")
    r_before = report["before"]["readability"]
    r_after = report["after"]["readability"]
    print(f"  Readability: Grade {r_before['grade_level']} ({r_before['label']})  ->  "
          f"Grade {r_after['grade_level']} ({r_after['label']})")
    print("-" * 52)

    if report.get("pass_results"):
        print("  Pass breakdown:")
        for pr in report["pass_results"]:
            delta = pr["score_after"] - pr["score_before"]
            print(f"    Pass {pr['pass']}: {pr['style']} via {pr['engine']} "
                  f"({pr['score_before']:.0f}% -> {pr['score_after']:.0f}%, "
                  f"{'+' if delta >= 0 else ''}{delta:.0f}%)")
        print("-" * 52)

    if report["fixes"]:
        for name, count in sorted(report["fixes"].items(), key=lambda x: -x[1]):
            print(f"  {name}: {count} removed")
    if report["before"]["concerns"]:
        print("-" * 52)
        print("  Concerns in original:")
        for c in report["before"]["concerns"]:
            print(f"  ! {c}")
    if report["after"]["concerns"]:
        print()
        print("  Remaining concerns:")
        for c in report["after"]["concerns"]:
            print(f"  ! {c}")
    print("=" * 52)
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="humanise",
        description="AI text humanization -- make AI writing sound human",
    )
    sub = parser.add_subparsers(dest="cmd")

    humanize_cmd = sub.add_parser("humanize", help="Humanize text")
    humanize_cmd.add_argument("--text", "-t", help="Text to humanize")
    humanize_cmd.add_argument("--file", "-f", help="File to humanize")
    humanize_cmd.add_argument("--strength", "-s", default="medium",
                              choices=["light", "medium", "aggressive", "ninja"])
    humanize_cmd.add_argument("--feedback", action="store_true",
                              help="Use detection feedback loop")
    humanize_cmd.add_argument("--score", action="store_true",
                              help="Show before/after human score")
    humanize_cmd.add_argument("--report", action="store_true",
                              help="Show full score report with diagnostics")
    humanize_cmd.add_argument("--output", "-o", help="Output file")
    humanize_cmd.add_argument("--ollama-model", default="llama3.1:8b")
    humanize_cmd.add_argument("--gemini-key", default=None,
                              help="Gemini API key (or set GEMINI_API_KEY env var)")
    humanize_cmd.add_argument("--groq-key", default=None,
                              help="Groq API key (or set GROQ_API_KEY env var)")

    detect_cmd = sub.add_parser("detect", help="Detect AI patterns in text")
    detect_cmd.add_argument("--text", "-t")
    detect_cmd.add_argument("--file", "-f")
    detect_cmd.add_argument("--full", action="store_true",
                            help="Full analysis with readability, burstiness, perplexity")

    rules_cmd = sub.add_parser("rules", help="Rule-based polish only (no LLM)")
    rules_cmd.add_argument("--text", "-t")
    rules_cmd.add_argument("--file", "-f")

    scramble_cmd = sub.add_parser("scramble", help="Break token-level AI detection patterns (no LLM)")
    scramble_cmd.add_argument("--text", "-t")
    scramble_cmd.add_argument("--file", "-f")
    scramble_cmd.add_argument("--strength", "-s", default="medium",
                              choices=["light", "medium", "aggressive", "ninja"])

    args = parser.parse_args()

    if args.cmd == "humanize":
        text = _get_text(args)
        if not text:
            print("Error: no text provided", file=sys.stderr)
            sys.exit(1)

        h = Humanise(
            ollama_model=args.ollama_model,
            gemini_key=_get_key(args.gemini_key, "GEMINI_API_KEY"),
            groq_key=_get_key(args.groq_key, "GROQ_API_KEY"),
            groq_models=MULTI_MODEL_ROTATION if _get_key(args.groq_key, "GROQ_API_KEY") else None,
        )

        if args.report:
            result = h.humanize_with_report(text, strength=args.strength)
            _print_score_report(result)
            _output(result["text"], args.output)
            return

        if args.score:
            from humanise.detection.feedback import full_analysis
            before = full_analysis(text)
            if args.feedback:
                result = h.humanize_with_feedback(text, strength=args.strength)
            else:
                result = h.humanize(text, strength=args.strength)
            after = full_analysis(result)
            improvement = round(after["human_score"] - before["human_score"], 1)
            print()
            print(f"  Human Score: {before['human_score']}%  ->  "
                  f"{after['human_score']}%  "
                  f"({'+' if improvement >= 0 else ''}{improvement}%)")
            print(f"  Readability: {after['readability']['label']} "
                  f"(Grade {after['readability']['grade_level']})")
            print()
            _output(result, args.output)
            return

        if args.feedback:
            result = h.humanize_with_feedback(text, strength=args.strength)
        else:
            result = h.humanize(text, strength=args.strength)

        _output(result, args.output)

    elif args.cmd == "detect":
        text = _get_text(args)
        h = Humanise()
        if args.full:
            analysis = h.analyze(text)
            print(json.dumps(analysis, indent=2))
        else:
            analysis = h.detect(text)
            print(json.dumps(analysis, indent=2))

    elif args.cmd == "rules":
        text = _get_text(args)
        result = rule_based_polish(text)
        _output(result, None)

    elif args.cmd == "scramble":
        text = _get_text(args)
        result = scramble(text, strength=args.strength)
        _output(result, None)

    else:
        parser.print_help()


def _get_text(args) -> str:
    if args.text:
        return args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def _output(text: str, filepath: str | None):
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved to {filepath}")
    else:
        try:
            print(text)
        except UnicodeEncodeError:
            safe = text.encode("cp1252", errors="replace").decode("cp1252", errors="replace")
            print(safe)


if __name__ == "__main__":
    main()
