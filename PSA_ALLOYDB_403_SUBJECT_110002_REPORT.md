# Relatório de Auditoria (2026) — Bloqueio PSA/AlloyDB (`403 Forbidden`, `subject: 110002`)

Data do relatório: **2026-01-26**
Contexto do incidente (fornecido): **2026-01-25** — projeto `vertice-ai`, região `us-central1`, Terraform via Cloud Build.
Erro observado no `terraform apply`: `googleapi: Error 403: Permission denied to add peering for service 'servicenetworking.googleapis.com'` com `PreconditionFailure` `subject: "110002"`.

---

## 1) O que está falhando, exatamente

O fluxo de “Private Services Access (PSA)” é:

1. Reservar um range interno (`purpose=VPC_PEERING`) na VPC do consumidor.
2. Criar a **private connection** (peering via Service Networking) entre a VPC do consumidor e o “service producer” Google.

A sua infra já criou a VPC, a subnet e o range (`vertice-psa-range`). O bloqueio acontece **somente** ao tentar criar a conexão:

- Recurso Terraform: `google_service_networking_connection.private_vpc_connection`
- Arquivo local: `infra/terraform/network.tf` (linhas 16–30 mostram range `VPC_PEERING` + conexão `servicenetworking.googleapis.com`)

Isso é coerente com a documentação do AlloyDB: para criar um cluster, você precisa apontar uma VPC **já configurada com private services access** (ou seja, com a conexão criada).
Evidência (doc AlloyDB “Private services access overview”): linhas **483–494** deixam explícito que a VPC precisa estar configurada com PSA antes de criar o cluster.

---

## 2) O que “Permission denied to add peering … servicenetworking.googleapis.com” significa (documentado)

### 2.1. Causa #1 (mais comum): falta de permissão `servicenetworking.services.addPeering`

O próprio Google documenta este erro e o significado:

- Doc “Troubleshooting (Parallelstore)”: o erro “Permission denied to add peering …” significa que a conta **não tem** a permissão IAM `servicenetworking.services.addPeering` (linhas **277–284**).

E o Google documenta quais papéis concedem esse permission:

- Doc IAM “Service Networking roles and permissions”: `servicenetworking.services.addPeering` é incluído em `roles/owner`, `roles/compute.networkAdmin`, `roles/servicenetworking.networksAdmin` (linhas **1501–1512**).

**Implicação:** se o principal que está fazendo a chamada realmente tem `roles/owner` *no projeto e na VPC correta*, esse erro **não deveria** persistir. Logo, quando ele persiste após “dar Owner”, quase sempre existe um “bloqueio acima do IAM allow” (política organizacional/deny/escopo/projeto incorreto).

### 2.2. Causa #2 (muito frequente em orgs): Organization Policy bloqueando peering (`constraints/compute.restrictVpcPeering`)

Mesmo que o IAM permita, uma **Organization Policy** pode negar a criação de peerings.

Evidência forte (Google, troubleshooting do Managed Microsoft AD — mas o mecanismo é o mesmo: peering):

- Se a org policy negar peerings, a criação falha; o doc mostra o erro de exemplo e, principalmente, mostra como **ver e permitir** o policy “Restrict VPC peering usage” / `constraints/compute.restrictVpcPeering` (linhas **292–316**), incluindo comandos `gcloud resource-manager org-policies describe` e `... allow`.

Evidência adicional (catálogo de constraints):

- Doc “Organization policy constraints” lista `constraints/compute.restrictVpcPeering` como constraint disponível (linhas **634–635**).

**Implicação:** se `constraints/compute.restrictVpcPeering` está em `DENY` (ou allowlist que não inclui o seu projeto/rede), nenhuma combinação de papéis “Owner/NetworkAdmin” vai resolver — o fix é ajustar a política (ou obter exceção).

### 2.3. Causa #3: IAM Deny Policy (ou políticas que negam APIs/serviços)

Mesmo com `roles/owner`, uma **Deny Policy** (IAM Deny) ou uma **policy de restrição de serviços/APIs** pode bloquear operações específicas.

O seu log já mostra que `servicenetworking.googleapis.com` está habilitada, então o cenário “API não habilitada” é improvável. Mas **Deny** continua possível (porque Deny vence Allow).

### 2.4. Causa #4: principal/projeto errado (Terraform/CI aplicando em “contexto” diferente)

Existe histórico público de confusão de “qual projeto está sendo tocado” ao criar `google_service_networking_connection` quando o principal pertence a outro projeto (ex.: service account em “control-project”), ainda que a VPC esteja em “data-project”.
Referência: issue pública `terraform-provider-google` #10066 (descrição + exemplo de comportamento).

