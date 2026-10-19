# Braiinz Education

[![CI](https://github.com/braiinz94/braiinz-education/actions/workflows/ci.yml/badge.svg)](https://github.com/braiinz94/braiinz-education/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Code style](https://img.shields.io/badge/lint-ruff-000000.svg)
![Status](https://img.shields.io/badge/status-v0.1%20alpha-orange.svg)

**Open-source AI tutoring agents that make quality learning accessible to everyone** — students, self-learners, and people in professional reskilling.

Built on the Anthropic Claude API and delivered through Telegram, Braiinz Education brings adaptive, personalized pedagogy to any device — at zero cost for learners.

---

## Why

Good tutoring is scarce and expensive. Large language models can close that gap — but only if the pedagogy is deliberate (not just "ask the chatbot"), the cost is controlled, and learner data is handled responsibly. Braiinz Education is an attempt to do all three, in the open.

## The three agents

| Agent | Role | Method |
|-------|------|--------|
| **Tuteur Socratique** | Guides discovery | Asks targeted questions instead of giving answers; adapts difficulty to each response to build genuine understanding. |
| **Coach Pratique** | Turns theory into skill | Hands-on exercises and project-based challenges calibrated to the learner's level, with immediate actionable feedback. |
| **Diagnostiqueur** | Maps what to learn next | Assesses knowledge, surfaces gaps and misconceptions, and builds a personalized roadmap scheduled with **spaced repetition (FSRS)** for long-term retention. |

## Highlights

- 🎯 **Deliberate pedagogy** — Socratic questioning, project-based practice, and diagnostic roadmapping, not generic chat.
- 🧠 **Spaced repetition** — reviews scheduled with the [FSRS](https://github.com/open-spaced-repetition) algorithm for durable memory.
- 💸 **Cost-aware LLM router** — every request is routed to the cheapest capable Claude model across three tiers (Haiku → Sonnet → Opus), with per-tier cost tracking in EUR.
- 🇪🇺 **EU-ready by design** — switch `LLM_PROVIDER` to AWS Bedrock (region `eu-west-3`, Paris) to keep learner data in the EU (Schrems II). A [France compliance matrix](docs/legal/2026-04-18-compliance-matrix-france.md) documents the analysis.
- 🛡️ **Guardrails** — input/output safety checks tailored to a learning context.
- 📚 **Pluggable curricula** — subjects are JSON packs; ships with a French *Seconde* mathematics pack, and new packs are easy to add.
- 📱 **Telegram-native** — no app to install for learners.

## How it works

```
Learner (Telegram)
        │
   ┌────▼─────┐   handlers route messages to the right agent
   │   Bot    │
   └────┬─────┘
        │
 ┌──────▼───────┐   Tuteur · Coach · Diagnostiqueur
 │    Agents    │   (each a BaseAgent, guardrail-wrapped)
 └──────┬───────┘
        │
 ┌──────▼───────┐   fast / standard / deep tiers
 │  LLM Router  │   Anthropic API  ─or─  AWS Bedrock (EU)
 └──────────────┘
```

## Quick start

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Configure
cp .env.example .env
#   → set ANTHROPIC_API_KEY and TELEGRAM_BOT_TOKEN
#   → (optional) LLM_PROVIDER=bedrock for EU data residency

# 3. Run the Telegram bot
python -m src.bot.telegram_bot
```

### Requirements

- Python **3.12+**
- An [Anthropic API key](https://console.anthropic.com/) — or AWS Bedrock access for EU residency
- A Telegram bot token from [@BotFather](https://t.me/botfather)

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_PROVIDER` | `anthropic` | `anthropic` (direct API) or `bedrock` (AWS, EU region) |
| `ANTHROPIC_API_KEY` | — | Required when `LLM_PROVIDER=anthropic` |
| `AWS_REGION` | `eu-west-3` | Bedrock region (EU data residency) |
| `TELEGRAM_BOT_TOKEN` | — | Required — from @BotFather |
| `LLM_MODEL_FAST` / `_STANDARD` / `_DEEP` | built-in | Override the model used per tier |

See [`.env.example`](.env.example) for the full list.

## Project structure

```
src/
  base_agent.py         # shared agent contract
  llm_router.py         # 3-tier, cost-aware, provider-switchable routing
  guardrails.py         # safety checks
  student_profile.py    # per-learner state
  agents/               # tuteur_socratique · coach_pratique · diagnostiqueur
  bot/                  # telegram_bot · handlers
  curriculum/           # loader + JSON packs (pack_fr_maths_seconde.json)
docs/legal/             # France compliance matrix
tests/                  # full suite (agents, router, guardrails, bot, curriculum)
```

## Development

```bash
pytest            # run the test suite
pytest --cov=src  # with coverage
ruff check .      # lint
```

## Roadmap

- [ ] Additional curriculum packs (other subjects and levels)
- [ ] Web delivery alongside Telegram
- [ ] Learner-facing progress dashboard
- [ ] Evaluation harness for pedagogical quality

Contributions and curriculum packs are welcome — open an issue to discuss.

## License

- **Code** — [Apache-2.0](LICENSE)
- **Educational content** — CC-BY-SA 4.0 (free to share and adapt with attribution)

---

*Braiinz Education is a separate open-source project from [Braiinz](https://braiinz.fr), the commercial AI consulting firm. Its mission is to democratize access to quality AI-assisted education.*
