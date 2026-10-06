"""Review dashboard: watch every rendered clip, fix its title, approve or reject.

Deliberately stdlib-only (http.server + json) so it still runs after a sandbox
wipes pip packages. Start it with:

    python3 -m autoclip.dashboard --outdir Shorts

Decisions are written next to the clips in `review.json`, so nothing is lost if
the server restarts. "Export approved" writes `approved.csv` ready for upload.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path("Shorts")
REVIEW = "review.json"


# --------------------------------------------------------------------------- data
def _review_path(d: Path) -> Path:
    return d / REVIEW


def load_clips() -> list[dict]:
    """Every clip under ROOT, merged with its saved review state."""
    out: list[dict] = []
    for cj in sorted(ROOT.rglob("clips.json")):
        try:
            data = json.loads(cj.read_text(encoding="utf-8"))
        except Exception:
            continue
        src = data.get("source", {}) if isinstance(data, dict) else {}
        clips = data.get("clips", data) if isinstance(data, dict) else data
        state = {}
        rp = _review_path(cj.parent)
        if rp.is_file():
            try:
                state = json.loads(rp.read_text(encoding="utf-8"))
            except Exception:
                state = {}
        for c in clips:
            if not isinstance(c, dict):
                continue
            mp4 = Path(c.get("mp4", ""))
            if not mp4.is_file():
                continue
            st = state.get(c["name"], {})
            out.append({
                "id": str(mp4.resolve()),
                "dir": str(cj.parent.resolve()),
                "name": c["name"],
                "title": st.get("title", c.get("title") or ""),
                "status": st.get("status", "pending"),
                "note": st.get("note", ""),
                "duration": round(float(c.get("duration", 0)), 1),
                "size_mb": c.get("size_mb"),
                "start": c.get("start"),
                "hook": c.get("hook", ""),
                "video": c.get("title", ""),
                "source_title": src.get("title", cj.parent.name),
                "source_url": src.get("url", ""),
            })
    return out


def save_review(clip_dir: str, name: str, patch: dict) -> None:
    d = Path(clip_dir)
    rp = _review_path(d)
    state = {}
    if rp.is_file():
        try:
            state = json.loads(rp.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    state.setdefault(name, {}).update(patch)
    rp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def suggest_titles(clip: dict, n: int = 3) -> list[str]:
    """Ask the configured LLM for alternative titles. Empty list if no key."""
    key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        return []
    base = os.getenv("AUTOCLIP_LLM_BASE") or (
        "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else None)
    model = os.getenv("AUTOCLIP_LLM_MODEL",
                      "llama-3.3-70b-versatile" if os.getenv("GROQ_API_KEY")
                      else "gpt-4o-mini")
    try:
        from openai import OpenAI
        r = OpenAI(api_key=key, base_url=base).chat.completions.create(
            model=model, response_format={"type": "json_object"}, temperature=0.9,
            messages=[
                {"role": "system", "content":
                 f'Write {n} different on-screen titles for a Short. 3-6 words each, '
                 f'1-2 fitting emoji, same language as the transcript, no quotes. '
                 f'Return ONLY JSON: {{"titles":[str]}}'},
                {"role": "user", "content": clip.get("hook", "")[:600]}])
        return json.loads(r.choices[0].message.content).get("titles", [])[:n]
    except Exception as exc:  # noqa: BLE001
        return [f"(LLM error: {exc.__class__.__name__})"]


def export_approved() -> str:
    rows = ["title,duration_s,file,source_url"]
    for c in load_clips():
        if c["status"] == "approved":
            t = '"' + (c["title"] or "").replace('"', "'") + '"'
            rows.append(f'{t},{c["duration"]},"{c["id"]}","{c["source_url"]}"')
    p = ROOT / "approved.csv"
    p.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return str(p.resolve())


# --------------------------------------------------------------------------- jobs
JOB: dict = {"running": False, "log": [], "t0": 0.0, "elapsed": 0.0,
             "done": False, "error": "", "made": 0}


class _Tee:
    """Capture pipeline prints into JOB['log'] while still showing them."""

    def __init__(self, real):
        self.real = real
        self.buf = ""

    def write(self, t):
        self.real.write(t)
        self.buf += t
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            if line.strip():
                JOB["log"].append(line.rstrip())
                del JOB["log"][:-400]

    def flush(self):
        self.real.flush()


def run_job(opts: dict) -> None:
    import contextlib
    import sys
    import time as _t
    from . import pipeline

    JOB.update(running=True, log=[], t0=_t.time(), elapsed=0.0,
               done=False, error="", made=0)
    try:
        with contextlib.redirect_stdout(_Tee(sys.__stdout__)):
            res = pipeline.run(
                opts["url"], clips=int(opts.get("clips", 3)),
                genre=opts.get("genre", "vlog"),
                caption_style=opts.get("caption_style") or None,
                profile=opts.get("profile") or None,
                outdir=str(ROOT), limit=int(opts.get("limit", 1)),
                safe_level=int(opts.get("safe", 1)),
                height=int(opts.get("sheight", 1080)),
                caption_box=True if opts.get("cbox") else None,
                crf=int(opts["crf"]) if opts.get("crf") else None,
                langs=tuple((opts.get("langs") or "hi en").split()))
        JOB["made"] = len(res)
    except Exception as exc:  # noqa: BLE001
        JOB["error"] = f"{exc.__class__.__name__}: {exc}"
        JOB["log"].append("ERROR " + JOB["error"])
    finally:
        JOB["elapsed"] = round(_t.time() - JOB["t0"], 1)
        JOB.update(running=False, done=True)


def restyle(clip_id: str, style: str) -> dict:
    """Re-render one clip with a different caption style (no re-download)."""
    import json as _j
    import time as _t
    from . import captions as _c
    from . import transcribe as _tr
    from .pipeline import _one
    from .render import probe_size

    for cj in ROOT.rglob("clips.json"):
        data = _j.loads(cj.read_text(encoding="utf-8"))
        hit = next((c for c in data.get("clips", [])
                    if str(Path(c.get("mp4", "")).resolve()) == clip_id), None)
        if not hit:
            continue

        src = (data.get("source") or {}).get("path", "")
        wj = data.get("words_json", "")
        if not Path(src).is_file():
            return {"error": "source video /tmp se delete ho chuka hai - "
                             "poora link dobara chalao"}
        if not wj or not Path(wj).is_file():
            return {"error": "transcript cache nahi mila - poora link dobara chalao"}

        cfg = data.get("profile") or {}
        # same placement maths the pipeline uses, else captions jump into the
        # blurred band when a clip is restyled
        sw, sh = probe_size(src)
        mv = _c.auto_margin_v(cfg.get("width", 1080), cfg.get("height", 1920),
                              sw, sh, cfg.get("blur_bg", True))
        words = _tr.dedupe(_j.loads(Path(wj).read_text())["words"])
        rel = [{"word": w["word"], "start": w["start"] - hit["start"],
                "end": w["end"] - hit["start"]}
               for w in words if hit["start"] <= w["start"] < hit["end"]]

        name = hit["name"]
        vdir = cj.parent
        ass = _c.build(rel, vdir / f"{name}.ass", width=cfg.get("width", 1080),
                       height=cfg.get("height", 1920),
                       font=cfg.get("caption_font", "Arial"),
                       size_pct=cfg.get("caption_size_pct", 0.062), margin_v=mv,
                       primary=cfg.get("caption_color", "&H00FFFFFF"),
                       highlight=cfg.get("caption_highlight", "&H0024E8FF"),
                       style=style,
                       box=bool(cfg.get("caption_box", False)),
                       max_cps=float(cfg.get("max_cps", 20.0)))
        tp = vdir / f"{name}_title.png"
        t0 = _t.time()
        try:
            _one({"src": src, "start": hit["start"], "end": hit["end"],
                  "out": str(vdir / f"{name}.mp4"), "profile": cfg,
                  "ass": str(ass), "title_png": str(tp) if tp.is_file() else None,
                  "punches": [], "safe_level": data.get("safe_level", 1),
                  "name": name, "title": hit.get("title", ""),
                  "hook": hit.get("hook", "")})
        except Exception as exc:  # noqa: BLE001
            return {"error": f"{exc.__class__.__name__}: {str(exc)[:160]}"}
        data["caption_style"] = style
        cj.write_text(_j.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "style": style, "secs": round(_t.time() - t0, 1)}
    return {"error": "clip nahi mila"}


# --------------------------------------------------------------------------- page
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>autoclip review</title><style>
*{box-sizing:border-box}
body{margin:0;background:#0f1216;color:#e8eaed;
 font:15px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
header{position:sticky;top:0;z-index:9;background:#151a21;border-bottom:1px solid #263040;
 padding:14px 20px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
h1{font-size:17px;margin:0;font-weight:650;letter-spacing:.2px}
.sp{flex:1}
.pill{background:#1d2530;border:1px solid #2d3848;border-radius:999px;
 padding:4px 12px;font-size:13px;color:#9fb0c6}
.pill b{color:#e8eaed}
button{font:inherit;border:0;border-radius:9px;padding:8px 14px;cursor:pointer;
 background:#232c38;color:#e8eaed;transition:.12s}
button:hover{background:#2c3644}
.ok{background:#15803d}.ok:hover{background:#17914a}
.no{background:#3f1d24}.no:hover{background:#512530}
.on-ok{background:#15803d;box-shadow:0 0 0 2px #22c55e55}
.on-no{background:#b91c1c;box-shadow:0 0 0 2px #ef444455}
.wrap{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));
 gap:18px;padding:20px;max-width:1500px;margin:0 auto}
.card{background:#151a21;border:1px solid #263040;border-radius:14px;overflow:hidden;
 display:flex;flex-direction:column}
.card.approved{border-color:#22c55e66}
.card.rejected{border-color:#ef444455;opacity:.55}
video{width:100%;display:block;background:#000;aspect-ratio:9/16;object-fit:contain}
.body{padding:12px 13px 13px;display:flex;flex-direction:column;gap:9px}
input.title{width:100%;background:#0f1216;border:1px solid #2d3848;border-radius:8px;
 color:#e8eaed;padding:9px 10px;font:inherit;font-weight:600}
input.title:focus{outline:0;border-color:#4b7bec}
.meta{font-size:12px;color:#7d8da3;display:flex;gap:8px;flex-wrap:wrap}
.row{display:flex;gap:8px;margin-top:8px}.row button{flex:1}
.ig{background:#c13584;color:#fff}.ig:hover{background:#d4409a}
.ig.story{background:#2b3444;color:#e8b3d4}
.sugg{display:flex;flex-direction:column;gap:5px}
.sugg button{text-align:left;font-size:13px;padding:7px 10px;
 background:#1b2430;color:#cfe0f5}
.src{font-size:11px;color:#5d6b80;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.saved{color:#22c55e;font-size:12px}
.empty{padding:60px 20px;text-align:center;color:#7d8da3}
.gen{max-width:1500px;margin:18px auto 0;padding:0 20px}
.grid{background:#151a21;border:1px solid #263040;border-radius:14px;padding:16px;
 display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.grid label{display:flex;flex-direction:column;gap:5px;font-size:12px;color:#8fa0b6}
.grid .f2{grid-column:span 2;min-width:260px}
.grid input,.grid select{background:#0f1216;border:1px solid #2d3848;border-radius:8px;
 color:#e8eaed;padding:9px 10px;font:inherit}
.grid input:focus,.grid select:focus{outline:0;border-color:#4b7bec}
.run{background:#2563eb;font-weight:600}.run:hover{background:#2f6ff0}
.run:disabled{background:#2a3340;color:#7d8da3;cursor:default}
.prog{background:#151a21;border:1px solid #263040;border-top:0;
 border-radius:0 0 14px 14px;padding:14px 16px;margin-top:-2px}
.pbar{height:6px;background:#0f1216;border-radius:99px;overflow:hidden}
#pfill{height:100%;width:0;background:linear-gradient(90deg,#2563eb,#22c55e);
 transition:width .4s}
.pmeta{display:flex;justify-content:space-between;font-size:12px;color:#8fa0b6;
 margin:8px 0 6px}
#plog{margin:0;max-height:150px;overflow:auto;font-size:11.5px;line-height:1.45;
 color:#7d8da3;white-space:pre-wrap;font-family:ui-monospace,Menlo,monospace}
.cs{display:flex;gap:6px;align-items:center}
.cs select{flex:1;background:#0f1216;border:1px solid #2d3848;border-radius:8px;
 color:#cfe0f5;padding:7px 9px;font:inherit;font-size:13px}
</style></head><body>
<header>
  <h1>autoclip review</h1>
  <span class="pill">approved <b id="na">0</b></span>
  <span class="pill">pending <b id="np">0</b></span>
  <span class="pill">rejected <b id="nr">0</b></span>
  <span class="sp"></span>
  <button onclick="exportCsv()">Export approved CSV</button>
</header>
<section class="gen">
  <div class="grid">
    <label class="f2">Video / channel / search link
      <input id="url" placeholder="https://youtu.be/...  ya  @channel  ya  ytsearch5:bigg boss fight">
    </label>
    <label>Clips kitni
      <input id="clips" type="number" min="1" max="10" value="3">
    </label>
    <label>Caption style
      <select id="cstyle"></select>
    </label>
    <label>Genre
      <select id="genre">
        <option>vlog</option><option selected>reality</option>
        <option>gaming</option><option>news</option>
      </select>
    </label>
    <label>Profile
      <select id="profile"></select>
    </label>
    <label>Safe filter
      <select id="safe">
        <option value="0">0 - off</option><option value="1" selected>1 - light</option>
        <option value="2">2 - medium</option><option value="3">3 - strong</option>
      </select>
    </label>
    <label>Languages
      <input id="langs" value="hi en">
    </label>
    <label>Source quality
      <select id="sheight">
        <option value="720">720p - fastest</option>
        <option value="1080" selected>1080p - best</option>
        <option value="1440">1440p - slow</option>
      </select>
    </label>
    <label>Caption plate
      <select id="cbox">
        <option value="">off - outline only</option>
        <option value="1">on - solid plate (bright/busy video)</option>
      </select>
    </label>
    <label>&nbsp;
      <button id="go" class="run" onclick="runJob()">Generate</button>
    </label>
  </div>
  <div id="prog" class="prog" style="display:none">
    <div class="pbar"><div id="pfill"></div></div>
    <div class="pmeta"><span id="pstep">starting...</span><span id="ptime">0.0s</span></div>
    <pre id="plog"></pre>
  </div>
</section>
<div class="wrap" id="wrap"></div>
<script>
let CLIPS=[];
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

async function load(){
  CLIPS=await (await fetch('/api/clips')).json();
  render();
}
function counts(){
  const c={approved:0,pending:0,rejected:0};
  CLIPS.forEach(x=>c[x.status]=(c[x.status]||0)+1);
  na.textContent=c.approved;np.textContent=c.pending;nr.textContent=c.rejected;
}
function render(){
  if(!CLIPS.length){wrap.innerHTML='<div class="empty">Koi clip nahi mila.<br>'+
    'Pehle autoclip chalao, phir refresh karo.</div>';counts();return;}
  wrap.innerHTML=CLIPS.map((c,i)=>`
  <div class="card ${c.status}" id="c${i}">
    <video src="/video?p=${encodeURIComponent(c.id)}" controls preload="metadata"></video>
    <div class="body">
      <input class="title" value="${esc(c.title)}" placeholder="title likho..."
             onchange="setTitle(${i},this.value)">
      <div class="meta"><span>${c.duration}s</span><span>${c.size_mb||'?'} MB</span>
        <span>@${Math.round(c.start||0)}s</span><span class="saved" id="s${i}"></span></div>
      <div class="row">
        <button class="ok ${c.status==='approved'?'on-ok':''}"
                onclick="setStatus(${i},'approved')">Approve</button>
        <button class="no ${c.status==='rejected'?'on-no':''}"
                onclick="setStatus(${i},'rejected')">Reject</button>
      </div>
      <div class="row">
        <button class="ig" onclick="toInsta(${i},false)">Instagram Reel</button>
        <button class="ig story" onclick="toInsta(${i},true)">Reel + Story</button>
      </div>
      <div class="cs">
        <select id="cs${i}sel" onchange="setStyle(${i},this.value)">
          ${STYLES.map(s=>`<option ${s===c.caption_style?'selected':''}>${s}</option>`).join('')}
        </select>
      </div>
      <div id="cs${i}"></div>
      <button onclick="suggest(${i})">Naye title suggest karo</button>
      <div class="sugg" id="g${i}"></div>
      <div class="src">${esc(c.source_title)}</div>
    </div>
  </div>`).join('');
  counts();
}
async function post(url,body){
  return (await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)})).json();
}
function flash(i){const e=document.getElementById('s'+i);if(!e)return;
  e.textContent='saved';setTimeout(()=>e.textContent='',1200);}
async function setTitle(i,v){CLIPS[i].title=v;
  await post('/api/save',{dir:CLIPS[i].dir,name:CLIPS[i].name,title:v});flash(i);}
async async function toInsta(i, story){
  const c = CLIPS[i];
  const label = story ? 'Reel + Story' : 'Reel';
  if(!confirm('Post "'+(c.title||c.name)+'" to Instagram as '+label+'?')) return;
  const r = await fetch('/api/instagram', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({id:c.id, story:story})});
  const d = await r.json();
  if(d.error){ alert('Instagram: '+d.error); return; }
  alert('Posted. reel='+(d.reel||'-')+' story='+(d.story||'-')+' quota='+(d.quota||'-'));
}

function setStatus(i,s){
  CLIPS[i].status=CLIPS[i].status===s?'pending':s;
  await post('/api/save',{dir:CLIPS[i].dir,name:CLIPS[i].name,status:CLIPS[i].status});
  render();
}
async function suggest(i){
  const box=document.getElementById('g'+i);
  box.innerHTML='<button disabled>soch raha hoon...</button>';
  const r=await post('/api/suggest',{id:CLIPS[i].id});
  if(!r.titles||!r.titles.length){
    box.innerHTML='<button disabled>koi LLM key set nahi hai</button>';return;}
  box.innerHTML=r.titles.map(t=>
    `<button onclick="pick(${i},this.textContent)">${esc(t)}</button>`).join('');
}
function pick(i,t){
  CLIPS[i].title=t;
  document.querySelector('#c'+i+' input.title').value=t;
  setTitle(i,t);
}
async function exportCsv(){
  const r=await post('/api/export',{});
  alert('Likh diya:\\n'+r.path);
}

const STEPS=[['[1/5]',12,'queued'],['[2/5]',30,'downloading'],
             ['[3/5]',52,'transcript'],['[4/5]',66,'picking clips'],
             ['[5/5]',80,'rendering'],['done in',100,'done']];
let POLL=null, STYLES=[];

async function initOpts(){
  const r=await (await fetch('/api/styles')).json();
  STYLES=r.styles;
  cstyle.innerHTML=r.styles.map(s=>
    `<option ${s==='hormozi'?'selected':''}>${s}</option>`).join('');
  profile.innerHTML='<option value="">default</option>'+
    r.profiles.map(p=>`<option value="profiles/${p}">${p.replace('.json','')}</option>`).join('');
}
async function runJob(){
  const body={url:url.value.trim(),clips:clips.value,genre:genre.value,
    caption_style:cstyle.value,profile:profile.value,safe:safe.value,langs:langs.value,sheight:sheight.value,cbox:cbox.value};
  if(!body.url){alert('Link daalo');return;}
  const r=await post('/api/run',body);
  if(r.error){alert(r.error);return;}
  go.disabled=true;go.textContent='Chal raha hai...';
  prog.style.display='block';plog.textContent='';pfill.style.width='4%';
  POLL=setInterval(poll,700);
}
async function poll(){
  const j=await (await fetch('/api/job')).json();
  ptime.textContent=j.elapsed+'s';
  plog.textContent=j.log.join('\n');plog.scrollTop=plog.scrollHeight;
  const txt=j.log.join('\n');
  let pc=8,st='working';
  STEPS.forEach(([k,v,label])=>{if(txt.includes(k)){pc=v;st=label;}});
  pfill.style.width=pc+'%';pstep.textContent=st;
  if(j.done){
    clearInterval(POLL);go.disabled=false;go.textContent='Generate';
    pfill.style.width='100%';
    pstep.textContent=j.error?('FAILED - '+j.error)
      :`${j.made} clip(s) in ${j.elapsed}s  (${(j.elapsed/Math.max(j.made,1)).toFixed(1)}s per clip)`;
    load();
  }
}
async function setStyle(i,st){
  const box=document.getElementById('cs'+i);
  const old=box.innerHTML;
  box.innerHTML='<span style="font-size:12px;color:#8fa0b6">re-rendering...</span>';
  const r=await post('/api/restyle',{id:CLIPS[i].id,style:st});
  if(r.error){alert(r.error);box.innerHTML=old;return;}
  box.innerHTML=old;
  const v=document.querySelector('#c'+i+' video');
  v.src='/video?p='+encodeURIComponent(CLIPS[i].id)+'&t='+Date.now();
  const e=document.getElementById('s'+i);
  e.textContent=st+' '+r.secs+'s';setTimeout(()=>e.textContent='',2500);
}
initOpts();load();
</script></body></html>"""


