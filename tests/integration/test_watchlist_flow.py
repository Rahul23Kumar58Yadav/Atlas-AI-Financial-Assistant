from src.core.memory.long_term_memory import LongTermMemory
from src.db.repositories.watchlist_repository import WatchlistRepository
from src.services.personalization_service import personalization_service


async def test_add_and_list_watchlist(db_session, sample_user):
    repo = WatchlistRepository(db_session)
    await repo.add(sample_user.id, "aapl")
    await repo.add(sample_user.id, "TSLA", note="earnings watch")

    symbols = await repo.get_symbols_for_user(sample_user.id)
    assert sorted(symbols) == ["AAPL", "TSLA"]


async def test_adding_duplicate_symbol_is_idempotent(db_session, sample_user):
    repo = WatchlistRepository(db_session)
    await repo.add(sample_user.id, "aapl")
    await repo.add(sample_user.id, "AAPL")  # different casing, same symbol

    symbols = await repo.get_symbols_for_user(sample_user.id)
    assert symbols == ["AAPL"]  # only one row, not two


async def test_remove_from_watchlist(db_session, sample_user):
    repo = WatchlistRepository(db_session)
    await repo.add(sample_user.id, "NVDA")
    await repo.remove(sample_user.id, "nvda")  # case-insensitive removal

    symbols = await repo.get_symbols_for_user(sample_user.id)
    assert symbols == []


async def test_personalization_service_add_to_watchlist(db_session, sample_user):
    await personalization_service.add_to_watchlist(db_session, sample_user.id, "msft")
    symbols = await personalization_service.get_watchlist(db_session, sample_user.id)
    assert symbols == ["MSFT"]


async def test_long_term_memory_context_includes_watchlist(db_session, sample_user):
    repo = WatchlistRepository(db_session)
    await repo.add(sample_user.id, "GOOGL")

    memory = LongTermMemory(db_session)
    context = await memory.get_context_for_user(sample_user.id)
    assert "GOOGL" in context


async def test_long_term_memory_context_for_new_user_with_no_data(db_session, sample_user):
    memory = LongTermMemory(db_session)
    context = await memory.get_context_for_user(sample_user.id)
    assert "No stored preferences yet" in context
