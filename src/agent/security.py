from __future__ import annotations

import time
from collections import defaultdict, deque


class Allowlist:
    def __init__(self, allowed_user_ids: set[int]) -> None:
        self._allowed = allowed_user_ids

    def is_allowed(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self._allowed


class RateLimiter:
    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max_per_minute
        self._events: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, key: int) -> bool:
        now = time.time()
        cutoff = now - 60
        events = self._events[key]
        while events and events[0] < cutoff:
            events.popleft()
        if len(events) >= self.max_per_minute:
            return False
        events.append(now)
        return True
