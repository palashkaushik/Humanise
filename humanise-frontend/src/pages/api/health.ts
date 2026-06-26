import type { APIRoute } from "astro";
import { getAvailableEngines } from "../../lib/ai";

interface Env {
  AI?: unknown;
  GEMINI_API_KEY?: string;
  GROQ_API_KEY?: string;
}

async function checkGroqHealth(apiKey: string): Promise<{ healthy: boolean; error?: string }> {
  try {
    const resp = await fetch("https://api.groq.com/openai/v1/models", {
      headers: { Authorization: `Bearer ${apiKey}` },
    });
    if (resp.ok) return { healthy: true };
    const data = await resp.json() as any;
    if (resp.status === 429) return { healthy: false, error: "rate_limited" };
    return { healthy: false, error: data?.error?.message?.slice(0, 100) || "unknown" };
  } catch (e) {
    return { healthy: false, error: "connection_failed" };
  }
}

export const GET: APIRoute = async ({ locals }) => {
  const env = (locals as any)._env as Env | undefined;
  const engineNames = getAvailableEngines(env || {});

  const engines: { name: string; available: boolean; healthy?: boolean; error?: string }[] = [];
  for (const name of engineNames) {
    const entry: { name: string; available: boolean; healthy?: boolean; error?: string } = { name, available: true };
    if (name === "groq" && env?.GROQ_API_KEY) {
      const health = await checkGroqHealth(env.GROQ_API_KEY);
      entry.healthy = health.healthy;
      if (health.error) entry.error = health.error;
    } else {
      entry.healthy = true;
    }
    engines.push(entry);
  }

  return new Response(JSON.stringify({
    status: "ok",
    version: "0.2.0",
    engines,
  }), {
    headers: { "Content-Type": "application/json" },
  });
};
