import type { APIRoute } from "astro";
import { getAvailableEngines } from "../../lib/ai";

interface Env {
  AI?: unknown;
  GEMINI_API_KEY?: string;
  GROQ_API_KEY?: string;
}

export const GET: APIRoute = async ({ locals }) => {
  const env = (locals as any)._env as Env | undefined;
  const engines = getAvailableEngines(env || {});

  return new Response(JSON.stringify({
    status: "ok",
    version: "0.2.0",
    engines,
  }), {
    headers: { "Content-Type": "application/json" },
  });
};
