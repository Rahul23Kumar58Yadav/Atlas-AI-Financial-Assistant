# Demo Script

A suggested walkthrough for the submission video, built around what's actually working end-to-end — not the stubbed pieces. Aim for 3-4 minutes.

## 1. Cold start — conversational onboarding (30s)

Send `/start` on a fresh account. Show that onboarding is a real conversation, not a form:
- "What best describes you?" → answer naturally, e.g. "I'm an analyst"
- "Any companies you'd like me to watch?" → "AAPL, NVDA, and TSLA"
- "What kind of updates matter most?" → "earnings and filings"
- "When would you like your briefing?" → "8am"

Call out: every answer can be skipped ("skip") and the user is never blocked from just starting to chat instead.

## 2. Natural research, no commands (45s)

Ask something specific, not a command:
> "What's happening with NVDA today?"

Show the tool-calling happening live (Claude pulling a real quote via Finnhub) and the answer explaining *why* it matters, not just repeating the price.

Then ask something deliberately vague:
> "Tell me about Apple"

Show the assistant asking a clarifying question (news? earnings? valuation?) instead of guessing — this is the single most product-differentiating behavior in the whole build; make sure it's on camera.

## 3. Comparison (20s)

> "Compare Microsoft and Google from an investment perspective"

Shows `research_service.compare_companies` pulling live snapshots for both and reasoning across them in one answer.

## 4. Document upload (30s)

Upload a sample PDF (an earnings report or 10-K excerpt works well). Show:
- The bot extracts real text (not a stub — this is `pypdf` doing genuine extraction)
- It immediately summarizes on upload
- A follow-up question like "what's the biggest risk mentioned?" gets answered from the actual document content

## 5. Watchlist + alert (20s)

> "Add TSLA to my watchlist"
> "Notify me if TSLA moves more than 5% in a day"

Then either wait for a real trigger, or briefly show the `alert_check` job log line confirming it's checking on a schedule (5 minutes) rather than claiming to without proof.

## 6. Daily briefing (15s — can be pre-recorded/sped up)

Show a real briefing message that arrived at the scheduled time, and mention the "nothing notable" rule: if nothing moved, no message gets sent at all — quality over frequency, straight from the brief's own design principles.

## 7. Close (10s)

One line on what's stubbed vs. built, framed honestly: Gmail/Calendar/Drive OAuth flow is real and tested (show the `/oauth/google/authorize` redirect briefly if there's time), but the calendar/email *tools* themselves are wired to clear extension points rather than fully built out — a deliberate scope choice to get the finance-first experience polished rather than spreading thin across every integration.

## Things to avoid on camera

- Don't demo `/help` or any slash-command menu — the brief explicitly penalizes command-based interaction.
- Don't show a raw JSON tool-call response; let the model's natural-language answer be what's on screen.
- Don't claim a stubbed feature works — if asked to compare "what's built vs. what's aspirational," the honest answer is stronger than pretending everything is finished.
