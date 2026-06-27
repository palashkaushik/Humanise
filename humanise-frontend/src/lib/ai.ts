import { ANTI_DETECTION_PROMPT } from "./prompts";

export interface EngineResult {
  text: string;
  engine: string;
}

type EngineFn = () => Promise<EngineResult>;

interface AiEnv {
  AI?: {
    run(model: string, options: {
      messages: { role: string; content: string }[];
      temperature?: number;
    }): Promise<{ response?: string }>;
  };
  GEMINI_API_KEY?: string;
  GROQ_API_KEY?: string;
}

export async function rewriteText(
  text: string,
  env: AiEnv,
  temperature: number = 0.9,
  engineIndex: number = 0,
): Promise<EngineResult> {
  const engines: EngineFn[] = [];

  if (env.AI) {
    engines.push(async () => {
      const result = await env.AI!.run("@cf/meta/llama-3.1-8b-instruct", {
        messages: [
          { role: "system", content: ANTI_DETECTION_PROMPT },
          { role: "user", content: `Rewrite this to sound human:\n\n${text}` },
        ],
        temperature,
      });
      return { text: result.response || "", engine: "cloudflare-ai" };
    });
  }

  if (env.GEMINI_API_KEY) {
    engines.push(async () => {
      const resp = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${env.GEMINI_API_KEY}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ parts: [{ text: `${ANTI_DETECTION_PROMPT}\n\nRewrite this to sound human:\n\n${text}` }] }],
            generationConfig: { temperature },
          }),
        },
      );
      const data = await resp.json() as any;
      return { text: data.candidates?.[0]?.content?.parts?.[0]?.text || "", engine: "gemini" };
    });
  }

  if (env.GROQ_API_KEY) {
    engines.push(async () => {
      const resp = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${env.GROQ_API_KEY}`,
        },
        body: JSON.stringify({
          model: "openai/gpt-oss-20b",
          messages: [
            { role: "system", content: ANTI_DETECTION_PROMPT },
            { role: "user", content: `Rewrite this to sound human:\n\n${text}` },
          ],
          temperature,
        }),
      });
      const data = await resp.json() as any;
      return { text: data.choices?.[0]?.message?.content || "", engine: "groq" };
    });
  }

  if (engines.length === 0) {
    return { text, engine: "none" };
  }

  const engine = engines[engineIndex % engines.length];
  try {
    return await engine();
  } catch {
    return { text, engine: "error" };
  }
}

export function getAvailableEngineCount(env: AiEnv): number {
  let count = 0;
  if (env.AI) count++;
  if (env.GEMINI_API_KEY) count++;
  if (env.GROQ_API_KEY) count++;
  return count;
}

export function getAvailableEngines(env: AiEnv): string[] {
  const engines: string[] = [];
  if (env.AI) engines.push("cloudflare-ai");
  if (env.GEMINI_API_KEY) engines.push("gemini");
  if (env.GROQ_API_KEY) engines.push("groq");
  return engines;
}
