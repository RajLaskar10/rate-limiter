from fastapi import APIRouter, HTTPException

from app.api.schemas import CheckRequest, CheckResponse, StatsResponse
from app.config.rules import get_rule
from app.core.redis_client import get_redis_client
from app.core.token_bucket import check_rate_limit, get_bucket_stats

router = APIRouter()


@router.post("/check", response_model=CheckResponse)
def check(request: CheckRequest):
    try:
        rule = get_rule(request.rule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    r = get_redis_client()
    allowed, tokens_remaining, retry_after = check_rate_limit(r, request.identifier, rule)

    return CheckResponse(
        allowed=allowed,
        tokens_remaining=tokens_remaining,
        retry_after=retry_after if not allowed else None,
    )


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/stats/{identifier}", response_model=StatsResponse)
def stats(identifier: str, rule: str = "default"):
    try:
        rule_obj = get_rule(rule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    r = get_redis_client()
    tokens, capacity = get_bucket_stats(r, identifier, rule_obj)

    return StatsResponse(
        identifier=identifier,
        tokens=tokens,
        capacity=capacity,
    )
