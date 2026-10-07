# Micro lab 06 (GCP) - Kubernetes administrado: GKE Autopilot
#   Cluster regional privado (nodos sin IP pública), Workload Identity, Dataplane V2 (NetworkPolicy)
#   Workload endurecido: Pod Security "restricted", non-root, probes, HPA, PDB, NetworkPolicy
#   Todo con Terraform: infraestructura (google) + objetos de Kubernetes (kubernetes provider)

locals {
  name      = "lab11-${var.environment}-gke"
  namespace = "lab11-app"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "06-gke-autopilot"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "container.googleapis.com",
    "compute.googleapis.com",
    "artifactregistry.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
  ]
}

module "vpc" {
  source     = "../../modules/vpc"
  project_id = var.project_id
  name       = local.name
  region     = var.region
  subnets    = { nodes = var.nodes_cidr }
  secondary_ranges = {
    nodes = {
      pods     = var.pods_cidr
      services = var.services_cidr
    }
  }
  enable_nat = true # nodos privados descargan imágenes externas por Cloud NAT
  depends_on = [module.services]
}

# ---------------- Cluster ----------------
resource "google_container_cluster" "this" {
  name                = local.name
  location            = var.region
  enable_autopilot    = true
  network             = module.vpc.network_id
  subnetwork          = module.vpc.subnet_ids["nodes"]
  deletion_protection = var.deletion_protection

  release_channel {
    channel = "REGULAR"
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
  }

  master_authorized_networks_config {
    dynamic "cidr_blocks" {
      for_each = var.authorized_networks
      content {
        cidr_block   = cidr_blocks.value
        display_name = "admin-${cidr_blocks.key}"
      }
    }
  }

  # Mantenimiento fuera del horario de clases
  maintenance_policy {
    recurring_window {
      start_time = "2026-01-01T08:00:00Z"
      end_time   = "2026-01-01T12:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SA,SU"
    }
  }

  resource_labels = local.common_labels
}

# ---------------- Workload Identity: KSA -> GSA ----------------
module "app_gsa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-app"
  display_name  = "Identidad de Google del workload"
  project_roles = ["roles/logging.logWriter", "roles/monitoring.metricWriter"]
  depends_on    = [module.services]
}

resource "google_service_account_iam_member" "workload_identity" {
  service_account_id = module.app_gsa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${local.namespace}/app]"
  depends_on         = [google_container_cluster.this]
}

# ---------------- Kubernetes ----------------
data "google_client_config" "this" {}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.this.endpoint}"
  token                  = data.google_client_config.this.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.this.master_auth[0].cluster_ca_certificate)
}

resource "kubernetes_namespace_v1" "app" {
  metadata {
    name = local.namespace
    labels = {
      "pod-security.kubernetes.io/enforce" = "restricted"
      "pod-security.kubernetes.io/warn"    = "restricted"
    }
  }
}

resource "kubernetes_service_account_v1" "app" {
  metadata {
    name      = "app"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
    annotations = {
      "iam.gke.io/gcp-service-account" = module.app_gsa.email
    }
  }
}

resource "kubernetes_deployment_v1" "app" {
  metadata {
    name      = "web"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
    labels    = { app = "web" }
  }

  spec {
    replicas = var.min_replicas

    selector {
      match_labels = { app = "web" }
    }

    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_surge       = "1"
        max_unavailable = "0"
      }
    }

    template {
      metadata {
        labels = { app = "web" }
      }

      spec {
        service_account_name = kubernetes_service_account_v1.app.metadata[0].name

        security_context {
          run_as_non_root = true
          seccomp_profile {
            type = "RuntimeDefault"
          }
        }

        # Reparte réplicas entre zonas
        topology_spread_constraint {
          max_skew           = 1
          topology_key       = "topology.kubernetes.io/zone"
          when_unsatisfiable = "ScheduleAnyway"
          label_selector {
            match_labels = { app = "web" }
          }
        }

        container {
          name  = "web"
          image = var.image

          port {
            container_port = 8080
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "256Mi"
            }
            limits = {
              memory = "256Mi"
            }
          }

          security_context {
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            capabilities {
              drop = ["ALL"]
            }
          }

          readiness_probe {
            http_get {
              path = "/"
              port = 8080
            }
            period_seconds = 5
          }

          liveness_probe {
            http_get {
              path = "/"
              port = 8080
            }
            initial_delay_seconds = 10
            period_seconds        = 10
          }

          volume_mount {
            name       = "tmp"
            mount_path = "/tmp"
          }
        }

        volume {
          name = "tmp"
          empty_dir {}
        }
      }
    }
  }

  # El HPA controla las réplicas después del primer despliegue
  lifecycle {
    ignore_changes = [spec[0].replicas]
  }
}

resource "kubernetes_service_v1" "app" {
  metadata {
    name      = "web"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  spec {
    type     = "LoadBalancer"
    selector = { app = "web" }

    port {
      port        = 80
      target_port = 8080
    }
  }
}

resource "kubernetes_horizontal_pod_autoscaler_v2" "app" {
  metadata {
    name      = "web"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  spec {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment_v1.app.metadata[0].name
    }

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = 60
        }
      }
    }
  }
}

resource "kubernetes_pod_disruption_budget_v1" "app" {
  metadata {
    name      = "web"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  spec {
    min_available = "1"
    selector {
      match_labels = { app = "web" }
    }
  }
}

# Zero-trust dentro del namespace: todo denegado salvo el tráfico HTTP hacia web
resource "kubernetes_network_policy_v1" "default_deny" {
  metadata {
    name      = "default-deny-ingress"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  spec {
    pod_selector {}
    policy_types = ["Ingress"]
  }
}

resource "kubernetes_network_policy_v1" "allow_web" {
  metadata {
    name      = "allow-web-8080"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = { app = "web" }
    }

    ingress {
      ports {
        port     = "8080"
        protocol = "TCP"
      }
    }

    policy_types = ["Ingress"]
  }
}
