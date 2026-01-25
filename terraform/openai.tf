# -----------------------------------------------------------------------------
# Azure OpenAI
# -----------------------------------------------------------------------------

resource "azurerm_cognitive_account" "openai" {
  name                  = "${var.project_name}-openai"
  location              = azurerm_resource_group.main.location
  resource_group_name   = azurerm_resource_group.main.name
  kind                  = "OpenAI"
  sku_name              = var.openai_sku
  custom_subdomain_name = "${var.project_name}-openai"

  tags = var.tags
}

# Model deployments
resource "azurerm_cognitive_deployment" "models" {
  for_each = { for d in var.openai_deployments : d.name => d }

  name                 = each.value.name
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = each.value.model
    version = each.value.version
  }

  sku {
    name     = "Standard"
    capacity = each.value.capacity
  }
}
