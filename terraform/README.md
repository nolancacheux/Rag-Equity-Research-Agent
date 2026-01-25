# Terraform Infrastructure

Infrastructure as Code for Equity Research Agent on Azure.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Resource Group                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Key Vault │  │ Azure OpenAI│  │ Container Registry  │  │
│  │   (secrets) │  │ (LLM + Emb) │  │      (images)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Container Apps Environment                  ││
│  │  ┌─────────────────────────────────────────────────┐    ││
│  │  │            equity-research-agent                 │    ││
│  │  │              (FastAPI + LangGraph)               │    ││
│  │  └─────────────────────────────────────────────────┘    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Qdrant (Container Instance)                 ││
│  │                  (Vector Database)                       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. [Terraform](https://terraform.io) >= 1.5.0
2. [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) logged in
3. Azure subscription with required permissions

## Quick Start

```bash
# 1. Login to Azure
az login

# 2. Bootstrap remote state (first time only)
az group create -n terraform-state-rg -l swedencentral
az storage account create \
  -n tfstateequityresearch \
  -g terraform-state-rg \
  -l swedencentral \
  --sku Standard_LRS \
  --encryption-services blob
az storage container create \
  -n tfstate \
  --account-name tfstateequityresearch

# 3. Uncomment backend block in backend.tf, then:
terraform init

# 4. Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 5. Preview changes
terraform plan

# 6. Apply infrastructure
terraform apply

# 7. Get outputs
terraform output
```

## Remote State

The tfstate file contains sensitive data (API keys, passwords). **Never commit it to git.**

State is stored in Azure Blob Storage with:
- Encryption at rest
- State locking (prevents concurrent modifications)
- Versioning (rollback capability)

See `backend.tf` for configuration.

## Files

| File | Description |
|------|-------------|
| `versions.tf` | Terraform and provider versions |
| `variables.tf` | Input variables |
| `outputs.tf` | Output values |
| `resource_group.tf` | Azure Resource Group |
| `key_vault.tf` | Azure Key Vault for secrets |
| `openai.tf` | Azure OpenAI resource |
| `container_registry.tf` | Azure Container Registry |
| `container_apps.tf` | Container Apps Environment + App |
| `qdrant.tf` | Qdrant Container Instance |

## Secrets Management

Secrets are stored in Azure Key Vault, not in plain environment variables.

**How it works:**
1. Terraform creates Key Vault and stores secrets
2. Container App references secrets from Key Vault
3. No secrets in code or Terraform state (keys are auto-generated)

**Sensitive outputs:**
```bash
# View sensitive values (careful!)
terraform output -json | jq '.openai_api_key.value'
```

## Deploy Application

After infrastructure is ready:

```bash
# Get ACR name
ACR_NAME=$(terraform output -raw acr_login_server | cut -d. -f1)

# Build and push image
az acr build --registry $ACR_NAME --image equity-research-agent:v1 ..

# Update container app
terraform output deploy_commands
```

## Destroy

```bash
# Preview destruction
terraform plan -destroy

# Destroy all resources
terraform destroy
```

## Cost Estimation

| Resource | SKU | ~Monthly Cost |
|----------|-----|---------------|
| Container Apps | Consumption | $0-20 (scale to zero) |
| Azure OpenAI | S0 | Pay per token |
| Container Registry | Basic | ~$5 |
| Container Instance (Qdrant) | 1 CPU / 2GB | ~$35 |
| Key Vault | Standard | ~$0.03/10k ops |
| **Total** | | **~$40-60/month** |

## Troubleshooting

### Terraform init fails
```bash
# Clear cache and retry
rm -rf .terraform .terraform.lock.hcl
terraform init
```

### Permission denied
```bash
# Check current account
az account show

# Re-authenticate
az login
```

### Container App not starting
```bash
# Check logs
az containerapp logs show --name equity-research-agent --resource-group equity-research-rg
```
