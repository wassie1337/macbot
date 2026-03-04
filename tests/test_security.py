from agent.security import Allowlist, RateLimiter


def test_allowlist():
    a = Allowlist({1, 2})
    assert a.is_allowed(1)
    assert not a.is_allowed(99)


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(max_per_minute=2)
    assert limiter.allow(1)
    assert limiter.allow(1)
    assert not limiter.allow(1)
