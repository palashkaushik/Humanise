import type { APIRoute } from "astro";

const BACKEND_URL = "https://humanise.onrender.com";

export const POST: APIRoute = async ({ request }) => {
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

  try {
    const resp = await fetch(`${BACKEND_URL}/api/humanize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        strength: body.strength || "medium",
        feedback: body.feedback || false,
      }),
    });
    const data = await resp.json();
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: "Backend unavailable" }), { status: 502 });
  }
};
