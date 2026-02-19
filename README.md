# Rate Limiter

A Redis-backed rate limiting API using the token bucket algorithm. Built with FastAPI and Python.

## What It Does

This service sits in front of your application and decides whether a given request should be allowed or blocked based on configurable rate limits. Each client (identified by a string like a user ID or IP address) gets a token bucket that refills at a steady rate and caps at a maximum capacity.

## Tech Stack

| Component    | Technology      |
|-------------|----------------|
| API         | FastAPI         |
| Backend     | Python 3.11     |
| Data Store  | Redis           |
| Dashboard   | Streamlit       |
| Load Testing| Locust          |
| Deployment  | AWS EC2         |

## How the Token Bucket Works

Each client gets a bucket of tokens. Every request costs one token. Tokens refill at a constant rate.

- **Capacity** = maximum burst size. A bucket with capacity 10 handles 10 requests in rapid succession before blocking.
- **Refill rate** = steady-state throughput. At 2 tokens/second, the client can sustain 2 requests/second indefinitely.

When the bucket is empty, requests are blocked and a `retry_after` value tells the client how long to wait.

## API

### `POST /check`

Check whether a request should be allowed.

**Request body:**
```json
{
  "identifier": "user-123",
  "rule": "default"
}
```

**Response:**
```json
{
  "allowed": true,
  "tokens_remaining": 9.0,
  "retry_after": null
}
```

### Available Rules

| Rule     | Capacity | Refill Rate    |
|----------|----------|---------------|
| default  | 10       | 2 tokens/sec  |
| strict   | 5        | 0.5 tokens/sec|
| relaxed  | 50       | 10 tokens/sec |

## Getting Started

### Prerequisites

- Python 3.11+
- Redis (easiest via Docker)

### Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/RajLaskar10/rate-limiter.git
   cd rate-limiter
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Redis**
   ```bash
   docker run -d -p 6379:6379 redis
   ```

4. **Copy the env file**
   ```bash
   cp .env.example .env
   ```

5. **Run the API**
   ```bash
   uvicorn app.main:app --reload
   ```

   API will be available at `http://localhost:8000`. Check `http://localhost:8000/docs` for the interactive Swagger docs.

### Dashboard

```bash
streamlit run dashboard/app.py
```

Opens a browser with controls for sending requests and visualizing token levels in real time.

## Load Testing

```bash
locust -f tests/load_test.py
```

Open `http://localhost:8089`, set the number of users, and point the host at `http://localhost:8000`. Results go in `docs/benchmarks.md`.

## Unit Tests

```bash
pytest tests/unit_test.py -v
```

Requires a running Redis instance. Tests use db=1 to avoid interfering with dev data.

---


