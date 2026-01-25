# LangGraph Orchestration

## Pourquoi LangGraph ?

LangGraph orchestre les différents agents de recherche financière dans un workflow structuré et déterministe.

### Avantages par rapport à LangChain classique

| Critère | LangGraph | LangChain Agents |
|---------|-----------|------------------|
| **Contrôle du flux** | Explicite (graphe) | Implicite (LLM décide) |
| **Déterminisme** | Élevé | Variable |
| **Debugging** | Facile (visualisation) | Difficile |
| **État partagé** | Natif (TypedDict) | Manuel |
| **Coûts LLM** | Prévisibles | Imprévisibles |

### Raisons du choix

1. **Workflow financier structuré** : L'ordre des analyses est important (data → docs → news → synthèse)
2. **État typé** : TypedDict garantit la cohérence des données entre agents
3. **Debugging** : Visualisation claire du flux pour identifier les erreurs
4. **Coûts maîtrisés** : Pas de boucles infinies possibles

## Architecture du graphe

```
[parse_query] → [market_data] → [document_reader?] → [news_sentiment] → [synthesizer] → END
                                       ↓
                              (skip si pas de doc queries)
```

### Nodes

| Node | Responsabilité | Input | Output |
|------|----------------|-------|--------|
| `parse_query` | Extraction tickers + queries | `query` | `tickers`, `document_queries` |
| `market_data` | Prix, fondamentaux yfinance | `tickers` | `market_data` |
| `document_reader` | RAG sur SEC filings | `tickers`, `document_queries` | `document_analysis` |
| `news_sentiment` | Analyse sentiment news | `tickers` | `news_analysis` |
| `synthesizer` | Rapport final LLM | Tous les outputs | `report` |

## État du graphe (ResearchState)

```python
class ResearchState(TypedDict, total=False):
    # Input
    query: str
    tickers: list[str]
    document_queries: list[str]
    
    # Agent outputs
    market_data: dict[str, Any] | None
    document_analysis: list[dict[str, Any]] | None
    news_analysis: list[dict[str, Any]] | None
    
    # Final output
    report: dict[str, Any] | None
    
    # Errors
    errors: list[str]
```

## Utilisation

### Recherche asynchrone

```python
from src.agents.graph import run_research

result = await run_research(
    query="Analyze NVDA and check their 10-K for China risks",
    tickers=["NVDA"]  # Optionnel, auto-détecté sinon
)

print(result["report"])
```

### Recherche synchrone

```python
from src.agents.graph import run_research_sync

result = run_research_sync("Compare AAPL and MSFT revenue growth")
```

## Edges conditionnels

Le graphe inclut une logique conditionnelle :

```python
def should_analyze_documents(state: ResearchState) -> str:
    """Skip document analysis si pas de queries documentaires."""
    if state.get("document_queries"):
        return "document_reader"
    return "news_sentiment"  # Skip direct vers news
```

## Tracing avec LangSmith

Activé via variables d'environnement :

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_xxx
LANGCHAIN_PROJECT=equity-research-agent
```

Permet de visualiser :
- Temps d'exécution par node
- Tokens consommés
- Erreurs et retries

## Ressources

- [Documentation LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangSmith](https://smith.langchain.com/)
