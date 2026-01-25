// Azure Container Apps deployment for Equity Research Agent

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
param environmentName string = 'dev'

@description('Container image tag')
param imageTag string = 'latest'

@description('OpenAI API Key')
@secure()
param openaiApiKey string

@description('LangSmith API Key (optional)')
@secure()
param langsmithApiKey string = ''

var appName = 'equity-research-agent'
var containerRegistryName = 'cr${uniqueString(resourceGroup().id)}'
var containerAppsEnvName = '${appName}-env-${environmentName}'
var logAnalyticsName = '${appName}-logs-${environmentName}'

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Container Apps Environment
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppsEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Redis Container App
resource redisApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${appName}-redis'
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: false
        targetPort: 6379
        transport: 'tcp'
      }
    }
    template: {
      containers: [
        {
          name: 'redis'
          image: 'redis:7-alpine'
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          command: ['redis-server', '--appendonly', 'yes']
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

// Main App Container
resource mainApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      secrets: [
        {
          name: 'openai-api-key'
          value: openaiApiKey
        }
        {
          name: 'langsmith-api-key'
          value: langsmithApiKey
        }
      ]
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'registry-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'app'
          image: '${containerRegistry.properties.loginServer}/${appName}:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
            {
              name: 'LANGCHAIN_API_KEY'
              secretRef: 'langsmith-api-key'
            }
            {
              name: 'LANGCHAIN_TRACING_V2'
              value: 'true'
            }
            {
              name: 'LANGCHAIN_PROJECT'
              value: 'equity-research-agent'
            }
            {
              name: 'REDIS_URL'
              value: 'redis://${appName}-redis:6379'
            }
            {
              name: 'QDRANT_URL'
              value: 'http://${appName}-qdrant:6333'
            }
            {
              name: 'APP_ENV'
              value: environmentName
            }
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output appUrl string = 'https://${mainApp.properties.configuration.ingress.fqdn}'
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
