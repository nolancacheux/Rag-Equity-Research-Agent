# Azure Deployment

> **Recommended**: Use [Terraform](../terraform/README.md) for infrastructure management. This doc covers manual deployment.

## Current Production

| Resource | Value |
|----------|-------|
| **API URL** | https://equity-research-agent.thankfulhill-01e4fbbb.swedencentral.azurecontainerapps.io |
| **Resource Group** | equity-research-rg |
| **Location** | Sweden Central |
| **ACR** | equityresearchacrblipenk7.azurecr.io |
| **Key Vault** | eqres-kv-* |

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Azure Resource Group                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │             Azure Container Apps Environment            │    │
│   ├─────────────────────────────────────────────────────────┤    │
│   │  ┌──────────────────┐    ┌──────────────────┐          │    │
│   │  │   Main App       │    │   Qdrant         │          │    │
│   │  │   (FastAPI)      │───▶│   (Vectors)      │          │    │
│   │  │   :8000          │    │   :6333          │          │    │
│   │  └────────┬─────────┘    └──────────────────┘          │    │
│   │           │                                             │    │
│   │      ┌────┴────┐                                       │    │
│   │      │ Ingress │◀─── HTTPS                             │    │
│   │      └─────────┘                                       │    │
│   └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │              Azure OpenAI Service                       │    │
│   │  ┌──────────────────┐    ┌──────────────────┐          │    │
│   │  │   gpt-4o-mini    │    │   text-embedding │          │    │
│   │  │   (LLM)          │    │   -ada-002       │          │    │
│   │  └──────────────────┘    └──────────────────┘          │    │
│   └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│   ┌──────────────────┐    ┌──────────────────┐                   │
│   │ Container        │    │ Log Analytics    │                   │
│   │ Registry (ACR)   │    │ Workspace        │                   │
│   └──────────────────┘    └──────────────────┘                   │
└──────────────────────────────────────────────────────────────────┘
```

## Resources Deployed

| Resource | Purpose | SKU |
|----------|---------|-----|
| Container Apps | Host FastAPI app | Consumption |
| Container Registry | Store Docker images | Basic |
| Azure OpenAI | LLM + Embeddings | Standard |
| Container Instance | Qdrant vector DB | Standard |
| Log Analytics | Centralized logging | Pay-as-you-go |

## Prerequisites

1. **Azure CLI** installed and logged in
2. **Docker** installed locally (optional with ACR Tasks)
3. **Azure subscription** with credits (Azure for Students works)

## Deployment Options

### Option 1: Terraform (Recommended)

Infrastructure as Code - reproducible, versioned, secrets in Key Vault.

```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

See [terraform/README.md](../terraform/README.md) for details.

### Option 2: Manual (Below)

Step-by-step Azure CLI commands.

## Environment Variables

### Required for Container App

```bash
AZURE_OPENAI_ENDPOINT=https://equity-research-openai-se.openai.azure.com
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2024-02-01
QDRANT_URL=http://qdrant-vector-db:6333
```

## Deployment Steps

### 1. Build & Push Docker Image

```bash
# Login to ACR
az acr login --name cae661ada46dacr

# Build with ACR Tasks (recommended)
az acr build \
  --registry cae661ada46dacr \
  --image equity-research-agent:v6 \
  .
```

### 2. Update Container App

```bash
az containerapp update \
  --name equity-research-agent \
  --resource-group equity-research-rg \
  --image cae661ada46dacr.azurecr.io/equity-research-agent:v6
```

### 3. Set Environment Variables

```bash
az containerapp update \
  --name equity-research-agent \
  --resource-group equity-research-rg \
  --set-env-vars \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002 \
    AZURE_OPENAI_API_VERSION=2024-02-01
```

## Endpoints

| Service | URL |
|---------|-----|
| API | https://equity-research-agent.wonderfulstone-1de7f015.swedencentral.azurecontainerapps.io |
| Health | /health |
| Docs | /docs |

## Monitoring

### View Logs

```bash
az containerapp logs show \
  --name equity-research-agent \
  --resource-group equity-research-rg \
  --follow
```

### Check Status

```bash
az containerapp show \
  --name equity-research-agent \
  --resource-group equity-research-rg \
  --query "{status:properties.runningStatus, replicas:properties.template.scale}"
```

## Scaling Configuration

```yaml
scale:
  minReplicas: 0      # Scale to zero when idle
  maxReplicas: 3
  cooldownPeriod: 300  # 5 minutes
```

## Cost Optimization

1. **Scale to zero**: `minReplicas: 0` saves money when idle
2. **Consumption plan**: Pay only for actual usage
3. **Azure for Students**: $100 free credits
4. **Azure OpenAI**: Included in credits

## Troubleshooting

### Cold Start Issues

With `minReplicas: 0`, first request after idle period may take 10-30s.
Solutions:
- Set `minReplicas: 1` for always-on (costs more)
- Implement health check warmup

### Container Crash Loop

Check logs for errors:
```bash
az containerapp logs show --name equity-research-agent --resource-group equity-research-rg --tail 100
```

### Image Pull Errors

Verify ACR access:
```bash
az containerapp identity show --name equity-research-agent --resource-group equity-research-rg
```

## Cleanup

```bash
# Delete all resources
az group delete --name equity-research-rg --yes --no-wait
```

## Cost Control

### Container Apps Scaling
- `min_replicas = 0`: Scale to zero when idle
- `max_replicas = 1`: Limit concurrent instances

### Azure OpenAI
- Quota: 10K tokens/min (free tier)
- Model: gpt-4o-mini (cheapest)

### Budget Alerts (Manual Setup)
1. Go to Azure Portal > Cost Management + Billing
2. Create Budget: $10/month for equity-research-rg
3. Set alert at 80% threshold

### Estimated Monthly Cost (Low Usage)
| Resource | Cost |
|----------|------|
| Container Apps (idle) | ~$0 |
| Azure OpenAI (10K tokens) | ~$0.01 |
| Container Registry (Basic) | ~$5 |
| Storage (tfstate) | ~$0.02 |
| **Total** | **~$5-10/month** |
