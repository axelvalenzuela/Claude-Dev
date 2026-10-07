# Productivo de referencia: HANA primario + secundario (HSR) en 2 AZ.
# Los tamanos DEBEN salir del sizing (Quick Sizer), no de este ejemplo.
environment        = "prd"
region             = "us-east-1"
ha_enabled         = true
hana_instance_type = "r6i.24xlarge" # 768 GiB de RAM; verificar certificacion
app_instance_type  = "m6i.4xlarge"
app_servers        = ["ascs-pas", "aas1"]
admin_cidrs        = [] # rangos corporativos / VPN

backup_retention_days = 730

hana_volumes = {
  data_gb         = 1000 # >= 1.2 x RAM
  log_gb          = 384  # ~0.5 x RAM
  shared_gb       = 768  # ~1 x RAM
  backup_gb       = 1536 # >= 2 x RAM
  data_iops       = 16000
  data_throughput = 1000
  log_iops        = 16000
  log_throughput  = 1000
}
