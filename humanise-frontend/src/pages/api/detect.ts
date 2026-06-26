import type { APIRoute } from "astro";

const BACKEND_URL = "https://humanise.onrender.com";

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

  try {
    const resp = await fetch(`${BACKEND_URL}/api/detect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: body.text }),
    });
    const data = await resp.json();
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: "Backend unavailable" }), { status: 502 });
  }
};
