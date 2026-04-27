# OneLocalApp — architektura i plan

> Dokument projektowy: cel, zakres, decyzje, struktura repo. Kod referencyjny dla uzasadnienia "dlaczego tak", a nie tylko "co jest zrobione".

## Problem & cel

Aplikacja demo pokazująca jak działają usługi Azure AI w wersji **connected** (kontenery odpalone w Azure Container Apps) z możliwością przepięcia do trybu **disconnected** (on-premise / air-gapped) wyłącznie przez zmienne środowiskowe. Jeden front (Next.js) z zakładkami per usługa, backend FastAPI orkiestrujący wywołania, wyniki zapisywane w Storage + Cosmos i wyświetlane z historią/filtrami. Pełna integracja z Entra ID, Managed Identity wszędzie gdzie to możliwe, Key Vault na klucze (disconnected). Deploy przez azd + Bicep + GitHub Actions z OIDC.

## Zakres usług AI (po wykluczeniu deprecated do 2029)

- **Speech**: Speech-to-Text, Neural Text-to-Speech
- **Translator**: Text Translation
- **Language** (tylko aktywne): Language Detection, PII Detection, Text Analytics for Health, Prebuilt NER, Custom NER (placeholder)
- **Document Intelligence**: Read, Layout, Prebuilt (invoice/receipt/id)
- **Content Safety**: Text moderation, Image moderation, Prompt Shields, Groundedness Detection

## Architektura wysokiego poziomu

```
                ┌────────────────────────── VNet (hub) ──────────────────────────┐
   Internet ──► │  Container Apps Environment (internal, VNet-injected)          │
                │   ┌─────────────┐   ┌─────────────┐                             │
                │   │ web (Next15)│──►│ api (FastAPI)│──► [AI containers x 8]    │
                │   │ EasyAuth    │   │ EasyAuth/JWT │     speech-stt/tts        │
                │   │ public ing. │   │ internal ing │     translator / language │
                │   └─────────────┘   └─────────────┘     docintel-read/layout   │
                │           │                 │           content-safety-text/img│
                │           ▼                 ▼                                  │
                │   Private Endpoints: Blob • Cosmos • Key Vault • ACR           │
                │   Cognitive Services accounts (5 kinds) → KV secrets auto-fed  │
                └────────────────────────────────────────────────────────────────┘
```

- **Container Apps Environment**: VNet-injected, internal endpoints dla AI containers + backendu, public ingress tylko na froncie.
- **AI containers (8 instancji)**: oficjalne obrazy `mcr.microsoft.com/azure-cognitive-services/...`. Connected: `Eula=accept`, `Billing=<endpoint accounta>`, `ApiKey=<klucz z KV>`. Disconnected: dodatkowo `DownloadLicense=true` przy pierwszym starcie + zamontowany license file.
- **Cognitive Services accounts (5 kinds)**: tworzone w Bicepie (`Microsoft.CognitiveServices/accounts`), klucze i billing endpoints zapisywane do Key Vault automatycznie, bez manualnego seedu.
- **Private Endpoints**: Storage / Cosmos / Key Vault / ACR + Private DNS Zones.

## Tryb connected ↔ disconnected (kluczowy wymóg)

Backend wybiera klienta na podstawie ENV per usługa:

```
MODE=connected|disconnected                # globalny domyślny
AI_<SERVICE>_MODE=connected|disconnected   # override per usługa
AI_<SERVICE>_ENDPOINT=https://...          # endpoint kontenera lub Azure
AI_<SERVICE>_KEY=<opcjonalnie>             # tylko gdy disconnected/on-prem
AI_<SERVICE>_REGION=...                    # gdzie istotne (Speech, Translator)
USE_MANAGED_IDENTITY=true|false            # auth do Storage/Cosmos/KV
```

`<SERVICE>` ∈ `SPEECH_STT, SPEECH_TTS, TRANSLATOR, LANGUAGE, DOCINTEL_READ, DOCINTEL_LAYOUT, CONTENT_SAFETY_TEXT, CONTENT_SAFETY_IMAGE`.

