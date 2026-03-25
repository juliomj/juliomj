import time
from collections import deque


class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int):
        self.limit = limit_per_minute
        self.timestamps = deque()

    def allow(self) -> bool:
        now = time.time()
        while self.timestamps and self.timestamps[0] <= now - 60:
            self.timestamps.popleft()
        if len(self.timestamps) >= self.limit:
            return False
        self.timestamps.append(now)
        return True
