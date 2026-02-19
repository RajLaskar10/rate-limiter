import time

import pytest
import redis

from app.config.rules import RateLimitRule
from app.core.token_bucket import check_rate_limit, get_bucket_stats

# Use Redis db=1 for testing so we don't interfere with production data
TEST_REDIS_DB = 1


@pytest.fixture(autouse=True)
def redis_client():
    """Provide a clean Redis connection for each test."""
    r = redis.Redis(host="localhost", port=6379, db=TEST_REDIS_DB, decode_responses=True)
    r.flushdb()
    yield r
    r.flushdb()


@pytest.fixture
def default_rule():
    return RateLimitRule(name="default", capacity=10, refill_rate=2.0)


@pytest.fixture
def strict_rule():
    return RateLimitRule(name="strict", capacity=5, refill_rate=0.5)


class TestTokenBucket:
    def test_first_request_allowed(self, redis_client, default_rule):
        """The very first request should always be allowed."""
        allowed, tokens, retry_after = check_rate_limit(redis_client, "user-1", default_rule)
        assert allowed is True
        assert tokens == 9.0  # started at 10, consumed 1
        assert retry_after == 0.0

    def test_bucket_drains(self, redis_client, default_rule):
        """After exhausting all tokens, further requests should be blocked."""
        for _ in range(10):
            check_rate_limit(redis_client, "user-1", default_rule)

        allowed, tokens, retry_after = check_rate_limit(redis_client, "user-1", default_rule)
        assert allowed is False
        assert tokens < 1

    def test_retry_after_is_positive_when_blocked(self, redis_client, strict_rule):
        """When blocked, retry_after should tell the client how long to wait."""
        # Drain the strict bucket (capacity=5)
        for _ in range(5):
            check_rate_limit(redis_client, "user-1", strict_rule)

        allowed, tokens, retry_after = check_rate_limit(redis_client, "user-1", strict_rule)
        assert allowed is False
        assert retry_after > 0

    def test_tokens_refill_over_time(self, redis_client, default_rule):
        """After draining the bucket, waiting should refill tokens."""
        # Drain all tokens
        for _ in range(10):
            check_rate_limit(redis_client, "user-1", default_rule)

        # Wait 2 seconds — should refill ~4 tokens (refill_rate=2.0)
        time.sleep(2)

        allowed, tokens, retry_after = check_rate_limit(redis_client, "user-1", default_rule)
        assert allowed is True
        assert tokens >= 2.0  # at least 2 tokens should be available after consuming 1

    def test_different_identifiers_are_independent(self, redis_client, default_rule):
        """Each identifier gets its own bucket."""
        # Drain user-1
        for _ in range(10):
            check_rate_limit(redis_client, "user-1", default_rule)

        # user-2 should still have tokens
        allowed, tokens, retry_after = check_rate_limit(redis_client, "user-2", default_rule)
        assert allowed is True
        assert tokens == 9.0

    def test_burst_capped_at_capacity(self, redis_client, default_rule):
        """Even after a long idle period, tokens should never exceed capacity."""
        # Make one request to initialize the bucket
        check_rate_limit(redis_client, "user-1", default_rule)

        # Wait long enough that refill would exceed capacity
        time.sleep(3)

        tokens, capacity = get_bucket_stats(redis_client, "user-1", default_rule)
        assert tokens <= capacity
        assert tokens == capacity  # should be capped at capacity