**Implicação:** se o Cloud Build está autenticando com uma service account de outro projeto/identity pool e o provider estiver inferindo “billing project”/UPO, pode haver divergência de escopo. Isso não é o primeiro suspeito aqui (seu `network` aponta `projects/vertice-ai/...`), mas é um check obrigatório.

---

## 3) Fix recomendado (com ordem de execução)

> Objetivo: produzir um “fix determinístico”, não “tentativa e erro”.

### Passo 0 — Descobrir “quem” está fazendo a chamada que falha

Sem isso, você pode estar dando permissão no lugar errado.

**Ação:** abrir o Cloud Audit Log do erro e capturar:

- `principalEmail`
- `serviceName` = `servicenetworking.googleapis.com`
- método (algo como `google.cloud.servicenetworking.v1.ServiceNetworking/...` / “connections.create” / “addPeering”)
- `status.message` e `status.details` (muitas vezes detalha `permission` e/ou `constraint` violado)

**Query sugerida (Cloud Logging, ajuste o project):**

```
resource.type="audited_resource"
protoPayload.serviceName="servicenetworking.googleapis.com"
severity>=ERROR
```

Se necessário, filtre por `protoPayload.status.code=7` (PERMISSION_DENIED) e por janela de tempo do build.

#### ✅ Achado no seu projeto `vertice-ai` (coleta via `gcloud`, 2026-01-26)

O Cloud Audit Log do erro mostrou que a chamada que falha está sendo feita por:

- `principalEmail`: `239800439060-compute@developer.gserviceaccount.com` (**Compute Engine default service account**)
- `methodName`: `google.cloud.servicenetworking.v1.ServicePeeringManager.CreateConnection`
- `authorizationInfo[0]`: `granted=false` para `permission=servicenetworking.services.addPeering`

Isso explica por que conceder `roles/owner` / `roles/compute.networkAdmin` para
`239800439060@cloudbuild.gserviceaccount.com` **não resolveu**: o Terraform dentro do Cloud Build **não estava
rodando com essa service account**.

Confirmação adicional: o build Cloud Build `5863b818-05a8-491b-af19-e54d4cf47384` executou com:

- `serviceAccount`: `projects/vertice-ai/serviceAccounts/239800439060-compute@developer.gserviceaccount.com`
  (saída de `gcloud builds describe ... --format='get(serviceAccount)'`)

**Conclusão imediata:** este incidente (no seu estado atual) é um **IAM Allow faltando no principal real**,
não uma Org Policy/Deny “invisível”.

### Passo 1 — Verificar `constraints/compute.restrictVpcPeering` (mais provável quando “Owner não resolve”)

**Ação (rápida):** pedir para um Org Admin checar no Console:

- Organization Policies → “Restrict VPC peering usage”
- Confirmar se o projeto `vertice-ai`/a rede `vertice-vpc` está permitida.

**Ação (CLI, conforme doc Google):**

1. Ver policy:
   - O doc de troubleshooting do Managed Microsoft AD mostra:
     `gcloud resource-manager org-policies describe constraints/compute.restrictVpcPeering --organization=ORGANIZATION_ID` (linhas **308–312**)
2. Permitir peerings para o projeto:
   - `gcloud resource-manager org-policies allow constraints/compute.restrictVpcPeering under:projects/PROJECT_ID --organization=ORGANIZATION_ID` (linhas **312–315**)

**Resultado esperado:** após permitir o peering para o projeto (ou adicionar allowlist correta), o `terraform apply` deve conseguir criar `google_service_networking_connection`.

### Passo 2 — Confirmar permissão `servicenetworking.services.addPeering` no *principal correto*

Mesmo que você já tenha tentado, valide “no principal que o Audit Log mostrou”.

#### Fix direto para o seu caso (recomendado)

Você tem duas opções corretas; escolha **uma**.

**Opção A (mais rápida):** conceder as permissões necessárias ao principal que o build está usando hoje
(`239800439060-compute@developer.gserviceaccount.com`).

**Opção B (mais limpa):** mudar o Cloud Build para executar com uma service account dedicada (ex. a própria
`239800439060@cloudbuild.gserviceaccount.com`) e conceder permissões só nela.

Na prática, a Opção B evita “superpoderes” no Compute default SA e reduz risco de segurança.

**Comandos (Opção A):**

```bash
PROJECT_ID=vertice-ai
PROJECT_NUMBER=239800439060
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA}" \
  --role="roles/servicenetworking.networksAdmin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA}" \
  --role="roles/compute.networkAdmin"
```

**Comandos (Opção B, exemplo com build manual):**

```bash
PROJECT_ID=vertice-ai
PROJECT_NUMBER=239800439060
BUILD_SA="projects/${PROJECT_ID}/serviceAccounts/${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud builds submit --project="$PROJECT_ID" \
  --service-account="$BUILD_SA" \
  --config=cloudbuild.yaml .
```

