#!/usr/bin/env python3
"""
🔮 Mind Reader — Web GUI (local) powered by Gemma 4 on Ollama.

A zero-dependency web app: Python's stdlib http.server serves a single-page
browser UI and proxies each turn to the local Ollama model. The game state
(the Q&A history) lives in the browser; the server is a thin, stateless brain
that just decides the next move.

Run:
  python3 webapp.py                 # then open http://localhost:8000
  python3 webapp.py --port 8080 --model gemma4:26b
"""

import argparse
import json
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma4:e4b"
MAX_QUESTIONS = 20

SYSTEM = (
    "You are the AI in a 20-questions guessing game. The human is thinking of a "
    "specific famous person, fictional character, animal, or object. Your job is to "
    "identify it by asking the single most informative yes/no question each turn, "
    "using all previous answers to narrow the space. Reason like an expert: split the "
    "remaining possibilities roughly in half. Only make a final guess when you are "
    "genuinely confident or running low on questions. Never repeat a question."
)

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🔮 Mind Reader — Gemma 4</title>
<style>
  :root { --bg:#0f1020; --card:#1b1d3a; --accent:#a855f7; --accent2:#22d3ee;
          --text:#e8e8ff; --dim:#9aa0c0; --good:#34d399; --bad:#fb7185; }
  * { box-sizing:border-box; }
  body { margin:0; min-height:100vh; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
         background:radial-gradient(1200px 800px at 50% -10%, #2a1d52 0%, var(--bg) 60%);
         color:var(--text); display:flex; align-items:center; justify-content:center; padding:24px; }
  .card { width:100%; max-width:560px; background:linear-gradient(180deg,#20224a,#16182f);
          border:1px solid #34376b; border-radius:20px; padding:28px;
          box-shadow:0 20px 60px rgba(0,0,0,.45); }
  h1 { margin:0 0 4px; font-size:26px; letter-spacing:.5px; }
  .sub { color:var(--dim); font-size:14px; margin-bottom:20px; }
  .counter { float:right; font-size:13px; color:var(--accent2); border:1px solid #2c4a55;
             padding:3px 10px; border-radius:999px; }
  .q { font-size:21px; line-height:1.4; min-height:64px; margin:10px 0 22px;
       padding:18px; background:#11132a; border-radius:14px; border:1px solid #2b2e5c; }
  .q.guess { border-color:var(--accent); box-shadow:0 0 0 2px rgba(168,85,247,.25) inset; }
  .row { display:flex; gap:10px; flex-wrap:wrap; }
  button { flex:1 1 auto; min-width:84px; cursor:pointer; font-size:15px; font-weight:600;
           padding:13px 14px; border-radius:12px; border:1px solid #3a3d72; color:var(--text);
           background:#23264f; transition:transform .05s, background .15s; }
  button:hover { background:#2c2f63; } button:active { transform:translateY(1px); }
  .yes { background:#14532d; border-color:#1f7a43; } .yes:hover{background:#1a6638;}
  .no  { background:#5b1f2c; border-color:#8a3146; } .no:hover{background:#732838;}
  .ghost { background:transparent; }
  .big { width:100%; margin-top:14px; background:linear-gradient(90deg,var(--accent),#6d28d9);
         border:none; font-size:16px; padding:15px; }
  .hint { color:var(--dim); font-size:13px; text-align:center; margin-top:14px; }
  .spin { display:inline-block; width:16px; height:16px; border:2px solid #555;
          border-top-color:var(--accent2); border-radius:50%; animation:s .7s linear infinite;
          vertical-align:-3px; margin-right:8px; }
  @keyframes s { to { transform:rotate(360deg); } }
  .hidden { display:none; }
  .result { text-align:center; font-size:20px; padding:10px 0; }
  .good { color:var(--good); } .bad { color:var(--bad); }
</style>
</head>
<body>
  <div class="card">
    <span class="counter" id="counter">0 / 20</span>
    <h1>🔮 Mind Reader</h1>
    <div class="sub">Powered by Gemma 4 · running locally on Ollama</div>

    <!-- Start screen -->
    <div id="start">
      <div class="q">Think of a <b>famous person, character, animal, or object</b>.
        I'll ask yes/no questions and try to read your mind.</div>
      <button class="big" onclick="startGame()">Start reading your mind →</button>
    </div>

    <!-- Game screen -->
    <div id="game" class="hidden">
      <div class="q" id="question">…</div>
      <div class="row" id="answers">
        <button class="yes" onclick="answer('yes')">Yes</button>
        <button class="no"  onclick="answer('no')">No</button>
        <button class="ghost" onclick="answer('maybe')">Maybe</button>
        <button class="ghost" onclick="answer('unknown')">Don't know</button>
      </div>
      <div class="row hidden" id="guessRow">
        <button class="yes" onclick="guessResult(true)">🎉 Yes, that's it!</button>
        <button class="no"  onclick="guessResult(false)">Nope, keep going</button>
      </div>
      <div class="hint" id="hint"></div>
    </div>

    <!-- End screen -->
    <div id="end" class="hidden">
      <div class="result" id="resultText"></div>
      <button class="big" onclick="location.reload()">Play again ↺</button>
    </div>
  </div>

<script>
const MAX = 20;
let history = [];      // [{q, a}]
let turn = 0;
let pending = null;    // {action, text}

const $ = id => document.getElementById(id);

function setCounter(){ $('counter').textContent = turn + " / " + MAX; }

async function move(){
  $('question').innerHTML = '<span class="spin"></span> thinking…';
  $('answers').classList.add('hidden');
  $('guessRow').classList.add('hidden');
  try {
    const res = await fetch('/api/move', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({history, questions_left: MAX - turn})
    });
    const data = await res.json();
    pending = data;
    const qEl = $('question');
    if (data.action === 'guess'){
      qEl.classList.add('guess');
      qEl.innerHTML = "🤔 Is it… <b>" + escapeHtml(data.text) + "</b>?";
      $('guessRow').classList.remove('hidden');
      $('hint').textContent = "My best guess so far.";
    } else {
      qEl.classList.remove('guess');
      qEl.textContent = data.text;
      $('answers').classList.remove('hidden');
      $('hint').textContent = "Answer honestly — it makes me smarter.";
    }
  } catch(e){
    $('question').textContent = "⚠️ Couldn't reach the model. Is Ollama running?";
  }
}

function startGame(){
  $('start').classList.add('hidden');
  $('game').classList.remove('hidden');
  turn = 0; history = []; setCounter();
  move();
}

function answer(a){
  history.push({q: pending.text, a});
  turn++; setCounter();
  if (turn >= MAX){ finalGuess(); return; }
  move();
}

function guessResult(correct){
  if (correct){
    endGame(true, "🎉 Read your mind in " + turn + " questions! GG.");
  } else {
    history.push({q: "Is it " + pending.text + "?", a: "no"});
    turn++; setCounter();
    if (turn >= MAX){ finalGuess(); return; }
    move();
  }
}

async function finalGuess(){
  $('question').innerHTML = '<span class="spin"></span> final guess…';
  $('answers').classList.add('hidden'); $('guessRow').classList.add('hidden');
  const res = await fetch('/api/move', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({history, questions_left: 0})
  });
  const data = await res.json();
  $('question').classList.add('guess');
  $('question').innerHTML = "🎯 Final answer: <b>" + escapeHtml(data.text) + "</b>?";
  pending = data;
  $('guessRow').classList.remove('hidden');
  // override buttons for final
  $('guessRow').innerHTML =
    '<button class="yes" onclick="endGame(true, \'😎 Buzzer-beater — got it!\')">Yes!</button>' +
    '<button class="no" onclick="endGame(false, \'🏳️ You win — you stumped me!\')">No, you lose</button>';
}

function endGame(win, msg){
  $('game').classList.add('hidden');
  $('end').classList.remove('hidden');
  const el = $('resultText');
  el.textContent = msg;
  el.className = "result " + (win ? "good" : "bad");
}

function escapeHtml(s){ const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
</script>
</body>
</html>"""


def gemma_move(history, questions_left, model):
    """Ask Gemma for the next move (question or guess) as JSON."""
    transcript = "\n".join(f"Q: {h['q']}\nA: {h['a']}" for h in history) or "(no questions yet)"
    prompt = (
        f"Questions asked so far:\n{transcript}\n\n"
        f"You have {questions_left} questions left.\n\n"
        "Respond with ONLY a JSON object:\n"
        '  {"action":"question","text":"<a single yes/no question>"}\n'
        "or, if confident or low on questions:\n"
        '  {"action":"guess","text":"<the specific thing you think it is>"}'
    )
    payload = {
        "model": model, "system": SYSTEM, "prompt": prompt,
        "stream": False, "format": "json", "options": {"temperature": 0.7},
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = json.loads(resp.read()).get("response", "").strip()
    try:
        obj = json.loads(raw)
        if obj.get("action") in ("question", "guess") and obj.get("text", "").strip():
            return {"action": obj["action"], "text": obj["text"].strip()}
    except json.JSONDecodeError:
        pass
    return {"action": "question", "text": raw or "Is it a living thing?"}


def make_handler(model):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet console
            pass

        def _send(self, code, body, ctype="text/html; charset=utf-8"):
            data = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, PAGE)
            else:
                self._send(404, "not found", "text/plain")

        def do_POST(self):
            if self.path != "/api/move":
                self._send(404, "not found", "text/plain")
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                req = json.loads(self.rfile.read(length) or "{}")
                move = gemma_move(req.get("history", []), req.get("questions_left", MAX), model)
                self._send(200, json.dumps(move), "application/json")
            except Exception as e:
                self._send(500, json.dumps({"action": "question", "text": f"(error: {e})"}),
                           "application/json")
    return Handler


def main():
    p = argparse.ArgumentParser(description="Mind Reader web GUI (Gemma 4 via Ollama)")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--host", default="127.0.0.1")
    args = p.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), make_handler(args.model))
    print(f"🔮 Mind Reader running at http://localhost:{args.port}  (model: {args.model})")
    print("   Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye 👋")
        server.shutdown()


if __name__ == "__main__":
    main()
