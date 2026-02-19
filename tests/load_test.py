"""
Locust load test for the Rate Limiter API.

Usage:
    locust -f tests/load_test.py

    Then open http://localhost:8089 in your browser.

Suggested test runs:
    - 100 concurrent users:  Baseline. Should handle easily. Record avg latency and % blocked.
    - 500 concurrent users:  Moderate load. Watch for increased latency and Redis contention.
    - 1000 concurrent users: Stress test. Record p99 latency and error rate. This is where
                              the WATCH/MULTI/EXEC retry loop gets exercised.

Record results in docs/benchmarks.md after each run.
"""

import random

from locust import HttpUser, between, task


class RateLimiterUser(HttpUser):
    """
    Simulates a steady stream of rate-limit check requests.
    Mixes default and strict rules to exercise different bucket configs.
    """

    wait_time = between(0.1, 0.5)

    @task(3)
    def check_default(self):
        self.client.post(
            "/check",
            json={
                "identifier": f"user-{random.randint(1, 50)}",
                "rule": "default",
            },
        )

    @task(1)
    def check_strict(self):
        self.client.post(
            "/check",
            json={
                "identifier": f"user-{random.randint(1, 50)}",
                "rule": "strict",
            },
        )


class BurstUser(HttpUser):
    """
    Simulates burst traffic: fires 20 requests rapidly, then waits.
    Tests that the bucket correctly caps burst at capacity.
    """

    wait_time = between(2, 5)

    @task
    def burst_check(self):
        identifier = f"burst-user-{random.randint(1, 10)}"
        for _ in range(20):
            self.client.post(
                "/check",
                json={
                    "identifier": identifier,
                    "rule": "default",
                },
            )
