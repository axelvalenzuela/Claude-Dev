# Módulo: VPC custom de GCP.
#   - Subnets regionales con Private Google Access y flow logs
#   - Cloud Router + Cloud NAT opcional (salida sin IPs públicas)
#   - Firewall: deny-all de entrada (con logs) + reglas explícitas (IAP, health checks)
#   - Private Service Access opcional (Cloud SQL / Memorystore con IP privada)

resource "google_compute_network" "this" {
  name                            = var.name
  project                         = var.project_id
  auto_create_subnetworks         = false
  routing_mode                    = "REGIONAL"
  delete_default_routes_on_create = false
}

resource "google_compute_subnetwork" "this" {
  for_each                 = var.subnets
  name                     = "${var.name}-${each.key}"
  project                  = var.project_id
  region                   = var.region
  network                  = google_compute_network.this.id
  ip_cidr_range            = each.value
  private_ip_google_access = true

  dynamic "secondary_ip_range" {
    for_each = lookup(var.secondary_ranges, each.key, {})
    content {
      range_name    = secondary_ip_range.key
      ip_cidr_range = secondary_ip_range.value
    }
  }

  dynamic "log_config" {
    for_each = var.enable_flow_logs ? [1] : []
    content {
      aggregation_interval = "INTERVAL_5_SEC"
      flow_sampling        = 0.5
      metadata             = "INCLUDE_ALL_METADATA"
    }
  }
}

# ---------------- Cloud NAT ----------------
resource "google_compute_router" "this" {
  count   = var.enable_nat ? 1 : 0
  name    = "${var.name}-router"
  project = var.project_id
  region  = var.region
  network = google_compute_network.this.id
}

resource "google_compute_router_nat" "this" {
  count                              = var.enable_nat ? 1 : 0
  name                               = "${var.name}-nat"
  project                            = var.project_id
  region                             = var.region
  router                             = google_compute_router.this[0].name
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# ---------------- Firewall ----------------
resource "google_compute_firewall" "deny_all_ingress" {
  name      = "${var.name}-deny-all-ingress"
  project   = var.project_id
  network   = google_compute_network.this.id
  direction = "INGRESS"
  priority  = 65534

  deny {
    protocol = "all"
  }

  source_ranges = ["0.0.0.0/0"]

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "iap_ssh" {
  count     = var.allow_iap_ssh ? 1 : 0
  name      = "${var.name}-allow-iap-ssh"
  project   = var.project_id
  network   = google_compute_network.this.id
  direction = "INGRESS"
  priority  = 1000

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # Rango de Identity-Aware Proxy: SSH sin IP pública ni bastion
  source_ranges = ["35.235.240.0/20"]
}

resource "google_compute_firewall" "health_checks" {
  count     = length(var.health_check_ports) > 0 ? 1 : 0
  name      = "${var.name}-allow-health-checks"
  project   = var.project_id
  network   = google_compute_network.this.id
  direction = "INGRESS"
  priority  = 1000

  allow {
    protocol = "tcp"
    ports    = var.health_check_ports
  }

  # Rangos de los health checks y del proxy del balanceador de Google
  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = var.health_check_target_tags
}

# ---------------- Private Service Access ----------------
resource "google_compute_global_address" "psa" {
  count         = var.enable_private_service_access ? 1 : 0
  name          = "${var.name}-psa"
  project       = var.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20
  network       = google_compute_network.this.id
}

resource "google_service_networking_connection" "psa" {
  count                   = var.enable_private_service_access ? 1 : 0
  network                 = google_compute_network.this.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.psa[0].name]
  deletion_policy         = "ABANDON"
}
