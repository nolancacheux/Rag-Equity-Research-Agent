# Azure Deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Azure Container Apps                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │   Main App   │   │    Redis     │   │   Qdrant     │    │
│  │   (FastAPI)  │──▶│   (Cache)    │   │  (Vectors)   │    │
│  │   :8000      │   │   :6379      │   │  :6333       │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│         │                                                   │
│    ┌────┴────┐                                             │
│    │ Ingress │◀─── HTTPS                                   │
│    └─────────┘                                             │
├─────────────────────────────────────────────────────────────┤
│  Container Registry │ Log Analytics │ Managed Environment   │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Azure CLI** installé et connecté
2. **Docker** installé localement
3. **Variables d'environnement** :
   - `OPENAI_API_KEY` (requis)
   - `LANGSMITH_API_KEY` (optionnel)

## Quick Deploy

```bash
# Set required env vars
export OPENAI_API_KEY="sk-xxx"
export LANGSMITH_API_KEY="ls-xxx"  # optional

# Deploy
chmod +x infra/deploy.sh
./infra/deploy.sh
```

## Manual Deployment

### 1. Create Resource Group

```bash
az group create \
    --name equity-research-rg \
    --location westeurope
```

### 2. Deploy Infrastructure

```bash
az deployment group create \
    --resource-group equity-research-rg \
    --template-file infra/main.bicep \
    --parameters \
        environmentName=dev \
        openaiApiKey=$OPENAI_API_KEY
```

### 3. Build & Push Image

```bash
# Get registry name
REGISTRY=$(az acr list --resource-group equity-research-rg --query "[0].loginServer" -o tsv)

# Login to registry
az acr login --name ${REGISTRY%%.*}

# Build and push
docker build -t $REGISTRY/equity-research-agent:latest .
docker push $REGISTRY/equity-research-agent:latest
```

### 4. Update Container App

```bash
az containerapp update \
    --name equity-research-agent \
    --resource-group equity-research-rg \
    --image $REGISTRY/equity-research-agent:latest
```

## CI/CD with GitHub Actions

Le workflow `.github/workflows/ci.yml` inclut un job de déploiement Azure.

### Secrets GitHub requis

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Service principal JSON |
| `OPENAI_API_KEY` | Clé API OpenAI |
| `LANGSMITH_API_KEY` | Clé API LangSmith (optionnel) |

### Créer le Service Principal

```bash
az ad sp create-for-rbac \
    --name "equity-research-agent-sp" \
    --role contributor \
    --scopes /subscriptions/{subscription-id}/resourceGroups/equity-research-rg \
    --sdk-auth
```

Copier le JSON output dans le secret `AZURE_CREDENTIALS`.

## Coûts estimés

| Resource | SKU | Coût estimé/mois |
|----------|-----|------------------|
| Container Apps | Consumption | ~$10-30 |
| Container Registry | Basic | ~$5 |
| Log Analytics | Pay-as-you-go | ~$2-5 |

**Total estimé**: ~$17-40/mois (selon utilisation)

## Scaling

Le déploiement utilise le scaling HTTP automatique :
- **Min replicas**: 0 (scale to zero)
- **Max replicas**: 3
- **Trigger**: 10 requêtes concurrentes

## Monitoring

### Logs

```bash
az containerapp logs show \
    --name equity-research-agent \
    --resource-group equity-research-rg \
    --follow
```

### Metrics

Disponibles dans Azure Portal > Container App > Metrics :
- Requests per second
- CPU/Memory usage
- Response times

## Cleanup

```bash
az group delete --name equity-research-rg --yes --no-wait
```
