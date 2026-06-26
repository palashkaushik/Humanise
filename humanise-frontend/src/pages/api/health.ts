import type { APIRoute } from "astro";

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
  } catch {
    return { healthy: false, error: "connection_failed" };
  }
}

async function checkGeminiHealth(apiKey: string): Promise<{ healthy: boolean; error?: string }> {
  try {
    const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
    if (resp.ok) return { healthy: true };
    if (resp.status === 429) return { healthy: false, error: "rate_limited" };
    return { healthy: false, error: "unknown" };
  } catch {
    return { healthy: false, error: "connection_failed" };
  }
}

export const GET: APIRoute = async ({ locals }) => {
  const env = (locals as any)._env as Env | undefined;
  const engines: { name: string; available: boolean; healthy: boolean; error?: string }[] = [];

  if (env?.GROQ_API_KEY) {
    const h = await checkGroqHealth(env.GROQ_API_KEY);
    engines.push({ name: "groq", available: true, healthy: h.healthy, error: h.error });
  }
  if (env?.GEMINI_API_KEY) {
    const h = await checkGeminiHealth(env.GEMINI_API_KEY);
    engines.push({ name: "gemini", available: true, healthy: h.healthy, error: h.error });
  }
  if (env?.AI) {
    engines.push({ name: "cloudflare-ai", available: true, healthy: true });
  }

  return new Response(JSON.stringify({
    status: "ok",
    version: "0.2.0",
    engines,
  }), {
    headers: { "Content-Type": "application/json" },
  });
};
