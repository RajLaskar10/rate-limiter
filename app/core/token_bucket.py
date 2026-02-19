import time
from typing import Tuple

import redis

from app.config.rules import RateLimitRule


def check_rate_limit(
    r: redis.Redis, identifier: str, rule: RateLimitRule
) -> Tuple[bool, float, float]:
    """
    Token bucket rate limiter using Redis WATCH/MULTI/EXEC for atomicity.

    Returns:
        (allowed, tokens_remaining, retry_after)
        - allowed: True if the request is permitted
        - tokens_remaining: number of tokens left after this check
        - retry_after: seconds until a token is available (0.0 if allowed)
    """
    bucket_key = f"bucket:{identifier}:{rule.name}"
    tokens_key = f"{bucket_key}:tokens"
    ts_key = f"{bucket_key}:ts"

    while True:
        try:
            pipe = r.pipeline()
            pipe.watch(tokens_key, ts_key)

            now = time.time()

            raw_tokens = pipe.get(tokens_key)
            raw_ts = pipe.get(ts_key)

            if raw_tokens is None:
                # First request — bucket starts full
                tokens = rule.capacity
                last_refill = now
            else:
                tokens = float(raw_tokens)
                last_refill = float(raw_ts)

            # Refill tokens based on elapsed time
            elapsed = now - last_refill
            tokens = min(rule.capacity, tokens + elapsed * rule.refill_rate)
            last_refill = now

            if tokens >= 1:
                tokens -= 1
                allowed = True
                retry_after = 0.0
            else:
                allowed = False
                retry_after = (1 - tokens) / rule.refill_rate

            pipe.multi()
            pipe.set(tokens_key, str(tokens))
            pipe.set(ts_key, str(last_refill))
            pipe.execute()

            return allowed, round(tokens, 2), round(retry_after, 2)

        except redis.WatchError:
            # Another client modified the key — retry
            continue


def get_bucket_stats(
    r: redis.Redis, identifier: str, rule: RateLimitRule
) -> Tuple[float, float]:
    """
    Read current token level without consuming a token.

    Returns:
        (tokens, capacity)
    """
    bucket_key = f"bucket:{identifier}:{rule.name}"
    tokens_key = f"{bucket_key}:tokens"
    ts_key = f"{bucket_key}:ts"

    now = time.time()

    raw_tokens = r.get(tokens_key)
    raw_ts = r.get(ts_key)

    if raw_tokens is None:
        return rule.capacity, rule.capacity

    tokens = float(raw_tokens)
    last_refill = float(raw_ts)

    elapsed = now - last_refill
    tokens = min(rule.capacity, tokens + elapsed * rule.refill_rate)

    return round(tokens, 2), rule.capacity
