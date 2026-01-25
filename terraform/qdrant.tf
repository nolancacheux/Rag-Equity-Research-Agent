# -----------------------------------------------------------------------------
# Qdrant Vector Database - Container Instance
# -----------------------------------------------------------------------------

resource "azurerm_container_group" "qdrant" {
  name                = "${var.project_name}-qdrant"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  ip_address_type     = "Public"
  dns_name_label      = "${var.project_name}-qdrant"

  container {
    name   = "qdrant"
    image  = "qdrant/qdrant:latest"
    cpu    = var.qdrant_cpu
    memory = var.qdrant_memory

    ports {
      port     = 6333
      protocol = "TCP"
    }

    ports {
      port     = 6334
      protocol = "TCP"
    }

    # Persistence via Azure Files (optional, uncomment to enable)
    # volume {
    #   name                 = "qdrant-data"
    #   mount_path           = "/qdrant/storage"
    #   storage_account_name = azurerm_storage_account.main.name
    #   storage_account_key  = azurerm_storage_account.main.primary_access_key
    #   share_name           = azurerm_storage_share.qdrant.name
    # }
  }

  tags = var.tags
}

# Optional: Azure Files for Qdrant persistence
# Uncomment if you need data persistence across container restarts

# resource "azurerm_storage_account" "main" {
#   name                     = "${replace(var.project_name, "-", "")}storage"
#   resource_group_name      = azurerm_resource_group.main.name
#   location                 = azurerm_resource_group.main.location
#   account_tier             = "Standard"
#   account_replication_type = "LRS"
#   tags                     = var.tags
# }

# resource "azurerm_storage_share" "qdrant" {
#   name                 = "qdrant-data"
#   storage_account_name = azurerm_storage_account.main.name
#   quota                = 5  # GB
# }
