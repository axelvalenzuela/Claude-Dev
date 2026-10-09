variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "aie"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "owner" {
  type = string
}

variable "cost_center" {
  type    = string
  default = "training"
}

variable "audit_log_retention_days" {
  description = "Retención de CloudTrail/Config (365+ para cumplimiento)."
  type        = number
  default     = 365
}

variable "record_global_resources" {
  description = "Registrar recursos globales (IAM) en AWS Config: actívalo solo en UNA región."
  type        = bool
  default     = true
}

variable "config_recording_frequency" {
  description = "CONTINUOUS | DAILY (DAILY reduce costo en laboratorio)."
  type        = string
  default     = "DAILY"
}

variable "config_managed_rules" {
  description = "Reglas administradas de AWS Config => input_parameters JSON (\"\" si no aplica)."
  type        = map(string)
  default = {
    ROOT_ACCOUNT_MFA_ENABLED                 = ""
    IAM_USER_MFA_ENABLED                     = ""
    ACCESS_KEYS_ROTATED                      = "{\"maxAccessKeyAge\":\"90\"}"
    S3_BUCKET_SSL_REQUESTS_ONLY              = ""
    S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED = ""
    ENCRYPTED_VOLUMES                        = ""
    RDS_STORAGE_ENCRYPTED                    = ""
    RDS_MULTI_AZ_SUPPORT                     = ""
    VPC_FLOW_LOGS_ENABLED                    = ""
    INCOMING_SSH_DISABLED                    = ""
    EC2_IMDSV2_CHECK                         = ""
    CLOUD_TRAIL_LOG_FILE_VALIDATION_ENABLED  = ""
    LAMBDA_FUNCTION_PUBLIC_ACCESS_PROHIBITED = ""
    DYNAMODB_PITR_ENABLED                    = ""
  }
}

variable "guardduty_features" {
  type    = list(string)
  default = ["S3_DATA_EVENTS", "EBS_MALWARE_PROTECTION", "LAMBDA_NETWORK_LOGS", "RDS_LOGIN_EVENTS"]
}

variable "securityhub_standards" {
  type = list(string)
  default = [
    "aws-foundational-security-best-practices/v/1.0.0",
    "cis-aws-foundations-benchmark/v/3.0.0",
  ]
}

variable "security_emails" {
  type    = list(string)
  default = []
}

variable "rbac_roles" {
  description = "Roles RBAC por función. trusted_principals vacío = identidades de esta cuenta con MFA."
  type = map(object({
    description         = string
    managed_policy_arns = list(string)
    max_session_hours   = optional(number, 1)
    use_boundary        = optional(bool, false)
    trusted_principals  = optional(list(string), [])
  }))
  default = {
    "break-glass-admin" = {
      description         = "Emergencias. Cada uso genera alerta."
      managed_policy_arns = ["arn:aws:iam::aws:policy/AdministratorAccess"]
      max_session_hours   = 1
    }
    "platform-engineer" = {
      description         = "Plataforma/SRE: infraestructura compartida"
      managed_policy_arns = ["arn:aws:iam::aws:policy/PowerUserAccess", "arn:aws:iam::aws:policy/IAMReadOnlyAccess"]
      max_session_hours   = 4
    }
    "developer" = {
      description         = "Desarrolladores: workloads, limitado por boundary y ABAC"
      managed_policy_arns = ["arn:aws:iam::aws:policy/PowerUserAccess"]
      max_session_hours   = 8
      use_boundary        = true
    }
    "auditor" = {
      description         = "Auditoría y cumplimiento: solo lectura"
      managed_policy_arns = ["arn:aws:iam::aws:policy/SecurityAudit", "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"]
      max_session_hours   = 4
    }
    "finops" = {
      description         = "Costos y presupuestos"
      managed_policy_arns = ["arn:aws:iam::aws:policy/job-function/Billing", "arn:aws:iam::aws:policy/AWSBudgetsReadOnlyAccess"]
      max_session_hours   = 4
    }
  }
}

variable "manage_scps" {
  description = "true solo si se ejecuta en la cuenta de management de Organizations."
  type        = bool
  default     = false
}

variable "scp_target_ids" {
  description = "OUs o cuentas donde adjuntar las SCPs (nunca la raíz en un laboratorio)."
  type        = list(string)
  default     = []
}
