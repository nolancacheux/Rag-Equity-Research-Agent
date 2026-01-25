# -----------------------------------------------------------------------------
# Container Apps Environment
# -----------------------------------------------------------------------------

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

resource "azurerm_container_app_environment" "main" {
  name                       = "${var.project_name}-env"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = var.tags
}

# -----------------------------------------------------------------------------
# Container App - Main API
# -----------------------------------------------------------------------------

resource "azurerm_container_app" "api" {
  name                         = "${var.project_name}-agent"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  # Registry credentials
  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  # Secrets
  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  secret {
    name  = "azure-openai-key"
    value = azurerm_cognitive_account.openai.primary_access_key
  }

  # Ingress
  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  # Container template
  template {
    min_replicas = var.container_app_min_replicas
    max_replicas = var.container_app_max_replicas

    container {
      name   = "api"
      image  = "${azurerm_container_registry.main.login_server}/equity-research-api:latest"
      cpu    = var.container_app_cpu
      memory = var.container_app_memory

      # Environment variables
      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = azurerm_cognitive_account.openai.endpoint
      }

      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-key"
      }

      env {
        name  = "AZURE_OPENAI_DEPLOYMENT"
        value = "gpt-4o-mini"
      }

      env {
        name  = "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        value = "text-embedding-ada-002"
      }

      env {
        name  = "OPENAI_API_VERSION"
        value = "2024-08-01-preview"
      }

      env {
        name  = "QDRANT_URL"
        value = "http://${azurerm_container_group.qdrant.ip_address}:6333"
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      # Probes
      liveness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 8000
      }

      readiness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 8000
      }
    }
  }

  tags = var.tags
}

# -----------------------------------------------------------------------------
# Container App - Telegram Bot
# -----------------------------------------------------------------------------

resource "azurerm_container_app" "telegram_bot" {
  name                         = "${var.project_name}-telegram-bot"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  # Registry credentials
  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  # Secrets
  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  secret {
    name  = "azure-openai-key"
    value = azurerm_cognitive_account.openai.primary_access_key
  }

  secret {
    name  = "telegram-bot-token"
    value = var.telegram_bot_token
  }

  # No ingress - bot uses outbound polling only

  # Container template
  template {
    min_replicas = 1 # Bot should always run
    max_replicas = 1 # Single instance to avoid duplicate messages

    container {
      name   = "telegram-bot"
      image  = "${azurerm_container_registry.main.login_server}/equity-research-telegram-bot:latest"
      cpu    = var.telegram_bot_cpu
      memory = var.telegram_bot_memory

      # Environment variables
      env {
        name        = "TELEGRAM_BOT_TOKEN"
        secret_name = "telegram-bot-token"
      }

      env {
        name  = "API_BASE_URL"
        value = "https://${azurerm_container_app.api.ingress[0].fqdn}"
      }

      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = azurerm_cognitive_account.openai.endpoint
      }

      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-key"
      }

      env {
        name  = "AZURE_OPENAI_DEPLOYMENT"
        value = "gpt-4o-mini"
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }
    }
  }

  tags = var.tags

  depends_on = [azurerm_container_app.api]
}
