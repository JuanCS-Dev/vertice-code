# Project Singularity — Fase 1 (Dados Soberanos)
## Provisionamento Google Cloud: AlloyDB AI & Networking (Terraform)

**Data:** 2026-01-26
**Owner:** Infra / Google Cloud
**Objetivo:** Prover rede privada + AlloyDB para o `vertice-backend` (Cloud Run) acessar o banco via IP privado, de forma idempotente e “Google Native”.

---

## 1) O que foi entregue (Terraform)

Arquivos:
- `infra/terraform/network.tf`
- `infra/terraform/alloydb.tf`
- `infra/terraform/outputs.tf`

Provider:
- `hashicorp/google` `~> 5.0` (validado com `v5.45.2`)

Validação executada:
- `terraform fmt`
- `terraform validate`
- `terraform plan -refresh=false` (com `TF_VAR_project_id` dummy para checagem de schema/graph)

---

## 2) Arquitetura resultante (alto nível)

**Rede (VPC)**
- VPC dedicada: `vertice-vpc` (sem subnets automáticas).
- Subnet principal (workloads): `vertice-subnet` (default `10.10.0.0/24`).
- Subnet dedicada ao Serverless VPC Access Connector: `vertice-vpc-conn-subnet` (default `10.10.10.0/28`).
- `private_ip_google_access = true` nas subnets (boa prática para acesso a APIs Google via rede privada quando aplicável).

**Private Service Access (PSA) para AlloyDB**
- Reserva de range global interno (`purpose = VPC_PEERING`) para serviços gerenciados: `vertice-alloydb-psa-range` (default `/16`).
- Conexão com Service Networking: `google_service_networking_connection` usando `servicenetworking.googleapis.com`.

**Serverless VPC Access (Cloud Run -> VPC)**
- Connector: `vertice-vpc-conn` (`google_vpc_access_connector`) hospedado na subnet dedicada.
- Autoscaling default: `min_instances=2`, `max_instances=3`, `machine_type=e2-standard-4`.

**AlloyDB**
- Cluster: `vertice-memory-cluster` em `var.region` (default `us-central1`).
- Instância primária: `vertice-memory-primary`.
- Sizing: `cpu_count = 4` (equivalente ao requisito de capacidade “db-custom-4-32768” no contexto AlloyDB; em Terraform o ajuste é por vCPU via `machine_config.cpu_count`).
- Flags: adicionada por default `google_ml_integration.enable_model_support = "on"` (toggle via variável).
- IAM DB Auth: “habilitado” por design via criação opcional de usuário `ALLOYDB_IAM_USER` (quando `var.alloydb_iam_user_id` for definido).

---

## 3) Componentes e dependências (por recurso)

**APIs (habilitadas via Terraform)**
- `compute.googleapis.com`
- `run.googleapis.com`
- `alloydb.googleapis.com`
- `servicenetworking.googleapis.com` (PSA)
- `vpcaccess.googleapis.com` (Serverless Connector)
- (mantidas as já existentes no `main.tf`)

**Ordem lógica**
1. APIs
2. VPC + subnets
3. Reserva PSA range + service networking connection
4. AlloyDB cluster/instance (dependem do PSA)
5. Serverless VPC Connector (para Cloud Run consumir)

---

## 4) Variáveis (sem hardcoding)

Obrigatórias:
- `var.project_id`

Com default (podem ser sobrescritas):
- `var.region` (`us-central1`)
- Rede: `network_name`, `subnet_*`, `serverless_connector_*`
- PSA: `psa_range_name`, `psa_prefix_length`
- AlloyDB: `alloydb_cluster_id`, `alloydb_primary_instance_id`, `alloydb_primary_cpu_count`
- Flags: `enable_alloydb_model_support`, `alloydb_model_support_flag_value`, `alloydb_database_flags`
- IAM DB user (opcional): `alloydb_iam_user_id`, `alloydb_iam_database_roles`

---

## 5) Outputs para integração

- `cluster_private_ip`: IP privado da instância primária AlloyDB (para o backend usar como host).
- `vpc_connector_id`: ID do Serverless VPC Access connector (para configurar Cloud Run).

---

## 6) Como o Cloud Run deve consumir (referência operacional)

No deploy do `vertice-backend`:
- Setar o connector do serviço Cloud Run para o `vertice-vpc-conn`.
- Recomenda-se `vpc-egress = private-ranges-only` (mantém saída pública fora do connector).
- Usar `cluster_private_ip` como destino (porta PostgreSQL/AlloyDB padrão).

IAM (mínimo esperado, fora do escopo do Terraform atual):
- Conceder ao Service Account do Cloud Run permissão para conexão AlloyDB (ex.: papéis do AlloyDB/Cloud IAM conforme política da org).
- Se usando IAM DB Auth, garantir que o usuário `ALLOYDB_IAM_USER` corresponda ao principal (ex.: email do SA) e que o app use fluxo de autenticação compatível.

---

## 7) Notas e próximos passos (para “apply” real)

1. Definir `terraform.tfvars` (ou variáveis de ambiente `TF_VAR_*`) com `project_id` real.
2. Executar `terraform apply` com credenciais GCP válidas.
3. Confirmar se o valor `"on"` do flag `google_ml_integration.enable_model_support` é o esperado no ambiente; caso necessário, ajustar via `var.alloydb_model_support_flag_value` sem mudar código.
4. (Opcional) Amarrar `alloydb_iam_user_id` ao email do SA do Cloud Run para ativar IAM DB Auth desde o primeiro `apply`.
