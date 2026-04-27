targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment used to generate a short unique hash for resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Principal ID of the user/SP running azd (used for KV and Cosmos data plane access during dev).')
param principalId string = ''

@description('Tags applied to all resources.')
param tags object = {
  'azd-env-name': environmentName
  workload: 'onelocalapp'
}

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var rgName = '${abbrs.resourcesResourceGroups}${environmentName}'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: rgName
  location: location
  tags: tags
}

module network 'modules/network.bicep' = {
  scope: rg
  name: 'network'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
  }
}

module observability 'modules/observability.bicep' = {
  scope: rg
  name: 'observability'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
  }
}

module identity 'modules/identity.bicep' = {
  scope: rg
  name: 'identity'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
  }
}

module acr 'modules/acr.bicep' = {
  scope: rg
  name: 'acr'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    privateEndpointSubnetId: network.outputs.peSubnetId
    privateDnsZoneId: network.outputs.acrPrivateDnsZoneId
    appIdentityPrincipalId: identity.outputs.appIdentityPrincipalId
  }
}

module storage 'modules/storage.bicep' = {
  scope: rg
  name: 'storage'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    privateEndpointSubnetId: network.outputs.peSubnetId
    blobPrivateDnsZoneId: network.outputs.blobPrivateDnsZoneId
    appIdentityPrincipalId: identity.outputs.appIdentityPrincipalId
    devPrincipalId: principalId
  }
}

module cosmos 'modules/cosmos.bicep' = {
  scope: rg
  name: 'cosmos'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    privateEndpointSubnetId: network.outputs.peSubnetId
    cosmosPrivateDnsZoneId: network.outputs.cosmosPrivateDnsZoneId
    appIdentityPrincipalId: identity.outputs.appIdentityPrincipalId
    devPrincipalId: principalId
  }
}

module keyvault 'modules/keyvault.bicep' = {
  scope: rg
  name: 'keyvault'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    privateEndpointSubnetId: network.outputs.peSubnetId
    kvPrivateDnsZoneId: network.outputs.kvPrivateDnsZoneId
    appIdentityPrincipalId: identity.outputs.appIdentityPrincipalId
    devPrincipalId: principalId
  }
}

module cae 'modules/containerapps-env.bicep' = {
  scope: rg
  name: 'cae'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    infrastructureSubnetId: network.outputs.caeSubnetId
    logAnalyticsCustomerId: observability.outputs.logAnalyticsCustomerId
    logAnalyticsSharedKey: observability.outputs.logAnalyticsSharedKey
    appInsightsConnectionString: observability.outputs.appInsightsConnectionString
  }
}

@description('AI services to deploy as containers. image is the official MCR image.')
param aiServices array = [
  {
    name: 'speech-stt'
    image: 'mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:latest'
    cpu: '2.0'
    memory: '4Gi'
    targetPort: 5000
    serviceKey: 'speech'
  }
  {
    name: 'speech-tts'
    image: 'mcr.microsoft.com/azure-cognitive-services/speechservices/neural-text-to-speech:latest'
    cpu: '2.0'
    memory: '4Gi'
    targetPort: 5000
    serviceKey: 'speech'
  }
  {
    name: 'translator'
    image: 'mcr.microsoft.com/azure-cognitive-services/translator/text-translation:latest'
    cpu: '1.0'
    memory: '2Gi'
    targetPort: 5000
    serviceKey: 'translator'
  }
  {
    name: 'language'
    image: 'mcr.microsoft.com/azure-cognitive-services/textanalytics/language:latest'
    cpu: '2.0'
    memory: '4Gi'
    targetPort: 5000
    serviceKey: 'language'
  }
  {
    name: 'docintel-read'
    image: 'mcr.microsoft.com/azure-cognitive-services/form-recognizer/read-3.1:latest'
    cpu: '2.0'
    memory: '4Gi'
    targetPort: 5000
    serviceKey: 'docintel'
  }
  {
    name: 'docintel-layout'
    image: 'mcr.microsoft.com/azure-cognitive-services/form-recognizer/layout-3.1:latest'
    cpu: '2.0'
    memory: '4Gi'
    targetPort: 5000
    serviceKey: 'docintel'
  }
  {
    name: 'content-safety-text'
    image: 'mcr.microsoft.com/azure-cognitive-services/contentsafety/text-analyze:latest'
    cpu: '1.0'
    memory: '2Gi'
    targetPort: 5000
    serviceKey: 'contentsafety'
  }
  {
    name: 'content-safety-image'
    image: 'mcr.microsoft.com/azure-cognitive-services/contentsafety/image-analyze:latest'
    cpu: '1.0'
    memory: '2Gi'
    targetPort: 5000
    serviceKey: 'contentsafety'
  }
]

