from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.integration_token import IntegrationToken


class IntegrationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: int, provider: str) -> IntegrationToken | None:
        result = await self.session.execute(
            select(IntegrationToken).where(
                IntegrationToken.user_id == user_id, IntegrationToken.provider == provider
            )
        )
        return result.scalar_one_or_none()

    async def is_connected(self, user_id: int, provider: str) -> bool:
        return await self.get(user_id, provider) is not None

    async def upsert(
        self,
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        scopes: list[str] | None = None,
    ) -> IntegrationToken:
        """Called after OAuth consent completes — creates or refreshes the stored token for one provider."""
        existing = await self.get(user_id, provider)
        if existing:
            existing.access_token = access_token
            existing.refresh_token = refresh_token or existing.refresh_token
            existing.client_id = client_id or existing.client_id
            existing.client_secret = client_secret or existing.client_secret
            existing.scopes = scopes or existing.scopes
            self.session.add(existing)
            return existing

        token = IntegrationToken(
            user_id=user_id,
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes or [],
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def disconnect(self, user_id: int, provider: str) -> None:
        token = await self.get(user_id, provider)
        if token:
            await self.session.delete(token)
