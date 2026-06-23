import type { APIRoute } from "astro";
import { ruleBasedPolish } from "../../lib/rules";

export const POST: APIRoute = async ({ request }) => {
  let body: { text?: string };
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON" }), { status: 400 });
  }

  if (!body.text?.trim()) {
    return new Response(JSON.stringify({ error: "No text provided" }), { status: 400 });
  }

  const result = ruleBasedPolish(body.text);

  return new Response(JSON.stringify({ text: result }), {
    headers: { "Content-Type": "application/json" },
  });
};
