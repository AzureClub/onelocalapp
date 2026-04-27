param name string
param location string
param tags object
param environmentId string
param appIdentityResourceId string
param appIdentityClientId string
param acrLoginServer string
param apiBaseUrl string
param appInsightsConnectionString string
param entraTenantId string

param webImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'web' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${appIdentityResourceId}': {} }
  }
  properties: {
    environmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 3000
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
          name: 'web'
          image: webImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'API_BASE_URL', value: apiBaseUrl }
            { name: 'AZURE_CLIENT_ID', value: appIdentityClientId }
            { name: 'AZURE_TENANT_ID', value: entraTenantId }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
            { name: 'NEXT_TELEMETRY_DISABLED', value: '1' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output fqdn string = app.properties.configuration.ingress.fqdn
output name string = app.name
