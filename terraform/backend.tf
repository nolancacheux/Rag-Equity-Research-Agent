terraform {
  backend "azurerm" {
    resource_group_name  = "equity-research-rg"
    storage_account_name = "tfstateequity2026"
    container_name       = "tfstate"
    key                  = "equity-research.tfstate"
  }
}
