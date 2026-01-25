# CI/CD Setup Guide

This project uses GitHub Actions with Terraform for fully automated deployments.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Pull Request                              │
├─────────────────────────────────────────────────────────────────┤
│  Lint ──▶ Test ──▶ Security ──▶ Terraform Plan ──▶ Build        │
│                                      │                           │
│                              (Plan uploaded as artifact)         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Merge to Main                               │
├─────────────────────────────────────────────────────────────────┤
│  Lint ──▶ Test ──▶ Security ──▶ Terraform Plan                  │
│                                      │                           │
│                                      ▼                           │
│                              Terraform Apply                     │
│                                      │                           │
│                                      ▼                           │
│                              Deploy Images                       │
│                              (API + Bot)                         │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Azure Service Principal

Create a service principal for GitHub Actions:

```bash
# Create SP with Contributor role
az ad sp create-for-rbac \
  --name "github-actions-equity-research" \
  --role Contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID> \
  --sdk-auth
```

Save the JSON output - you'll need it for `AZURE_CREDENTIALS`.

### 2. Terraform State Backend

Create the storage account for Terraform state:

```bash
# Create resource group
az group create -n terraform-state-rg -l swedencentral

# Create storage account
az storage account create \
  -n tfstateequityresearch \
  -g terraform-state-rg \
  -l swedencentral \
  --sku Standard_LRS \
  --encryption-services blob

# Create container
az storage container create \
  -n tfstate \
  --account-name tfstateequityresearch

# Grant SP access to storage
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee <SP_CLIENT_ID> \
  --scope /subscriptions/<SUB_ID>/resourceGroups/terraform-state-rg
```

### 3. GitHub Secrets

Go to **Settings > Secrets and variables > Actions** and add:

| Secret | Description | How to get |
|--------|-------------|------------|
| `ARM_CLIENT_ID` | Service Principal App ID | From `az ad sp create-for-rbac` output |
| `ARM_CLIENT_SECRET` | Service Principal Password | From `az ad sp create-for-rbac` output |
| `ARM_SUBSCRIPTION_ID` | Azure Subscription ID | `az account show --query id` |
| `ARM_TENANT_ID` | Azure AD Tenant ID | `az account show --query tenantId` |
| `AZURE_CREDENTIALS` | Full SP JSON | Entire output of `az ad sp create-for-rbac --sdk-auth` |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Create bot on Telegram |
| `SEC_USER_AGENT` | SEC EDGAR identifier | `"AppName your-email@example.com"` |

### 4. GitHub Environment

Create a `production` environment:

1. Go to **Settings > Environments > New environment**
2. Name: `production`
3. (Optional) Add required reviewers for manual approval
4. (Optional) Restrict to `main` branch

## First Deployment

After setting up secrets:

```bash
# Initialize Terraform locally first (to create initial state)
cd terraform
terraform init
terraform plan -var="telegram_bot_token=YOUR_TOKEN" -var="sec_user_agent=YOUR_EMAIL"
terraform apply

# Push to trigger CI/CD
git push origin main
```

## Workflow Jobs

| Job | Trigger | Description |
|-----|---------|-------------|
| `lint` | PR + Push | Ruff linter and formatter |
| `test` | PR + Push | Pytest with coverage |
| `security` | PR + Push | Bandit security scan |
| `terraform-plan` | PR + Push | Plan infrastructure changes |
| `build` | PR + Push | Build Docker images (no push) |
| `terraform-apply` | Push to main | Apply infrastructure |
| `deploy-images` | Push to main | Build, push, and deploy containers |

## Troubleshooting

### Terraform state lock

If a pipeline fails mid-apply, the state might be locked:

```bash
az storage blob lease break \
  --blob-name equity-research.tfstate \
  --container-name tfstate \
  --account-name tfstateequityresearch
```

### ACR authentication issues

Ensure the SP has `AcrPush` role on the Container Registry:

```bash
az role assignment create \
  --role AcrPush \
  --assignee <SP_CLIENT_ID> \
  --scope /subscriptions/<SUB_ID>/resourceGroups/equity-research-rg/providers/Microsoft.ContainerRegistry/registries/<ACR_NAME>
```

### Container App not updating

Force a new revision:

```bash
az containerapp revision restart \
  --name equity-research-api \
  --resource-group equity-research-rg \
  --revision <REVISION_NAME>
```

## Cost Optimization

The pipeline uses:
- **GitHub Actions**: Free for public repos, 2000 min/month for private
- **Azure Container Apps**: Scale to zero when idle
- **Terraform State**: ~$0.01/month for storage

To minimize costs, Container Apps are configured with `min_replicas = 0` for the API (scales to zero when idle). The Telegram bot always runs (`min_replicas = 1`).
