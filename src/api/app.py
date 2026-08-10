from __future__ import annotations

from fastapi import FastAPI

from src.api.routes import health, oauth, watchlist

app = FastAPI(title="Atlas Financial Assistant API")

app.include_router(health.router)
app.include_router(oauth.router)
app.include_router(watchlist.router)