# --------------------------------------------------------------------------- server
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode(),
                   "application/json; charset=utf-8")

    # ---- GET
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        if u.path == "/api/clips":
            return self._json(load_clips())
        if u.path == "/api/job":
            j = dict(JOB)
            if j["running"]:
                j["elapsed"] = round(time.time() - j["t0"], 1)
            j["log"] = j["log"][-14:]
            return self._json(j)
        if u.path == "/api/styles":
            from . import captions as _c
            profs = sorted(x.name for x in Path("profiles").glob("*.json")) \
                if Path("profiles").is_dir() else []
            return self._json({"styles": list(_c.STYLES), "profiles": profs})
        if u.path == "/video":
            q = urllib.parse.parse_qs(u.query)
            return self._video(q.get("p", [""])[0])
        self._send(404, b"not found", "text/plain")

    def _video(self, path: str):
        p = Path(path)
        allowed = ROOT.resolve()
        try:
            if not p.is_file() or allowed not in p.resolve().parents:
                return self._send(403, b"forbidden", "text/plain")
        except Exception:
            return self._send(403, b"forbidden", "text/plain")

        size = p.stat().st_size
        ctype = mimetypes.guess_type(str(p))[0] or "video/mp4"
        rng = self.headers.get("Range")
        if not rng:
            return self._send(200, p.read_bytes(), ctype,
                              {"Accept-Ranges": "bytes"})
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        a = int(m.group(1)) if m and m.group(1) else 0
        b = int(m.group(2)) if m and m.group(2) else size - 1
        b = min(b, size - 1)
        with p.open("rb") as f:
            f.seek(a)
            chunk = f.read(b - a + 1)
        self._send(206, chunk, ctype, {
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {a}-{b}/{size}"})

    # ---- POST
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            body = {}
        u = urllib.parse.urlparse(self.path)

        if u.path == "/api/save":
            patch = {k: body[k] for k in ("title", "status", "note") if k in body}
            save_review(body["dir"], body["name"], patch)
            return self._json({"ok": True})

        if u.path == "/api/suggest":
            clip = next((c for c in load_clips() if c["id"] == body.get("id")), None)
            return self._json({"titles": suggest_titles(clip) if clip else []})

        if u.path == "/api/export":
            return self._json({"path": export_approved()})

        if u.path == "/api/run":
            if JOB["running"]:
                return self._json({"error": "ek job pehle se chal rahi hai"}, 409)
            if not (body.get("url") or "").strip():
                return self._json({"error": "link daalo"}, 400)
            threading.Thread(target=run_job, args=(body,), daemon=True).start()
            return self._json({"ok": True})

        if u.path == "/api/instagram":
            # Meta FETCHES the file, so it needs a public URL, not a local
            # path. The browser reached this dashboard somehow -- that same
            # host is what Meta has to use, so reuse the Host header.
            host = self.headers.get("Host", "")
            proto = "https" if not host.startswith(("localhost", "127.")) else "http"
            return self._json(post_to_instagram(
                body.get("id", ""), f"{proto}://{host}",
                story=bool(body.get("story"))))

        if u.path == "/api/restyle":
            return self._json(restyle(body.get("id", ""), body.get("style", "karaoke")))

        self._json({"error": "unknown"}, 404)


def _instapost_dir() -> Path:
    """Find the instapost package.

    Checked in order so both layouts work: bundled inside this repo (what you
    get from `git clone`), then a standalone ~/instapost checkout.
    """
    here = Path(__file__).resolve().parent.parent / "instapost"
    return here if (here / "instapost").is_dir() else Path.home() / "instapost"


INSTAPOST = _instapost_dir()


def post_to_instagram(clip_id: str, public_base: str, story: bool = False) -> dict:
    """Publish one rendered clip as a Reel, optionally to Stories too."""
    import sys as _sys
    if str(INSTAPOST) not in _sys.path:
        _sys.path.insert(0, str(INSTAPOST))
    try:
        from instapost.ig import IGError, check_clip, verify_public
        from instapost.private import PrivateInstagram, get_driver
        from instapost import store
    except ImportError as e:
        return {"error": f"instapost not importable: {e}"}

    clip = next((c for c in load_clips() if c["id"] == clip_id), None)
    if not clip:
        return {"error": "clip not found"}

    ig = get_driver()
    private = isinstance(ig, PrivateInstagram)
    if not ig.configured():
        return {"error": "Instagram not set up yet - see instapost/README.md"}

    mp4 = Path(clip["mp4"])
    bad = check_clip(mp4, float(clip.get("duration") or 0), 1080, 1920)
    if bad:
        return {"error": "; ".join(bad)}

    # The two drivers want different things: instagrapi uploads the local
    # file, the Graph API makes Meta fetch a public URL.
    #
    # The Host header is only right when the browser reached us over a
    # publicly resolvable address. The e2b preview host, for instance, needs
    # an auth header that Meta will never send. INSTAPOST_PUBLIC_BASE lets a
    # tunnel override it.
    base = os.environ.get("INSTAPOST_PUBLIC_BASE", "").strip().rstrip("/")
    target = (str(mp4) if private
              else f"{base or public_base}/video?p={urllib.parse.quote(clip_id)}")
    caption = (clip.get("title") or "").strip()
    out = {"driver": "instagrapi" if private else "graph",
           "source": target if private else target}
    if not private:
        why = verify_public(target)
        if why:
            return {"error": f"{why}. Meta fetches the file itself, so the "
                             f"dashboard must be on a public https address "
                             f"(cloudflared tunnel), and INSTAPOST_PUBLIC_BASE "
                             f"must point at it.", "url_tried": target}
    try:
        used, total = ig.quota()
        out["quota"] = f"{used}/{total}"
        if used >= total:
            return {"error": f"daily limit reached ({used}/{total})"}
        if store.already_posted(clip_id, "reel"):
            out["reel"] = "already posted"
        else:
            mid = ig.post_reel(target, caption)
            store.record(clip_id, "reel", mid, caption)
            out["reel"] = mid
        if story:
            if store.already_posted(clip_id, "story"):
                out["story"] = "already posted"
            else:
                sid = ig.post_story(target)
                store.record(clip_id, "story", sid)
                out["story"] = sid
    except IGError as e:
        out["error"] = str(e)
    return out


def main() -> None:
    global ROOT
    ap = argparse.ArgumentParser(prog="autoclip-dashboard")
    ap.add_argument("--outdir", default="Shorts", help="folder holding rendered clips")
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--host", default="0.0.0.0")
    a = ap.parse_args()

    try:
        from .cli import _load_env
        _load_env()
    except Exception:
        pass

    ROOT = Path(a.outdir)
    ROOT.mkdir(parents=True, exist_ok=True)
    n = len(load_clips())
    print(f"autoclip review  ->  http://{a.host}:{a.port}   ({n} clip(s) in {ROOT})")
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
