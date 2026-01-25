# -----------------------------------------------------------------------------
# Key Vault - Secure secrets storage
# -----------------------------------------------------------------------------

data "azurerm_client_config" "current" {}

resource "random_string" "kv_suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_key_vault" "main" {
  name                = "${var.project_name}-kv-${random_string.kv_suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Enable Azure RBAC for access (recommended over access policies)
  enable_rbac_authorization = true

  # Soft delete settings
  soft_delete_retention_days = 7
  purge_protection_enabled   = false  # Set to true in production

  tags = var.tags
}

# Grant current user/SP access to manage secrets
resource "azurerm_role_assignment" "kv_admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

# -----------------------------------------------------------------------------
# Secrets - Values set manually or via CI/CD (not in state)
# -----------------------------------------------------------------------------

# Placeholder for Azure OpenAI API Key (populated after OpenAI resource created)
resource "azurerm_key_vault_secret" "openai_api_key" {
  name         = "azure-openai-api-key"
  value        = azurerm_cognitive_account.openai.primary_access_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.kv_admin]
}

# SEC User Agent (optional)
resource "azurerm_key_vault_secret" "sec_user_agent" {
  count        = var.sec_user_agent != "" ? 1 : 0
  name         = "sec-user-agent"
  value        = var.sec_user_agent
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.kv_admin]
}