module aiContainers 'modules/containerapp-ai.bicep' = [for svc in aiServices: {
  scope: rg
  name: 'ai-${svc.name}'
  params: {
    name: 'ca-ai-${svc.name}-${resourceToken}'
    location: location
    tags: tags
    environmentId: cae.outputs.environmentId
    image: svc.image
    cpu: svc.cpu
    memory: svc.memory
    targetPort: svc.targetPort
    keyVaultName: keyvault.outputs.name
    apiKeySecretName: 'ai-${svc.serviceKey}-apikey'
    billingEndpointSecretName: 'ai-${svc.serviceKey}-billing'
    appIdentityResourceId: identity.outputs.appIdentityResourceId
  }
}]

module api 'modules/containerapp-api.bicep' = {
  scope: rg
  name: 'api'
  params: {
    name: 'ca-api-${resourceToken}'
    location: location
    tags: tags
    environmentId: cae.outputs.environmentId
    appIdentityResourceId: identity.outputs.appIdentityResourceId
    appIdentityClientId: identity.outputs.appIdentityClientId
    acrLoginServer: acr.outputs.loginServer
    storageAccountName: storage.outputs.name
    cosmosAccountName: cosmos.outputs.name
    cosmosDatabaseName: cosmos.outputs.databaseName
    cosmosContainerName: cosmos.outputs.containerName
    keyVaultName: keyvault.outputs.name
    appInsightsConnectionString: observability.outputs.appInsightsConnectionString
    aiServiceEndpoints: [for (svc, i) in aiServices: {
      name: svc.name
      fqdn: aiContainers[i].outputs.fqdn
    }]
    entraTenantId: subscription().tenantId
  }
}

module web 'modules/containerapp-web.bicep' = {
  scope: rg
  name: 'web'
  params: {
    name: 'ca-web-${resourceToken}'
    location: location
    tags: tags
    environmentId: cae.outputs.environmentId
    appIdentityResourceId: identity.outputs.appIdentityResourceId
    appIdentityClientId: identity.outputs.appIdentityClientId
    acrLoginServer: acr.outputs.loginServer
    apiBaseUrl: 'https://${api.outputs.fqdn}'
    appInsightsConnectionString: observability.outputs.appInsightsConnectionString
    entraTenantId: subscription().tenantId
  }
}

output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = subscription().tenantId
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acr.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = acr.outputs.name
output AZURE_KEY_VAULT_NAME string = keyvault.outputs.name
output AZURE_KEY_VAULT_ENDPOINT string = keyvault.outputs.endpoint
output AZURE_STORAGE_ACCOUNT_NAME string = storage.outputs.name
output AZURE_COSMOS_ACCOUNT_NAME string = cosmos.outputs.name
output AZURE_COSMOS_DATABASE_NAME string = cosmos.outputs.databaseName
output AZURE_COSMOS_CONTAINER_NAME string = cosmos.outputs.containerName
output AZURE_APP_IDENTITY_CLIENT_ID string = identity.outputs.appIdentityClientId
output AZURE_APP_INSIGHTS_CONNECTION_STRING string = observability.outputs.appInsightsConnectionString
output SERVICE_API_FQDN string = api.outputs.fqdn
output SERVICE_WEB_FQDN string = web.outputs.fqdn
output API_BASE_URL string = 'https://${api.outputs.fqdn}'
output WEB_BASE_URL string = 'https://${web.outputs.fqdn}'
output AI_CONTAINER_FQDNS array = [for (svc, i) in aiServices: {
  name: svc.name
  fqdn: aiContainers[i].outputs.fqdn
}]
