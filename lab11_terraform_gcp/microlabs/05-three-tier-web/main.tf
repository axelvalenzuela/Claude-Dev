# Micro lab 05 (GCP) - Arquitectura web de 3 niveles
#   Web:   Global external Application Load Balancer + Cloud Armor (WAF OWASP + rate limit)
#   App:   Managed Instance Group REGIONAL (multi-zona), autohealing, autoscaling, sin IP pública, OS Login
#   Datos: Cloud SQL PostgreSQL HA (REGIONAL), solo IP privada (PSA), TLS obligatorio, PITR, Secret Manager

locals {
  name    = "lab11-${var.environment}-3t"
  db_user = "app"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "05-three-tier-web"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "servicenetworking.googleapis.com",
    "secretmanager.googleapis.com",
    "iap.googleapis.com",
  ]
}

# =============================================================================
# Red
# =============================================================================
module "vpc" {
  source                        = "../../modules/vpc"
  project_id                    = var.project_id
  name                          = local.name
  region                        = var.region
  subnets                       = { app = var.app_subnet_cidr }
  enable_nat                    = true
  enable_private_service_access = true
  health_check_ports            = [tostring(var.app_port)]
  health_check_target_tags      = ["${local.name}-app"]
  depends_on                    = [module.services]
}

# =============================================================================
# Capa de datos
# =============================================================================
resource "random_password" "db" {
  length  = 24
  special = false
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "${local.name}-db-password"
  replication {
    auto {}
  }
  depends_on = [module.services]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db.result
}

resource "google_sql_database_instance" "db" {
  name                = "${local.name}-pg"
  database_version    = var.db_version
  region              = var.region
  deletion_protection = var.deletion_protection

  settings {
    tier              = var.db_tier
    edition           = "ENTERPRISE"
    availability_type = var.db_high_availability ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = var.db_disk_gb
    disk_autoresize   = true
    user_labels       = local.common_labels

    ip_configuration {
      ipv4_enabled    = false # sin IP pública
      private_network = module.vpc.network_id
      ssl_mode        = "ENCRYPTED_ONLY"
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "08:00"
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
      }
    }

    maintenance_window {
      day  = 7
      hour = 9
    }

    insights_config {
      query_insights_enabled  = true
      record_application_tags = true
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }
  }

  depends_on = [module.vpc]
}

resource "google_sql_database" "app" {
  name     = "appdb"
  instance = google_sql_database_instance.db.name
}

resource "google_sql_user" "app" {
  name     = local.db_user
  instance = google_sql_database_instance.db.name
  password = random_password.db.result
}

# =============================================================================
# Capa app
# =============================================================================
module "app_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-app"
  display_name  = "VMs de la capa app"
  project_roles = ["roles/logging.logWriter", "roles/monitoring.metricWriter"]
  depends_on    = [module.services]
}

resource "google_secret_manager_secret_iam_member" "app_reads_password" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = module.app_sa.member
}

