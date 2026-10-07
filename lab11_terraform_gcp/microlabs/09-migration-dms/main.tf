# Micro lab 09 (GCP) - Migración de bases de datos con Database Migration Service (DMS)
#   Origen: PostgreSQL 15 "on-premises" simulado en una VM (pglogical) o tu servidor real
#   Destino: Cloud SQL PostgreSQL creado por DMS, solo IP privada
#   Job CONTINUOUS (full dump + CDC) sobre VPC peering -> promote = cutover
# Para servidores completos (VMs) GCP usa Migrate to Virtual Machines: ver README.

data "google_project" "this" {}

locals {
  name = "lab11-${var.environment}-dms"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "09-migration-dms"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "datamigration.googleapis.com",
    "sqladmin.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
    "secretmanager.googleapis.com",
  ]
}

module "vpc" {
  source                        = "../../modules/vpc"
  project_id                    = var.project_id
  name                          = local.name
  region                        = var.region
  subnets                       = { onprem = var.source_subnet_cidr }
  enable_nat                    = true
  enable_private_service_access = true
  depends_on                    = [module.services]
}

# ---------------- Credenciales ----------------
resource "random_password" "migration" {
  length  = 24
  special = false
}

resource "random_password" "root" {
  length  = 24
  special = false
}

resource "google_secret_manager_secret" "migration" {
  secret_id = "${local.name}-migration-password"
  replication {
    auto {}
  }
  depends_on = [module.services]
}

resource "google_secret_manager_secret_version" "migration" {
  secret      = google_secret_manager_secret.migration.id
  secret_data = random_password.migration.result
}

# ---------------- Origen simulado ----------------
module "source_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-src"
  display_name  = "VM de origen simulada"
  project_roles = ["roles/logging.logWriter"]
  depends_on    = [module.services]
}

resource "google_secret_manager_secret_iam_member" "source_reads" {
  secret_id = google_secret_manager_secret.migration.id
  role      = "roles/secretmanager.secretAccessor"
  member    = module.source_sa.member
}

resource "google_compute_instance" "source" {
  count        = var.create_demo_source ? 1 : 0
  name         = "${local.name}-onprem-pg"
  zone         = "${var.region}-a"
  machine_type = "e2-medium"
  tags         = ["${local.name}-source"]
  labels       = local.common_labels

  boot_disk {
    initialize_params {
      image = "projects/debian-cloud/global/images/family/debian-12"
      size  = 20
    }
  }

  network_interface {
    subnetwork = module.vpc.subnet_self_links["onprem"]
  }

  service_account {
    email  = module.source_sa.email
    scopes = ["cloud-platform"]
  }

  shielded_instance_config {
    enable_secure_boot = true
  }

  metadata = {
    enable-oslogin = "TRUE"
    startup-script = templatefile("${path.module}/source-startup.sh.tpl", {
      project_id   = var.project_id
      secret_id    = google_secret_manager_secret.migration.secret_id
      allowed_cidr = "10.0.0.0/8"
    })
  }

  depends_on = [google_secret_manager_secret_version.migration, google_secret_manager_secret_iam_member.source_reads]
}

# DMS y Cloud SQL llegan desde el rango de Private Service Access (peering)
resource "google_compute_firewall" "dms_to_source" {
  name          = "${local.name}-allow-dms-5432"
  network       = module.vpc.network_id
  direction     = "INGRESS"
  priority      = 1000
  source_ranges = ["10.0.0.0/8"]
  target_tags   = ["${local.name}-source"]

  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }
}

locals {
  source_host = var.create_demo_source ? google_compute_instance.source[0].network_interface[0].network_ip : var.source_host
}

# ---------------- Perfiles de conexión ----------------
resource "google_database_migration_service_connection_profile" "source" {
  location              = var.region
  connection_profile_id = "${local.name}-source"
  display_name          = "Origen PostgreSQL on-prem"
  labels                = local.common_labels

  postgresql {
    host     = local.source_host
    port     = 5432
    username = "migration"
    password = random_password.migration.result
  }

  depends_on = [module.services]
}

# DMS crea y administra la instancia de Cloud SQL de destino
resource "google_database_migration_service_connection_profile" "destination" {
  location              = var.region
  connection_profile_id = "${local.name}-destination"
  display_name          = "Destino Cloud SQL"
  labels                = local.common_labels

  cloudsql {
    settings {
      database_version          = "POSTGRES_15"
      tier                      = var.destination_tier
      edition                   = "ENTERPRISE"
      storage_auto_resize_limit = "0"
      activation_policy         = "ALWAYS"
      auto_storage_increase     = true
      data_disk_type            = "PD_SSD"
      data_disk_size_gb         = "20"
      zone                      = "${var.region}-b"
      source_id                 = "projects/${var.project_id}/locations/${var.region}/connectionProfiles/${google_database_migration_service_connection_profile.source.connection_profile_id}"
      root_password             = random_password.root.result
      user_labels               = local.common_labels

      ip_config {
        enable_ipv4     = false
        private_network = module.vpc.network_id
        require_ssl     = false
      }
    }
  }

  depends_on = [module.vpc]
}

# ---------------- Job de migración ----------------
resource "google_database_migration_service_migration_job" "this" {
  location         = var.region
  migration_job_id = "${local.name}-job"
  display_name     = "on-prem ventas -> Cloud SQL"
  type             = "CONTINUOUS" # dump completo + replicación continua (CDC) hasta el cutover
  source           = google_database_migration_service_connection_profile.source.name
  destination      = google_database_migration_service_connection_profile.destination.name
  labels           = local.common_labels

  vpc_peering_connectivity {
    vpc = module.vpc.network_id
  }

  # Terraform crea el job en estado NOT_STARTED; verify/start/promote se operan con scripts/migrate.sh
}
