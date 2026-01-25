# -----------------------------------------------------------------------------
# Azure Container Registry
# -----------------------------------------------------------------------------

resource "random_string" "acr_suffix" {
  length  = 8
  special = false
  upper   = false
  numeric = true
}

resource "azurerm_container_registry" "main" {
  name                = "${replace(var.project_name, "-", "")}acr${random_string.acr_suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true  # Required for Container Apps without managed identity

  tags = var.tags
}
