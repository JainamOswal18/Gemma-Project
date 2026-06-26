#!/usr/bin/env python3
"""
🔮 Mind Reader — Streamlit GUI, powered by Gemma 4 on Ollama (fully local).

Think of a famous person, character, animal, or object. Gemma asks questions and
narrows it down using your graded answers (not just yes/no), then guesses.

Run:
  ./.venv/bin/streamlit run app.py
"""

import json
import urllib.request

import streamlit as st

OLLAMA_URL = "http://localhost:11434/api/generate"
MAX_QUESTIONS = 20

SYSTEM = (
    "You are the AI in a 20-questions guessing game. The human is thinking of a "
    "specific famous person, fictional character, animal, or object. Ask the single "
    "most informative question each turn and use ALL previous answers to narrow the "
    "space. Answers are graded, not just yes/no — weigh 'probably', 'somewhat', and "
    "'probably not' as partial evidence, and treat \"don't know\" as no information. "
    "Reason like an expert: split the remaining possibilities roughly in half. Only "
    "guess when genuinely confident or low on questions. Never repeat a question."
)

# Graded answer scale: label -> (text sent to model, button styling tier)
ANSWERS = [
    ("✅ Yes", "yes", "yes"),
    ("🟢 Probably", "probably yes", "soft"),
    ("🤷 Somewhat / partly", "somewhat — partially true", "soft"),
    ("🟠 Probably not", "probably no", "soft"),
    ("❌ No", "no", "no"),
    ("❔ Don't know", "unknown / no information", "ghost"),
]


# ----------------------------- model call ----------------------------- #

