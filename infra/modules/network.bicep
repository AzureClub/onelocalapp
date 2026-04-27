param location string
param tags object
param resourceToken string

param vnetAddressPrefix string = '10.50.0.0/16'
param caeSubnetPrefix string = '10.50.0.0/23'
param peSubnetPrefix string = '10.50.4.0/24'

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: 'vnet-${resourceToken}'
  location: location
  tags: tags
  properties: {
    addressSpace: { addressPrefixes: [ vnetAddressPrefix ] }
    subnets: [
      {
        name: 'cae'
        properties: {
          addressPrefix: caeSubnetPrefix
          delegations: [
            {
              name: 'cae-delegation'
              properties: { serviceName: 'Microsoft.App/environments' }
            }
          ]
        }
      }
      {
        name: 'pe'
        properties: {
          addressPrefix: peSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

var privateZones = [
  'privatelink.blob.${environment().suffixes.storage}'
  'privatelink.documents.azure.com'
  'privatelink.vaultcore.azure.net'
  'privatelink.azurecr.io'
]

resource zones 'Microsoft.Network/privateDnsZones@2024-06-01' = [for z in privateZones: {
  name: z
  location: 'global'
  tags: tags
}]

resource zoneLinks 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = [for (z, i) in privateZones: {
  parent: zones[i]
  name: 'link-${resourceToken}'
  location: 'global'
  properties: {
    virtualNetwork: { id: vnet.id }
    registrationEnabled: false
  }
}]

output vnetId string = vnet.id
output caeSubnetId string = vnet.properties.subnets[0].id
output peSubnetId string = vnet.properties.subnets[1].id
output blobPrivateDnsZoneId string = zones[0].id
output cosmosPrivateDnsZoneId string = zones[1].id
output kvPrivateDnsZoneId string = zones[2].id
output acrPrivateDnsZoneId string = zones[3].id