Se você usa build trigger (não é o seu caso hoje), ajuste o `serviceAccount` do trigger para o SA desejado.

Pelos docs Google:

- O erro indica falta de `servicenetworking.services.addPeering` (Parallelstore troubleshooting, linhas **277–284**).
- Papéis que incluem a permissão (IAM roles/permissions, linhas **1501–1512**): `roles/owner`, `roles/compute.networkAdmin`, `roles/servicenetworking.networksAdmin`.

**Cuidado:** se existir **IAM Deny**, isso pode continuar falhando apesar do allow.

### Passo 3 — Verificar se existe Deny Policy ou policy de restrição de serviços

Se o Audit Log indicar “denied by IAM Deny” (ou semelhante), o fix é remover/ajustar a Deny.

### Passo 4 — Validar o caminho “Terraform ↔ documentação oficial”

O Terraform provider documenta que este resource cria a conexão de PSA e referencia a doc oficial do VPC:

- `google_service_networking_connection` docs (provider, v5.26.0) apontam para “Configure private services access” e para a API “services.connections” (linhas **12–16**) e mostram exatamente o recurso com `service = "servicenetworking.googleapis.com"` (linhas **31–36**).

E a doc do VPC mostra:

- Como criar a conexão via `gcloud services vpc-peerings connect ... --service=servicenetworking.googleapis.com` (linhas **499–520**).
- Como criar via Terraform (snippet) (linhas **522–530**).

Se o `gcloud ... connect` falhar no Console/Cloud Shell para o mesmo principal, você confirma que o problema é **política/permissão**, não Terraform.

---

## 4) Checklist de validação (para fechar o incidente)

1. `gcloud services vpc-peerings list --network=vertice-vpc` mostra o peering (VPC doc, linhas **545–552**).
2. No Console: VPC → Private services access → “Private connections to services” mostra conexão ativa.
3. `terraform apply` cria o `google_service_networking_connection` sem erro.
4. Só então o `google_alloydb_cluster` passa a ser criado.

---

## 5) Referências exatas (página + linha)

### Google Cloud — AlloyDB

- Enable private services access (AlloyDB): operação de conexão via `gcloud services vpc-peerings connect` (linhas **573–592**) e visão geral das 2 operações (linhas **469–472**).
  URL: https://docs.cloud.google.com/alloydb/docs/configure-connectivity
- Private services access overview (AlloyDB): exige VPC já configurada com PSA antes do cluster (linhas **483–494**).
  URL: https://docs.cloud.google.com/alloydb/docs/about-private-services-access
- Private IP overview (AlloyDB): PSA é implementado como VPC peering (linha **477**).
  URL: https://docs.cloud.google.com/alloydb/docs/private-ip

### Google Cloud — VPC / PSA

- Configure private services access (VPC): `gcloud services vpc-peerings connect` (linhas **499–520**) e snippet Terraform (linhas **522–530**); nota “não reutilizar allocated range” (linha **482**).
  URL: https://docs.cloud.google.com/vpc/docs/configure-private-services-access

### Google Cloud — Troubleshooting / IAM / Org Policy

- Troubleshooting (Parallelstore): “Permission denied to add peering …” = falta `servicenetworking.services.addPeering` (linhas **277–284**).
  URL: https://docs.cloud.google.com/parallelstore/docs/troubleshooting
- Service Networking roles and permissions (IAM): roles que contêm `servicenetworking.services.addPeering` (linhas **1501–1512**).
  URL: https://docs.cloud.google.com/iam/docs/roles-permissions/servicenetworking
- Troubleshoot Managed Microsoft AD: como ver e permitir `constraints/compute.restrictVpcPeering` (linhas **292–316**).
  URL: https://docs.cloud.google.com/managed-microsoft-ad/docs/troubleshooting
- Organization policy constraints: lista `constraints/compute.restrictVpcPeering` (linhas **634–635**).
  URL: https://docs.cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints

### Terraform provider docs (espelho público, sem JS)

- `google_service_networking_connection` doc (provider v5.26.0): referência à doc oficial + API, e exemplo (linhas **12–36**).
  URL: https://third-party-mirror.googlesource.com/terraform-provider-google/%2B/refs/tags/v5.26.0/website/docs/r/service_networking_connection.html.markdown

---

## 6) “Fix” em uma frase (para o executivo)

Se `roles/owner`/`compute.networkAdmin` já foram concedidos e o erro persiste, o fix mais provável é **liberar VPC peering na Organization Policy** (`constraints/compute.restrictVpcPeering`) para o projeto `vertice-ai` (ou conceder exceção), validando pelo **Cloud Audit Log** qual principal/política está negando a operação.
