# Load Test Benchmarks

## Results

Run these tests with Locust (`locust -f tests/load_test.py`) and fill in the table after each run.

| Concurrent Users | Requests/sec | Avg Latency (ms) | p99 Latency (ms) | % Blocked | Notes |
|------------------|-------------|-------------------|-------------------|-----------|-------|
| 100              |             |                   |                   |           |       |
| 500              |             |                   |                   |           |       |
| 1000             |             |                   |                   |           |       |

## What to Look For

- **Avg Latency**: Should stay under 10ms for 100 users. If it spikes, check Redis connection pooling.
- **p99 Latency**: Watch for tail latency. High p99 with low avg means contention on hot keys.
- **% Blocked**: Should increase as concurrent users go up. If it's 0% even at 1000 users, your refill rate is too high for the test to exercise blocking.
- **Errors**: Any 500s indicate a problem — likely Redis connection issues under load.

## Resume Bullet Template

After running the tests, you can write something like:

> Built a Redis-backed rate limiter handling X req/sec at p99 latency of Yms with Z concurrent users, using the token bucket algorithm with WATCH/MULTI/EXEC for concurrency control.
