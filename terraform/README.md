# Terraform Infrastructure

Azure infrastructure for the Equity Research Agent.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure Container Apps                          │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐   │
│  │     API Container       │  │   Telegram Bot Container    │   │
│  │   (equity-research-api) │  │ (equity-research-telegram)  │   │
│  │                         │  │                             │   │
│  │  - FastAPI              │  │  - python-telegram-bot      │   │
│  │  - All endpoints        │  │  - Polling mode             │   │
│  │  - Auto-scale 0-3       │  │  - Single instance          │   │
│  └───────────┬─────────────┘  └──────────────┬──────────────┘   │
│              │                               │                   │
│              └───────────────┬───────────────┘                   │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Azure OpenAI   │   │     Qdrant      │   │   Key Vault     │
│  (Sweden)       │   │ (Container Grp) │   │   (Secrets)     │
│                 │   │                 │   │                 │
│  - gpt-4o-mini  │   │  - Vector DB    │   │  - API keys     │
│  - ada-002      │   │  - 6333 port    │   │  - Bot token    │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

## Resources Created

| Resource | Type | Purpose |
|----------|------|---------|
| Resource Group | `azurerm_resource_group` | Container for all resources |
| Container Registry | `azurerm_container_registry` | Docker images |
| Container Apps Env | `azurerm_container_app_environment` | Serverless container runtime |
| API Container App | `azurerm_container_app` | FastAPI backend |
| Bot Container App | `azurerm_container_app` | Telegram bot |
| Qdrant | `azurerm_container_group` | Vector database |
| Azure OpenAI | `azurerm_cognitive_account` | LLM + embeddings |
| Key Vault | `azurerm_key_vault` | Secrets management |
| Log Analytics | `azurerm_log_analytics_workspace` | Logging |

## Prerequisites

1. Azure CLI installed and logged in:
```bash
az login
az account set --subscription "Your Subscription"
```

2. Terraform installed (v1.5+):
```bash
terraform --version
```

## Quick Start

```bash
# 1. Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 2. Initialize Terraform
terraform init

# 3. Preview changes
terraform plan

# 4. Apply (creates resources)
terraform apply
```

## Variables

### Required

| Variable | Description |
|----------|-------------|
| `telegram_bot_token` | Telegram bot token from @BotFather |

### Recommended

| Variable | Description |
|----------|-------------|
| `sec_user_agent` | SEC EDGAR User-Agent (email) |
| `api_secret_key` | API auth key (`openssl rand -hex 32`) |

### Optional

| Variable | Description |
|----------|-------------|
| `groq_api_key` | Groq API key (free LLM alternative) |
| `langchain_api_key` | LangSmith tracing key |

### Infrastructure

| Variable | Default | Description |
|----------|---------|-------------|
| `project_name` | `equity-research` | Resource naming prefix |
| `location` | `swedencentral` | Azure region |
| `container_app_min_replicas` | `0` | Scale to zero |
| `container_app_max_replicas` | `1` | Max instances |
| `container_app_cpu` | `0.5` | CPU cores |
| `container_app_memory` | `1Gi` | Memory |

## Environment Variables

The containers are configured with these env vars:

### API Container
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` - Azure OpenAI key (from secret)
- `AZURE_OPENAI_DEPLOYMENT` - Model deployment name
- `QDRANT_URL` - Qdrant vector DB URL
- `API_SECRET_KEY` - API authentication (from secret)
- `GROQ_API_KEY` - Optional Groq key (from secret)
- `LANGCHAIN_API_KEY` - Optional LangSmith (from secret)
- `SEC_USER_AGENT` - SEC EDGAR identifier

### Bot Container
- `TELEGRAM_BOT_TOKEN` - Bot token (from secret)
- `API_BASE_URL` - Internal API URL
- `API_SECRET_KEY` - API authentication (from secret)

## Using Secrets Securely

For CI/CD, use environment variables instead of tfvars:

```bash
export TF_VAR_telegram_bot_token="123456789:ABC..."
export TF_VAR_api_secret_key="$(openssl rand -hex 32)"
export TF_VAR_sec_user_agent="YourApp your@email.com"

terraform apply
```

## Costs

Estimated monthly cost (Sweden Central, minimal usage):

| Resource | Cost |
|----------|------|
| Container Apps (scale to zero) | ~$0-5 |
| Container Registry (Basic) | ~$5 |
| Azure OpenAI (10K tokens/min) | ~$0-10 |
| Qdrant (Container Instance) | ~$15-30 |
| Log Analytics | ~$0-5 |
| **Total** | **~$20-50/month** |

With Azure Student credits ($100/year): essentially free.

## Outputs

After `terraform apply`:

```bash
# Get outputs
terraform output

# Key outputs:
# - api_url: https://equity-research-agent.xxx.azurecontainerapps.io
# - acr_login_server: xxx.azurecr.io
```

## Updating

After code changes:

```bash
# Build and push new images
docker build -t $ACR_URL/equity-research-api:latest -f Dockerfile.api .
docker push $ACR_URL/equity-research-api:latest

# Restart containers to pull new images
az containerapp revision restart -n equity-research-agent -g equity-research-rg
```

## Destroying

```bash
# Remove all resources
terraform destroy

# Or just specific resources
terraform destroy -target=azurerm_container_app.api
```

## Files

| File | Purpose |
|------|---------|
| `versions.tf` | Provider versions |
| `variables.tf` | Variable definitions |
| `terraform.tfvars.example` | Example values |
| `resource_group.tf` | Resource group |
| `container_registry.tf` | ACR |
| `container_apps.tf` | API + Bot containers |
| `qdrant.tf` | Vector database |
| `openai.tf` | Azure OpenAI |
| `key_vault.tf` | Secrets |
| `outputs.tf` | Output values |
