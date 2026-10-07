# Micro lab 11 (GCP) - Seguridad y gobernanza del proyecto
#   Detectivos: Data Access audit logs, sinks (Log bucket 365 d + GCS CMEK), alertas basadas en logs
#   Preventivos: IAM Deny Policy (llaves de SA y desactivación de logs), VPC-SC opcional
#   Identidad: RBAC por función (roles predefinidos + rol custom), break-glass temporal con IAM Conditions
#   Respuesta: SCC notificaciones -> Pub/Sub (opcional, requiere organización)

data "google_project" "this" {}

locals {
  name = "lab11-${var.environment}-sec"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "11-security-iam-deny-rbac"
  }

  gcs_agent = "serviceAccount:service-${data.google_project.this.number}@gs-project-accounts.iam.gserviceaccount.com"
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudkms.googleapis.com",
    "iam.googleapis.com",
    "securitycenter.googleapis.com",
    "pubsub.googleapis.com",
    "accesscontextmanager.googleapis.com",
    "cloudasset.googleapis.com",
  ]
}

# =============================================================================
# 1. Auditoría
# =============================================================================
resource "google_project_iam_audit_config" "data_access" {
  for_each = toset(var.data_access_audit_services)
  project  = var.project_id
  service  = each.value

  audit_log_config {
    log_type = "ADMIN_READ"
  }
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

# Log bucket con retención larga y Log Analytics (consultas SQL sobre logs)
resource "google_logging_project_bucket_config" "audit" {
  project          = var.project_id
  location         = "global"
  bucket_id        = "${local.name}-audit"
  retention_days   = var.log_retention_days
  enable_analytics = true
  locked           = var.lock_log_bucket
  description      = "Audit logs del proyecto (inmutables si locked = true)"
  depends_on       = [module.services]
}

resource "google_logging_project_sink" "audit_to_bucket" {
  name                   = "${local.name}-audit-to-log-bucket"
  destination            = "logging.googleapis.com/${google_logging_project_bucket_config.audit.id}"
  filter                 = "logName:\"cloudaudit.googleapis.com\""
  unique_writer_identity = true
}

# Copia de archivo en GCS con CMEK y retención (WORM opcional)
module "kms" {
  source            = "../../modules/kms-key"
  project_id        = var.project_id
  name              = "${local.name}-logs"
  location          = var.region
  encrypter_members = [local.gcs_agent]
  depends_on        = [module.services]
}

module "archive" {
  source              = "../../modules/gcs-secure-bucket"
  project_id          = var.project_id
  name                = "${var.project_id}-${local.name}-archive"
  location            = var.region
  kms_key_name        = module.kms.key_id
  versioning          = false
  retention_days      = var.archive_retention_days
  lock_retention      = false
  nearline_after_days = 30
  force_destroy       = var.environment != "prod"
  labels              = local.common_labels
  depends_on          = [module.kms]
}

resource "google_logging_project_sink" "audit_to_gcs" {
  name                   = "${local.name}-audit-to-gcs"
  destination            = "storage.googleapis.com/${module.archive.name}"
  filter                 = "logName:\"cloudaudit.googleapis.com\""
  unique_writer_identity = true
}

resource "google_storage_bucket_iam_member" "sink_writer" {
  bucket = module.archive.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.audit_to_gcs.writer_identity
}

# =============================================================================
# 2. Alertas basadas en logs (eventos de alto riesgo)
# =============================================================================
resource "google_monitoring_notification_channel" "security" {
  for_each     = toset(var.security_emails)
  display_name = "03-cloud-e-infraestructura/lab11-terraform-gcp seguridad ${each.value}"
  type         = "email"
  labels = {
    email_address = each.value
  }
  depends_on = [module.services]
}

locals {
  log_alerts = {
    owner_granted = {
      title  = "Se otorgó roles/owner"
      filter = "protoPayload.methodName=\"SetIamPolicy\" AND protoPayload.serviceData.policyDelta.bindingDeltas.role=\"roles/owner\" AND protoPayload.serviceData.policyDelta.bindingDeltas.action=\"ADD\""
    }
    sa_key_created = {
      title  = "Se creó una llave de service account"
      filter = "protoPayload.methodName=\"google.iam.admin.v1.CreateServiceAccountKey\""
    }
    audit_config_changed = {
      title  = "Cambió la configuración de auditoría o un sink"
      filter = "protoPayload.methodName=(\"SetIamPolicy\" AND \"auditConfigDeltas\") OR protoPayload.methodName:(\"DeleteSink\" OR \"UpdateSink\" OR \"DeleteBucket\")"
    }
    firewall_open = {
      title  = "Regla de firewall abierta a 0.0.0.0/0"
      filter = "resource.type=\"gce_firewall_rule\" AND protoPayload.methodName:(\"insert\" OR \"patch\") AND protoPayload.request.sourceRanges=\"0.0.0.0/0\""
    }
  }
}

resource "google_monitoring_alert_policy" "log_alerts" {
  for_each     = local.log_alerts
  display_name = "${local.name} ${each.value.title}"
  combiner     = "OR"
  severity     = "CRITICAL"

  conditions {
    display_name = each.value.title
    condition_matched_log {
      filter = each.value.filter
    }
  }

  alert_strategy {
    notification_rate_limit {
      period = "300s"
    }
    auto_close = "1800s"
  }

  notification_channels = [for c in google_monitoring_notification_channel.security : c.id]
  depends_on            = [module.services]
}

# =============================================================================
# 3. IAM Deny Policy: nadie (salvo excepción) puede crear llaves de SA ni apagar la auditoría
# =============================================================================
resource "google_iam_deny_policy" "guardrails" {
  parent       = urlencode("cloudresourcemanager.googleapis.com/projects/${var.project_id}")
  name         = "${local.name}-guardrails"
  display_name = "Guardrails lab11"

  rules {
    description = "Prohibir llaves JSON de service accounts y tocar sinks de auditoría"
    deny_rule {
      denied_principals = ["principalSet://goog/public:all"]
      exception_principals = [
        for m in var.deny_exception_principals : m
      ]
      # Protección de sinks opcional: si se activa, quien ejecuta terraform destroy debe ser excepción
      denied_permissions = concat(
        ["iam.googleapis.com/serviceAccountKeys.create", "iam.googleapis.com/serviceAccountKeys.upload"],
        var.protect_audit_sinks ? [
          "logging.googleapis.com/sinks.delete",
          "logging.googleapis.com/sinks.update",
          "logging.googleapis.com/buckets.delete",
        ] : []
      )
    }
  }

  depends_on = [module.services]
}

# SA de prueba: el smoke test intenta crearle una llave (debe fallar por la deny policy)
module "probe_sa" {
  source       = "../../modules/service-account"
  project_id   = var.project_id
  account_id   = "${local.name}-probe"
  display_name = "Prueba de deny policy (sin permisos)"
  depends_on   = [module.services]
}

# =============================================================================
# 4. RBAC por función
# =============================================================================
resource "google_project_iam_custom_role" "deployer" {
  role_id     = replace("${local.name}_deployer", "-", "_")
  title       = "03-cloud-e-infraestructura/lab11-terraform-gcp deployer (mínimo para desplegar funciones)"
  description = "Despliega Cloud Run functions sin poder administrar IAM"
  permissions = [
    "cloudfunctions.functions.create",
    "cloudfunctions.functions.update",
    "cloudfunctions.functions.get",
    "cloudfunctions.functions.list",
    "cloudfunctions.operations.get",
    "run.services.get",
    "run.services.list",
    "run.services.update",
    "storage.objects.create",
    "storage.objects.get",
    "iam.serviceAccounts.actAs",
  ]
}

locals {
  rbac = {
    developer = concat(["roles/run.developer", "roles/datastore.user", "roles/logging.viewer", "roles/monitoring.viewer"],
    ["projects/${var.project_id}/roles/${google_project_iam_custom_role.deployer.role_id}"])
    sre     = ["roles/monitoring.editor", "roles/logging.viewer", "roles/compute.viewer", "roles/run.viewer", "roles/errorreporting.viewer"]
    auditor = ["roles/iam.securityReviewer", "roles/logging.privateLogViewer", "roles/cloudasset.viewer"]
    finops  = ["roles/recommender.viewer", "roles/billing.projectManager"]
  }

  rbac_bindings = merge([
    for team, roles in local.rbac : {
      for pair in setproduct(roles, lookup(var.rbac_members, team, [])) :
      "${team}|${pair[0]}|${pair[1]}" => { role = pair[0], member = pair[1] }
    }
  ]...)
}

resource "google_project_iam_member" "rbac" {
  for_each = local.rbac_bindings
  project  = var.project_id
  role     = each.value.role
  member   = each.value.member
}

# Break-glass: owner TEMPORAL que expira solo (IAM Condition de tiempo)
resource "google_project_iam_member" "break_glass" {
  for_each = var.break_glass_until == null ? toset([]) : toset(var.break_glass_members)
  project  = var.project_id
  role     = "roles/owner"
  member   = each.value

  condition {
    title       = "break-glass-hasta-${replace(var.break_glass_until, ":", "-")}"
    description = "Acceso de emergencia con caducidad automática"
    expression  = "request.time < timestamp(\"${var.break_glass_until}\")"
  }
}

# =============================================================================
# 5. Opcional con organización: SCC -> Pub/Sub y VPC Service Controls
# =============================================================================
resource "google_pubsub_topic" "scc_findings" {
  count      = var.org_id == null ? 0 : 1
  name       = "${local.name}-scc-findings"
  depends_on = [module.services]
}

resource "google_scc_v2_organization_notification_config" "findings" {
  count        = var.org_id == null ? 0 : 1
  config_id    = "${local.name}-high-findings"
  organization = var.org_id
  location     = "global"
  description  = "Hallazgos HIGH/CRITICAL activos del proyecto"
  pubsub_topic = google_pubsub_topic.scc_findings[0].id

  streaming_config {
    filter = "state=\"ACTIVE\" AND (severity=\"HIGH\" OR severity=\"CRITICAL\") AND resource.project_display_name=\"${var.project_id}\""
  }
}

resource "google_access_context_manager_service_perimeter" "data" {
  count  = var.access_policy_id == null ? 0 : 1
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/${replace(local.name, "-", "_")}_data"
  title  = "${local.name}-data"

  # Modo dry-run primero: registra violaciones sin bloquear (cámbialo a status cuando no haya falsos positivos)
  use_explicit_dry_run_spec = true
  spec {
    resources           = ["projects/${data.google_project.this.number}"]
    restricted_services = ["storage.googleapis.com", "bigquery.googleapis.com", "secretmanager.googleapis.com"]
  }
}
