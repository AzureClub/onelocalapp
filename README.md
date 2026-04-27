# OneLocalApp — Azure AI Containers showcase

Demo aplikacji prezentującej **Azure AI Services jako kontenery** w trybie **connected** (Azure Container Apps) i **disconnected** (on-premise / air-gapped). Te same obrazy, ten sam kod aplikacji — przełącznik wyłącznie w zmiennych środowiskowych.

## Stack

- **web**: Next.js 15 + React 19 + Tailwind + shadcn-style UI, EasyAuth (Entra ID)
- **api**: FastAPI (Python 3.12), DefaultAzureCredential / ManagedIdentity
- **AI containers**: Speech (STT/TTS), Translator, Language (Detect/PII/NER/Health), Document Intelligence (Read/Layout/Prebuilt), Content Safety (Text/Image/Prompt Shields)
- **Storage**: Azure Blob (raw results) + Cosmos DB NoSQL (run index)
- **Identity**: User-assigned Managed Identity, Key Vault na klucze AI
- **IaC**: Bicep (subscription scope) + azd
- **CI/CD**: GitHub Actions z OIDC (federated credentials)

## Deploy do Azure

```bash
azd auth login
azd env new dev
azd env set AZURE_LOCATION westeurope
azd up
```

`azd up` wykona: `provision` (Bicep) → utworzenie 5 Azure AI Services accounts (Speech, Translator, Language, DocIntel, ContentSafety) → automatyczny zapis kluczy i billing endpointów do Key Vault → konfiguracja Entra App Registration + EasyAuth → `deploy` (build images → ACR → Container Apps).

### Disconnected commitment plans (opcjonalne)

Disconnected containers wymagają **commitment plan** w Cognitive Services account. To wymaga zatwierdzenia przez Microsoft ([request access form](https://aka.ms/csdisconnectedcontainers)). Po otrzymaniu approval:

```bash
azd env set ENABLE_DISCONNECTED_COMMITMENT true
```

I edytuj `infra/main.parameters.json` aby dodać `disconnectedCommitments`, np:
```json
"disconnectedCommitments": { "value": [
  { "accountIndex": 0, "planType": "STT", "tier": "T1" },
  { "accountIndex": 1, "planType": "TTOTEXT", "tier": "T1" }
]}
```
`accountIndex` to indeks w `aiAccounts` (0=speech, 1=translator, 2=language, 3=docintel, 4=contentsafety).

## Tryb connected ↔ disconnected

Globalny domyślny tryb sterowany ENV `MODE` w api. Per-usługa override:

```text
MODE=connected|disconnected
USE_MANAGED_IDENTITY=true|false

AI_<SERVICE>_MODE=connected|disconnected     # opcjonalny override
AI_<SERVICE>_ENDPOINT=https://...            # endpoint kontenera (Azure lub on-prem)
AI_<SERVICE>_KEY=<sekret>                    # klucz / billing / apiKey (disconnected)
AI_<SERVICE>_REGION=...                      # tylko Speech / Translator
```

`<SERVICE>` ∈ `SPEECH_STT, SPEECH_TTS, TRANSLATOR, LANGUAGE, DOCINTEL_READ, DOCINTEL_LAYOUT, CONTENT_SAFETY_TEXT, CONTENT_SAFETY_IMAGE`.

W trybie connected w Azure: ustawione przez Bicep, klucze pobierane z Key Vault przez Managed Identity. W trybie disconnected (on-prem): podajesz `endpoint` i `key` z lokalnego deploymentu.

## Disconnected on-premise

1. Kup commitment tier dla wybranej usługi w Azure Portal (Disconnected containers wymaga commitment tier).
2. Pobierz license file: uruchom kontener jednorazowo z `DownloadLicense=true Mounts:License=/license` zgodnie z [docs](https://learn.microsoft.com/en-us/azure/ai-services/containers/disconnected-containers).
3. W produkcji uruchom kontener z zamontowanym license file (`Mounts:License`) bez połączenia z internetem.
4. Skonfiguruj front+api do wskazania na lokalny endpoint:
   ```
   MODE=disconnected
   USE_MANAGED_IDENTITY=false
   AI_SPEECH_STT_ENDPOINT=http://onprem-stt:5000
   AI_SPEECH_STT_KEY=<api-key-z-license>
   STORAGE_CONNECTION_STRING=...     # MinIO/lokalny S3-zgodny ze schematem Azure
   COSMOS_CONNECTION_STRING=...      # CosmosDB Emulator lub MongoDB API
   ```

## Struktura repo

```
infra/        # Bicep modules
src/api/      # FastAPI backend
src/web/      # Next.js frontend
scripts/      # azd hooks
.github/workflows/  # CI/CD
```

## Lokalny dev

```bash
# api
cd src/api && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --reload

# web
cd src/web && npm install && npm run dev
```

## Bezpieczeństwo

- **EasyAuth (Entra ID)** chroni publiczny endpoint web → user musi się zalogować.
- **Backend** w internal ingress, dostępny tylko dla web w VNet.
- **AI containers** w internal ingress, dostępne tylko z backendu w VNet.
- **Storage / Cosmos / KV / ACR** za Private Endpoints.
- **Klucze AI** w Key Vault, mountowane do Container Apps przez `secretRef`.
- **Managed Identity** wszędzie gdzie to możliwe (Storage, Cosmos, KV, ACR).

## CI/CD

Skonfiguruj GitHub repo variables:
- `AZURE_CLIENT_ID` — clientId federated credential
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_ENV_NAME` (np. `dev`)
- `AZURE_LOCATION` (np. `westeurope`)

Federated credential dla OIDC ustaw w Entra App Registration → Federated credentials, scope: `repo:<org>/<repo>:ref:refs/heads/main`.

## Troubleshooting

- **Container AI startuje i kończy z błędem `Eula must be accepted`** — upewnij się, że secret `ai-<service>-apikey` w KV nie jest pusty (placeholder z post-provision wystarczy do startu, ale faktyczne wywołania zwrócą 401 dopóki nie podmienisz na prawdziwy klucz / endpoint billingowy z Azure AI Foundry).
- **EasyAuth pętla logowania** — sprawdź, że redirect URI w Entra App Registration jest dokładnie `https://<web-fqdn>/.auth/login/aad/callback`.
- **Cosmos `Forbidden`** — Managed Identity musi mieć role assignment na Cosmos (Bicep tworzy automatycznie). Dla dev: ustaw `principalId` w `azd env set AZURE_PRINCIPAL_ID <your-oid>` przed `azd up`.
