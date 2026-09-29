# Presupuesto con alertas por correo al 50 %, 90 % y 100 %.
# IMPORTANTE: un presupuesto AVISA, no DETIENE el gasto. Para cortar el gasto
# hay que apagar recursos (terraform destroy) o desligar la facturación.
# Solo se crea si defines billing_account_id (necesitas rol de administrador
# de facturación o "Billing Account Costs Manager" en esa cuenta).
data "google_project" "actual" {}

resource "google_billing_budget" "lab" {
  count = var.billing_account_id == "" ? 0 : 1

  billing_account = var.billing_account_id
  display_name    = "lab8-migracion-sas"

  budget_filter {
    projects = ["projects/${data.google_project.actual.number}"]
  }

  amount {
    specified_amount {
      currency_code = var.moneda_presupuesto
      units         = tostring(var.presupuesto_mensual)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.9
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  depends_on = [google_project_service.apis]
}
