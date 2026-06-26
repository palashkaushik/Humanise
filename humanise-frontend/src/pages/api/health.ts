import type { APIRoute } from "astro";

const BACKEND_URL = "https://humanise.onrender.com";

export const GET: APIRoute = async () => {
  try {
    const resp = await fetch(`${BACKEND_URL}/api/health`);
    const data = await resp.json();
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({
      status: "error",
      engines: [],
      error: "Backend unavailable",
    }), {
      headers: { "Content-Type": "application/json" },
      status: 502,
    });
  }
};
