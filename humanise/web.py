from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.responses import Response
from pydantic import BaseModel, Field
from typing import Optional
import os

from humanise.pipeline import Humanise
from humanise.rules.polish import rule_based_polish
from humanise.detection.feedback import detect_patterns
from humanise import api_keys

app = FastAPI(title="Humanise", description="AI text humanization API — free, open-source", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_keys.init()

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434").replace("tcp://", "http://")
if not OLLAMA_URL.startswith("http"):
    OLLAMA_URL = f"http://{OLLAMA_URL}"


def _get_humaniser():
    return Humanise(
        ollama_url=OLLAMA_URL,
        gemini_key=GEMINI_KEY,
        groq_key=GROQ_KEY,
    )


class HumaniseRequest(BaseModel):
    text: str = Field(..., description="AI-generated text to humanize")
    strength: str = Field("medium", description="Rewrite intensity: light, medium, aggressive, ninja")
    feedback: bool = Field(False, description="Enable detection feedback loop")


class HumaniseResponse(BaseModel):
    text: str
    engine: Optional[str] = None


class DetectRequest(BaseModel):
    text: str = Field(...)


class DetectResponse(BaseModel):
    total_score: int = Field(..., description="AI-likeness score (0=human, 100=AI)")
    matches: dict = {}
    pattern_count: int = 0
    sentence_uniformity: float = 0.0
    concerns: list[str] = []


class RulesRequest(BaseModel):
    text: str = Field(...)


class RulesResponse(BaseModel):
    text: str


class KeyRequest(BaseModel):
    name: str = Field("", description="Optional name for the key")


def _get_api_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return request.headers.get("X-API-Key", "")


def _require_key(request: Request) -> dict:
    key = _get_api_key(request)
    if not key:
        raise HTTPException(status_code=401, detail={
            "error": "missing_key",
            "message": "Include an API key: Authorization: Bearer hu_...",
            "get_key": "https://humanise.pages.dev/keys",
        })
    origin = request.headers.get("Origin", "") or request.headers.get("Referer", "")
    result = api_keys.check_rate_limit(key, origin=origin)
    if not result["allowed"]:
        raise HTTPException(status_code=429, detail=result)
    return result


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=WEB_UI, status_code=200)


@app.post("/api/keys/generate")
async def generate_key(req: KeyRequest):
    api_key = api_keys.generate_key(name=req.name)
    return {
        "key": api_key.key,
        "tier": api_key.tier,
        "message": "Save this key — it won't be shown again. Add to your site: <script src='https://humanise.pages.dev/widget.js?key=" + api_key.key + "'></script>",
    }


@app.get("/api/keys/usage")
async def key_usage(request: Request):
    key = _get_api_key(request)
    if not key:
        raise HTTPException(status_code=401, detail={"error": "missing_key"})
    usage = api_keys.get_usage(key)
    if not usage:
        raise HTTPException(status_code=404, detail={"error": "key_not_found"})
    return usage


