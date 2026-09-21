# Sandbox / desarrollo: un nodo HANA, sin HA.
# Verificar que el tipo de instancia este certificado para HANA en el
# directorio de plataformas certificadas de SAP antes de aplicar.
environment          = "dev"
region               = "us-east-1"
ha_enabled           = false
hana_instance_type   = "r6i.8xlarge" # 256 GiB de RAM
app_instance_type    = "m6i.2xlarge"
app_servers          = ["ascs-pas"]
admin_cidrs          = [] # agregar tu IP/32 o el rango de la VPN
backup_force_destroy = true

hana_volumes = {
  data_gb         = 320 # >= 1.2 x RAM
  log_gb          = 128 # ~0.5 x RAM
  shared_gb       = 256 # ~1 x RAM
  backup_gb       = 512 # >= 2 x RAM
  data_iops       = 6000
  data_throughput = 400
  log_iops        = 6000
  log_throughput  = 300
}
