# Redis Caching

## Why Redis?

Redis is used to cache expensive API responses (yfinance, SEC EDGAR) and reduce latency + costs.

### Advantages

1. **Performance**: Sub-millisecond latency for reads
2. **Native TTL**: Automatic expiration of stale data
3. **Persistence**: AOF (Append Only File) for crash recovery
4. **Production-proven**: Industry standard for caching

### What We Cache

| Data | TTL | Reason |
|------|-----|--------|
| Real-time prices | 5 min | Market data changes fast |
| Fundamentals | 1h | Rarely change |
| SEC filings metadata | 24h | Stable |
| News headlines | 15 min | Breaking news |

## Architecture

```
src/utils/cache.py
└── RedisCache
    ├── get()           # Read with JSON deserialization
    ├── set()           # Write with TTL
    ├── delete()        # Invalidation
    └── _make_key()     # SHA256 key generation
```

## Configuration

### Docker Compose

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes  # AOF persistence
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Connection URL | `redis://localhost:6379` |
| `CACHE_TTL_SECONDS` | Default TTL | `3600` (1h) |

## Usage

### Basic Pattern

```python
from src.utils.cache import get_cache

cache = get_cache()

# Check cache first
cached = cache.get("market:NVDA:price")
if cached:
    return cached

# Fetch fresh data
data = fetch_from_api()

# Cache for next time
cache.set("market:NVDA:price", data, ttl=300)  # 5 min

return data
```

### Key Generation

Keys are generated via SHA256 hash to avoid collisions:

```python
key = RedisCache._make_key("market", "NVDA", metric="price")
# → "market:a1b2c3d4e5f6g7h8"
```

## Error Handling

Cache is **non-blocking**: if Redis is down, the app continues without cache.

```python
def get(self, key: str) -> Any | None:
    client = self._connect()
    if client is None:
        return None  # Graceful degradation
    # ...
```

## Monitoring

### Check Connection

```python
cache = get_cache()
print(cache.is_connected)  # True/False
```

### Redis Stats (CLI)

```bash
docker exec -it equity-research-agent-redis-1 redis-cli INFO stats
```

## Resources

- [Redis Documentation](https://redis.io/documentation)
- [redis-py](https://github.com/redis/redis-py)
