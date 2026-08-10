from unittest.mock import AsyncMock, patch

from src.services.alert_service import alert_service
from src.services.market_data.provider_interface import Quote


async def test_create_and_list_alerts(db_session, sample_user):
    alert = await alert_service.create_alert(db_session, sample_user.id, symbol="tsla", threshold_percent=5.0)
    assert alert.symbol == "TSLA"
    assert alert.is_active is True

    alerts = await alert_service.list_alerts(db_session, sample_user.id)
    assert len(alerts) == 1
    assert alerts[0].id == alert.id


async def test_remove_alert_deactivates_not_deletes(db_session, sample_user):
    alert = await alert_service.create_alert(db_session, sample_user.id, symbol="AAPL", threshold_percent=3.0)
    await alert_service.remove_alert(db_session, alert.id)

    active_alerts = await alert_service.list_alerts(db_session, sample_user.id)
    assert active_alerts == []  # not returned when active_only=True (the default)


async def test_evaluate_alert_triggers_when_threshold_exceeded():
    alert = type("Rule", (), {"condition_type": "percent_move", "threshold_percent": 5.0, "symbol": "TSLA"})()

    with patch("src.services.alert_service.market_data.get_quote", new=AsyncMock(
        return_value=Quote(symbol="TSLA", price=250.0, change_percent=7.2)
    )):
        message = await alert_service.evaluate_alert(alert)

    assert message is not None
    assert "TSLA" in message
    assert "7.20%" in message
    assert "$250.00" in message


async def test_evaluate_alert_does_not_trigger_below_threshold():
    alert = type("Rule", (), {"condition_type": "percent_move", "threshold_percent": 5.0, "symbol": "TSLA"})()

    with patch("src.services.alert_service.market_data.get_quote", new=AsyncMock(
        return_value=Quote(symbol="TSLA", price=250.0, change_percent=1.5)
    )):
        message = await alert_service.evaluate_alert(alert)

    assert message is None


async def test_check_all_alerts_sends_notification_and_marks_triggered(db_session, sample_user, fake_bot):
    await alert_service.create_alert(db_session, sample_user.id, symbol="TSLA", threshold_percent=5.0)
    await db_session.commit()

    with patch("src.services.alert_service.market_data.get_quote", new=AsyncMock(
        return_value=Quote(symbol="TSLA", price=250.0, change_percent=7.2)
    )), patch("src.services.alert_service.get_session") as mock_get_session:
        # check_all_alerts opens its own session via get_session() (a context manager),
        # not the db_session fixture, so it needs to be pointed at the same test DB.
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _use_test_session():
            yield db_session

        mock_get_session.side_effect = _use_test_session

        triggered_count = await alert_service.check_all_alerts(fake_bot)

    assert triggered_count == 1
    assert len(fake_bot.sent_messages) == 1
    assert "TSLA" in fake_bot.sent_messages[0][1]
