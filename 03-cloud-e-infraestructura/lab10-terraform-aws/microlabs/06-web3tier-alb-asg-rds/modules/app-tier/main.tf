# Capa 2 (aplicación): Auto Scaling Group en subnets privadas.
# Sin SSH ni llaves: acceso administrativo por SSM Session Manager. IMDSv2 obligatorio.

data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

resource "aws_security_group" "app" {
  name        = "${var.name}-app"
  description = "Capa app: solo acepta tráfico del ALB"
  vpc_id      = var.vpc_id
  tags        = var.tags
}

resource "aws_vpc_security_group_ingress_rule" "from_alb" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = var.alb_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = var.app_port
  to_port                      = var.app_port
  description                  = "HTTP desde el ALB"
}

resource "aws_vpc_security_group_egress_rule" "https_out" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "Paquetes, SSM y APIs de AWS"
}

resource "aws_vpc_security_group_egress_rule" "http_out" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  description       = "Repositorios de paquetes"
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app" {
  name               = "${var.name}-app-instance"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "app" {
  for_each = {
    ssm = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    cw  = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  }
  role       = aws_iam_role.app.name
  policy_arn = each.value
}

resource "aws_iam_role_policy" "db_secret" {
  name = "read-db-secret"
  role = aws_iam_role.app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = var.db_secret_arn
    }]
  })
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.name}-app"
  role = aws_iam_role.app.name
}

resource "aws_launch_template" "app" {
  name_prefix   = "${var.name}-app-"
  image_id      = data.aws_ssm_parameter.al2023.value
  instance_type = var.instance_type
  user_data = base64encode(templatefile("${path.module}/user_data.sh.tpl", {
    app_port      = var.app_port
    region        = var.region
    db_endpoint   = var.db_endpoint
    db_name       = var.db_name
    db_secret_arn = var.db_secret_arn
  }))

  vpc_security_group_ids = [aws_security_group.app.id]

  iam_instance_profile {
    arn = aws_iam_instance_profile.app.arn
  }

  metadata_options {
    http_tokens                 = "required" # IMDSv2
    http_put_response_hop_limit = 1
    http_endpoint               = "enabled"
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = var.root_volume_gb
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags          = merge(var.tags, { Name = "${var.name}-app", Tier = "app" })
  }

  tag_specifications {
    resource_type = "volume"
    tags          = var.tags
  }
}

resource "aws_autoscaling_group" "app" {
  name                      = "${var.name}-app"
  vpc_zone_identifier       = var.app_subnet_ids
  min_size                  = var.min_size
  max_size                  = var.max_size
  desired_capacity          = var.min_size
  health_check_type         = "ELB"
  health_check_grace_period = 120
  target_group_arns         = [var.target_group_arn]

  launch_template {
    id      = aws_launch_template.app.id
    version = aws_launch_template.app.latest_version
  }

  # Despliegues sin caída al cambiar el launch template.
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }

  dynamic "tag" {
    for_each = var.tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}

resource "aws_autoscaling_policy" "cpu" {
  name                   = "${var.name}-cpu-target"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = var.cpu_target
  }
}
