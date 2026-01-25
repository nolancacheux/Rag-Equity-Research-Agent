# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

# Resource Group
output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

# Container Registry
output "acr_login_server" {
  description = "ACR login server URL"
  value       = azurerm_container_registry.main.login_server
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = azurerm_container_registry.main.admin_username
}

output "acr_admin_password" {
  description = "ACR admin password"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

# Container App - API
output "api_url" {
  description = "API public URL"
  value       = "https://${azurerm_container_app.api.latest_revision_fqdn}"
}

output "api_container_app_name" {
  description = "API Container App name"
  value       = azurerm_container_app.api.name
}

# Container App - Telegram Bot
output "telegram_bot_container_app_name" {
  description = "Telegram Bot Container App name"
  value       = azurerm_container_app.telegram_bot.name
}

# Azure OpenAI
output "openai_endpoint" {
  description = "Azure OpenAI endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_api_key" {
  description = "Azure OpenAI API key"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

# Qdrant
output "qdrant_url" {
  description = "Qdrant REST API URL"
  value       = "http://${azurerm_container_group.qdrant.ip_address}:6333"
}

output "qdrant_fqdn" {
  description = "Qdrant FQDN"
  value       = azurerm_container_group.qdrant.fqdn
}

# Key Vault
output "key_vault_name" {
  description = "Key Vault name"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "Key Vault URI"
  value       = azurerm_key_vault.main.vault_uri
}

# -----------------------------------------------------------------------------
# Deployment commands (for reference)
# -----------------------------------------------------------------------------

output "deploy_commands" {
  description = "Commands to build and deploy"
  value = <<-EOT
    # Build and push API image
    az acr build --registry ${azurerm_container_registry.main.name} --image ${var.project_name}-api:latest --file Dockerfile.api ..
    
    # Build and push Telegram Bot image
    az acr build --registry ${azurerm_container_registry.main.name} --image ${var.project_name}-telegram-bot:latest --file Dockerfile.bot ..
    
    # Update API container
    az containerapp update --name ${azurerm_container_app.api.name} --resource-group ${azurerm_resource_group.main.name} --image ${azurerm_container_registry.main.login_server}/${var.project_name}-api:latest
    
    # Update Telegram Bot container
    az containerapp update --name ${azurerm_container_app.telegram_bot.name} --resource-group ${azurerm_resource_group.main.name} --image ${azurerm_container_registry.main.login_server}/${var.project_name}-telegram-bot:latest
  EOT
}
