param name string
param location string
param tags object
param environmentId string
param appIdentityResourceId string
param appIdentityClientId string
param acrLoginServer string
param storageAccountName string
param cosmosAccountName string
param cosmosDatabaseName string
param cosmosContainerName string
param keyVaultName string
param appInsightsConnectionString string
param entraTenantId string

@description('List of AI service FQDNs (internal). Each: { name, fqdn }')
param aiServiceEndpoints array

@description('Container image for the API. Replaced by azd at deploy time.')
param apiImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

var endpointEnvVars = [for ep in aiServiceEndpoints: {
  name: 'AI_${toUpper(replace(ep.name, '-', '_'))}_ENDPOINT'
  value: 'https://${ep.fqdn}'
}]

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'api' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${appIdentityResourceId}': {} }
  }
  properties: {
    environmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: acrLoginServer
          identity: appIdentityResourceId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: concat([
            { name: 'MODE', value: 'connected' }
            { name: 'USE_MANAGED_IDENTITY', value: 'true' }
            { name: 'AZURE_CLIENT_ID', value: appIdentityClientId }
            { name: 'AZURE_TENANT_ID', value: entraTenantId }
            { name: 'STORAGE_ACCOUNT_NAME', value: storageAccountName }
            { name: 'COSMOS_ACCOUNT_NAME', value: cosmosAccountName }
            { name: 'COSMOS_DATABASE_NAME', value: cosmosDatabaseName }
            { name: 'COSMOS_CONTAINER_NAME', value: cosmosContainerName }
            { name: 'KEY_VAULT_NAME', value: keyVaultName }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
          ], endpointEnvVars)
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output fqdn string = app.properties.configuration.ingress.fqdn
output name string = app.name
