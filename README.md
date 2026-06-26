# 🔮 Mind Reader — local Akinator powered by Gemma 4

Think of a **famous person, fictional character, animal, or object**. Gemma asks
smart yes/no questions, narrows the possibilities each turn, and tries to guess
what's in your head — all running **100% offline** on your machine via Ollama.

No API keys. No cloud. No dependencies beyond Python's standard library.

## Three ways to play

**1. Streamlit GUI (recommended)** — polished browser UI with graded answers:
```bash
./.venv/bin/streamlit run app.py
# then open http://localhost:8501
```
Instead of plain yes/no, you answer on a scale — **Yes · Probably · Somewhat ·
Probably not · No · Don't know** — and Gemma weighs partial answers as partial
evidence. Pick the model (e4b/26b) and watch the live transcript in the sidebar.

**2. Terminal version:**
```bash
python3 mindreader.py
python3 mindreader.py --model gemma4:26b   # smarter, slower
```
Answer with `y` / `n` / `maybe` / `unknown` (or `quit`).

**3. Zero-dependency web app** (no Streamlit needed, pure stdlib):
```bash
python3 webapp.py            # open http://localhost:8000
```

> Setup note: Streamlit lives in a local virtualenv at `.venv/` (the system Python
> had no pip). Recreate with: `python3 -m venv .venv && .venv/bin/python -m pip install streamlit`.

## How it works
- Each turn the full Q&A history is sent to Gemma, which is prompted to ask the
  **single most informative** yes/no question — splitting the remaining
  possibility space roughly in half (classic 20-questions strategy).
- Ollama's `"format": "json"` mode forces Gemma to reply as structured JSON
  (`{"action": "question"|"guess", "text": "..."}`), so parsing is reliable.
- When confident — or running low on questions — it switches to a guess. A wrong
  guess is recorded as new evidence and the hunt continues.

## Why it's a fun showcase
It exercises the part of an LLM that's hard to fake: **multi-step deductive
reasoning under uncertainty**, with state carried across turns. Easy to demo,
endlessly replayable, and it really does feel like it's reading your mind.

## Ideas to extend
- Reverse it: *you* guess what *Gemma* is thinking.
- Keep a local scoreboard (questions-to-guess) across games.
- Add a "learn" file so wrong guesses improve future games.
