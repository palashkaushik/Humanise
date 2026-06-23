import type { APIRoute } from "astro";
import { ruleBasedPolish, scramble } from "../../lib/rules";
import { fullAnalysis } from "../../lib/detection";
import { rewriteText, getAvailableEngineCount } from "../../lib/ai";

interface Env {
  AI?: unknown;
  GEMINI_API_KEY?: string;
  GROQ_API_KEY?: string;
}

const STRENGTH_CONFIG: Record<string, {
  temperature: number;
  passes: number;
  rulePolish: boolean;
  doScramble: boolean;
  targetScore: number;
  maxFeedbackIterations: number;
}> = {
  light: { temperature: 0.8, passes: 1, rulePolish: true, doScramble: false, targetScore: 60, maxFeedbackIterations: 1 },
  medium: { temperature: 0.9, passes: 1, rulePolish: true, doScramble: false, targetScore: 75, maxFeedbackIterations: 1 },
  aggressive: { temperature: 1.0, passes: 2, rulePolish: true, doScramble: true, targetScore: 85, maxFeedbackIterations: 2 },
  ninja: { temperature: 1.1, passes: 3, rulePolish: true, doScramble: true, targetScore: 95, maxFeedbackIterations: 3 },
};

export const POST: APIRoute = async ({ request, locals }) => {
  let body: { text?: string; strength?: string; feedback?: boolean };
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON" }), { status: 400 });
  }

  const text = body.text?.trim();
  if (!text) {
    return new Response(JSON.stringify({ error: "No text provided" }), { status: 400 });
  }

  const strength = STRENGTH_CONFIG[body.strength || "medium"] ? body.strength! : "medium";
  const config = STRENGTH_CONFIG[strength];
  const useFeedback = body.feedback === true;
  const env = (locals as any)._env as Env | undefined;

  const engineCount = getAvailableEngineCount(env || {});
  const maxIter = useFeedback ? config.maxFeedbackIterations : 1;

  let result = text;
  let engineUsed = "rules-only";

  for (let iter = 0; iter < maxIter; iter++) {
    if (engineCount > 0) {
      for (let pass = 0; pass < config.passes; pass++) {
        const temp = iter > 0 ? 1.0 : config.temperature;
        const engineIdx = pass + iter * config.passes;
        try {
          const rewrote = await rewriteText(result, env || {}, temp, engineIdx);
          if (rewrote.text.trim()) {
            result = rewrote.text;
            engineUsed = rewrote.engine;
          }
        } catch {
          engineUsed = "error";
        }
      }
    }

    if (config.rulePolish) {
      result = ruleBasedPolish(result);
    }
    if (config.doScramble) {
      result = scramble(result, strength);
    }

    if (useFeedback && iter < maxIter - 1) {
      const analysis = fullAnalysis(result);
      if (analysis.human_score >= config.targetScore) break;
    }
  }

  return new Response(JSON.stringify({ text: result, engine: engineUsed }), {
    headers: { "Content-Type": "application/json" },
  });
};
