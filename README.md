# Atlas — AI Financial Assistant for Telegram

Atlas is an AI-powered financial assistant that lives inside Telegram. It talks like an experienced financial analyst — not a command-driven bot — helping investors, analysts, and finance professionals research companies, track markets, and stay on top of what actually matters without switching between a dozen tabs.

Built for the **Atlas AI Financial Assistant Hackathon**.

🔗 Talk to it: [@atlas_12finance_bot](https://t.me/atlas_12finance_bot)

---

## What it does

- **Natural conversation, no commands.** Ask questions the way you'd ask a colleague — "what's Apple's stock price," "compare Microsoft and Google," "track Tesla for me" — no slash commands, menus, or rigid syntax.
- **Live market research.** Pulls real-time quotes, company profiles, and recent news on demand instead of relying on stale training data.
- **Intent-aware routing.** Classifies each message (research, scheduling, preference updates, smalltalk) and asks a clarifying question when a request is genuinely ambiguous, rather than guessing.
- **Proactive daily briefings.** A scheduled job checks each user's watchlist and sends a summary only when something's actually worth reporting — silence by default, not noise.
- **Watchlist alerts.** Price-move thresholds and earnings reminders, monitored continuously in the background.
- **Provider-agnostic AI layer.** One internal interface (`LLMClient`) backs onto Groq, Gemini, or Anthropic — swap providers with a single environment variable, no code changes elsewhere in the app.

---

## Tech stack

| Layer | Choice |
|---|---|
| Bot framework | [aiogram](https://docs.aiogram.dev/) (long polling) |
| API server | FastAPI + Uvicorn (health checks, future OAuth callbacks) |
| Scheduler | APScheduler (daily briefings, alert/earnings monitoring) |
| Database | SQLite via `sqlite+aiosqlite` (swappable for Postgres/MySQL) |
| AI providers | Groq (default), Gemini, Anthropic — behind one shared interface |
| Market data | Finnhub, SEC EDGAR |
| Config | `pydantic-settings`, single source of truth in `src/config/settings.py` |
| Logging | `structlog` |

---

## Project structure

```
src/
  main.py                  Entrypoint - runs bot, API, and scheduler together
  bot/
    client.py               Bot/dispatcher setup
    router.py                Registers all handlers
    handlers/                 text, voice, image, document handlers
    middlewares/               auth, rate limiting, typing indicator
  core/
    orchestrator.py          Routes an incoming message into the agent
  services/
    ai/
      llm_client.py           Provider-agnostic LLM wrapper (Groq/Gemini/Anthropic)
      agent.py                 Conversation + tool-use orchestration
      prompts/                  System prompts (research, classifier, clarify)
    document_service.py       Document ingestion/analysis
    finance/                   Market data, news, SEC filings
  jobs/
    scheduler.py               APScheduler bootstrap
  config/
    settings.py                Centralized environment configuration
    logging.py                  Structured logging setup
  db/
    base.py                    Database init
```

---

## Getting started

**Requirements:** Python 3.10+, a Telegram bot token from [@BotFather](https://t.me/BotFather), and at least one AI provider key (Groq recommended — free tier, no cloud console needed).

```bash
git clone <this-repo>
cd atlas
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env          # fill in your keys
python -m src.main
```

### Environment variables

| Variable | Required | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | From @BotFather |
| `AI_PROVIDER` | Yes | `groq` \| `gemini` \| `anthropic` |
| `GROQ_API_KEY` | If using Groq | Free tier available |
| `GROQ_MODEL` | No | Defaults to `llama-3.3-70b-versatile` |
| `GEMINI_API_KEY` | If using Gemini | |
| `ANTHROPIC_API_KEY` | If using Anthropic | |
| `FINNHUB_API_KEY` | Yes | Live quotes, company profiles, news |
| `DATABASE_URL` | No | Defaults to local SQLite file |
| `API_PORT` | No | Defaults to `8000` |

See `.env.example` for the full list.

---

## Design notes

- **No commands, ever.** Every input — text, voice, image — routes through the same natural-language pipeline. The product goal is a bot that feels conversational, not a menu tree.
- **Quality over frequency.** The briefing job explicitly returns nothing when there's no meaningful move or news, so users aren't trained to ignore notifications.
- **Resilient tool-calling.** Smaller/faster LLMs occasionally emit malformed function calls or leak them as plain text instead of structured calls. The Groq path in `llm_client.py` detects both cases, retries once, and fails gracefully with a clear message rather than crashing or shipping garbage to the user.
- **One LLM interface, three providers.** Nothing outside `llm_client.py` knows or cares which model is running — this made it possible to develop against Groq's free tier and fall back to Gemini/Anthropic without touching the agent, prompts, or handlers.

---

## Known limitations

This is a hackathon MVP, not a production system:

- Voice transcription and image/document analysis pipelines are scaffolded but not fully wired up.
- Google OAuth (Gmail/Calendar/Drive) integration is stubbed pending client credentials.
- SQLite is fine for a single-instance demo; a concurrent-safe database is needed to scale beyond one worker process.
- Groq's free tier has a daily token limit — expect to see a graceful rate-limit message rather than a crash if it's exceeded during heavy testing.

---

## License

Built for hackathon submission. License TBD.
