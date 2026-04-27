param location string
param tags object
param resourceToken string
param privateEndpointSubnetId string
param cosmosPrivateDnsZoneId string
param appIdentityPrincipalId string
param devPrincipalId string = ''

param databaseName string = 'onelocalapp'
param containerName string = 'runs'

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: 'cosmos-${resourceToken}'
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [ { locationName: location, failoverPriority: 0 } ]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
    capabilities: [ { name: 'EnableServerless' } ]
  }
}

resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmos
  name: databaseName
  properties: {
    resource: { id: databaseName }
  }
}

resource runs 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: db
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: { paths: [ '/service' ], kind: 'Hash' }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/"_etag"/?' } ]
      }
    }
  }
}

// Built-in Cosmos DB Data Contributor
var dataContribRoleDefId = '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'

resource appCosmosAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmos
  name: guid(cosmos.id, appIdentityPrincipalId, 'data-contrib')
  properties: {
    roleDefinitionId: dataContribRoleDefId
    principalId: appIdentityPrincipalId
    scope: cosmos.id
  }
}

resource devCosmosAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = if (!empty(devPrincipalId)) {
  parent: cosmos
  name: guid(cosmos.id, devPrincipalId, 'data-contrib-dev')
  properties: {
    roleDefinitionId: dataContribRoleDefId
    principalId: devPrincipalId
    scope: cosmos.id
  }
}

resource pe 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: 'pe-cosmos-${resourceToken}'
  location: location
  tags: tags
  properties: {
    subnet: { id: privateEndpointSubnetId }
    privateLinkServiceConnections: [
      {
        name: 'cosmos'
        properties: {
          privateLinkServiceId: cosmos.id
          groupIds: [ 'Sql' ]
        }
      }
    ]
  }
}

resource peDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: pe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      { name: 'cosmos', properties: { privateDnsZoneId: cosmosPrivateDnsZoneId } }
    ]
  }
}

output name string = cosmos.name
output id string = cosmos.id
output endpoint string = cosmos.properties.documentEndpoint
output databaseName string = databaseName
output containerName string = containerName
