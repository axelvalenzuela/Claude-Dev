# Capa 3 (datos): RDS PostgreSQL en subnets aisladas (sin ruta a Internet).
# Contraseña administrada por RDS en Secrets Manager (rotación automática), TLS forzado, cifrado KMS.

resource "aws_security_group" "db" {
  name        = "${var.name}-db"
  description = "Capa datos: las reglas de entrada se agregan desde la capa app"
  vpc_id      = var.vpc_id
  tags        = var.tags
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-db"
  subnet_ids = var.data_subnet_ids
  tags       = var.tags
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.name}-pg${var.engine_major_version}"
  family = "postgres${var.engine_major_version}"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000" # registra queries > 1 s
  }

  tags = var.tags
}

resource "aws_db_instance" "this" {
  identifier     = "${var.name}-db"
  engine         = "postgres"
  engine_version = var.engine_major_version
  instance_class = var.instance_class
  db_name        = var.db_name
  username       = "app_admin"

  manage_master_user_password = true

  allocated_storage     = var.allocated_storage_gb
  max_allocated_storage = var.max_allocated_storage_gb
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = var.kms_key_arn

  multi_az               = var.multi_az
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  parameter_group_name   = aws_db_parameter_group.this.name

  iam_database_authentication_enabled = true
  backup_retention_period             = var.backup_retention_days
  backup_window                       = "08:00-09:00"
  maintenance_window                  = "sun:09:30-sun:10:30"
  auto_minor_version_upgrade          = true
  copy_tags_to_snapshot               = true
  deletion_protection                 = var.deletion_protection
  skip_final_snapshot                 = !var.deletion_protection
  final_snapshot_identifier           = var.deletion_protection ? "${var.name}-db-final" : null

  performance_insights_enabled    = true
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = var.tags
}