def gemma_move(history, questions_left, model):
    transcript = "\n".join(f"Q: {h['q']}\nA: {h['a']}" for h in history) or "(no questions yet)"
    prompt = (
        f"Questions asked so far:\n{transcript}\n\n"
        f"You have {questions_left} questions left.\n\n"
        "Respond with ONLY a JSON object:\n"
        '  {"action":"question","text":"<a single yes/no-style question>"}\n'
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


# ------------------------------- state -------------------------------- #

def init():
    ss = st.session_state
    ss.setdefault("stage", "start")     # start | playing | end
    ss.setdefault("history", [])
    ss.setdefault("turn", 0)
    ss.setdefault("pending", None)       # current {action, text}
    ss.setdefault("result", None)        # (won, message)
    ss.setdefault("model", "gemma4:e4b")


def reset():
    st.session_state.update(stage="start", history=[], turn=0, pending=None, result=None)


def record(answer_text):
    """Store the answer to the current question and advance."""
    ss = st.session_state
    ss.history.append({"q": ss.pending["text"], "a": answer_text})
    ss.turn += 1
    ss.pending = None
    if ss.turn >= MAX_QUESTIONS:
        _final_guess()


def confirm_guess(correct):
    ss = st.session_state
    if correct:
        ss.result = (True, f"🎉 Read your mind in {ss.turn} questions! GG.")
        ss.stage = "end"
        return

    # Wrong guess. Record it as evidence.
    ss.history.append({"q": f"Is it {ss.pending['text']}?", "a": "no"})

    # If that was the last-resort final guess (or we're out of questions),
    # the human wins — end the game instead of asking more.
    if ss.pending.get("final") or ss.turn >= MAX_QUESTIONS:
        ss.result = (False, "🏳️ You win — you stumped me! What were you thinking of?")
        ss.stage = "end"
        return

    # Otherwise keep hunting.
    ss.turn += 1
    ss.pending = None
    if ss.turn >= MAX_QUESTIONS:
        _final_guess()


def _final_guess():
    ss = st.session_state
    move = gemma_move(ss.history, 0, ss.model)
    move["action"] = "guess"
    move["final"] = True
    ss.pending = move


# -------------------------------- UI ---------------------------------- #

CSS = """
<style>
  .stApp { background: radial-gradient(1100px 700px at 50% -10%, #2a1d52 0%, #0f1020 60%); }
  .block-container { max-width: 760px; }
  .title { font-size: 34px; font-weight: 800; letter-spacing:.5px; margin-bottom:0; }
  .sub { color:#9aa0c0; margin-top:2px; margin-bottom:18px; }
  .qcard { background:#11132a; border:1px solid #2b2e5c; border-radius:16px;
           padding:26px; font-size:23px; line-height:1.4; color:#e8e8ff; }
  .qcard.guess { border-color:#a855f7; box-shadow:0 0 0 2px rgba(168,85,247,.25) inset; }
  .pill { display:inline-block; background:#1b1d3a; border:1px solid #34376b; color:#22d3ee;
          padding:3px 12px; border-radius:999px; font-size:13px; }
  div[data-testid="stHorizontalBlock"] button { font-weight:600; border-radius:12px; }
</style>
"""


def main():
    st.set_page_config(page_title="🔮 Mind Reader", page_icon="🔮", layout="centered")
    st.markdown(CSS, unsafe_allow_html=True)
    init()
    ss = st.session_state

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        ss.model = st.selectbox(
            "Model", ["gemma4:e4b", "gemma4:26b"],
            index=0 if ss.model == "gemma4:e4b" else 1,
            help="e4b = fast · 26b = smarter, slower",
        )
        st.caption("Running locally via Ollama. Nothing leaves your machine.")
        if ss.history:
            st.markdown("### 🧾 Transcript")
            for i, h in enumerate(ss.history, 1):
                st.markdown(f"**{i}.** {h['q']}  \n→ *{h['a']}*")
        if st.button("↺ Restart game", use_container_width=True):
            reset(); st.rerun()

    # Header
    st.markdown('<div class="title">🔮 Mind Reader</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">A local Akinator powered by Gemma 4 · graded answers, not just yes/no</div>',
                unsafe_allow_html=True)

    # ---- START ----
    if ss.stage == "start":
        st.markdown(
            '<div class="qcard">Think of a <b>famous person, character, animal, or '
            'object</b>. I\'ll ask questions and read your mind. 🧠</div>',
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Start reading your mind →", type="primary", use_container_width=True):
            reset()
            ss.stage = "playing"
            st.rerun()
        return

    # ---- END ----
    if ss.stage == "end":
        won, msg = ss.result
        (st.success if won else st.error)(msg)
        st.balloons() if won else None
        if st.button("Play again ↺", type="primary", use_container_width=True):
            reset(); st.rerun()
        return

    # ---- PLAYING ----
    st.markdown(f'<span class="pill">Question {min(ss.turn + 1, MAX_QUESTIONS)} / {MAX_QUESTIONS}</span>',
                unsafe_allow_html=True)
    st.progress(min(ss.turn, MAX_QUESTIONS) / MAX_QUESTIONS)

    # Fetch next move if needed
    if ss.pending is None:
        with st.spinner("🔮 Gemma is thinking…"):
            ss.pending = gemma_move(ss.history, MAX_QUESTIONS - ss.turn, ss.model)

    move = ss.pending
    is_guess = move["action"] == "guess"
    is_final = move.get("final", False)

    if is_guess:
        label = "🎯 Final answer" if is_final else "🤔 My guess"
        st.markdown(f'<div class="qcard guess">{label}: <b>{move["text"]}</b>?</div>',
                    unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns(2)
        if c1.button("🎉 Yes, that's it!", type="primary", use_container_width=True):
            confirm_guess(True); st.rerun()
        no_label = "No — you lose 😎" if is_final else "Nope, keep going"
        if c2.button(no_label, use_container_width=True):
            confirm_guess(False); st.rerun()
    else:
        st.markdown(f'<div class="qcard">{move["text"]}</div>', unsafe_allow_html=True)
        st.write("")
        st.caption("Answer on the scale — partial answers help me too:")
        # Two rows of graded answers
        row1 = st.columns(3)
        row2 = st.columns(3)
        cols = list(row1) + list(row2)
        for col, (label, sent, _tier) in zip(cols, ANSWERS):
            if col.button(label, use_container_width=True, key=f"ans_{label}"):
                record(sent); st.rerun()


if __name__ == "__main__":
    main()
