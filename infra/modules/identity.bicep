param location string
param tags object
param resourceToken string

resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-07-31-preview' = {
  name: 'id-app-${resourceToken}'
  location: location
  tags: tags
}

output appIdentityResourceId string = appIdentity.id
output appIdentityPrincipalId string = appIdentity.properties.principalId
output appIdentityClientId string = appIdentity.properties.clientId
output appIdentityName string = appIdentity.name
