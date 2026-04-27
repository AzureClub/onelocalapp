param name string
param location string
param tags object
param environmentId string
param image string
param cpu string
param memory string
param targetPort int
param keyVaultName string
param apiKeySecretName string
param billingEndpointSecretName string
param appIdentityResourceId string

@description('Mode for AI container: connected (Eula+Billing+ApiKey) or disconnected (license file mounted).')
@allowed([ 'connected', 'disconnected' ])
param mode string = 'connected'

resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = {
  name: keyVaultName
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': name })
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
        targetPort: targetPort
        transport: 'http'
        allowInsecure: false
      }
      secrets: [
        {
          name: 'ai-api-key'
          keyVaultUrl: '${kv.properties.vaultUri}secrets/${apiKeySecretName}'
          identity: appIdentityResourceId
        }
        {
          name: 'ai-billing'
          keyVaultUrl: '${kv.properties.vaultUri}secrets/${billingEndpointSecretName}'
          identity: appIdentityResourceId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'ai'
          image: image
          resources: { cpu: json(cpu), memory: memory }
          env: [
            { name: 'Eula', value: 'accept' }
            { name: 'Billing', secretRef: 'ai-billing' }
            { name: 'ApiKey', secretRef: 'ai-api-key' }
            { name: 'Mode', value: mode }
          ]
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 2 }
    }
  }
}

output fqdn string = app.properties.configuration.ingress.fqdn
output name string = app.name
