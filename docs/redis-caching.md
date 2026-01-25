# Redis Caching

## Pourquoi Redis ?

Redis est utilisé pour cacher les réponses API coûteuses (yfinance, SEC EDGAR) et réduire la latence + les coûts.

### Avantages

1. **Performance** : Latence sub-milliseconde pour les lectures
2. **TTL natif** : Expiration automatique des données périmées
3. **Persistance** : AOF (Append Only File) pour récupération après crash
4. **Production-proven** : Standard industrie pour le caching

### Ce qu'on cache

| Donnée | TTL | Raison |
|--------|-----|--------|
| Prix temps réel | 5 min | Données marché changent vite |
| Fondamentaux | 1h | Changent rarement |
| SEC filings metadata | 24h | Stable |
| News headlines | 15 min | Actualité |

## Architecture

```
src/utils/cache.py
└── RedisCache
    ├── get()           # Lecture avec désérialization JSON
    ├── set()           # Écriture avec TTL
    ├── delete()        # Invalidation
    └── _make_key()     # Génération clé SHA256
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
  command: redis-server --appendonly yes  # Persistance AOF
```

### Variables d'environnement

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | URL de connexion | `redis://localhost:6379` |
| `CACHE_TTL_SECONDS` | TTL par défaut | `3600` (1h) |

## Utilisation

### Pattern de base

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

### Génération de clés

Les clés sont générées via hash SHA256 pour éviter les collisions :

```python
key = RedisCache._make_key("market", "NVDA", metric="price")
# → "market:a1b2c3d4e5f6g7h8"
```

## Gestion des erreurs

Le cache est **non-bloquant** : si Redis est down, l'app continue sans cache.

```python
def get(self, key: str) -> Any | None:
    client = self._connect()
    if client is None:
        return None  # Graceful degradation
    # ...
```

## Monitoring

### Vérifier la connexion

```python
cache = get_cache()
print(cache.is_connected)  # True/False
```

### Stats Redis (CLI)

```bash
docker exec -it equity-research-agent-redis-1 redis-cli INFO stats
```

## Ressources

- [Redis Documentation](https://redis.io/documentation)
- [redis-py](https://github.com/redis/redis-py)
