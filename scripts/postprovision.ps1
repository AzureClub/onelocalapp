#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

$kv  = $env:AZURE_KEY_VAULT_NAME
$rg  = $env:AZURE_RESOURCE_GROUP
$webName = $env:SERVICE_WEB_NAME
$tenantId = $env:AZURE_TENANT_ID
$webFqdn = $env:SERVICE_WEB_FQDN

if (-not $kv) { Write-Host "Key Vault name not set, skipping seed."; exit 0 }

$services = @("speech", "translator", "language", "docintel", "contentsafety")
foreach ($s in $services) {
  foreach ($suffix in @("apikey","billing")) {
    $name = "ai-$s-$suffix"
    $exists = az keyvault secret show --vault-name $kv --name $name 2>$null
    if (-not $exists) {
      Write-Host "Seeding placeholder secret $name"
      az keyvault secret set --vault-name $kv --name $name --value "PLACEHOLDER-REPLACE-ME" | Out-Null
    }
  }
}

if ($webName -and $tenantId -and $webFqdn) {
  $appName = "onelocalapp-$($env:AZURE_ENV_NAME)"
  $existing = az ad app list --display-name $appName --query "[0].appId" -o tsv 2>$null
  if (-not $existing) {
    Write-Host "Creating Entra App Registration $appName"
    $existing = az ad app create --display-name $appName `
      --web-redirect-uris "https://$webFqdn/.auth/login/aad/callback" `
      --enable-id-token-issuance true `
      --query appId -o tsv
    az ad sp create --id $existing | Out-Null
  } else {
    az ad app update --id $existing --web-redirect-uris "https://$webFqdn/.auth/login/aad/callback" --enable-id-token-issuance true | Out-Null
  }
  Write-Host "Configuring EasyAuth on $webName"
  az containerapp auth microsoft update -g $rg -n $webName --client-id $existing --tenant-id $tenantId --yes 2>$null | Out-Null
  az containerapp auth update -g $rg -n $webName --enabled true --action RedirectToLoginPage --redirect-provider azureactivedirectory --require-https true 2>$null | Out-Null
  Write-Host "EasyAuth configured."
}
