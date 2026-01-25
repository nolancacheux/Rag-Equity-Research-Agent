# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "equity-research"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "swedencentral"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    project     = "equity-research-agent"
    managed_by  = "terraform"
  }
}

# -----------------------------------------------------------------------------
# Azure OpenAI
# -----------------------------------------------------------------------------

variable "openai_sku" {
  description = "Azure OpenAI SKU"
  type        = string
  default     = "S0"
}

variable "openai_deployments" {
  description = "Azure OpenAI model deployments"
  type = list(object({
    name     = string
    model    = string
    version  = string
    capacity = number
  }))
  default = [
    {
      name     = "gpt-4o-mini"
      model    = "gpt-4o-mini"
      version  = "2024-07-18"
      capacity = 10
    },
    {
      name     = "text-embedding-ada-002"
      model    = "text-embedding-ada-002"
      version  = "2"
      capacity = 10
    }
  ]
}

# -----------------------------------------------------------------------------
# Container App
# -----------------------------------------------------------------------------

variable "container_app_cpu" {
  description = "CPU cores for container app"
  type        = number
  default     = 0.5
}

variable "container_app_memory" {
  description = "Memory (Gi) for container app"
  type        = string
  default     = "1Gi"
}

variable "container_app_min_replicas" {
  description = "Minimum replicas (0 for scale to zero)"
  type        = number
  default     = 0
}

variable "container_app_max_replicas" {
  description = "Maximum replicas (keep low to control costs)"
  type        = number
  default     = 1
}

# -----------------------------------------------------------------------------
# Qdrant
# -----------------------------------------------------------------------------

variable "qdrant_cpu" {
  description = "CPU cores for Qdrant"
  type        = number
  default     = 1
}

variable "qdrant_memory" {
  description = "Memory (GB) for Qdrant"
  type        = number
  default     = 2
}

# -----------------------------------------------------------------------------
# Telegram Bot
# -----------------------------------------------------------------------------

variable "telegram_bot_cpu" {
  description = "CPU cores for Telegram bot"
  type        = number
  default     = 0.25
}

variable "telegram_bot_memory" {
  description = "Memory (Gi) for Telegram bot"
  type        = string
  default     = "0.5Gi"
}

# -----------------------------------------------------------------------------
# Secrets (sensitive - use tfvars or env vars)
# -----------------------------------------------------------------------------

variable "sec_user_agent" {
  description = "SEC EDGAR User-Agent email"
  type        = string
  sensitive   = true
  default     = ""
}

variable "telegram_bot_token" {
  description = "Telegram Bot API token from @BotFather"
  type        = string
  sensitive   = true
}
