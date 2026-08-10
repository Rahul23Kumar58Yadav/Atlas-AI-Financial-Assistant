# Atlas — Architecture

Reflects what's actually implemented (not aspirational) as of this build. See `README.md` for setup and the honest "implemented vs. stubbed" list.

## Layers

```
bot/          Telegram layer. No business logic — normalizes text/voice/image/
              document into a common shape and hands off to services/ai/agent.py.

services/ai/  The brain. agent.py classifies intent, decides whether to ask a
              clarifying question, and delegates. prompts/ holds every system
              prompt as its own file. tools/ + registry.py are the tool-calling
              layer Claude uses for live data. memory/ re-exports core/memory/
              so everything AI-related lives under one tree on disk.

core/         Agents (research, briefing) and the two-tier memory
              implementation (short-term conversation history, long-term
              preferences + freeform facts) that services/ai/ wraps.

services/     Feature-oriented business logic: onboarding_service,
              briefing_service, research_service, document_service,
              alert_service, personalization_service. Each wraps
              repositories/agents into one clean API — jobs and bot handlers
              call these, not repositories directly.

services/
integrations/ External API clients: Google (Gmail/Calendar/Drive/Sheets),
              market data (Finnhub, SEC EDGAR), voice (Whisper STT).
              Thin and swappable — provider_interface.py means adding a
              new market data source never touches agent code.

db/           SQLAlchemy async models + one repository per model. Watchlist
              is a normalized table (not JSON) so alert/briefing queries can
              join against it directly.

jobs/         Scheduled tasks (APScheduler): daily briefing, alert watcher,
              earnings reminder. Each is a thin trigger — the actual logic
              lives in the corresponding services/*.py.

api/          FastAPI: health check, Google OAuth flow (real, tested), and
              a watchlist CRUD endpoint demonstrating the schemas/ layer.

schemas/      Pydantic request/response models, decoupled from the
              SQLAlchemy models so API shapes can evolve independently.

utils/        formatting.py (currency/percent/large-number) and
              rate_limiter.py (sliding window, in-memory) — shared by
              multiple services rather than each reimplementing.
```

## Data flow for a typical message

1. `bot/handlers/text.py` receives the message, `AuthMiddleware` resolves/creates the `User` row, `RateLimitMiddleware` checks the sliding window first.
2. `services/ai/agent.py::run_agent` classifies intent, decides if clarification is needed, pulls conversation history + long-term context.
3. For research: Claude gets `RESEARCH_SCHEMAS` (quote + snapshot tools only — calendar/email/alert tools are dispatched directly by intent, never offered to the model, so it can't "choose" an unconnected integration).
4. Reply gets persisted via `ConversationMemory`, returned to the bot, chunked for Telegram's message-length limit.

## Known simplifications (see code comments for each)

- Single-process deployment (bot + API + scheduler share one event loop) — fine for a hackathon, split into separate processes to scale independently.
- Watchlist/alert/briefing timezone handling compares against UTC directly; `Preference.timezone` is stored but not yet applied to the comparison.
- Document Q&A stuffs full extracted text into the prompt rather than real RAG (chunking + embeddings) — fine for single documents within context limits, not for a large filing collection.
- OAuth `state` param is the raw telegram_id, not a signed CSRF-safe token.
- In-memory rate limiter and Finnhub ticker→CIK cache don't share state across multiple worker processes.

## Testing

`tests/unit/` — pure logic, no DB (formatting, rate limiter, PDF extraction).
`tests/integration/` — real in-memory SQLite DB per test, exercising repositories/services together (watchlist normalization, alert evaluation, earnings reminder dedup — the latter two are regression tests for bugs actually caught during manual testing of this project).
`tests/fixtures/` — static sample data (Finnhub-shaped earnings JSON, a sample filing text) shared across tests.

Run with `pytest` from the project root.
