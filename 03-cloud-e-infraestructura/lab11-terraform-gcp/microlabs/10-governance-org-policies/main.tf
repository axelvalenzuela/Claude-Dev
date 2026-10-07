# Micro lab 10 (GCP) - Gobernanza de organización (equivalente a CloudFormation StackSets + SCPs)
#   Jerarquía: Organización -> carpeta 03-cloud-e-infraestructura/lab11-terraform-gcp -> carpetas por entorno (dev, prod)
#   Organization Policies heredadas por carpeta · Tags con política condicional · Firewall jerárquico
#   Fábrica de proyectos: cada proyecto recibe el mismo baseline (APIs, auditoría, presupuesto, sin red default)
# Requiere una ORGANIZACIÓN (Cloud Identity / Workspace) y permisos de admin de carpetas y org policies.

locals {
  parent = var.parent_folder_id == null ? "organizations/${var.org_id}" : "folders/${var.parent_folder_id}"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "10-governance-org-policies"
  }

  # Políticas booleanas que se aplican a la carpeta raíz del lab (y se heredan)
  boolean_policies = {
    "iam.disableServiceAccountKeyCreation"  = "Sin llaves JSON de service accounts: usar WIF o SA adjuntas"
    "storage.uniformBucketLevelAccess"      = "Buckets sin ACLs"
    "storage.publicAccessPrevention"        = "Buckets nunca públicos"
    "compute.requireOsLogin"                = "SSH solo con identidades de Google (OS Login)"
    "compute.skipDefaultNetworkCreation"    = "Proyectos nuevos sin red default"
    "sql.restrictPublicIp"                  = "Cloud SQL sin IP pública"
    "compute.restrictXpnProjectLienRemoval" = "Protege los host projects de Shared VPC"
  }
}

# ---------------- Jerarquía ----------------
resource "google_folder" "root" {
  display_name        = "lab11-${var.environment}"
  parent              = local.parent
  deletion_protection = false
}

resource "google_folder" "env" {
  for_each            = toset(var.environments)
  display_name        = each.value
  parent              = google_folder.root.name
  deletion_protection = false
}

# ---------------- Organization Policies (guardrails preventivos) ----------------
resource "google_org_policy_policy" "boolean" {
  for_each = local.boolean_policies
  name     = "${google_folder.root.name}/policies/${each.key}"
  parent   = google_folder.root.name

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

resource "google_org_policy_policy" "no_external_ip" {
  name   = "${google_folder.root.name}/policies/compute.vmExternalIpAccess"
  parent = google_folder.root.name

  spec {
    rules {
      deny_all = "TRUE"
    }
  }
}

resource "google_org_policy_policy" "locations" {
  name   = "${google_folder.root.name}/policies/gcp.resourceLocations"
  parent = google_folder.root.name

  spec {
    rules {
      values {
        allowed_values = var.allowed_locations
      }
    }
  }
}

# ---------------- Tags + política condicional ----------------
resource "google_tags_tag_key" "env" {
  parent      = "organizations/${var.org_id}"
  short_name  = "lab11-environment"
  description = "Entorno del recurso"
}

resource "google_tags_tag_value" "env" {
  for_each   = toset(var.environments)
  parent     = google_tags_tag_key.env.id
  short_name = each.value
}

resource "google_tags_tag_binding" "env_folder" {
  for_each  = toset(var.environments)
  parent    = "//cloudresourcemanager.googleapis.com/${google_folder.env[each.key].name}"
  tag_value = google_tags_tag_value.env[each.key].id
}

# En dev se permiten servicios extra para experimentar; en prod no (regla condicionada por tag)
resource "google_org_policy_policy" "restrict_services" {
  name   = "${google_folder.root.name}/policies/gcp.restrictServiceUsage"
  parent = google_folder.root.name

  spec {
    rules {
      condition {
        title      = "dev permite todo"
        expression = "resource.matchTag('${var.org_id}/lab11-environment', 'dev')"
      }
      allow_all = "TRUE"
    }
    rules {
      values {
        denied_values = var.prod_denied_services
      }
    }
  }

  depends_on = [google_tags_tag_value.env]
}

# ---------------- Firewall jerárquico ----------------
resource "google_compute_firewall_policy" "baseline" {
  parent      = google_folder.root.name
  short_name  = "lab11-${var.environment}-baseline"
  description = "Reglas que ningún proyecto de la carpeta puede relajar"
}

resource "google_compute_firewall_policy_rule" "allow_iap" {
  firewall_policy = google_compute_firewall_policy.baseline.name
  priority        = 1000
  action          = "allow"
  direction       = "INGRESS"
  description     = "SSH/RDP solo vía IAP"
  enable_logging  = true

  match {
    src_ip_ranges = ["35.235.240.0/20"]
    layer4_configs {
      ip_protocol = "tcp"
      ports       = ["22", "3389"]
    }
  }
}

resource "google_compute_firewall_policy_rule" "deny_admin_ports" {
  firewall_policy = google_compute_firewall_policy.baseline.name
  priority        = 1100
  action          = "deny"
  direction       = "INGRESS"
  description     = "SSH/RDP desde Internet prohibido"
  enable_logging  = true

  match {
    src_ip_ranges = ["0.0.0.0/0"]
    layer4_configs {
      ip_protocol = "tcp"
      ports       = ["22", "3389"]
    }
  }
}

resource "google_compute_firewall_policy_association" "baseline" {
  firewall_policy   = google_compute_firewall_policy.baseline.id
  attachment_target = google_folder.root.name
  name              = "lab11-${var.environment}-baseline"
}

# ---------------- Fábrica de proyectos ----------------
module "projects" {
  source           = "./modules/project-baseline"
  for_each         = var.projects
  name             = each.key
  project_id       = "${each.key}-${var.project_suffix}"
  folder_id        = google_folder.env[each.value.environment].name
  billing_account  = var.billing_account
  services         = concat(var.baseline_services, each.value.extra_services)
  operator_members = each.value.operators
  monthly_budget   = each.value.monthly_budget
  labels           = merge(local.common_labels, { environment = each.value.environment, app = each.key })

  depends_on = [google_org_policy_policy.boolean]
}