- **connected (Azure)**: front+backend używają **User-assigned Managed Identity** do Storage/Cosmos/Key Vault. Do kontenerów AI w tym samym Container Apps Env — wewnętrzny HTTP, `ApiKey` mountowany z Key Vault przez `secretRef`.
- **disconnected (on-prem)**: brak MI → backend czyta klucze z ENV (lub zamontowanego secret file). Te same kontenery, ten sam kod aplikacji, inne ENV.

## Komponenty i repo (monorepo, azd-friendly)

```
onelocalapp/
├── azure.yaml                     # azd manifest (web + api services)
├── infra/
│   ├── main.bicep                 # subscription scope, RG + main module
│   ├── main.parameters.json
│   └── modules/
│       ├── network.bicep          # VNet, subnets, NSGs, Private DNS
│       ├── identity.bicep         # User-assigned MI
│       ├── keyvault.bicep         # KV + RBAC
│       ├── storage.bicep          # Storage account (Blob) + containers
│       ├── cosmos.bicep           # Cosmos DB (NoSQL) + DB + container
│       ├── acr.bicep              # ACR (Premium dla PE)
│       ├── observability.bicep    # Log Analytics + App Insights
│       ├── ai-services.bicep      # 5x Cognitive Services accounts (+ optional commitment plans)
│       ├── ai-secrets.bicep       # listKeys() → KV secrets
│       ├── containerapps-env.bicep
│       ├── containerapp-web.bicep        # Next.js, public ingress, EasyAuth
│       ├── containerapp-api.bicep        # FastAPI, internal ingress
│       └── containerapp-ai.bicep         # generyczny moduł AI container
├── src/
│   ├── web/                       # Next.js 15, Tailwind, shadcn-style
│   │   ├── app/
│   │   │   ├── speech/
│   │   │   ├── translator/
│   │   │   ├── language/
│   │   │   ├── document-intelligence/
│   │   │   ├── content-safety/
│   │   │   ├── history/           # lista wyników z Cosmos + podgląd Blob
│   │   │   ├── dashboard/         # metryki z App Insights
│   │   │   ├── settings/          # podgląd MODE, endpoints, health
│   │   │   └── api/proxy/[...path]/route.ts  # SSR → FastAPI internal
│   │   └── lib/{api,auth,utils}.ts
│   └── api/                       # FastAPI
│       ├── app/main.py
│       ├── app/config.py          # pydantic-settings, ENV → modes
│       ├── app/auth.py            # parsuje x-ms-client-principal* (EasyAuth)
│       ├── app/credentials.py     # ManagedIdentityCredential
│       ├── app/clients/           # 5 klientów AI (REST przez httpx)
│       ├── app/routers/           # 1 router per usługa + history + health
│       ├── app/storage/{blob,cosmos}.py
│       └── app/telemetry.py       # OpenTelemetry → App Insights
├── scripts/postprovision.{ps1,sh} # Entra App Reg + EasyAuth wiring
└── .github/workflows/
    ├── ci.yml                     # lint, typecheck, bicep build
    ├── infra.yml                  # azd provision (OIDC)
    └── deploy.yml                 # azd deploy (OIDC)
```

## Schemat danych

**Blob layout**: `results/{service}/{yyyy}/{mm}/{dd}/{run_id}.json` + opcjonalnie `inputs/{service}/.../{run_id}.bin` (audio/obraz/PDF).

**Cosmos `runs`** (partition key: `/service`):
```json
{
  "id": "run_id",
  "service": "speech|translator|language|docintel|content-safety",
  "operation": "stt|tts|detect|translate|read|...",
  "mode": "connected|disconnected",
  "userId": "<oid z Entra>",
  "createdAt": "ISO8601",
  "durationMs": 0,
  "status": "ok|error",
  "blobInputUri": "...",
  "blobResultUri": "...",
  "summary": { /* skrót do listy */ },
  "tags": ["demo", ...]
}
```

## Bezpieczeństwo / tożsamość

- **User-assigned MI** dla web i api (jedna `id-app`), z rolami:
  - `Storage Blob Data Contributor` na storage
  - `Cosmos DB Built-in Data Contributor` (SQL role 00000000-...-00002) na Cosmos
  - `Key Vault Secrets User` na KV
  - `AcrPull` na ACR
