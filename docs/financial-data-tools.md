# Financial Data Tools

## Vue d'ensemble

Le projet utilise plusieurs sources de données financières :

```
src/tools/
├── yfinance_tool.py    # Prix, fondamentaux, historique
├── sec_edgar_tool.py   # SEC filings (10-K, 10-Q, 8-K)
└── search_tool.py      # DuckDuckGo pour news
```

## yfinance

### Pourquoi yfinance ?

- **Gratuit** : Pas d'API key requise
- **Complet** : Prix, fondamentaux, dividendes, institutionnels
- **Fiable** : Données Yahoo Finance

### Données disponibles

| Type | Méthode | Cache TTL |
|------|---------|-----------|
| Prix temps réel | `get_price()` | 5 min |
| Historique | `get_history()` | 1h |
| Fondamentaux | `get_fundamentals()` | 1h |
| Info entreprise | `get_info()` | 24h |

### Utilisation

```python
from src.tools.yfinance_tool import YFinanceTool

tool = YFinanceTool()

# Prix actuel
price = tool.get_price("NVDA")
# {"symbol": "NVDA", "price": 875.50, "change": 2.3, "volume": 45000000}

# Fondamentaux
fundamentals = tool.get_fundamentals("NVDA")
# {"pe_ratio": 65.2, "market_cap": 2150000000000, "revenue": 60922000000, ...}

# Historique
history = tool.get_history("NVDA", period="1mo")
# DataFrame avec Open, High, Low, Close, Volume
```

## SEC EDGAR

### Pourquoi SEC EDGAR ?

- **Officiel** : Source primaire pour les filings US
- **Complet** : 10-K, 10-Q, 8-K, proxy statements
- **Gratuit** : API publique

### Configuration

```env
SEC_USER_AGENT=EquityResearchAgent cachnolan@gmail.com
```

> **Important** : SEC requiert un User-Agent valide avec email de contact.

### Filings supportés

| Type | Description | Fréquence |
|------|-------------|-----------|
| 10-K | Rapport annuel | Annuel |
| 10-Q | Rapport trimestriel | Trimestriel |
| 8-K | Événements majeurs | Ad-hoc |

### Utilisation

```python
from src.tools.sec_edgar_tool import SECEdgarTool

tool = SECEdgarTool()

# Télécharger le dernier 10-K
filing = tool.download_filing("NVDA", "10-K")

# Lister les filings récents
filings = tool.list_filings("NVDA", form_type="10-K", count=5)
```

## DuckDuckGo Search

### Pourquoi DuckDuckGo ?

- **Gratuit** : Pas d'API key
- **Pas de tracking** : Respect de la vie privée
- **News** : Recherche d'actualités récentes

### Utilisation

```python
from src.tools.search_tool import SearchTool

tool = SearchTool()

# Recherche web générale
results = tool.search("NVIDIA earnings Q4 2024")

# Recherche news
news = tool.search_news("NVDA stock", max_results=10)
```

## Rate Limiting

Toutes les sources externes ont du rate limiting :

| Source | Limite | Implémentation |
|--------|--------|----------------|
| yfinance | 2000/h | Built-in |
| SEC EDGAR | 10/sec | `tenacity` retry |
| DuckDuckGo | 20/min | `slowapi` |

### Exemple avec tenacity

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10)
)
def fetch_with_retry():
    ...
```

## Ressources

- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [SEC EDGAR](https://www.sec.gov/developer)
- [DuckDuckGo Search](https://github.com/deedy5/duckduckgo_search)
