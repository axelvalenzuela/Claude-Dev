variable "region" {
  type        = string
  default     = "us-east-1"
  description = "Region de AWS."
}

variable "project" {
  type        = string
  default     = "s4hana"
  description = "Nombre del proyecto (prefijo de recursos)."
}

variable "environment" {
  type        = string
  description = "Entorno: dev, qas o prd."

  validation {
    condition     = contains(["dev", "qas", "prd"], var.environment)
    error_message = "environment debe ser dev, qas o prd."
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.60.0.0/16"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  default     = ["10.60.1.0/24", "10.60.2.0/24"]
  description = "Dos subredes privadas, una por AZ."
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.60.100.0/24"
}

variable "admin_cidrs" {
  type        = list(string)
  default     = []
  description = "CIDRs con acceso a SAP GUI y HTTPS. Usar rangos concretos, nunca 0.0.0.0/0."

  validation {
    condition     = !contains(var.admin_cidrs, "0.0.0.0/0")
    error_message = "No se permite 0.0.0.0/0 en admin_cidrs."
  }
}

variable "sap_instance_number" {
  type        = string
  default     = "00"
  description = "Numero de instancia SAP (NN), dos digitos."

  validation {
    condition     = can(regex("^[0-9]{2}$", var.sap_instance_number))
    error_message = "sap_instance_number debe tener exactamente dos digitos."
  }
}

variable "ha_enabled" {
  type        = bool
  default     = false
  description = "true crea un segundo nodo HANA en otra AZ (destino de System Replication)."
}

variable "ami_id" {
  type        = string
  default     = null
  description = "AMI de SLES/RHEL for SAP. Si es null se busca con ami_name_pattern."
}

variable "ami_name_pattern" {
  type    = string
  default = "suse-sles-sap-15-sp*-v*-hvm-ssd-x86_64"
}

variable "ami_owners" {
  type    = list(string)
  default = ["amazon", "aws-marketplace"]
}

variable "hana_instance_type" {
  type        = string
  description = "Tipo de instancia certificado para SAP HANA."
}

variable "hana_volumes" {
  type = object({
    data_gb         = number
    log_gb          = number
    shared_gb       = number
    backup_gb       = number
    data_iops       = number
    data_throughput = number
    log_iops        = number
    log_throughput  = number
  })
  description = "Tamano y rendimiento de discos HANA (ver PREREQUISITOS.md, seccion 4)."
}

variable "app_instance_type" {
  type = string
}

variable "app_servers" {
  type        = list(string)
  default     = ["ascs-pas"]
  description = "Nombres de servidores de aplicacion a crear."
}

variable "backup_retention_days" {
  type    = number
  default = 365
}

variable "backup_force_destroy" {
  type        = bool
  default     = false
  description = "Permite destruir el bucket de backup con datos. Solo laboratorio."
}

variable "extra_tags" {
  type    = map(string)
  default = {}
}
