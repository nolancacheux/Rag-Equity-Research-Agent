# -----------------------------------------------------------------------------
# Remote State Backend - Azure Storage
# -----------------------------------------------------------------------------
# 
# The tfstate contains sensitive data (keys, passwords).
# Store it in Azure Storage with encryption + locking.
#
# BOOTSTRAP (run once before terraform init):
#
#   # Create storage account for state
#   az group create -n terraform-state-rg -l swedencentral
#   az storage account create \
#     -n tfstateequityresearch \
#     -g terraform-state-rg \
#     -l swedencentral \
#     --sku Standard_LRS \
#     --encryption-services blob
#   az storage container create \
#     -n tfstate \
#     --account-name tfstateequityresearch
#
# Then uncomment the backend block below and run: terraform init -migrate-state
# -----------------------------------------------------------------------------

# Uncomment after creating the storage account:
# terraform {
#   backend "azurerm" {
#     resource_group_name  = "terraform-state-rg"
#     storage_account_name = "tfstateequityresearch"
#     container_name       = "tfstate"
#     key                  = "equity-research.tfstate"
#   }
# }
