import time

from src.utils.rate_limiter import RateLimiter


def test_allows_up_to_max_requests():
    limiter = RateLimiter(max_requests=3, window_seconds=1.0)
    for _ in range(3):
        assert limiter.is_allowed("user1") is True


def test_rejects_beyond_max_requests():
    limiter = RateLimiter(max_requests=3, window_seconds=1.0)
    for _ in range(3):
        limiter.is_allowed("user1")
    assert limiter.is_allowed("user1") is False


def test_keys_are_independent():
    limiter = RateLimiter(max_requests=1, window_seconds=1.0)
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is False
    assert limiter.is_allowed("user2") is True  # separate key, separate budget


def test_window_expires_and_allows_again():
    limiter = RateLimiter(max_requests=1, window_seconds=0.2)
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is False
    time.sleep(0.25)
    assert limiter.is_allowed("user1") is True


def test_seconds_until_next_slot_reports_remaining_wait():
    limiter = RateLimiter(max_requests=1, window_seconds=0.3)
    limiter.is_allowed("user1")
    wait = limiter.seconds_until_next_slot("user1")
    assert 0 < wait <= 0.3


def test_reset_clears_state():
    limiter = RateLimiter(max_requests=1, window_seconds=1.0)
    limiter.is_allowed("user1")
    assert limiter.is_allowed("user1") is False
    limiter.reset("user1")
    assert limiter.is_allowed("user1") is True
