"""
Feature-oriented facade for watchlist alerts: "notify me if TSLA moves
more than 5% in a day". Persists via AlertRule/AlertRepository and
evaluates against live quotes — this is real, working logic, not a stub;
jobs/alert_check_job.py just needs to call check_all_alerts() on a schedule.
"""
from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.db.base import get_session
from src.db.models.alert_rule import AlertRule
from src.db.models.user import User
from src.db.repositories.alert_repository import AlertRepository
from src.services.market_data.aggregator import market_data
from src.utils.formatting import format_currency, format_percent

logger = get_logger(__name__)


class AlertService:
    async def create_alert(self, session: AsyncSession, user_id: int, symbol: str, threshold_percent: float) -> AlertRule:
        repo = AlertRepository(session)
        return await repo.create(user_id, symbol, threshold_percent)

    async def list_alerts(self, session: AsyncSession, user_id: int) -> list[AlertRule]:
        repo = AlertRepository(session)
        return await repo.get_for_user(user_id)

    async def remove_alert(self, session: AsyncSession, alert_id: int) -> None:
        repo = AlertRepository(session)
        await repo.deactivate(alert_id)

    async def evaluate_alert(self, rule: AlertRule) -> str | None:
        """Returns a human-readable trigger message if the rule's condition is currently met, else None."""
        if rule.condition_type != "percent_move" or rule.threshold_percent is None:
            return None  # other condition types (sec_filing, etc.) need their own evaluator

        quote = await market_data.get_quote(rule.symbol)
        if quote is None:
            return None

        if abs(quote.change_percent) >= rule.threshold_percent:
            direction = "up" if quote.change_percent > 0 else "down"
            return (
                f"{rule.symbol} is {direction} {format_percent(abs(quote.change_percent), show_sign=False)} today "
                f"(you asked to be notified at {rule.threshold_percent:.1f}%+) — now at {format_currency(quote.price)}."
            )
        return None

    async def check_all_alerts(self, bot: Bot) -> int:
        """
        Evaluates every active alert across all users and sends notifications
        for triggered ones. Called by jobs/alert_check_job.py on a schedule.
        Returns the count of alerts triggered, for logging/testing.
        """
        triggered_count = 0

        async with get_session() as session:
            repo = AlertRepository(session)
            rules = await repo.get_all_active()

            for rule in rules:
                try:
                    message = await self.evaluate_alert(rule)
                    if message is None:
                        continue

                    user = await session.get(User, rule.user_id)
                    if user is None:
                        continue

                    await bot.send_message(user.telegram_id, f"Alert: {message}")
                    await repo.mark_triggered(rule.id)
                    triggered_count += 1
                    logger.info("alert_triggered", alert_id=rule.id, user_id=rule.user_id, symbol=rule.symbol)
                except Exception as exc:  # noqa: BLE001 — one bad rule shouldn't block the rest of the batch
                    logger.error("alert_evaluation_failed", alert_id=rule.id, error=str(exc))

        return triggered_count


alert_service = AlertService()
