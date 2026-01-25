#!/bin/bash
# =============================================================================
# Deploy Equity Research Agent to Azure
# =============================================================================
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Load environment variables if .env exists
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    log "Loading .env file..."
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Required variables
: "${TELEGRAM_BOT_TOKEN:?Error: TELEGRAM_BOT_TOKEN is not set}"

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------
check_prerequisites() {
    log "Checking prerequisites..."
    
    command -v az >/dev/null 2>&1 || error "Azure CLI not installed"
    command -v terraform >/dev/null 2>&1 || error "Terraform not installed"
    command -v docker >/dev/null 2>&1 || error "Docker not installed"
    
    # Check Azure login
    az account show >/dev/null 2>&1 || error "Not logged in to Azure. Run 'az login'"
    
    log "All prerequisites met"
}

terraform_init() {
    log "Initializing Terraform..."
    cd "$TERRAFORM_DIR"
    terraform init -upgrade
}

terraform_plan() {
    log "Planning infrastructure changes..."
    cd "$TERRAFORM_DIR"
    terraform plan \
        -var="telegram_bot_token=$TELEGRAM_BOT_TOKEN" \
        -var="sec_user_agent=${SEC_USER_AGENT:-}" \
        -out=tfplan
}

terraform_apply() {
    log "Applying infrastructure changes..."
    cd "$TERRAFORM_DIR"
    terraform apply tfplan
}

build_and_push_images() {
    log "Building and pushing Docker images..."
    cd "$TERRAFORM_DIR"
    
    # Get ACR info from Terraform outputs
    ACR_NAME=$(terraform output -raw acr_login_server | cut -d'.' -f1)
    ACR_SERVER=$(terraform output -raw acr_login_server)
    RG_NAME=$(terraform output -raw resource_group_name)
    
    log "Building API image..."
    az acr build \
        --registry "$ACR_NAME" \
        --image equity-research-api:latest \
        --file "$PROJECT_ROOT/Dockerfile.api" \
        "$PROJECT_ROOT"
    
    log "Building Telegram Bot image..."
    az acr build \
        --registry "$ACR_NAME" \
        --image equity-research-telegram-bot:latest \
        --file "$PROJECT_ROOT/Dockerfile.bot" \
        "$PROJECT_ROOT"
}

update_containers() {
    log "Updating container apps..."
    cd "$TERRAFORM_DIR"
    
    RG_NAME=$(terraform output -raw resource_group_name)
    API_APP=$(terraform output -raw api_container_app_name)
    BOT_APP=$(terraform output -raw telegram_bot_container_app_name)
    ACR_SERVER=$(terraform output -raw acr_login_server)
    
    log "Updating API container..."
    az containerapp update \
        --name "$API_APP" \
        --resource-group "$RG_NAME" \
        --image "$ACR_SERVER/equity-research-api:latest"
    
    log "Updating Telegram Bot container..."
    az containerapp update \
        --name "$BOT_APP" \
        --resource-group "$RG_NAME" \
        --image "$ACR_SERVER/equity-research-telegram-bot:latest"
}

show_outputs() {
    log "Deployment complete!"
    cd "$TERRAFORM_DIR"
    
    echo ""
    echo "============================================="
    echo "              DEPLOYMENT INFO               "
    echo "============================================="
    echo ""
    echo "API URL: $(terraform output -raw api_url)"
    echo ""
    echo "Telegram Bot: @finance12383839Bot"
    echo ""
    echo "============================================="
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
main() {
    local command="${1:-full}"
    
    case "$command" in
        init)
            check_prerequisites
            terraform_init
            ;;
        plan)
            terraform_plan
            ;;
        apply)
            terraform_apply
            ;;
        build)
            build_and_push_images
            ;;
        update)
            update_containers
            ;;
        full)
            check_prerequisites
            terraform_init
            terraform_plan
            terraform_apply
            build_and_push_images
            update_containers
            show_outputs
            ;;
        *)
            echo "Usage: $0 {init|plan|apply|build|update|full}"
            exit 1
            ;;
    esac
}

main "$@"
