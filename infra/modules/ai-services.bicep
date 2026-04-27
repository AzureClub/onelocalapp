@description('Cognitive Services accounts (one per AI workload kind) used by container deployments and as billing endpoints in connected mode.')
param location string
param tags object
param resourceToken string

@description('List of AI accounts to create.')
param accounts array

@description('Whether to create commitment plans for disconnected containers. Requires prior approval (request access form). Default false.')
param enableDisconnectedCommitment bool = false

@description('Per-account commitment plan definitions used when enableDisconnectedCommitment=true. Key must match accounts[].key. tier is "T1"|"T2" etc., planType is one of "STT","TTS","TA","TTOTEXT","FR","CS".')
param disconnectedCommitments array = []

resource accountResources 'Microsoft.CognitiveServices/accounts@2024-10-01' = [for acc in accounts: {
  name: 'cog-${acc.key}-${take(resourceToken, 8)}'
  location: location
  tags: tags
  kind: acc.kind
  sku: { name: acc.sku }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: 'cog-${acc.key}-${take(resourceToken, 8)}'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
    disableLocalAuth: false
  }
}]

resource commitmentPlans 'Microsoft.CognitiveServices/accounts/commitmentPlans@2024-10-01' = [for (c, i) in disconnectedCommitments: if (enableDisconnectedCommitment) {
  parent: accountResources[c.accountIndex]
  name: '${c.planType}-commitment'
  properties: {
    hostingModel: 'DisconnectedContainer'
    planType: c.planType
    current: {
      tier: c.tier
    }
    autoRenew: false
  }
}]

output accountInfos array = [for (acc, i) in accounts: {
  key: acc.key
  name: accountResources[i].name
  id: accountResources[i].id
  endpoint: accountResources[i].properties.endpoint
}]
