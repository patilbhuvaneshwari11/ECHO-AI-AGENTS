# ECHO-AI-AGENTS

# ECHO: Decision Safety Agent

> **ECHO tests a decision on the campus before the campus lives it.**

Organisations make decisions, for example moving all exams into one building, without seeing the second and third order consequences: exam clashes, overloaded rooms, double-booked rooms, and students who cannot reach their next exam in time. ECHO takes one proposed decision, simulates it on a copy of the timetable, counts the exact problems with code, asks an AI to predict knock-on effects, and recommends a safer option. A human always approves.

**Track:** Track 4 (a harmful decision is treated as the threat to campus operations)
**Team:** [Team name] — Person A: [name], Person B: [name], Person C: [name]

---

## Table of contents

1. [How ECHO works](#how-echo-works)
2. [Key idea: computed vs predicted](#key-idea-computed-vs-predicted)
3. [Project structure](#project-structure)
4. [Quick start](#quick-start)
5. [Configuration](#configuration)
6. [Running tests](#running-tests)
7. [Demo walkthrough](#demo-walkthrough)
8. [Synthetic data and planted problems](#synthetic-data-and-planted-problems)
9. [The rule engine and risk score](#the-rule-engine-and-risk-score)
10. [Security measures and red-team tests](#security-measures-and-red-team-tests)
11. [Handover to college IT](#handover-to-college-it)
12. [Limitations](#limitations)
13. [Troubleshooting](#troubleshooting)

---

## How ECHO works

ECHO is an agent that **senses, thinks, acts and explains**.

| Stage | What happens | Where |
|---|---|---|
| **Sense** | Loads timetable, room and distance data. Rejects tampered data (for example room capacity 0 or 99999). | `engine/loader.py` |
| **Think** | A rule engine counts four kinds of problems. An AI predicts knock-on effects. | `engine/checks.py`, `ai.py` |
| **Act** | Builds three scored options (keep, do exactly as proposed, safer version), recommends one and records human approval. | `engine/simulator.py`, `app.py` |
| **Explain** | Every finding is tagged **computed** (counted by code) or **predicted** (suggested by AI). | `app.py` |

Flow of one request:

```
User text
  -> Security check (length, blocked patterns, role)
  -> AI call 1: turn text into a structured decision (backup regex parser if AI is down)
  -> Validate the AI output ourselves
  -> Rule engine: simulate on a COPY of the timetable, run 4 checks, score 0-100
  -> AI call 2: predict knock-on effects (shown only the computed facts)
  -> Screen: options table, computed box, predicted box
  -> Human approval -> audit log
```

## Key idea: computed vs predicted

- **COMPUTED** results come from code and can be traced to exact rows of data. They are facts.
- **PREDICTED** results come from the AI, are labelled as such, and the AI is only shown the computed facts, so it cannot invent numbers.
- If the AI is unavailable, ECHO still shows all computed results.

## Project structure

```
echo/
├── app.py                  # Streamlit screen (Simulate, Red team, Audit log tabs)
├── ai.py                   # AI calls: parse_decision(), explain(); cache + fallback
├── config.py               # Reads settings and secrets from .env
├── check_ai.py             # Shows the real error if the AI call fails
├── security.py             # Input checks and role check
├── audit.py                # Append-only audit log (audit.log)
├── engine/
│   ├── __init__.py
│   ├── loader.py           # load_data(), data validation
│   ├── checks.py           # the four checks
│   ├── scorer.py           # risk score with visible weights
│   └── simulator.py        # simulate(decision) -> three scored options
├── redteam/
│   ├── __init__.py
│   └── runner.py           # 8 attack and mistake scenarios
├── scripts/
│   └── generate_data.py    # creates the synthetic CSV files
├── data/                   # rooms.csv, exams.csv, enrollments.csv,
│                           # distances.csv, ai_cache.json
├── tests/
│   ├── test_engine.py      # proves planted problems are found
│   └── test_security.py    # proves attacks are blocked
├── requirements.txt
├── .env.example
└── README.md
```

## Quick start

Requirements: **Python 3.11 or 3.12**, and a free Gemini API key from [Google AI Studio](https://aistudio.google.com) (optional; ECHO still shows computed results without it).

```bash
# 1. Get the code
git clone <your-repo-url> echo
cd echo

# 2. Create and activate a virtual environment
python -m venv venv                 # Mac/Linux: python3 -m venv venv
venv\Scripts\activate               # Mac/Linux: source venv/bin/activate

# 3. Install libraries
pip install -r requirements.txt

# 4. Create your private settings file
copy .env.example .env              # Mac/Linux: cp .env.example .env
# then open .env and fill in GEMINI_API_KEY and GEMINI_MODEL

# 5. Generate the synthetic data
python scripts/generate_data.py     # Mac/Linux: python3 ...

# 6. Run the tests
python -m pytest

# 7. Start the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Configuration

Settings live in `.env` (never committed to Git; see `.gitignore`):

| Variable | Meaning |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key. Never share it or put it in code, slides or screenshots. |
| `GEMINI_MODEL` | Exact model name copied from AI Studio (pick a free-tier model). |
| `DEMO_MODE` | `true` = never call the AI; answers come only from `data/ai_cache.json`. `false` = live AI. |

To check the AI connection: `python check_ai.py` (success prints `{'ok': True}`).

## Running tests

```bash
python -m pytest
```

| Test file | What it proves |
|---|---|
| `tests/test_engine.py` | The engine finds exactly the planted problems; the demo decision gives the expected counts and recommendation. |
| `tests/test_security.py` | Prompt injection is blocked, normal text is allowed, a viewer cannot run simulations, all red-team scenarios pass. |

The AI calls are not covered by automatic tests because they need a personal API key. Run `check_ai.py` to verify them.

## Demo walkthrough

1. In the sidebar choose role **admin**.
2. Enter: `Move all Block B exams to Block C` and press **Run ECHO**.
3. The options table shows three options:

| Option | Risk score | What it does |
|---|---|---|
| Keep the current plan | 13 | Changes nothing. |
| Do exactly what was proposed | 66 | Moves every Block B exam to the biggest room of Block C. |
| Safer version | 13 | Moves an exam only if the risk score does not rise (moves only E07). **Recommended.** |

4. "Do exactly what was proposed" gives: 4 clash students, 2 overloaded exams, **40 students who cannot walk to their next exam in time**, and 1 double-booked room. The 40-student travel problem is the hidden consequence of a seemingly harmless decision.
5. Open the **Red team** tab and run all scenarios.
6. Click **Approve recommended option** and open the **Audit log** tab (admin only) to see the approval.

**Offline demo:** run the exact demo sentence once with AI on (this fills `data/ai_cache.json`), then set `DEMO_MODE=true`. A different wording is a different cache entry, so rehearse the exact sentence.

## Synthetic data and planted problems

All data is **synthetic**. No real student data is used, which also protects privacy.

| Table | Content |
|---|---|
| `rooms.csv` | 6 rooms in blocks A, B, C with capacity, floor and lift flag |
| `exams.csv` | 8 exams over 1 and 2 December 2026 |
| `enrollments.csv` | One row per student per exam (578 rows) |
| `distances.csv` | Walking minutes: A to B 5, B to C 8, A to C 12 |

Problems planted on purpose so tests can prove the engine finds them:

- Students S001 to S004 sit exams E05 and E06 at the same time (4 clashes).
- Exam E08 has 55 students in a 50-seat room (1 overload).
- **Hidden trap:** S251 to S270 and S196 to S215 have only 10 minutes between exams in different blocks. Today the walk is 5 minutes (fine). If Block B moves to Block C the walk is 12 minutes, so 40 students cannot make it.

## The rule engine and risk score

For any decision, ECHO copies the timetable, applies the decision and runs four checks:

| Check | Finds |
|---|---|
| `find_clashes` | Students with two exams at the same time |
| `find_overloads` | Exams with more students than the room holds |
| `find_double_bookings` | Two exams in one room at overlapping times |
| `find_travel_problems` | Students whose gap between exams is shorter than the walk between blocks |

Each problem adds points. The weights are visible in `engine/scorer.py` and can be changed:

| Problem | Weight | Reason |
|---|---|---|
| Double-booked room | 8 | Stops an exam from happening |
| Overloaded exam | 5 | Stops an exam from happening safely |
| Clash (per student) | 2 | One student cannot sit both exams |
| Travel problem (per student) | 1 | One student's inconvenience |

The score is capped at 100. The "safer version" tries moving each exam one at a time and keeps a move only if the score does not get worse.

## Security measures and red-team tests

ECHO protects the **decision process** with five measures:

1. **Input checks:** minimum and maximum length (300 characters).
2. **Prompt-injection blocking:** blocked patterns, plus user text is passed to the AI as data between markers.
3. **Role-based access:** only `admin` can run simulations and see the audit log (demo login; the college replaces it with real login).
4. **Audit log:** every action (run, block, denial, approval, red-team run) is written to `audit.log`.
5. **Validation of every AI output:** AI answers are never trusted blindly; the engine validates blocks and structure itself.

Red-team scenarios (`redteam/runner.py`), each showing expected vs actual behaviour:

| Scenario | Expected |
|---|---|
| Main demo decision | runs |
| Missing information | needs_info (ECHO asks instead of guessing) |
| Contradiction (a closed block) | needs_info |
| Unknown block | needs_info |
| Prompt injection | blocked |
| Oversized input | blocked |
| Empty input | blocked |
| Viewer tries to run | blocked |

No text filter is perfect. That is why AI output is also treated as untrusted and validated.

## Handover to college IT

### What ECHO already includes
- Role check (`can_run`) ready to connect to real login
- Audit log of every action
- Input validation and data validation
- `.env` for secrets, no keys in code
- Separated logic files (security, AI, engine, screen)

### What the college must add
- Single sign-on (real login)
- HTTPS and hosting
- Backups
- Monitoring
- Data-privacy compliance review (the college should review its own requirements under applicable law such as India's DPDP Act 2023; ECHO makes no compliance claim)
- Penetration test before going live

### How to integrate
- Embed the Streamlit screen, or
- Wrap the engine (`simulate()`) in an API, or
- Run ECHO on the college's own server

## Limitations

- The data is synthetic, not a real campus.
- Only four kinds of problems are checked (an optional fifth, accessibility, is not part of the base build).
- Decisions are limited to moving exams between blocks.
- Login is a demo role selector, not real authentication.
- AI predictions depend on the Gemini free tier, whose limits and model names change.
- Not built: real data import, learning from past decisions.

## Troubleshooting

| What you see | Fix |
|---|---|
| `python is not recognized` | Re-run the installer and tick Add to PATH, then restart VS Code |
| `No module named pandas` or `streamlit` | Activate the venv, then `pip install -r requirements.txt` |
| `No module named engine` or `ai` | Run commands from the `echo` folder |
| `FileNotFoundError ... rooms.csv` | Run `python scripts/generate_data.py` |
| AI box says "AI explanation unavailable" | Run `python check_ai.py` and read its error (wrong key or model name, quota, no internet, or `DEMO_MODE` without a cache) |
| Error 429 or quota | Free limit reached: wait a minute and use the cache |
| `.env` shows in Git changes | Fix `.gitignore`, and create a new API key if it was already pushed |

## Team rules

- Each person edits only the files they own.
- Start each session with Fetch and Pull, end it with Commit and Push.
- Never share the API key in chats, slides, GitHub or screenshots.
