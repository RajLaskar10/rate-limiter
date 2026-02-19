import redis
from app.config.settings import settings

_client = None


def get_redis_client(db: int = 0) -> redis.Redis:
    global _client
    if _client is None or db != 0:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=db,
            decode_responses=True,
        )
        if db == 0:
            _client = client
        return client
    return _client
