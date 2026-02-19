from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Rate Limiter",
    description="Redis-backed rate limiting API using the token bucket algorithm",
    version="1.0.0",
)

app.include_router(router)
