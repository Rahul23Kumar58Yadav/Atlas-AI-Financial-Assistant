from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.alert_rule import AlertRule


class AlertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, symbol: str, threshold_percent: float, condition_type: str = "percent_move") -> AlertRule:
        rule = AlertRule(
            user_id=user_id,
            symbol=symbol.upper(),
            condition_type=condition_type,
            threshold_percent=threshold_percent,
        )
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def get_for_user(self, user_id: int, active_only: bool = True) -> list[AlertRule]:
        query = select(AlertRule).where(AlertRule.user_id == user_id)
        if active_only:
            query = query.where(AlertRule.is_active.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_active(self) -> list[AlertRule]:
        result = await self.session.execute(select(AlertRule).where(AlertRule.is_active.is_(True)))
        return list(result.scalars().all())

    async def deactivate(self, alert_id: int) -> None:
        rule = await self.session.get(AlertRule, alert_id)
        if rule:
            rule.is_active = False
            self.session.add(rule)

    async def mark_triggered(self, alert_id: int) -> None:
        rule = await self.session.get(AlertRule, alert_id)
        if rule:
            rule.last_triggered_at = dt.datetime.utcnow()
            self.session.add(rule)
