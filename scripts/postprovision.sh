#!/bin/sh
set -e
KV="$AZURE_KEY_VAULT_NAME"; RG="$AZURE_RESOURCE_GROUP"; WEB_NAME="$SERVICE_WEB_NAME"
TENANT_ID="$AZURE_TENANT_ID"; WEB_FQDN="$SERVICE_WEB_FQDN"; ENV_NAME="$AZURE_ENV_NAME"

if [ -z "$KV" ]; then echo "KV not set, skipping seed"; exit 0; fi

for s in speech translator language docintel contentsafety; do
  for suffix in apikey billing; do
    name="ai-${s}-${suffix}"
    if ! az keyvault secret show --vault-name "$KV" --name "$name" >/dev/null 2>&1; then
      echo "Seeding placeholder $name"
      az keyvault secret set --vault-name "$KV" --name "$name" --value "PLACEHOLDER-REPLACE-ME" >/dev/null
    fi
  done
done

if [ -n "$WEB_NAME" ] && [ -n "$TENANT_ID" ] && [ -n "$WEB_FQDN" ]; then
  APP_NAME="onelocalapp-${ENV_NAME}"
  APP_ID="$(az ad app list --display-name "$APP_NAME" --query '[0].appId' -o tsv 2>/dev/null || true)"
  if [ -z "$APP_ID" ]; then
    APP_ID="$(az ad app create --display-name "$APP_NAME" \
      --web-redirect-uris "https://$WEB_FQDN/.auth/login/aad/callback" \
      --enable-id-token-issuance true --query appId -o tsv)"
    az ad sp create --id "$APP_ID" >/dev/null
  else
    az ad app update --id "$APP_ID" --web-redirect-uris "https://$WEB_FQDN/.auth/login/aad/callback" --enable-id-token-issuance true >/dev/null
  fi
  az containerapp auth microsoft update -g "$RG" -n "$WEB_NAME" --client-id "$APP_ID" --tenant-id "$TENANT_ID" --yes >/dev/null 2>&1 || true
  az containerapp auth update -g "$RG" -n "$WEB_NAME" --enabled true --action RedirectToLoginPage --redirect-provider azureactivedirectory --require-https true >/dev/null 2>&1 || true
  echo "EasyAuth configured."
fi
