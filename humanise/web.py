from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
import os

from humanise.pipeline import Humanise
from humanise.rules.polish import rule_based_polish
from humanise.detection.feedback import detect_patterns

app = FastAPI(title="Humanise", description="AI text humanization API — free, open-source", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=WEB_UI, status_code=200)


@app.post("/api/humanize", response_model=HumaniseResponse)
async def humanize(req: HumaniseRequest):
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
async def detect(req: DetectRequest):
    analysis = detect_patterns(req.text)
    return DetectResponse(**analysis)


@app.post("/api/rules", response_model=RulesResponse)
async def rules(req: RulesRequest):
    return RulesResponse(text=rule_based_polish(req.text))


@app.get("/api/health")
async def health():
    h = _get_humaniser()
    return {
        "status": "ok",
        "version": "0.1.0",
        "engines": [e.name for e in h.engines],
    }


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
