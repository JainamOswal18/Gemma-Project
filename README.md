<div align="center">

# 🔮 Mind Reader

### *I'll read your mind in 20 questions — and I run entirely on your machine.*

A local **Akinator-style** guessing game powered by **Gemma 4** running on **Ollama**.
Think of anything — a person, character, animal, or object — and watch a local LLM
deduce it through smart, graded questions. No cloud. No API keys. No data leaves your box.

<br>

![Gemma 4](https://img.shields.io/badge/Gemma_4-Ollama-a855f7?style=for-the-badge&logo=google&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-GUI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![100% Local](https://img.shields.io/badge/100%25-Local_&_Private-34d399?style=for-the-badge)

</div>

---

## ✨ What makes it cool

- 🧠 **Real deductive reasoning** — Gemma asks the *single most informative* question each turn, binary-searching through concept-space. 20 yes/no questions can pin down ~1,000,000 things.
- 🎚️ **Graded answers, not just yes/no** — reply with **Yes · Probably · Somewhat · Probably not · No · Don't know**, and the model weighs partial evidence accordingly.
- 🔒 **Fully offline & private** — the LLM, the game logic, and the UI all run locally via Ollama.
- 🎨 **Three ways to play** — a polished Streamlit GUI, a slick terminal version, and a zero-dependency web app.
- 🪶 **Featherweight** — the terminal and web versions use *only* the Python standard library.

---

## 🚀 Quick start

> **Prereq:** [Ollama](https://ollama.com) running with a `gemma4` model pulled (`ollama pull gemma4:e4b`).

### 1 · Streamlit GUI *(recommended)*
```bash
python3 -m venv .venv
.venv/bin/python -m pip install streamlit
.venv/bin/streamlit run app.py
# → open http://localhost:8501
```

### 2 · Terminal
```bash
python3 mindreader.py
python3 mindreader.py --model gemma4:26b   # smarter, slower
```

### 3 · Zero-dependency web app
```bash
python3 webapp.py        # → open http://localhost:8000
```

---

## 🤖 Why Gemma 4? (the use case)

**Gemma 4** is Google's open-weight large language model — small enough to run on
your own machine through Ollama, yet capable enough to *reason*. This game is built
specifically to show off the part of an LLM that's hard to fake:

| What the game needs | What Gemma provides |
|---------------------|---------------------|
| Ask a smart, *new* question every turn | Open-ended **generation** grounded in the conversation so far |
| Get closer with each answer | **Multi-step deductive reasoning** under uncertainty |
| Handle "probably / somewhat / don't know" | **Nuanced interpretation** of fuzzy, graded input |
| Decide *when* to stop and guess | **Judgment** — weighing confidence vs. questions remaining |
| Never break the program | **Structured JSON output** (`format: json`) the code can trust |

Because Gemma runs **locally via Ollama**, this use case is:

- 🔒 **Private** — your guesses never touch a third-party server
- 💸 **Free** — no per-token API billing
- ✈️ **Offline-capable** — works with no internet once the model is pulled
- 🔁 **Swappable** — `gemma4:e4b` for speed, `gemma4:26b` for sharper reasoning

In short: it's a tiny, fun demonstration that a **local open model can carry a real
reasoning task end-to-end** — no cloud LLM required.

---

## 🧩 How it works

```
You think of something  ──►  Gemma asks the best next question  ──►  you answer (graded)
        ▲                                                                      │
        └──────────────  full Q&A history re-fed each turn  ◄─────────────────┘
                          narrowing the space, until ──►  🎯 it GUESSES
```

1. **State across turns** — the entire transcript is sent back each round, so Gemma reasons over everything known so far.
2. **Binary search over ideas** — it's prompted to split the remaining possibilities roughly in half every question.
3. **Structured output** — Ollama's `format: json` forces a clean `{"action": "question" | "guess", "text": "…"}`, so the game logic never has to parse fuzzy text.

---

## 🗂️ Project layout

| File | What it is |
|------|------------|
| `app.py` | Streamlit GUI with graded answers, model picker, live transcript |
| `mindreader.py` | Colorful terminal version |
| `webapp.py` | Pure-stdlib browser version (no Streamlit needed) |

---

## 🛠️ Ideas to extend

- 🏆 Local scoreboard (questions-to-guess across games)
- 📚 "Learn from wrong guesses" memory file
- 🔁 Reverse mode — *you* guess what *Gemma* is thinking
- 🔐 Password gate before sharing publicly

---

<div align="center">

### Developed by **Jainam Oswal**

*Powered by Gemma 4 · Built to run anywhere, owned by no one but you.*

⭐ If this made you smile, give it a star!

</div>
