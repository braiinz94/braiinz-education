# Braiinz Education

Open-source AI educational agents that make quality learning accessible to everyone — students,
self-learners, and people in professional reskilling programs.

Built with the Anthropic Claude API and delivered via Telegram, these agents bring adaptive,
personalized pedagogy to any device, at zero cost for learners.

## Agents (v0.1)

### Tuteur Socratique
Guides learners through discovery using the Socratic method — asking targeted questions rather
than giving answers directly. Adapts question difficulty based on learner responses and builds
genuine conceptual understanding.

### Coach Pratique
Provides hands-on exercises, real-world application scenarios, and immediate actionable feedback.
Bridges the gap between theory and practice with project-based challenges calibrated to the
learner's current level.

### Diagnostiqueur
Assesses learner knowledge across a topic, identifies gaps and misconceptions, and generates
a personalized learning roadmap. Uses spaced repetition (FSRS algorithm) to schedule reviews
at optimal intervals for long-term retention.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY and TELEGRAM_BOT_TOKEN

# Start the Telegram bot
python -m src.bot.telegram_bot
```

## Requirements

- Python 3.12+
- An [Anthropic API key](https://console.anthropic.com/)
- A Telegram bot token (create one via [@BotFather](https://t.me/botfather))

## License

- **Code**: Apache-2.0 — see [LICENSE](LICENSE)
- **Educational content**: CC-BY-SA 4.0 — free to share and adapt with attribution

---

*Braiinz Education is a separate open-source project from Braiinz, the commercial AI consulting firm.
Its mission is to democratize access to quality AI-assisted education.*