- **EasyAuth (Container Apps Built-in Auth)** na froncie. Backend internal-only — bez publicznego ingressu.
- **App Registration** w Entra tworzona w postprovision hook (`az ad app create`) — nie przez Bicep.
- **Klucze AI**: zapisywane do KV automatycznie z `listKeys()` świeżo utworzonych Cognitive Services accounts; mountowane do Container Apps przez `secretRef` z `keyVaultUrl + identity`.
- **Storage**: `allowSharedKeyAccess: false` — wyłącznie MI/RBAC.
- **Cosmos**: `disableLocalAuth: true` — wyłącznie SQL role assignments.
- **Disconnected on-prem**: ENV / secret file zamiast KV+MI.

## CI/CD (GitHub Actions + OIDC)

- `ci.yml`: PR — ruff/mypy/pytest (planned) dla api, eslint/tsc dla web, `az bicep build`.
- `infra.yml`: trigger przy zmianie `infra/**` lub manualnie → `azd provision`.
- `deploy.yml`: trigger na push do `main` w `src/**` → build images do ACR → `azd deploy`.

Repo variables (nie secrets): `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_ENV_NAME`, `AZURE_LOCATION`. Federated credential w Entra App Reg: `repo:AzureClub/onelocalapp:ref:refs/heads/main`.

## UX frontu

- Sidebar: lista usług, dashboard, history, settings.
- Service pages: formularz (drop file / textarea / mic / upload) + JSON viewer wyniku.
- `/history`: filtry (service, mode, date range, status).
- `/dashboard`: stats per service (planned: wykresy z App Insights via REST).
- `/settings`: read-only podgląd skonfigurowanych endpointów i trybów (z ENV), health-check każdego kontenera AI.

## Decyzje / założenia

- Region default: `westeurope` (zmienialne przez `azd env set AZURE_LOCATION`).
- **Disconnected commitment plans**: opt-in przez `enableDisconnectedCommitment=true` + `disconnectedCommitments` array. Wymaga prior approval od Microsoft (request access form). Domyślnie wyłączone.
- AI container image tags `:latest` — w produkcji przypiąć do konkretnej wersji.
- Custom NER w UI: placeholder (wymaga osobnego trenowanego modelu).
- TTS/STT disconnected: license file pobierany ręcznie raz, mountowany jako volume.
- Język UI/komentarzy: PL (po preferencjach autora repo).

## Status (ukończone)

| Obszar | Status |
|---|---|
| Bicep — sieć, identity, KV, Storage, Cosmos, ACR, observability | ✅ |
| Bicep — Container Apps Env + 8 AI containers + api + web | ✅ |
| Bicep — Cognitive Services accounts + auto-write kluczy do KV | ✅ |
| Bicep — opcjonalne commitment plans dla disconnected | ✅ |
| FastAPI — config, auth, credentials, telemetry, storage | ✅ |
| FastAPI — 5 AI clients + 7 routers (per service + history + health) | ✅ |
| Next.js — layout, sidebar/header, 5 service pages, history, dashboard, settings | ✅ |
| Next.js — SSR proxy do internal API | ✅ |
| azd manifest + postprovision (KV seed idempotent + Entra + EasyAuth) | ✅ |
| GitHub Actions — ci / infra / deploy z OIDC | ✅ |
| README + docs/architecture.md | ✅ |
| Repo na GitHub: AzureClub/onelocalapp | ✅ |

## Możliwe następne kroki (nice-to-have)

- Pin AI container image tags do konkretnych wersji.
- Recharts na `/dashboard` z fetchem do App Insights REST.
- Per-request runtime override modu (np. dropdown w UI nadpisujący ENV per call).
- Custom NER trening pipeline.
- Prompt Shields / Groundedness Detection w Content Safety.
- E2E test smoke przez GitHub Actions po deploy.
- Private DNS zone dla Cognitive Services accounts (cognitiveservices.azure.com) + `publicNetworkAccess: Disabled`.
