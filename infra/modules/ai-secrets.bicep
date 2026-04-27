@description('Writes AI Services account keys and billing endpoints into Key Vault as secrets. Secret names match the contract used by containerapp-ai.bicep: ai-<key>-apikey, ai-<key>-billing.')
param keyVaultName string
param accountInfos array

resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = {
  name: keyVaultName
}

resource accounts 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = [for acc in accountInfos: {
  name: acc.name
}]

resource apiKeySecrets 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = [for (acc, i) in accountInfos: {
  parent: kv
  name: 'ai-${acc.key}-apikey'
  properties: {
    value: accounts[i].listKeys().key1
  }
}]

resource billingSecrets 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = [for (acc, i) in accountInfos: {
  parent: kv
  name: 'ai-${acc.key}-billing'
  properties: {
    value: acc.endpoint
  }
}]
