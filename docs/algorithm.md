# Token Bucket Algorithm

## Why a Simple Counter Doesn't Work

The obvious approach to rate limiting is to count requests in a fixed time window (e.g., 10 requests per minute). The problem is the boundary condition: a client can send 10 requests at 11:59:59 and another 10 at 12:00:01. That's 20 requests in 2 seconds, even though each individual window looks fine.

Sliding window counters improve on this but add complexity. The token bucket gives you both burst control and steady-state throughput in a simpler model.

## How the Token Bucket Works

Think of it as a bucket that holds tokens. Each request costs one token. Tokens get added at a constant rate (the refill rate). The bucket has a maximum size (the capacity).

- **Capacity** controls the maximum burst size. A bucket with capacity 10 can handle 10 rapid requests before blocking. This is independent of the refill rate.
- **Refill rate** controls the steady-state throughput. A refill rate of 2 tokens/second means the client can sustain 2 requests/second indefinitely.

These two knobs are independent. You can have high burst with low sustained rate, or low burst with high sustained rate.

## Redis Implementation

Here's what happens on every request:

1. **Read** the current token count and the last refill timestamp from Redis
2. **Calculate** how many tokens to add based on elapsed time: `elapsed * refill_rate`
3. **Cap** the total at the bucket capacity
4. **Check** if there's at least 1 token available
5. **Consume** 1 token if allowed, or calculate `retry_after` if not
6. **Write** the updated token count and timestamp back to Redis

If the bucket doesn't exist yet (first request), it starts full at capacity.

## Why WATCH/MULTI/EXEC Instead of Lua Scripts

Redis supports Lua scripts for atomic operations, and they'd work fine here. We used WATCH/MULTI/EXEC instead because:

- The logic is readable Python, not embedded Lua strings
- It's easier to test and debug
- The retry-on-contention pattern is explicit and visible
- For most deployments, the performance difference is negligible

The tradeoff: under very high contention on the same Key, the WATCH approach may retry more than a Lua script would. In practice, rate limit keys are distributed across many users, so contention on a single key is rare.

## Suggested Rule Parameters

| Use Case             | Capacity | Refill Rate   | Reasoning                                            |
|----------------------|----------|---------------|------------------------------------------------------|
| Public API           | 10       | 2/sec         | Allows short bursts but limits sustained abuse       |
| Authenticated User   | 50       | 10/sec        | Higher trust, higher limits                          |
| Login Endpoint       | 5        | 0.5/sec       | Tight limit to slow down brute force attempts        |
| Webhook Receiver     | 100      | 20/sec        | Needs to handle bursty webhook deliveries            |
| Internal Service     | 200      | 50/sec        | High throughput between trusted services             |
