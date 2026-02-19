from dataclasses import dataclass
from typing import Dict


@dataclass
class RateLimitRule:
    name: str
    capacity: float
    refill_rate: float  # tokens per second


RULES: Dict[str, RateLimitRule] = {
    "default": RateLimitRule(name="default", capacity=10, refill_rate=2.0),
    "strict": RateLimitRule(name="strict", capacity=5, refill_rate=0.5),
    "relaxed": RateLimitRule(name="relaxed", capacity=50, refill_rate=10.0),
}


def get_rule(name: str) -> RateLimitRule:
    if name not in RULES:
        raise ValueError(f"Unknown rate limit rule: '{name}'. Available rules: {list(RULES.keys())}")
    return RULES[name]
