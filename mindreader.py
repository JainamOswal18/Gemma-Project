#!/usr/bin/env python3
"""
🔮 Mind Reader — a local Akinator-style guessing game powered by Gemma 4 (Ollama).

You think of a famous person, character, animal, or object.
Gemma asks smart yes/no questions and tries to guess what you're thinking.
Runs 100% offline. No dependencies beyond Python stdlib + a running Ollama.

Run:
  python3 mindreader.py
  python3 mindreader.py --model gemma4:26b   # smarter (slower) guesser
"""

import argparse
import json
import sys
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma4:e4b"
MAX_QUESTIONS = 20

# ANSI colors for a nicer terminal feel
C = {
    "cyan": "\033[96m", "yellow": "\033[93m", "green": "\033[92m",
    "magenta": "\033[95m", "red": "\033[91m", "dim": "\033[2m",
    "bold": "\033[1m", "reset": "\033[0m",
}


def color(s, c):
    return f"{C[c]}{s}{C['reset']}"


SYSTEM = (
    "You are the AI in a 20-questions guessing game. The human is thinking of a "
    "specific famous person, fictional character, animal, or object. Your job is to "
    "identify it by asking the single most informative yes/no question each turn, "
    "using all previous answers to narrow the space. Reason like an expert: split the "
    "remaining possibilities roughly in half. Only make a final guess when you are "
    "genuinely confident or running low on questions. Never repeat a question."
)


def ask_model(history, questions_left, model):
    """Ask Gemma for its next move as strict JSON."""
    transcript = "\n".join(
        f"Q: {q}\nA: {a}" for q, a in history
    ) or "(no questions asked yet)"

    prompt = (
        f"Questions asked so far:\n{transcript}\n\n"
        f"You have {questions_left} questions left.\n\n"
        "Decide your next move. Respond with ONLY a JSON object, no prose:\n"
        '  {"action": "question", "text": "<a single yes/no question>"}\n'
        "or, if confident enough to guess:\n"
        '  {"action": "guess", "text": "<the specific thing you think it is>"}\n'
        "Make a guess if you are confident or if few questions remain."
    )

    payload = {
        "model": model,
        "system": SYSTEM,
        "prompt": prompt,
        "stream": False,
        "format": "json",  # force valid JSON from Ollama
        "options": {"temperature": 0.7},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = json.loads(resp.read()).get("response", "").strip()
    except urllib.error.URLError as e:
        sys.exit(color(f"\n[!] Can't reach Ollama at {OLLAMA_URL} — is it running? ({e})", "red"))

    try:
        obj = json.loads(raw)
        action = obj.get("action", "question")
        text = obj.get("text", "").strip()
        if action not in ("question", "guess") or not text:
            raise ValueError
        return action, text
    except (json.JSONDecodeError, ValueError):
        # Fallback: treat whatever came back as a question
        return "question", raw or "Is it a living thing?"


def get_answer(prompt):
    """Read a yes/no/maybe answer from the user."""
    valid = {
        "y": "yes", "yes": "yes", "n": "no", "no": "no",
        "m": "maybe", "maybe": "maybe", "u": "unknown", "unknown": "unknown",
        "d": "don't know", "dk": "don't know",
    }
    while True:
        raw = input(prompt).strip().lower()
        if raw in ("quit", "exit", "q"):
            print(color("\nGiving up? See you next time! 👋", "dim"))
            sys.exit(0)
        if raw in valid:
            return valid[raw]
        print(color("   (please answer: y / n / maybe / unknown — or 'quit')", "dim"))


def banner():
    print(color("\n" + "=" * 56, "magenta"))
    print(color("  🔮  M I N D   R E A D E R  —  powered by Gemma 4", "bold"))
    print(color("=" * 56, "magenta"))
    print("Think of a " + color("famous person, character, animal, or object", "cyan") + ".")
    print("I'll ask yes/no questions and try to read your mind.")
    print(color("Answer with: y / n / maybe / unknown   (or 'quit')\n", "dim"))


def play(model):
    banner()
    input(color("Got something in mind? Press Enter to begin... ", "yellow"))

    history = []
    for turn in range(1, MAX_QUESTIONS + 1):
        left = MAX_QUESTIONS - turn + 1
        print(color(f"\n[Question {turn}/{MAX_QUESTIONS}] ", "dim") + color("thinking...", "dim"), end="\r")
        action, text = ask_model(history, left, model)

        if action == "guess":
            print(" " * 60, end="\r")
            ans = get_answer(color(f"🤔 My guess: is it ", "magenta") + color(text, "bold") + "?  ")
            if ans == "yes":
                print(color(f"\n🎉 Read your mind in {turn} questions! GG.\n", "green"))
                return
            else:
                # Wrong guess — record it and keep going if questions remain
                history.append((f"Is it {text}?", "no"))
                print(color("   Hmm, not it. Let me dig deeper...", "yellow"))
                continue

        # action == question
        print(" " * 60, end="\r")
        ans = get_answer(color(f"Q{turn}: ", "cyan") + text + "  ")
        history.append((text, ans))

    # Out of questions — make one final desperate guess
    print(color("\nI'm out of questions! Final guess incoming...", "yellow"))
    _, final = ask_model(history, 0, model)
    ans = get_answer(color("🎯 Final answer — is it ", "magenta") + color(final, "bold") + "?  ")
    if ans == "yes":
        print(color("\n😎 Buzzer-beater! Got it.\n", "green"))
    else:
        print(color("\n🏳️  You win — you stumped me! What was it?", "red"))
        try:
            reveal = input(color("   (tell me so I learn): ", "dim"))
            if reveal.strip():
                print(color(f"   Ahh, {reveal.strip()}! I'll remember that.\n", "dim"))
        except EOFError:
            print()


def main():
    p = argparse.ArgumentParser(description="Mind Reader — local Akinator with Gemma 4")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
    args = p.parse_args()
    try:
        play(args.model)
    except (KeyboardInterrupt, EOFError):
        print(color("\n\nBye! 👋\n", "dim"))


if __name__ == "__main__":
    main()
