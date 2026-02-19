from pydantic import BaseModel
from typing import Optional


class CheckRequest(BaseModel):
    identifier: str
    rule: str = "default"


class CheckResponse(BaseModel):
    allowed: bool
    tokens_remaining: float
    retry_after: Optional[float] = None


class StatsResponse(BaseModel):
    identifier: str
    tokens: float
    capacity: float