resource "google_compute_instance_template" "app" {
  name_prefix  = "${local.name}-app-"
  machine_type = var.machine_type
  tags         = ["${local.name}-app"]
  labels       = local.common_labels

  disk {
    source_image = "projects/debian-cloud/global/images/family/debian-12"
    disk_size_gb = 10
    disk_type    = "pd-balanced"
    auto_delete  = true
    boot         = true
  }

  network_interface {
    subnetwork = module.vpc.subnet_self_links["app"]
    # Sin access_config: no hay IP pública (salida por Cloud NAT)
  }

  service_account {
    email  = module.app_sa.email
    scopes = ["cloud-platform"]
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  metadata = {
    enable-oslogin = "TRUE"
    startup-script = templatefile("${path.module}/startup.sh.tpl", {
      app_port   = var.app_port
      project_id = var.project_id
      db_secret  = google_secret_manager_secret.db_password.secret_id
      db_host    = google_sql_database_instance.db.private_ip_address
      db_name    = google_sql_database.app.name
      db_user    = local.db_user
    })
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_health_check" "app" {
  name                = "${local.name}-hc"
  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3

  http_health_check {
    port         = var.app_port
    request_path = "/health"
  }

  log_config {
    enable = true
  }
}

resource "google_compute_region_instance_group_manager" "app" {
  name               = "${local.name}-mig"
  region             = var.region
  base_instance_name = "${local.name}-app"

  version {
    instance_template = google_compute_instance_template.app.id
  }

  named_port {
    name = "http"
    port = var.app_port
  }

  # Autohealing: recrea VMs que fallan el health check
  auto_healing_policies {
    health_check      = google_compute_health_check.app.id
    initial_delay_sec = 180
  }

  # Despliegues sin caída al cambiar la plantilla
  update_policy {
    type                         = "PROACTIVE"
    minimal_action               = "REPLACE"
    max_surge_fixed              = 3
    max_unavailable_fixed        = 0
    instance_redistribution_type = "PROACTIVE"
  }
}

resource "google_compute_region_autoscaler" "app" {
  name   = "${local.name}-autoscaler"
  region = var.region
  target = google_compute_region_instance_group_manager.app.id

  autoscaling_policy {
    min_replicas    = var.min_replicas
    max_replicas    = var.max_replicas
    cooldown_period = 90

    cpu_utilization {
      target = 0.6
    }
  }
}

# =============================================================================
# Capa web: Load Balancer global + Cloud Armor
# =============================================================================
resource "google_compute_security_policy" "waf" {
  name        = "${local.name}-armor"
  description = "WAF OWASP + rate limit por IP"

  rule {
    action      = "deny(403)"
    priority    = 1000
    description = "SQL injection"
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 1})"
      }
    }
  }

  rule {
    action      = "deny(403)"
    priority    = 1010
    description = "Cross-site scripting"
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('xss-v33-stable', {'sensitivity': 1})"
      }
    }
  }

  rule {
    action      = "rate_based_ban"
    priority    = 2000
    description = "Rate limit por IP"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action   = "allow"
      exceed_action    = "deny(429)"
      enforce_on_key   = "IP"
      ban_duration_sec = 120
      rate_limit_threshold {
        count        = var.rate_limit_per_minute
        interval_sec = 60
      }
    }
  }

  rule {
    action      = "allow"
    priority    = 2147483647
    description = "Default"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }

  depends_on = [module.services]
}

resource "google_compute_backend_service" "app" {
  name                  = "${local.name}-backend"
  protocol              = "HTTP"
  port_name             = "http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  timeout_sec           = 30
  health_checks         = [google_compute_health_check.app.id]
  security_policy       = google_compute_security_policy.waf.id

  backend {
    group           = google_compute_region_instance_group_manager.app.instance_group
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_url_map" "app" {
  name            = "${local.name}-urlmap"
  default_service = google_compute_backend_service.app.id
}

resource "google_compute_target_http_proxy" "app" {
  name    = "${local.name}-http"
  url_map = google_compute_url_map.app.id
}

resource "google_compute_global_address" "lb" {
  name = "${local.name}-ip"
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "${local.name}-http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.lb.id
  port_range            = "80"
  target                = google_compute_target_http_proxy.app.id
}

# HTTPS opcional con certificado administrado (requiere un dominio que apunte a la IP)
resource "google_compute_managed_ssl_certificate" "app" {
  count = var.domain == null ? 0 : 1
  name  = "${local.name}-cert"
  managed {
    domains = [var.domain]
  }
}

resource "google_compute_target_https_proxy" "app" {
  count            = var.domain == null ? 0 : 1
  name             = "${local.name}-https"
  url_map          = google_compute_url_map.app.id
  ssl_certificates = [google_compute_managed_ssl_certificate.app[0].id]
}

resource "google_compute_global_forwarding_rule" "https" {
  count                 = var.domain == null ? 0 : 1
  name                  = "${local.name}-https"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.lb.id
  port_range            = "443"
  target                = google_compute_target_https_proxy.app[0].id
}