@app.post("/api/humanize", response_model=HumaniseResponse)
async def humanize(req: HumaniseRequest, request: Request):
    _require_key(request)
    try:
        h = _get_humaniser()
        if req.feedback:
            result = h.humanize_with_feedback(req.text, strength=req.strength)
        else:
            result = h.humanize(req.text, strength=req.strength)
        return HumaniseResponse(text=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/detect", response_model=DetectResponse)
async def detect(req: DetectRequest, request: Request):
    _require_key(request)
    analysis = detect_patterns(req.text)
    return DetectResponse(**analysis)


@app.post("/api/rules", response_model=RulesResponse)
async def rules(req: RulesRequest, request: Request):
    _require_key(request)
    return RulesResponse(text=rule_based_polish(req.text))


@app.get("/api/health")
async def health():
    h = _get_humaniser()
    engines_status = []
    for engine in h.engines:
        status = {"name": engine.name, "available": engine.available()}
        if engine.name == "groq":
            try:
                from groq import Groq
                client = Groq(api_key=engine.api_key)
                client.models.list()
                status["healthy"] = True
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    status["healthy"] = False
                    status["error"] = "rate_limited"
                else:
                    status["healthy"] = False
                    status["error"] = str(e)[:100]
        engines_status.append(status)
    return {
        "status": "ok",
        "version": "0.2.0",
        "engines": engines_status,
    }


@app.get("/widget.js")
async def widget_js(request: Request):
    api_key = request.query_params.get("key", "")
    js = f"""(function() {{
  const API = 'https://humanise.onrender.com';
  const KEY = '{api_key}';

  const css = document.createElement('style');
  css.textContent = `
    .humanise-widget {{
      position: fixed; bottom: 20px; right: 20px; z-index: 99999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    .humanise-btn {{
      background: #10b981; color: white; border: none; border-radius: 12px;
      padding: 12px 20px; font-size: 14px; font-weight: 600; cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: flex; align-items: center; gap: 8px;
      transition: all 0.2s;
    }}
    .humanise-btn:hover {{ background: #059669; transform: translateY(-1px); }}
    .humanise-btn.processing {{ opacity: 0.7; pointer-events: none; }}
    .humanise-panel {{
      display: none; position: fixed; bottom: 70px; right: 20px; width: 380px;
      background: #18181b; border: 1px solid #27272a; border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4); overflow: hidden; z-index: 99999;
    }}
    .humanise-panel.open {{ display: block; }}
    .humanise-panel-header {{
      padding: 12px 16px; border-bottom: 1px solid #27272a;
      display: flex; justify-content: space-between; align-items: center;
    }}
    .humanise-panel-header span {{ color: #fafafa; font-weight: 600; font-size: 14px; }}
    .humanise-panel-close {{
      background: none; border: none; color: #71717a; cursor: pointer; font-size: 18px;
    }}
    .humanise-panel-body {{ padding: 16px; }}
    .humanise-panel textarea {{
      width: 100%; min-height: 120px; background: #09090b; color: #fafafa;
      border: 1px solid #27272a; border-radius: 8px; padding: 12px; font-size: 13px;
      resize: vertical; font-family: inherit; box-sizing: border-box;
    }}
    .humanise-panel textarea:focus {{ outline: none; border-color: #3f3f46; }}
    .humanise-panel-controls {{ display: flex; gap: 8px; margin-top: 10px; align-items: center; }}
    .humanise-panel-controls select {{
      background: #09090b; color: #fafafa; border: 1px solid #27272a;
      border-radius: 6px; padding: 6px 10px; font-size: 13px;
    }}
    .humanise-panel-controls button {{
      background: #10b981; color: white; border: none; border-radius: 8px;
      padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer;
    }}
    .humanise-panel-controls button:hover {{ background: #059669; }}
    .humanise-panel-output {{
      margin-top: 12px; padding: 12px; background: #09090b; border: 1px solid #27272a;
      border-radius: 8px; font-size: 13px; color: #d4d4d8; white-space: pre-wrap;
      max-height: 200px; overflow-y: auto; display: none;
    }}
    .humanise-panel-footer {{
      padding: 8px 16px; border-top: 1px solid #27272a;
      font-size: 11px; color: #52525b; text-align: center;
    }}
    .humanise-panel-footer a {{ color: #71717a; text-decoration: none; }}
    .humanise-toast {{
      position: fixed; top: 20px; right: 20px; z-index: 999999;
      background: #ef4444; color: white; padding: 12px 20px; border-radius: 8px;
      font-size: 13px; font-family: -apple-system, sans-serif;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: none;
    }}
  `;
  document.head.appendChild(css);

  document.body.insertAdjacentHTML('beforeend', `
    <div class="humanise-widget">
      <div class="humanise-panel" id="humanisePanel">
        <div class="humanise-panel-header">
          <span>Humanise</span>
          <button class="humanise-panel-close" onclick="document.getElementById('humanisePanel').classList.remove('open')">&times;</button>
        </div>
        <div class="humanise-panel-body">
          <textarea id="humaniseInput" placeholder="Paste AI text here..."></textarea>
          <div class="humanise-panel-controls">
            <select id="humaniseStrength">
              <option value="medium">Medium</option>
              <option value="light">Light</option>
              <option value="aggressive">Aggressive</option>
              <option value="ninja">Ninja</option>
            </select>
            <button id="humaniseGo">Humanize</button>
          </div>
          <div class="humanise-panel-output" id="humaniseOutput"></div>
        </div>
        <div class="humanise-panel-footer">
          Powered by <a href="https://humanise.pages.dev" target="_blank">Humanise</a> &middot; Free tier: 50/day
        </div>
      </div>
      <button class="humanise-btn" id="humaniseToggle">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
        Humanise
      </button>
    </div>
    <div class="humanise-toast" id="humaniseToast"></div>
  `);

  document.getElementById('humaniseToggle').addEventListener('click', function() {{
    document.getElementById('humanisePanel').classList.toggle('open');
  }});

  document.getElementById('humaniseGo').addEventListener('click', async function() {{
    const input = document.getElementById('humaniseInput').value.trim();
    if (!input) return;
    const btn = this;
    const output = document.getElementById('humaniseOutput');
    btn.textContent = 'Processing...';
    btn.disabled = true;
    output.style.display = 'block';
    output.textContent = '';
    try {{
      const r = await fetch(API + '/api/humanize', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + KEY }},
        body: JSON.stringify({{ text: input, strength: document.getElementById('humaniseStrength').value }}),
      }});
      const d = await r.json();
      if (r.status === 429) {{
        output.textContent = d.message || 'Rate limit exceeded';
        output.style.color = '#ef4444';
      }} else if (r.status === 401) {{
        output.textContent = d.message || 'Invalid API key';
        output.style.color = '#ef4444';
      }} else {{
        output.textContent = d.text || d.detail || 'Error';
        output.style.color = '#d4d4d8';
      }}
    }} catch (e) {{
      output.textContent = 'Error: ' + e.message;
      output.style.color = '#ef4444';
    }}
    btn.textContent = 'Humanize';
    btn.disabled = false;
  }});
}})();
"""
    return Response(content=js, media_type="application/javascript")


WEB_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Humanise — AI Text Humanizer</title>
<style>
:root{--bg:#0d1117;--fg:#c9d1d9;--border:#30363d;--accent:#58a6ff;--green:#3fb950;--red:#f85149;--input-bg:#161b22}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--fg);min-height:100vh}
.container{max-width:900px;margin:0 auto;padding:2rem 1rem}
header{text-align:center;margin-bottom:2rem}
header h1{font-size:2rem;margin-bottom:.25rem}
header p{color:#8b949e}
.card{background:var(--input-bg);border:1px solid var(--border);border-radius:8px;padding:1.5rem;margin-bottom:1rem}
textarea{width:100%;min-height:180px;background:var(--bg);color:var(--fg);border:1px solid var(--border);border-radius:6px;padding:.75rem;font-size:14px;resize:vertical;font-family:inherit}
.controls{display:flex;gap:0.75rem;flex-wrap:wrap;align-items:center;margin-top:1rem}
select,button{padding:0.5rem 1rem;border-radius:6px;font-size:14px;border:1px solid var(--border);cursor:pointer}
select{background:var(--bg);color:var(--fg)}
button{background:var(--accent);color:#fff;border:none;font-weight:600}
button:hover{opacity:0.85}
button.secondary{background:var(--input-bg);border:1px solid var(--border);color:var(--fg)}
label{font-size:13px;color:#8b949e;display:flex;align-items:center;gap:.25rem}
#output{min-height:120px;white-space:pre-wrap;margin-top:1rem}
.score{font-size:3rem;font-weight:700;text-align:center}
.score.low{color:var(--green)}
.score.med{color:#d2991d}
.score.high{color:var(--red)}
.stats{display:flex;gap:2rem;justify-content:center;margin-top:.5rem;flex-wrap:wrap}
.stat{text-align:center}
.stat .val{font-size:1.5rem;font-weight:600}
.stat .lbl{font-size:12px;color:#8b949e}
.matches{margin-top:1rem}
.match{border:1px solid var(--border);border-radius:4px;padding:.5rem;margin-bottom:.25rem;display:flex;justify-content:space-between}
.tabs{display:flex;gap:0;margin-bottom:1rem}
.tab{padding:.5rem 1.25rem;border:1px solid var(--border);border-radius:6px 6px 0 0;cursor:pointer;font-size:14px;background:var(--bg);color:#8b949e}
.tab.active{background:var(--input-bg);color:var(--fg);border-bottom-color:transparent}
.spinner{display:none;text-align:center;padding:1rem}
.spinner.visible{display:block}
footer{text-align:center;color:#484f58;font-size:12px;margin-top:2rem}
footer a{color:var(--accent)}
</style>
</head>
<body>
<div class="container">
<header>
<h1>Humanise</h1>
<p>Free, open-source AI text humanization — make AI writing sound human</p>
</header>

<div class="tabs">
<div class="tab active" onclick="switchTab('humanize')">Humanize</div>
<div class="tab" onclick="switchTab('detect')">Detect</div>
</div>

<div id="tab-humanize" class="card">
<textarea id="input-text" placeholder="Paste AI-generated text here..."></textarea>
<div class="controls">
<select id="strength">
<option value="light">Light</option>
<option value="medium" selected>Medium</option>
<option value="aggressive">Aggressive</option>
<option value="ninja">Ninja</option>
</select>
<label><input type="checkbox" id="feedback"> Feedback loop</label>
<button onclick="humanize()">Humanize</button>
<button class="secondary" onclick="rulesOnly()">Rules only (instant)</button>
</div>
<div id="spinner-humanize" class="spinner">Rewriting...</div>
<div id="output"></div>
</div>

<div id="tab-detect" class="card" style="display:none">
<textarea id="detect-text" placeholder="Paste text to analyze..."></textarea>
<div class="controls">
<button onclick="detect()">Analyze</button>
</div>
<div id="detect-results"></div>
</div>

<footer>
Powered by Ollama (free, local) &middot; Gemini (1.5K/day free) &middot; Groq (30/min free) &middot;
<a href="https://github.com">GitHub</a>
</footer>
</div>
<script>
function switchTab(tab){
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
document.querySelectorAll('.card[id^="tab-"]').forEach(c=>c.style.display='none');
document.querySelector(`.tab:nth-child(${tab==='humanize'?1:2})`).classList.add('active');
document.getElementById('tab-'+tab).style.display='block';
}

async function humanize(){
const text=document.getElementById('input-text').value.trim();
if(!text)return;
document.getElementById('spinner-humanize').classList.add('visible');
document.getElementById('output').textContent='';
const strength=document.getElementById('strength').value;
const feedback=document.getElementById('feedback').checked;
try{
const r=await fetch('/api/humanize',{
method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({text,strength,feedback})
});
const d=await r.json();
document.getElementById('output').textContent=d.text||d.detail;
}catch(e){
document.getElementById('output').textContent='Error: '+e.message;
}
document.getElementById('spinner-humanize').classList.remove('visible');
}

async function rulesOnly(){
const text=document.getElementById('input-text').value.trim();
if(!text)return;
try{
const r=await fetch('/api/rules',{
method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({text})
});
const d=await r.json();
document.getElementById('output').textContent=d.text||d.detail;
}catch(e){
document.getElementById('output').textContent='Error: '+e.message;
}
}

async function detect(){
const text=document.getElementById('detect-text').value.trim();
if(!text)return;
try{
const r=await fetch('/api/detect',{
method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({text})
});
const d=await r.json();
let cls='low';if(d.total_score>30)cls='med';if(d.total_score>60)cls='high';
let html=`<div class="score ${cls}">${d.total_score}</div>
<div class="stats">
<div class="stat"><div class="val">${d.pattern_count}</div><div class="lbl">AI patterns</div></div>
<div class="stat"><div class="val">${d.sentence_uniformity.toFixed(2)}</div><div class="lbl">uniformity</div></div>
</div>`;
if(Object.keys(d.matches).length){
html+='<div class="matches">'+Object.entries(d.matches).map(([k,v])=>`<div class="match"><span>${k.replace(/_/g,' ')}</span><span>${v}</span></div>`).join('')+'</div>';
}
if(d.concerns.length){
html+='<div class="matches">'+d.concerns.map(c=>`<div class="match">${c}</div>`).join('')+'</div>';
}
document.getElementById('detect-results').innerHTML=html;
}catch(e){
document.getElementById('detect-results').textContent='Error: '+e.message;
}
}
</script>
</body>
</html>"""
