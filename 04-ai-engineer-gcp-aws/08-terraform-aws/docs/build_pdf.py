"""Genera docs/aie-arquitecturas.pdf: guía RBAC/DevSecOps + diagrama y tabla Terraform por micro lab.

Uso:  uv run --with reportlab python docs/build_pdf.py
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak, Flowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

OUT = Path(__file__).parent / "aie-arquitecturas.pdf"

# ---------------------------------------------------------------------------
# Tipografía (Arial de Windows para acentos y flechas; Helvetica como respaldo)
# ---------------------------------------------------------------------------
FONT, FONT_B = "Helvetica", "Helvetica-Bold"
for name, file in (("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf")):
    path = Path("C:/Windows/Fonts") / file
    if path.exists():
        pdfmetrics.registerFont(TTFont(name, str(path)))
if "Arial" in pdfmetrics.getRegisteredFontNames():
    FONT, FONT_B = "Arial", "Arial-Bold"

INK = colors.HexColor("#1F2933")
MUTED = colors.HexColor("#5B6770")
RULE = colors.HexColor("#D5DBE1")
ACCENT = colors.HexColor("#232F3E")  # azul marino AWS
HILITE = colors.HexColor("#FF9900")  # naranja AWS

# Categorías de componentes: (relleno, borde, nombre en leyenda)
CATS = {
    "ext": ("#F1F3F5", "#7A8691", "Externo / usuario"),
    "net": ("#EDE7F6", "#6A3FB5", "Red"),
    "compute": ("#FFF1E0", "#D86613", "Cómputo"),
    "data": ("#E3F0FB", "#2E73B8", "Datos / storage"),
    "int": ("#FCE4EF", "#C2185B", "Integración / API"),
    "ai": ("#E0F4F1", "#0E8A7B", "IA / ML"),
    "sec": ("#FDE8E8", "#C62828", "Seguridad / identidad"),
    "ops": ("#E8F5E9", "#2E7D32", "Operación / observabilidad"),
}

styles = {
    "title": ParagraphStyle("title", fontName=FONT_B, fontSize=26, leading=31, textColor=ACCENT),
    "subtitle": ParagraphStyle("subtitle", fontName=FONT, fontSize=13, leading=18, textColor=MUTED),
    "h1": ParagraphStyle("h1", fontName=FONT_B, fontSize=17, leading=21, textColor=ACCENT, spaceAfter=4),
    "h2": ParagraphStyle("h2", fontName=FONT_B, fontSize=11.5, leading=15, textColor=ACCENT, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("body", fontName=FONT, fontSize=9, leading=12.5, textColor=INK),
    "lead": ParagraphStyle("lead", fontName=FONT, fontSize=9.5, leading=13, textColor=MUTED, spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName=FONT, fontSize=7.8, leading=10, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName=FONT_B, fontSize=7.8, leading=10, textColor=INK),
    "head": ParagraphStyle("head", fontName=FONT_B, fontSize=8, leading=10, textColor=colors.white),
    "bullet": ParagraphStyle("bullet", fontName=FONT, fontSize=9, leading=12.5, textColor=INK, leftIndent=12, bulletIndent=2),
    "small": ParagraphStyle("small", fontName=FONT, fontSize=7.5, leading=9.5, textColor=MUTED),
    "center": ParagraphStyle("center", fontName=FONT, fontSize=9, leading=12, alignment=TA_CENTER, textColor=MUTED),
}


def P(text, style="body"):
    return Paragraph(text, styles[style])


# ---------------------------------------------------------------------------
# Diagramas: nodos en una rejilla 0-100 (x a la derecha, y hacia abajo)
# ---------------------------------------------------------------------------
class Diagram(Flowable):
    def __init__(self, nodes, edges, groups=(), width=10 * inch, height=3.7 * inch):
        super().__init__()
        self.nodes = {n[0]: n for n in nodes}
        self.edges = edges
        self.groups = groups
        self.width, self.height = width, height
        self.legend_h = 16

    def wrap(self, *_):
        return self.width, self.height

    # rejilla -> puntos
    def _rect(self, x, y, w, h):
        area_h = self.height - self.legend_h
        sx, sy = self.width / 100, area_h / 100
        return x * sx, self.height - (y + h) * sy, w * sx, h * sy

    def _center(self, nid):
        _, _, _, x, y, w, h = self.nodes[nid]
        rx, ry, rw, rh = self._rect(x, y, w, h)
        return rx + rw / 2, ry + rh / 2, rw / 2, rh / 2

    @staticmethod
    def _clip(cx, cy, hw, hh, tx, ty):
        dx, dy = tx - cx, ty - cy
        if dx == 0 and dy == 0:
            return cx, cy
        scale = min(hw / abs(dx) if dx else 1e9, hh / abs(dy) if dy else 1e9)
        return cx + dx * scale, cy + dy * scale

    def draw(self):
        c = self.canv
        # grupos (fronteras: cuenta, VPC, subnets, on-premises)
        for label, x, y, w, h, *opt in self.groups:
            rx, ry, rw, rh = self._rect(x, y, w, h)
            c.setStrokeColor(colors.HexColor(opt[0] if opt else "#8A97A3"))
            c.setFillColor(colors.HexColor(opt[1] if len(opt) > 1 else "#FAFBFC"))
            c.setDash(4, 3)
            c.setLineWidth(0.9)
            c.roundRect(rx, ry, rw, rh, 6, stroke=1, fill=1)
            c.setDash()
            # Etiqueta sobre el borde superior (estilo fieldset) para no tapar nodos
            tw = c.stringWidth(label, FONT_B, 7.5)
            c.setFillColor(colors.white)
            c.rect(rx + 6, ry + rh - 4, tw + 6, 8, stroke=0, fill=1)
            c.setFillColor(MUTED)
            c.setFont(FONT_B, 7.5)
            c.drawString(rx + 9, ry + rh - 2.5, label)

        # aristas
        for edge in self.edges:
            a, b = edge[0], edge[1]
            label = edge[2] if len(edge) > 2 else ""
            dashed = len(edge) > 3 and edge[3] == "dash"
            ax, ay, ahw, ahh = self._center(a)
            bx, by, bhw, bhh = self._center(b)
            x1, y1 = self._clip(ax, ay, ahw + 1, ahh + 1, bx, by)
            x2, y2 = self._clip(bx, by, bhw + 2, bhh + 2, ax, ay)
            c.setStrokeColor(colors.HexColor("#5B6770"))
            c.setFillColor(colors.HexColor("#5B6770"))
            c.setLineWidth(1)
            if dashed:
                c.setDash(3, 2)
            c.line(x1, y1, x2, y2)
            c.setDash()
            self._arrow(x1, y1, x2, y2)
            if label:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                c.setFont(FONT, 6.5)
                tw = c.stringWidth(label, FONT, 6.5)
                c.setFillColor(colors.white)
                c.rect(mx - tw / 2 - 2, my - 3, tw + 4, 9, stroke=0, fill=1)
                c.setFillColor(MUTED)
                c.drawCentredString(mx, my, label)

        # nodos
        for nid, label, cat, x, y, w, h in self.nodes.values():
            fill, stroke, _ = CATS[cat]
            rx, ry, rw, rh = self._rect(x, y, w, h)
            c.setFillColor(colors.HexColor(fill))
            c.setStrokeColor(colors.HexColor(stroke))
            c.setLineWidth(1.2)
            c.roundRect(rx, ry, rw, rh, 5, stroke=1, fill=1)
            c.setFillColor(colors.HexColor(stroke))
            c.rect(rx, ry + 4, 3, rh - 8, stroke=0, fill=1)
            lines = label.split("\n")
            lh = 9
            top = ry + rh / 2 + (len(lines) - 1) * lh / 2 - 2.5
            for i, line in enumerate(lines):
                c.setFillColor(INK)
                font = FONT_B if i == 0 else FONT
                size = 7.6 if i == 0 else 6.8
                c.setFont(font, size)
                c.drawCentredString(rx + rw / 2 + 1, top - i * lh, line)

        # leyenda
        lx = 0
        for key, (fill, stroke, name) in CATS.items():
            c.setFillColor(colors.HexColor(fill))
            c.setStrokeColor(colors.HexColor(stroke))
            c.rect(lx, 2, 9, 7, stroke=1, fill=1)
            c.setFillColor(MUTED)
            c.setFont(FONT, 6.5)
            c.drawString(lx + 12, 3, name)
            lx += 18 + c.stringWidth(name, FONT, 6.5) + 8

    def _arrow(self, x1, y1, x2, y2):
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        size = 5
        p = self.canv.beginPath()
        p.moveTo(x2, y2)
        p.lineTo(x2 - size * math.cos(ang - 0.4), y2 - size * math.sin(ang - 0.4))
        p.lineTo(x2 - size * math.cos(ang + 0.4), y2 - size * math.sin(ang + 0.4))
        p.close()
        self.canv.drawPath(p, stroke=0, fill=1)


def table(rows, widths, header=True, zebra=True):
    data = []
    for i, row in enumerate(rows):
        style = "head" if header and i == 0 else "cell"
        data.append([Paragraph(str(cell), styles["cellb" if (j == 0 and style == "cell") else style]) for j, cell in enumerate(row)])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), ACCENT))
    if zebra:
        for r in range(1 if header else 0, len(data)):
            if r % 2 == 0:
                cmds.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F6F8FA")))
    t.setStyle(TableStyle(cmds))
    return t


FULL_W = 10 * inch
TF_COLS = [1.75 * inch, 3.15 * inch, 5.1 * inch]
TF_HEAD = ["Componente", "Recurso / módulo Terraform", "Configuración clave (parámetros)"]

# ---------------------------------------------------------------------------
# Contenido de los micro labs
# ---------------------------------------------------------------------------
LABS = [
    {
        "id": "00", "title": "Bootstrap: estado remoto, GitLab OIDC y guardrails de costo",
        "goal": "Prepara la cuenta para desplegar todo desde GitLab sin llaves estáticas: estado cifrado, roles separados para plan y apply, permissions boundary y presupuesto.",
        "groups": [("GitLab", 1, 4, 23, 88), ("Cuenta AWS", 28, 4, 71, 88)],
        "nodes": [
            ("dev", "Desarrollador\nMR / push a main", "ext", 4, 10, 17, 14),
            ("ci", "Job de GitLab CI\nid_token (JWT)", "ops", 4, 46, 17, 16),
            ("oidc", "IAM OIDC Provider\ngitlab.com · aud", "sec", 32, 46, 17, 16),
            ("plan", "Rol gitlab-plan\nReadOnly + estado", "sec", 56, 20, 18, 15),
            ("apply", "Rol gitlab-apply\nAdmin ∩ Boundary", "sec", 56, 62, 18, 15),
            ("bnd", "Permissions boundary\nregiones · antitamper", "sec", 79, 70, 18, 15),
            ("s3", "S3 tfstate\nversionado · *.tflock", "data", 79, 34, 18, 15),
            ("kms", "KMS CMK\nrotación anual", "sec", 79, 6, 18, 13),
            ("bud", "AWS Budgets\n50 / 80 / 100 %", "ops", 32, 76, 17, 13),
        ],
        "edges": [("dev", "ci", "pipeline"), ("ci", "oidc", "AssumeRoleWithWebIdentity"), ("oidc", "plan", "sub = ref:*"),
                  ("oidc", "apply", "sub = ref:main"), ("plan", "s3", "lee"), ("apply", "s3", "escribe"),
                  ("kms", "s3", "SSE-KMS"), ("bnd", "apply", "limita", "dash")],
        "rows": [
            ("Llave de cifrado", "module.state_key → modules/kms-key", "alias = aie-dev-tfstate; enable_key_rotation = true"),
            ("Bucket de estado", "module.state_bucket → modules/s3-secure-bucket", "force_destroy = false; versionado; noncurrent 90 días; política TLS-only; BPA"),
            ("Proveedor OIDC", "aws_iam_openid_connect_provider.gitlab", "url = https://gitlab.com; client_id_list = [gitlab_audience]"),
            ("Rol de plan", "aws_iam_role.plan + ReadOnlyAccess + state_access", "Condición sub: project_path:&lt;grupo/proyecto&gt;:ref_type:branch:ref:*"),
            ("Rol de apply", "aws_iam_role.apply + AdministratorAccess", "sub = ...:ref:main; permissions_boundary = boundary; sesión de 1 h"),
            ("Boundary", "aws_iam_policy.boundary", "Deny fuera de allowed_regions; deny CloudTrail/GuardDuty/Config stop; deny iam:CreateUser/AccessKey"),
            ("Presupuesto", "aws_budgets_budget.monthly", "monthly_budget_usd = 50; alert_emails; 50/80 % real, 100 % pronosticado"),
            ("Backend", "versions.tf (local → s3)", "terraform init -migrate-state con use_lockfile = true (sin DynamoDB)"),
        ],
        "facts": [("Variables GitLab", "TF_STATE_BUCKET, AWS_PLAN_ROLE_ARN, AWS_APPLY_ROLE_ARN (protegida), AWS_REGION"),
                  ("Storage mínimo", "S3 < 1 MB por lab; 1 CMK (~USD 1/mes)"),
                  ("Well-Architected", "SEC: OIDC + boundary · OPS: IaC + estado versionado · COST: Budgets")],
    },
    {
        "id": "01", "title": "API serverless: API Gateway REST + Lambda + DynamoDB",
        "goal": "API REST definida por contrato OpenAPI, con defensa en profundidad (WAF, API key, JWT de Cognito y validación de esquema) y observabilidad completa.",
        "groups": [("Región us-east-1 (servicios administrados multi-AZ)", 16, 3, 83, 92)],
        "nodes": [
            ("cli", "Cliente\napp / curl", "ext", 1, 40, 12, 15),
            ("waf", "AWS WAF\nCommon · BadInputs · rate", "sec", 19, 40, 15, 15),
            ("api", "API Gateway REST\nstage v1 · OpenAPI", "int", 40, 40, 16, 15),
            ("cog", "Cognito User Pool\nJWT · MFA opcional", "sec", 40, 8, 16, 14),
            ("plan", "Usage plan + API key\nthrottle · cuota", "int", 40, 74, 16, 14),
            ("fn", "Lambda items\narm64 · X-Ray · conc. 20", "compute", 62, 40, 16, 15),
            ("ddb", "DynamoDB items\non-demand · PITR", "data", 83, 40, 15, 15),
            ("cw", "CloudWatch\naccess logs · alarmas", "ops", 62, 74, 16, 14),
        ],
        "edges": [("cli", "waf", "HTTPS"), ("waf", "api"), ("api", "cog", "valida JWT"), ("api", "plan", "x-api-key"),
                  ("api", "fn", "proxy"), ("fn", "ddb", "IAM"), ("fn", "cw", "logs JSON"), ("api", "cw", "5XX · p99")],
        "rows": [
            ("Contrato API", "openapi.yaml.tpl → templatefile()", "Rutas /health (MOCK), /items, /items/{id}; request validator; securitySchemes cognito + api_key"),
            ("API", "aws_api_gateway_rest_api / _deployment / _stage", "REGIONAL; redeploy por sha1(body); xray_tracing_enabled; access_log_settings JSON"),
            ("Throttling", "aws_api_gateway_method_settings + _usage_plan", "throttle_rate_limit = 50, burst = 100, monthly_quota = 100000; data_trace off"),
            ("Identidad", "aws_cognito_user_pool / _client", "Password de 12+ caracteres, MFA TOTP opcional, tokens de 60 min, prevent_user_existence_errors"),
            ("Cómputo", "module.items_fn → modules/lambda-function", "python3.13 arm64; reserved_concurrency = 20; política inline solo sobre la tabla"),
            ("Datos", "module.table → modules/dynamodb-table", "pk/sk (USER#sub / ITEM#uuid); PAY_PER_REQUEST; PITR; SSE"),
            ("Borde", "aws_wafv2_web_acl + _association", "enable_waf; waf_rate_limit_per_5min = 1000; reglas administradas de AWS"),
            ("Alarmas", "aws_cloudwatch_metric_alarm (5xx, latency_p99)", "5XX > 5 en 3 de 5 min; p99 > 1500 ms"),
        ],
        "facts": [("Variables GitLab", "AWS01_TFVARS (File)"), ("Storage mínimo", "DynamoDB on-demand; logs de 30 días; paquete Lambda < 1 MB"),
                  ("Well-Architected", "SEC: 5 capas de control · REL: throttling + PITR · COST: pago por uso + cuotas")],
    },
    {
        "id": "02", "title": "AWS AppSync (GraphQL) + DynamoDB + suscripciones en tiempo real",
        "goal": "API GraphQL administrada con resolvers JavaScript que acceden directo a DynamoDB (sin Lambda), autorización por usuario y WebSockets.",
        "groups": [("AWS AppSync", 28, 4, 46, 90)],
        "nodes": [
            ("app", "App web / móvil\nAmplify / Apollo", "ext", 2, 38, 15, 16),
            ("cog", "Cognito User Pool\nauth por defecto", "sec", 2, 74, 15, 14),
            ("api", "GraphQL API\nCognito + IAM · depth 5", "int", 32, 14, 18, 16),
            ("res", "Resolvers APPSYNC_JS\nget · list · create · delete", "compute", 32, 52, 18, 16),
            ("ws", "Suscripciones\nonCreateNote (WSS)", "int", 54, 14, 17, 16),
            ("cache", "API cache (opcional)\nSMALL · TTL 60 s", "data", 54, 52, 17, 16),
            ("ddb", "DynamoDB notes\nowner + id · PITR", "data", 81, 52, 17, 16),
            ("cw", "CloudWatch + X-Ray\nlogs ERROR", "ops", 81, 14, 17, 16),
        ],
        "edges": [("app", "api", "query / mutation"), ("app", "cog", "login", "dash"), ("api", "res"), ("api", "ws", "push"),
                  ("res", "ddb", "rol de servicio"), ("api", "cw"), ("res", "cache", "", "dash")],
        "rows": [
            ("Schema", "schema.graphql → file()", "Directivas @aws_cognito_user_pools / @aws_iam; @aws_subscribe(mutations: [createNote])"),
            ("API", "aws_appsync_graphql_api", "AMAZON_COGNITO_USER_POOLS + AWS_IAM; query_depth_limit = 5; introspection DISABLED en prod; xray"),
            ("Logs", "log_config + aws_iam_role.logs", "field_log_level = ERROR; exclude_verbose_content = true; retención de 30 días"),
            ("Data source", "aws_appsync_datasource.notes", "AMAZON_DYNAMODB con rol limitado a Get/Put/Delete/Query de la tabla"),
            ("Resolvers", "aws_appsync_resolver (for_each local.resolvers)", "runtime APPSYNC_JS 1.0.0; código en resolvers/*.js; filtran por ctx.identity.sub"),
            ("Datos", "module.notes_table", "hash owner, range id; on-demand; PITR"),
            ("Caché", "aws_appsync_api_cache (count)", "enable_cache = false; FULL_REQUEST_CACHING; cifrado en tránsito y en reposo"),
        ],
        "facts": [("Variables GitLab", "AWS02_TFVARS (File)"), ("Storage mínimo", "DynamoDB on-demand + PITR; logs de 30 días"),
                  ("Well-Architected", "PERF: sin cold starts · SEC: autorización por campo · COST: sin Lambda intermedia")],
    },
    {
        "id": "03", "title": "Arquitectura orientada a eventos con Amazon EventBridge",
        "goal": "Desacoplar productores y consumidores: filtrado por contenido, transformación, reintentos, DLQ, archive/replay, bus cross-account y Scheduler.",
        "groups": [("EventBridge", 22, 3, 30, 92)],
        "nodes": [
            ("prod", "Productores\napps · PutEvents", "ext", 1, 20, 16, 14),
            ("xacc", "Otras cuentas\nbus policy", "ext", 1, 56, 16, 14),
            ("bus", "Bus custom orders\nreglas por patrón", "int", 26, 30, 22, 16),
            ("arch", "Archive\nreplay 7 días", "data", 26, 70, 22, 13),
            ("sch", "EventBridge Scheduler\nrate(1h) · flexible", "int", 26, 6, 22, 13),
            ("fn", "Lambda processor\norder.created", "compute", 60, 22, 17, 14),
            ("sqs", "SQS high-value\namount ≥ 1000", "int", 60, 48, 17, 14),
            ("logs", "CloudWatch Logs\nauditoría total", "ops", 60, 74, 17, 13),
            ("rep", "Lambda reporter", "compute", 60, 2, 17, 11),
            ("dlq", "SQS DLQ\n14 días · alarma", "int", 84, 36, 14, 16),
        ],
        "edges": [("prod", "bus"), ("xacc", "bus", "PutEvents"), ("bus", "arch", "", "dash"), ("bus", "fn", "regla 1"),
                  ("bus", "sqs", "regla 2 + transform"), ("bus", "logs", "regla 3"), ("sch", "rep"),
                  ("fn", "dlq", "retry x3"), ("sqs", "dlq", "redrive")],
        "rows": [
            ("Bus y archive", "aws_cloudwatch_event_bus / _event_archive", "archive_retention_days = 7; replay desde la consola o la CLI"),
            ("Cross-account", "aws_cloudwatch_event_bus_policy (count)", "producer_account_ids = [] → events:PutEvents por cuenta"),
            ("Regla 1", "aws_cloudwatch_event_rule + _target", "source com.aie.orders, detail-type order.created; retry 3, edad máx. 1 h, DLQ"),
            ("Regla 2", "event_pattern numeric", "detail.amount ≥ high_value_threshold; input_transformer → JSON reducido a SQS"),
            ("Regla 3", "target CloudWatch Logs + log resource policy", "Log group /aws/events/...-audit; retención log_retention_days = 14"),
            ("Colas", "aws_sqs_queue (high_value, dlq) + policies", "SSE-SQS; políticas con aws:SourceArn de la regla; maxReceiveCount = 5"),
            ("Falla de código", "aws_lambda_function_event_invoke_config", "processor_async_retries = 1; on_failure → DLQ (la DLQ del target solo cubre fallas de entrega)"),
            ("Scheduler", "aws_scheduler_schedule", "report_schedule = rate(1 hour); zona horaria America/Tijuana; ventana flexible de 15 min; DLQ"),
            ("Alarmas", "dlq_not_empty, failed_invocations", "Mensajes en la DLQ > 0; FailedInvocations > 0"),
        ],
        "facts": [("Variables GitLab", "AWS03_TFVARS (File)"), ("Storage mínimo", "Archive de 7 días; DLQ de 14 días; logs de 14 días"),
                  ("Well-Architected", "REL: retry + DLQ + replay · SEC: SourceArn · COST: filtrar en el bus")],
    },
    {
        "id": "04", "title": "Chatbot de IA generativa con Amazon Bedrock",
        "goal": "Chatbot serverless con memoria conversacional, autenticación JWT, Bedrock Guardrails y controles de costo sobre tokens y concurrencia.",
        "groups": [("Región AWS", 18, 3, 81, 92)],
        "nodes": [
            ("fe", "Frontend\nCORS permitido", "ext", 1, 38, 14, 16),
            ("cog", "Cognito\nJWT", "sec", 22, 8, 14, 13),
            ("api", "HTTP API\nPOST /chat · 10 rps", "int", 22, 38, 15, 16),
            ("fn", "Lambda chat\n512 MB · conc. 10", "compute", 44, 38, 16, 16),
            ("ddb", "DynamoDB history\nTTL 24 h", "data", 44, 76, 16, 14),
            ("br", "Bedrock Converse\nmodel_id", "ai", 68, 38, 15, 16),
            ("gr", "Bedrock Guardrail\nPII · temas · prompt attack", "sec", 68, 8, 15, 15),
            ("cw", "CloudWatch\ntokens · throttles", "ops", 86, 70, 13, 16),
        ],
        "edges": [("fe", "api", "Bearer JWT"), ("api", "cog", "authorizer"), ("api", "fn"), ("fn", "ddb", "historial"),
                  ("fn", "br", "converse()"), ("br", "gr", "guardrailConfig"), ("br", "cw", "métricas"), ("fn", "cw", "", "dash")],
        "rows": [
            ("Guardrail", "aws_bedrock_guardrail + _version", "Filtros HATE/INSULTS/SEXUAL/VIOLENCE/MISCONDUCT HIGH; PROMPT_ATTACK; PII anonymize/block; tema DENY"),
            ("Modelo", "variable model_id", "amazon.nova-lite-v1:0 por defecto; Converse API (cambias de modelo sin tocar el código)"),
            ("Lambda", "module.chat_fn", "timeout = 60; memory = 512; reserved_concurrency = max_concurrency (tope de gasto)"),
            ("Política IAM", "data.aws_iam_policy_document.chat", "bedrock:InvokeModel (foundation-model, inference-profile); ApplyGuardrail; DynamoDB de la tabla"),
            ("Prompt y límites", "environment SYSTEM_PROMPT, MAX_TOKENS, HISTORY_TURNS", "max_tokens = 512; history_turns = 6; system_prompt parametrizable desde GitLab"),
            ("API", "aws_apigatewayv2_api / _authorizer / _route / _stage", "JWT con issuer de Cognito; CORS allowed_origins; throttling_rate_limit = 10"),
            ("Historial", "module.history", "session_id = sub#session, ts (N); ttl_attribute = expires_at"),
            ("Costo", "alarms throttles + output_tokens", "hourly_output_token_alarm = 200000 tokens/h"),
        ],
        "facts": [("Variables GitLab", "AWS04_TFVARS (File), TF_VAR_system_prompt"), ("Storage mínimo", "DynamoDB con TTL 24 h; logs de 30 días"),
                  ("Well-Architected", "Generative AI Lens · SEC: guardrails + JWT · COST: tokens y concurrencia acotados")],
    },
    {
        "id": "05", "title": "Pipeline de IA para documentos (Step Functions + Textract + Comprehend + Bedrock)",
        "goal": "Orquestar servicios de IA administrados: integraciones SDK directas, paralelismo, reintentos con jitter y manejo de errores centralizado.",
        "groups": [("Step Functions STANDARD", 38, 3, 61, 92)],
        "nodes": [
            ("u", "Usuario\nPutObject", "ext", 1, 8, 13, 13),
            ("s3", "S3 docs/incoming\nSSE-KMS · expira 30 d", "data", 1, 40, 15, 16),
            ("eb", "EventBridge\nObject Created", "int", 20, 40, 14, 16),
            ("ex", "ExtractText\nLambda + Textract", "compute", 42, 40, 15, 16),
            ("cp", "DetectEntities\nComprehend (SDK)", "ai", 63, 12, 15, 15),
            ("sm", "Summarize\nLambda + Bedrock", "ai", 63, 64, 15, 15),
            ("ddb", "SaveResult\nDynamoDB PutItem", "data", 84, 40, 14, 16),
            ("sns", "NotifyFailure\nSNS cifrado", "ops", 42, 80, 15, 13),
        ],
        "edges": [("u", "s3"), ("s3", "eb", "notificación"), ("eb", "ex", "StartExecution"), ("ex", "cp", "Parallel"),
                  ("ex", "sm", "Parallel"), ("cp", "ddb"), ("sm", "ddb"), ("ex", "sns", "Catch", "dash")],
        "rows": [
            ("Flujo", "statemachine.asl.json.tpl → templatefile()", "ASL con ${extract_fn_arn}, ${summarize_fn_arn}, ${table_name}, ${alerts_topic_arn}, ${language_code}"),
            ("Máquina de estados", "aws_sfn_state_machine.pipeline", "STANDARD; logging ERROR con include_execution_data = false; tracing activo"),
            ("Disparador", "aws_s3_bucket_notification (eventbridge=true) + event rule", "Filtro bucket.name y object.key prefix incoming/; rol events → states:StartExecution"),
            ("Extracción", "module.extract_fn", "Textract DetectDocumentText (png/jpg/pdf) o lectura de .txt; MAX_CHARS = 4500"),
            ("Entidades", "Integración arn:aws:states:::aws-sdk:comprehend:detectEntities", "language_code = es; sin Lambda intermedia"),
            ("Resumen", "module.summarize_fn", "Bedrock Converse; model_id; reserved_concurrency = 5; maxTokens 300"),
            ("Errores", "Retry (backoff + JITTER FULL) / Catch → SNS → Fail", "alert_emails; alarma ExecutionsFailed > 0"),
            ("Seguridad", "module.kms + module.documents", "CMK compartida S3/SNS; IAM s3:GetObject solo en incoming/*"),
        ],
        "facts": [("Variables GitLab", "AWS05_TFVARS (File)"), ("Storage mínimo", "S3 expira a 30 días; 1 ítem DynamoDB por documento"),
                  ("Well-Architected", "REL: retry/catch · SEC: sin datos en logs · PERF: paralelismo")],
    },
    {
        "id": "06", "title": "Arquitectura web de 3 niveles (ALB + Auto Scaling + RDS Multi-AZ)",
        "goal": "Arquitectura de referencia en VPC multi-AZ: un módulo por capa y seguridad encadenada (Internet → ALB → App → DB).",
        "groups": [("VPC 10.60.0.0/16 · 2 AZ", 14, 2, 85, 94, "#6A3FB5", "#FBFAFE"),
                   ("Subnets públicas", 17, 8, 26, 84, "#8A97A3", "#F7F9FB"),
                   ("Subnets app (privadas)", 46, 8, 24, 84, "#8A97A3", "#F7F9FB"),
                   ("Subnets data (aisladas)", 73, 8, 24, 84, "#8A97A3", "#F7F9FB")],
        "nodes": [
            ("inet", "Internet\nusuarios", "ext", 0, 42, 12, 14),
            ("waf", "AWS WAF\nCommon · SQLi · rate", "sec", 20, 16, 20, 14),
            ("alb", "ALB\n80/443 · drop invalid hdr", "net", 20, 42, 20, 15),
            ("nat", "NAT Gateway\nsalida app", "net", 20, 70, 20, 13),
            ("ec2a", "EC2 t4g · AZ-a\nIMDSv2 · SSM", "compute", 49, 22, 18, 14),
            ("ec2b", "EC2 t4g · AZ-b\nASG 2..4 · CPU 50 %", "compute", 49, 50, 18, 14),
            ("sec", "Secrets Manager\npassword de RDS", "sec", 49, 76, 18, 12),
            ("rdsp", "RDS PostgreSQL\nprimary · AZ-a", "data", 76, 22, 18, 14),
            ("rdss", "RDS standby\nAZ-b · síncrono", "data", 76, 50, 18, 14),
        ],
        "edges": [("inet", "alb", "HTTP(S)"), ("waf", "alb", "inspecciona", "dash"), ("alb", "ec2a", "SG alb→app"),
                  ("alb", "ec2b"), ("ec2a", "rdsp", "SG app→db 5432"), ("ec2b", "rdsp"), ("rdsp", "rdss", "Multi-AZ"),
                  ("ec2b", "sec", "GetSecretValue"), ("ec2b", "nat", "443", "dash")],
        "rows": [
            ("Red", "module.vpc → modules/vpc", "vpc_cidr = 10.60.0.0/16; az_count = 2; single_nat_gateway = true (false en prod); flow logs REJECT"),
            ("Capa web", "./modules/web-tier", "ALB + target group (/health); listener HTTP o HTTPS con certificate_arn; WAF Common + SQLi + rate 2000"),
            ("Capa app", "./modules/app-tier", "Launch template AL2023 arm64 (SSM param); IMDSv2; EBS gp3 cifrado; ASG min/max; target tracking 50 %"),
            ("App de prueba", "user_data.sh.tpl (systemd aie-app)", "Python stdlib: /, /health, /db (lee el secreto, SQL por TLS, tabla visits); sin credenciales en user_data"),
            ("Capa datos", "./modules/data-tier", "postgres 17; db.t4g.micro; 20 GB gp3 → 100 GB; multi_az; manage_master_user_password; rds.force_ssl"),
            ("Cadena de SG", "aws_vpc_security_group_ingress/egress_rule (root)", "db_from_app y app_to_db en el root para evitar el ciclo entre módulos"),
            ("Despliegue", "instance_refresh Rolling", "min_healthy_percentage = 50 → cambios sin caída"),
            ("Alarmas", "alb_5xx, unhealthy_hosts, db_cpu, db_storage", "5XX > 10; hosts no sanos > 0; CPU > 80 %; FreeStorage < 2 GiB"),
        ],
        "facts": [("Variables GitLab", "AWS06_TFVARS (File); job con timeout 1 h"), ("Storage mínimo", "EBS 8 GB gp3 por instancia; RDS 20 GB gp3 + backups de 7 días"),
                  ("Well-Architected", "REL: multi-AZ total · SEC: SG encadenados, sin SSH · COST: ~USD 95/mes, destruir al terminar")],
    },
    {
        "id": "07", "title": "SRE: SLOs, alertas por burn rate, Synthetics, ChatOps y Chaos Engineering",
        "goal": "Alertar por consumo del presupuesto de error (multi-window, multi-burn-rate), monitorear desde fuera, notificar en Slack y validar resiliencia con AWS FIS.",
        "groups": [("Amazon CloudWatch", 22, 3, 46, 92)],
        "nodes": [
            ("api", "API Gateway\n(micro lab 01)", "ext", 1, 14, 15, 14),
            ("asg", "ASG app\n(micro lab 06)", "ext", 1, 70, 15, 14),
            ("can", "Synthetics canary\nrate 5 min", "ops", 1, 42, 15, 14),
            ("fast", "Burn rápido 14.4x\n1 h AND 5 min → page", "ops", 26, 8, 18, 16),
            ("slow", "Burn lento 6x\n6 h AND 30 min → ticket", "ops", 26, 34, 18, 16),
            ("lat", "Latencia p99\n< 1000 ms", "ops", 26, 60, 18, 13),
            ("dash", "Dashboard\ngolden signals", "ops", 48, 8, 17, 14),
            ("calm", "Alarma canary\nSuccessPercent < 90", "ops", 48, 60, 17, 14),
            ("sns", "SNS cifrado\nalertas", "int", 74, 34, 13, 15),
            ("slack", "Slack on-call\nAmazon Q chat apps", "ext", 88, 16, 11, 16),
            ("mail", "Email", "ext", 88, 52, 11, 12),
            ("fis", "AWS FIS\nstop 1 instancia", "ops", 74, 74, 14, 14),
        ],
        "edges": [("api", "fast", "5XX/Count"), ("api", "slow"), ("can", "calm"), ("fast", "sns"), ("slow", "sns"),
                  ("lat", "sns"), ("calm", "sns"), ("sns", "slack"), ("sns", "mail"), ("fis", "asg", "GameDay", "dash"),
                  ("calm", "fis", "stop condition", "dash")],
        "rows": [
            ("SLO", "locals.error_budget, burn_windows", "slo_target = 0.999 → 43 min/mes; fast 14.4x (1 h/5 min), slow 6x (6 h/30 min)"),
            ("Burn rate", "aws_cloudwatch_metric_alarm.burn_long / burn_short", "metric_query: IF(requests>0, errors/requests, 0) > burn × presupuesto"),
            ("Alerta", "aws_cloudwatch_composite_alarm.slo_burn", "ALARM(long) AND ALARM(short); descripción con runbook_url"),
            ("Latencia", "latency_slo", "latency_p99_ms = 1000; 2 de 3 periodos de 5 min"),
            ("Caja negra", "aws_synthetics_canary.health + canary/…/index.js", "health_check_url; canary_runtime_version; artefactos en S3 7/14 días"),
            ("Dashboard", "aws_cloudwatch_dashboard + dashboard.json.tpl", "Tráfico, % 5XX, p50/p90/p99, saturación, éxito del canary"),
            ("ChatOps", "aws_chatbot_slack_channel_configuration (count)", "slack_team_id / slack_channel_id; guardrail ReadOnlyAccess"),
            ("Chaos", "aws_fis_experiment_template (count)", "enable_fis; aws:ec2:stop-instances COUNT(1) por tag MicroLab; reinicio en PT5M"),
        ],
        "facts": [("Variables GitLab", "AWS07_TFVARS (File); SLACK_* enmascaradas"), ("Storage mínimo", "S3 de artefactos del canary con expiración de 14 días"),
                  ("Well-Architected", "OPS: SLO + runbooks + postmortems · REL: chaos engineering con stop condition")],
    },
    {
        "id": "08", "title": "Amazon Neptune (grafos) Serverless v2 con openCypher",
        "goal": "Base de grafos totalmente privada con autenticación IAM (SigV4), carga masiva desde S3 y consultas openCypher para fraude y recomendaciones.",
        "groups": [("VPC 10.80.0.0/16 · sin NAT", 2, 2, 72, 94, "#6A3FB5", "#FBFAFE"),
                   ("Subnets app", 5, 10, 28, 80, "#8A97A3", "#F7F9FB"),
                   ("Subnets data (aisladas)", 40, 10, 31, 80, "#8A97A3", "#F7F9FB")],
        "nodes": [
            ("op", "Operador\nlambda invoke", "ext", 8, 16, 21, 13),
            ("fn", "Lambda client\nSigV4 · SG client", "compute", 8, 44, 21, 16),
            ("np", "Neptune cluster\ndb.serverless 1–4 NCU", "data", 44, 30, 24, 18),
            ("rep", "Réplica opcional\notra AZ", "data", 44, 62, 24, 13),
            ("vpce", "S3 gateway\nendpoint", "net", 8, 72, 21, 13),
            ("s3", "S3 load bucket\nnodes.csv · edges.csv", "data", 80, 50, 18, 15),
            ("kms", "KMS CMK", "sec", 80, 10, 18, 11),
            ("role", "Rol del loader\n(rds.amazonaws.com)", "sec", 80, 28, 18, 14),
            ("cw", "CloudWatch\naudit logs", "ops", 80, 76, 18, 13),
        ],
        "edges": [("op", "fn"), ("fn", "np", ":8182 openCypher"), ("np", "rep", "", "dash"), ("np", "vpce", "/loader"),
                  ("vpce", "s3", "GetObject"), ("role", "np", "iam_roles", "dash"), ("kms", "np", "storage"),
                  ("np", "cw", "audit")],
        "rows": [
            ("Red", "module.vpc", "enable_nat_gateway = false; S3 gateway endpoint en las route tables de app y data"),
            ("Cluster", "aws_neptune_cluster", "iam_database_authentication_enabled; storage_encrypted + KMS; backups de 7 días; audit logs"),
            ("Escalado", "serverless_v2_scaling_configuration", "min_ncu = 1, max_ncu = 4; instance_class db.serverless; instance_count = 1 (2 = HA)"),
            ("Parámetros", "aws_neptune_cluster_parameter_group", "neptune_family = neptune1.4 (debe coincidir con engine_version); audit log; timeout de query de 20 s"),
            ("Seguridad de red", "SG neptune ← SG client :8182", "Sin CIDR abiertos: solo referencia entre security groups"),
            ("Carga masiva", "aws_iam_role.loader + aws_s3_object.sample", "format opencypher; data/nodes.csv y edges.csv sincronizados por hash"),
            ("Cliente", "module.client_fn (vpc_subnet_ids)", "neptune-db:connect / Read / Write / StartLoaderJob sobre cluster_resource_id"),
        ],
        "facts": [("Variables GitLab", "AWS08_TFVARS (File)"), ("Storage mínimo", "Storage auto-escalable de 10 GB a 128 TiB (pago por GB-mes + I/O); backups de 7 días"),
                  ("Well-Architected", "SEC: sin Internet + IAM auth · COST: ~USD 115/mes con 1 NCU, destruir al terminar")],
    },
    {
        "id": "09", "title": "Migración rehost con AWS Application Migration Service (MGN)",
        "goal": "Landing zone de migración lift-and-shift: replicación continua, prueba, cutover y finalización, con credenciales temporales y cifrado KMS.",
        "groups": [("Datacenter / otra nube", 1, 4, 21, 90, "#7A8691", "#F7F7F7"),
                   ("AWS · VPC 10.90.0.0/16", 27, 4, 72, 90, "#6A3FB5", "#FBFAFE")],
        "nodes": [
            ("src", "Servidor origen\n+ Replication Agent", "ext", 3, 36, 17, 18),
            ("ops", "Operador\nassume-role + MFA", "ext", 3, 72, 17, 14),
            ("mgn", "AWS MGN\nconsola · waves", "ops", 31, 10, 17, 15),
            ("rs", "Replication servers\nsubnet staging · t3.small", "compute", 31, 40, 19, 16),
            ("ebs", "EBS staging gp3\n+ snapshots", "data", 31, 72, 19, 14),
            ("kms", "KMS CMK\nEBS", "sec", 56, 72, 15, 14),
            ("role", "Rol installer\npolítica MGN mínima", "sec", 56, 10, 15, 15),
            ("tgt", "Instancias migradas\nsubnet app · IMDSv2 · SSM", "compute", 78, 40, 19, 16),
            ("lt", "Launch template\noverrides JSON", "int", 78, 72, 19, 14),
        ],
        "edges": [("src", "rs", "TCP 1500 TLS"), ("src", "mgn", "443 control"), ("ops", "role", "STS", "dash"),
                  ("rs", "ebs"), ("kms", "ebs", "cifra"), ("mgn", "tgt", "test / cutover"), ("lt", "tgt", "configura")],
        "rows": [
            ("Red", "module.vpc + aws_subnet.staging", "vpc_cidr sin traslape con on-prem; subnet de staging dedicada (cidrsubnet 30)"),
            ("Replicación", "aws_security_group.replication", "Ingreso TCP 1500 solo desde source_cidrs; egreso 443"),
            ("Ruta", "replication_over_private_link", "false = IP pública + TLS; true = VPN/Direct Connect (PRIVATE_IP)"),
            ("Template de replicación", "templates/replication-template.json.tpl → local_file", "ebsEncryption CUSTOM + KMS; GP3; bandwidth_throttle_mbps; replication_server_instance_type"),
            ("Launch template", "templates/launch-template-overrides.json.tpl", "Subnet y SG destino; IamInstanceProfile SSM; HttpTokens required; etiquetas"),
            ("Aplicación de config", "scripts/configure-mgn.sh (AWS CLI + jq)", "initialize-service; update-replication-configuration-template; versiones de launch templates"),
            ("Identidad", "aws_iam_role.agent_installer", "AWSApplicationMigrationAgentInstallationPolicy; MFA obligatoria; installer_principal_arns"),
            ("Destino", "aws_security_group.target + instance profile", "target_app_ports = [80, 443] solo desde la VPC; SSM en lugar de SSH/RDP"),
        ],
        "facts": [("Variables GitLab", "AWS09_TFVARS (File); TF_VAR_source_cidrs"), ("Storage mínimo", "EBS staging ≈ discos origen; EBS destino del mismo tamaño"),
                  ("Well-Architected", "Migration Lens · REL: RPO de segundos, rollback al origen · SEC: credenciales temporales")],
    },
    {
        "id": "10", "title": "CloudFormation StackSets: baseline multi-cuenta y multi-región",
        "goal": "Gobernar N cuentas desde un punto: un StackSet SERVICE_MANAGED despliega el baseline de seguridad a las OUs y un bus central concentra los hallazgos.",
        "groups": [("Cuenta management / delegated admin", 1, 3, 98, 48, "#232F3E", "#F7F9FB"),
                   ("OU workloads (auto-deployment)", 1, 60, 98, 36, "#8A97A3", "#FAFBFC")],
        "nodes": [
            ("tf", "Terraform\n(GitLab CI)", "ops", 4, 12, 13, 15),
            ("ss", "StackSet baseline\nSERVICE_MANAGED", "int", 24, 12, 15, 15),
            ("yaml", "security-baseline.yaml\nversionado en Git", "data", 46, 12, 18, 15),
            ("bus", "Bus security-central\naws:PrincipalOrgID", "int", 66, 32, 16, 15),
            ("sns", "SNS\nequipo seguridad", "ops", 86, 32, 12, 15),
            ("a1", "Cuenta Dev\nrol audit · reglas EB", "sec", 4, 72, 18, 15),
            ("a2", "Cuenta Test\nrol audit · reglas EB", "sec", 28, 72, 18, 15),
            ("a3", "Cuenta Prod\nrol audit · reglas EB", "sec", 54, 72, 18, 15),
            ("a4", "Cuenta nueva\nauto-deploy", "sec", 80, 72, 17, 15),
        ],
        "edges": [("tf", "ss"), ("yaml", "ss", "template_body", "dash"), ("ss", "a1", "stack instance"), ("ss", "a2"),
                  ("ss", "a3"), ("ss", "a4"), ("a3", "bus", "root · findings · IAM"), ("a4", "bus"), ("bus", "sns")],
        "rows": [
            ("StackSet", "aws_cloudformation_stack_set.baseline", "permission_model SERVICE_MANAGED; call_as SELF / DELEGATED_ADMIN; CAPABILITY_NAMED_IAM"),
            ("Despliegue", "auto_deployment + operation_preferences", "Cuentas nuevas reciben el baseline; max_concurrent_percentage = 25; failure_tolerance = 10 %"),
            ("Instancias", "aws_cloudformation_stack_set_instance.ous (for_each región)", "deployment_targets.organizational_unit_ids = target_ou_ids; target_regions"),
            ("Self-managed", "stackset_admin + templates/stackset-execution-role.yaml", "Alternativa sin Organizations: target_account_ids × target_regions"),
            ("Baseline (CFN)", "templates/security-baseline.yaml", "Rol aie-security-audit (MFA); reglas EB: root, GuardDuty ≥ 7, Security Hub HIGH, IAM; Config rules"),
            ("Hub", "aws_cloudwatch_event_bus.security + policy", "organization_id restringe PutEvents; regla → SNS con input_transformer"),
            ("Versionado", "baseline_version", "Subir la versión y hacer MR: el plan muestra el update y CloudFormation lo propaga gradualmente"),
        ],
        "facts": [("Variables GitLab", "AWS10_TFVARS (File); AWS_APPLY_ROLE_ARN_ORG (cuenta management)"), ("Storage mínimo", "Ninguno (templates en Git)"),
                  ("Well-Architected", "Management & Governance Lens · OPS: drift detection · SEC: guardrails homogéneos")],
    },
    {
        "id": "11", "title": "Seguridad y gobernanza: detectivos, preventivos, RBAC/ABAC y SCPs",
        "goal": "Controles mínimos del pilar de Seguridad: registrar todo, detectar amenazas, medir cumplimiento (CIS/FSBP), prevenir configuraciones inseguras y controlar acceso por rol y atributo.",
        "groups": [("Preventivos", 1, 3, 30, 92, "#C62828", "#FFFBFB"), ("Detectivos", 35, 3, 34, 92, "#2E7D32", "#FAFDFA"),
                   ("Respuesta", 73, 3, 26, 92, "#C2185B", "#FFFAFC")],
        "nodes": [
            ("scp", "SCPs\nregiones · cifrado · root", "sec", 4, 10, 24, 13),
            ("bnd", "Boundary developer\n+ ABAC Team", "sec", 4, 30, 24, 13),
            ("rbac", "Roles RBAC + MFA\n5 funciones", "sec", 4, 50, 24, 13),
            ("acct", "Cuenta: password policy\nS3 BPA · EBS cifrado", "sec", 4, 70, 24, 15),
            ("ct", "CloudTrail\nmulti-región · validación", "ops", 38, 10, 28, 13),
            ("cfg", "AWS Config\n14 reglas administradas", "ops", 38, 30, 28, 13),
            ("gd", "GuardDuty\nS3 · EBS · Lambda · RDS", "ops", 38, 50, 28, 13),
            ("sh", "Security Hub\nFSBP + CIS 3.0", "ops", 38, 70, 28, 15),
            ("s3", "S3 audit (KMS)\nIA 30 d · expira 365 d", "data", 76, 10, 21, 15),
            ("eb", "EventBridge\nsev ≥ 7 · break-glass", "int", 76, 40, 21, 14),
            ("sns", "SNS (KMS)\nemail / Slack", "int", 76, 70, 21, 14),
        ],
        "edges": [("ct", "s3"), ("cfg", "s3"), ("gd", "eb", "findings"), ("sh", "eb"), ("eb", "sns"),
                  ("gd", "sh", "", "dash"), ("cfg", "sh", "", "dash")],
        "rows": [
            ("Auditoría", "aws_cloudtrail.this + module.audit_bucket", "is_multi_region_trail; enable_log_file_validation; KMS; audit_log_retention_days = 365"),
            ("Config", "recorder + delivery_channel + config_rule (for_each)", "config_recording_frequency DAILY/CONTINUOUS; record_global_resources en una región; mapa config_managed_rules"),
            ("Amenazas", "aws_guardduty_detector + _detector_feature", "guardduty_features = S3_DATA_EVENTS, EBS_MALWARE_PROTECTION, LAMBDA_NETWORK_LOGS, RDS_LOGIN_EVENTS"),
            ("Cumplimiento", "aws_securityhub_account + standards_subscription", "securityhub_standards = FSBP 1.0.0, CIS 3.0.0; control_finding_generator SECURITY_CONTROL"),
            ("Preventivos de cuenta", "password_policy, s3_account_public_access_block, ebs_encryption_by_default", "14+ caracteres, reuso 24, rotación 90 días; BPA total; EBS cifrado"),
            ("RBAC", "aws_iam_role.rbac (for_each var.rbac_roles)", "break-glass 1 h, platform 4 h, developer 8 h + boundary, auditor, finops; MFA de menos de 1 h"),
            ("ABAC", "policies/abac-ec2-team.json", "aws:ResourceTag/Team = aws:PrincipalTag/Team; etiqueta obligatoria al crear"),
            ("SCPs", "aws_organizations_policy (manage_scps)", "policies/scp/*.json → scp_target_ids (OU sandbox primero)"),
        ],
        "facts": [("Variables GitLab", "AWS11_TFVARS (File); aplicar antes que los workloads"), ("Storage mínimo", "S3: Standard → IA a 30 días → expira a 365; snapshots de Config diarios"),
                  ("Well-Architected", "SEC 1-6 completos: identidad, detección, infraestructura, datos e incidentes")],
    },
]

LAB_DIRS = ["00-platform-bootstrap-s3-oidc", "01-serverless-apigw-lambda-dynamodb", "02-serverless-appsync-graphql", "03-events-eventbridge-sqs",
            "04-genai-chatbot-bedrock", "05-genai-docs-stepfunctions", "06-web3tier-alb-asg-rds", "07-sre-slo-cloudwatch-fis",
            "08-data-neptune-graph", "09-migration-mgn", "10-governance-stacksets", "11-security-guardrails-rbac"]
SMOKE = [
    "bucket seguro, OIDC por rama, boundary niega iam:CreateUser",
    "200/401/403/400/201/204/404, throttling, logs y X-Ray",
    "aislamiento entre 2 usuarios, depth limit, 401",
    "ruteo, transformación, auditoría y DLQ por falla de código",
    "respuesta, memoria (4 ítems), guardrails tema + prompt injection",
    "SUCCEEDED con entidades y resumen; ruta FAILED; prefijo ignorado",
    "2 AZ sanas, /db TLS vía Secrets Manager, RDS privado, WAF SQLi; CHAOS=1",
    "canary PASSED, alarmas compuestas; GENERATE_ERRORS=1 dispara fast burn",
    "bulk load, 8 nodos / 9 aristas, recomendación y fraude",
    "landing zone segura, estado de replicación MGN",
    "StackSet ACTIVE, instancias SUCCEEDED, drift IN_SYNC",
    "detectivos, preventivos, simulación RBAC, hallazgo de muestra",
]

# ---------------------------------------------------------------------------
# Sección general: RBAC y seguridad DevOps
# ---------------------------------------------------------------------------
PIPELINE_DIAGRAM = dict(
    groups=[("GitLab (proyecto ai-engineer-gcp-aws)", 1, 3, 46, 92), ("AWS", 52, 3, 47, 92)],
    nodes=[
        ("dev", "Developer\nrama feature", "ext", 3, 10, 13, 14),
        ("mr", "Merge request\nCODEOWNERS + 1 aprobación", "ops", 19, 10, 25, 14),
        ("val", "validate · tflint\nfmt + validate", "ops", 3, 40, 13, 15),
        ("chk", "checkov\nSAST de IaC", "sec", 18, 40, 12, 15),
        ("pl", "plan\nartifact plan.txt", "ops", 32, 40, 13, 15),
        ("main", "main protegida\nmerge Maintainer", "ops", 3, 74, 18, 14),
        ("ap", "apply MANUAL\nprotected env", "ops", 25, 74, 20, 14),
        ("oidc", "STS + OIDC\nvalida aud y sub", "sec", 55, 40, 14, 15),
        ("rp", "Rol plan\nReadOnly", "sec", 75, 18, 14, 14),
        ("ra", "Rol apply\nAdmin ∩ Boundary", "sec", 75, 62, 14, 14),
        ("scp", "SCPs de la OU\ntope organizacional", "sec", 55, 78, 14, 14),
        ("st", "S3 tfstate\nKMS · lock", "data", 75, 40, 14, 14),
        ("ws", "Workloads\nlabs 01–11", "compute", 92, 40, 7, 16),
    ],
    edges=[("dev", "mr"), ("mr", "val"), ("val", "chk"), ("chk", "pl"), ("pl", "oidc", "JWT ref:*"),
           ("main", "ap"), ("ap", "oidc", "JWT ref:main"), ("oidc", "rp"), ("oidc", "ra"), ("rp", "st", "lee"),
           ("ra", "ws", "despliega"), ("scp", "ra", "limita", "dash")],
)

GUARDRAIL_ROWS = [
    ["Capa (de afuera hacia adentro)", "Dónde se define", "Qué limita", "Micro lab"],
    ["1. SCP (Organizations)", "policies/scp/*.json", "Máximo permitido para TODA la cuenta, incluido el admin: regiones, cifrado, root, servicios de seguridad", "11 / 10"],
    ["2. Permissions boundary", "aws_iam_policy.boundary / developer_boundary", "Máximo para un rol concreto aunque tenga AdministratorAccess o PowerUser", "00 / 11"],
    ["3. Política de identidad (RBAC)", "aws_iam_role.rbac + managed policies", "Lo que la función necesita: developer, platform, auditor, finops, break-glass", "11"],
    ["4. ABAC (etiquetas)", "abac-ec2-team.json", "Restringe dentro del rol a los recursos del propio equipo (Team)", "11"],
    ["5. Política de recurso", "Políticas de S3/SQS/SNS/KMS/bus", "Quién puede usar el recurso: aws:SourceArn, aws:PrincipalOrgID, TLS-only", "01–11"],
    ["6. Red", "Security groups encadenados, subnets aisladas, endpoints", "Alcance de red mínimo; sin SSH; datos sin ruta a Internet", "06 / 08 / 09"],
]

RBAC_MATRIX = [
    ["Rol", "GitLab (proyecto)", "AWS (IAM role / permission set)", "Puede hacer", "No puede hacer"],
    ["Developer", "Developer: push a ramas, abrir MR, ver plan", "aie-dev-sec-developer (boundary + ABAC), 8 h", "Workloads serverless/EC2 pequeñas, recursos de su Team, roles aie-* con boundary", "Merge a main, apply en CI, IAM users/keys, apagar seguridad, instancias grandes"],
    ["Platform / SRE", "Maintainer: merge, ejecutar apply/destroy", "aie-dev-sec-platform-engineer, 4 h", "Infraestructura compartida (VPC, módulos), operar pipelines y runbooks", "Cambiar SCPs o desactivar CloudTrail/GuardDuty (SCP)"],
    ["Security", "Owner del grupo security; CODEOWNER de los micro labs 10/11", "Cuenta de seguridad + aie-security-audit (StackSets)", "SCPs, baseline, Security Hub, respuesta a incidentes", "Desplegar workloads"],
    ["Auditor", "Reporter (solo lectura)", "aie-dev-sec-auditor, 4 h", "Leer configuración, Config, CloudTrail y Security Hub", "Cualquier escritura"],
    ["FinOps", "Reporter", "aie-dev-sec-finops, 4 h", "Billing, Budgets, Cost Explorer", "Cambios de infraestructura"],
    ["CI plan", "Job plan (cualquier rama/MR)", "aie-dev-gitlab-plan (OIDC sub ref:*)", "Leer AWS y el estado; escribir el lock", "Crear o modificar recursos"],
    ["CI apply", "Job apply (solo main, manual, protected env)", "aie-dev-gitlab-apply (OIDC sub ref:main) ∩ boundary", "Aplicar planes aprobados", "Salir de las regiones permitidas; tocar el estado; crear users/keys"],
    ["Break-glass", "N/A (fuera del pipeline)", "aie-dev-sec-break-glass-admin, 1 h, MFA de menos de 1 h", "Recuperación en emergencias", "Usarse sin alerta: cada AssumeRole notifica a seguridad"],
]

DEVSECOPS_CHECKS = [
    ["Control", "Implementación en aie", "Dónde"],
    ["Sin secretos de larga duración", "OIDC id_tokens → AssumeRoleWithWebIdentity; condiciones aud + sub", ".gitlab-ci.yml (.aws_oidc), micro lab 00"],
    ["Separación de funciones", "Rol plan (lectura) ≠ rol apply (rama protegida); apply manual", "micro lab 00, ci.yml de cada lab"],
    ["Revisión obligatoria", "Protected branch main, MR approvals, CODEOWNERS en modules/ y labs 10/11", "Settings → Repository / Merge requests"],
    ["Escaneo de IaC", "terraform fmt/validate, tflint, checkov (reporte JUnit en el MR)", "Etapas validate y security"],
    ["Plan inmutable", "apply usa el plan.tfplan exacto del job plan (artifact)", ".tf_plan → .tf_apply"],
    ["Concurrencia segura", "resource_group por lab/entorno + use_lockfile de S3", ".tf_apply / .tf_destroy"],
    ["Estado protegido", "S3 SSE-KMS, versionado, TLS-only, boundary que impide borrar el bucket", "micro lab 00"],
    ["Variables sensibles", "tfvars como variables File protegidas; masked para IDs/ARNs; *.tfvars en .gitignore", "Settings → CI/CD → Variables"],
    ["Entornos protegidos", "environment dev/&lt;lab&gt;, prod/&lt;lab&gt;; solo Maintainers despliegan", "Settings → CI/CD → Protected environments"],
    ["Trazabilidad", "Etiquetas por default_tags (Project, Owner, MicroLab, CostCenter); CloudTrail", "versions.tf, micro lab 11"],
    ["Detección continua", "GuardDuty, Security Hub, Config → EventBridge → SNS/Slack", "labs 07, 10, 11"],
    ["Costo como control", "AWS Budgets, concurrencia reservada, tokens máximos, destroy manual", "labs 00, 04, 05"],
]

GITLAB_VARS = [
    ["Variable", "Tipo", "Protegida", "Enmascarada", "Valor / origen"],
    ["TF_STATE_BUCKET", "Variable", "No", "No", "output tf_state_bucket (micro lab 00)"],
    ["AWS_PLAN_ROLE_ARN", "Variable", "No", "Sí", "output aws_plan_role_arn (micro lab 00)"],
    ["AWS_APPLY_ROLE_ARN", "Variable", "Sí", "Sí", "output aws_apply_role_arn (micro lab 00)"],
    ["AWS_REGION / TF_ENV", "Variable", "No", "No", "us-east-1 / dev (environment scope para prod)"],
    ["AWS01_TFVARS … AWS11_TFVARS", "File", "Sí", "No", "Contenido de terraform.tfvars de cada lab"],
    ["DESTROY_LAB", "Variable (al ejecutar)", "No", "No", "Nombre del lab a destruir, p. ej. 06-web3tier-alb-asg-rds"],
    ["TF_VAR_*", "Variable", "Según dato", "Según dato", "Sobrescribe una variable puntual (p. ej. TF_VAR_system_prompt)"],
]

WA_MATRIX = [
    ["Lab", "Excelencia operativa", "Seguridad", "Confiabilidad", "Eficiencia de rendimiento", "Costos", "Sostenibilidad"],
    ["00", "IaC + estado versionado", "OIDC, boundary, KMS", "Versionado del estado", "N/A", "Budgets", "Sin recursos ociosos"],
    ["01", "OpenAPI, logs JSON", "WAF, Cognito, API key", "Throttling, PITR", "arm64, MOCK", "Pago por uso", "Graviton"],
    ["02", "Schema en Git", "Auth por campo", "Condiciones DDB", "Sin Lambda", "Sin cómputo extra", "Menos saltos"],
    ["03", "Auditoría + replay", "SourceArn", "Retry + DLQ", "Filtro en el bus", "USD 1/M eventos", "Por evento"],
    ["04", "Tokens en logs", "Guardrails + JWT", "Alarmas de throttling", "Converse API", "Topes de tokens", "Modelo mínimo"],
    ["05", "Flujo visual", "Sin datos en logs", "Retry + Catch", "Parallel + SDK", "Concurrencia 5", "Expiración"],
    ["06", "Módulos por capa", "SG encadenados", "Multi-AZ total", "Target tracking", "NAT único en dev", "Graviton"],
    ["07", "SLO + runbooks", "Chatbot RO", "Chaos con FIS", "p99 SLI", "Canary de 5 min", "Menos ruido"],
    ["08", "Audit logs", "IAM auth, sin Internet", "6 copias en 3 AZ", "Serverless NCU", "Sin NAT", "Escala a demanda"],
    ["09", "Waves + test", "MFA, KMS, temporales", "RPO de segundos", "Right-sizing", "Finalizar rápido", "Apagar on-prem"],
    ["10", "Drift, versión", "Baseline homogéneo", "Tolerancia a fallas", "Paralelo", "Sin costo", "1 template para N cuentas"],
    ["11", "Hallazgos centralizados", "SEC 1–6", "Logs inmutables", "N/A", "Config DAILY", "Ciclo de vida de logs"],
]


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------
def on_page(canvas, doc):
    canvas.saveState()
    w, h = landscape(letter)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, h - 6, w, 6, stroke=0, fill=1)
    canvas.setFillColor(HILITE)
    canvas.rect(0, h - 6, 90, 6, stroke=0, fill=1)
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.5 * inch, 0.32 * inch, "AI Engineer GCP + AWS · Terraform en AWS · Well-Architected · GitLab CI")
    canvas.drawRightString(w - 0.5 * inch, 0.32 * inch, f"{doc.page}")
    canvas.restoreState()


def facts_table(facts):
    rows = [[Paragraph(k, styles["cellb"]), Paragraph(v, styles["cell"])] for k, v in facts]
    t = Table(rows, colWidths=[1.75 * inch, 8.25 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#FFF4E5")),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(
        str(OUT), pagesize=landscape(letter), leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.45 * inch, bottomMargin=0.55 * inch,
        title="Arquitecturas AWS con Terraform", author="Axel Valenzuela",
        subject="Micro labs AWS: serverless, SRE, IA, 3 niveles, migración y gobernanza",
    )
    s = []

    # Portada
    s += [Spacer(1, 0.6 * inch), P("Terraform en AWS: arquitecturas de los micro labs", "title"), Spacer(1, 6),
          P("Diagramas de arquitectura, implementación con Terraform, RBAC y seguridad DevOps sobre GitLab CI, "
            "alineados con el AWS Well-Architected Framework.", "subtitle"), Spacer(1, 18)]
    idx = [["#", "Micro lab", "Servicios principales", "Arquitectura"]]
    kinds = ["Plataforma", "Serverless", "Serverless GraphQL", "Event-driven", "IA generativa", "IA orquestada",
             "3 niveles", "SRE", "Grafos", "Migración", "Multi-cuenta", "Gobernanza"]
    services = ["S3 state, KMS, IAM OIDC, Budgets", "API Gateway REST, Lambda, DynamoDB, Cognito, WAF",
                "AppSync, resolvers JS, DynamoDB", "EventBridge, Scheduler, SQS, Lambda", "HTTP API, Lambda, Bedrock, Guardrails",
                "S3, Step Functions, Textract, Comprehend, Bedrock", "VPC, ALB, WAF, ASG, RDS Multi-AZ",
                "CloudWatch SLO, Synthetics, Q chat apps, FIS", "Neptune Serverless, Lambda VPC", "AWS MGN, KMS, IAM",
                "CloudFormation StackSets, Organizations", "CloudTrail, Config, GuardDuty, Security Hub, SCP"]
    names = ["Bootstrap", "API serverless", "AppSync GraphQL", "EventBridge event-driven", "Chatbot Bedrock",
             "Pipeline IA de documentos", "Web de 3 niveles", "SRE observabilidad", "Neptune grafos", "Migración MGN",
             "CloudFormation StackSets", "Seguridad y gobernanza"]
    for lab, name, svc, kind in zip(LABS, names, services, kinds):
        idx.append([lab["id"], name, svc, kind])
    s.append(table(idx, [0.4 * inch, 3.4 * inch, 4.3 * inch, 1.9 * inch]))
    s += [Spacer(1, 10), P("Código fuente: <b>08-terraform-aws/</b> (módulos en <b>modules/</b>, labs en <b>microlabs/NN-nombre/</b>). "
                           "Cada lab incluye README con instrucciones, terraform.tfvars.example y ci.yml. "
                           "Todos pasan terraform validate (Terraform 1.13 · AWS provider 6.x); no se han desplegado en una cuenta real.", "small"),
          PageBreak()]

    # Parte 1: RBAC y DevSecOps
    s += [P("Parte 1 · Cómo hacer el RBAC y la seguridad DevOps", "h1"),
          P("El acceso se diseña en dos planos que se refuerzan: <b>quién puede cambiar el código</b> (roles de GitLab, ramas y entornos protegidos) "
            "y <b>con qué identidad se despliega</b> (roles IAM asumidos por OIDC, nunca llaves). Ninguna persona necesita permisos de escritura "
            "permanentes en AWS: el pipeline aplica lo que se aprobó en el merge request.", "lead"),
          P("1.1 Flujo GitOps con OIDC y separación de funciones", "h2"),
          Diagram(PIPELINE_DIAGRAM["nodes"], PIPELINE_DIAGRAM["edges"], PIPELINE_DIAGRAM["groups"], height=3.3 * inch),
          Spacer(1, 4),
          P("La condición <b>sub</b> del token es la llave del modelo: <i>project_path:grupo/proyecto:ref_type:branch:ref:main</i> "
            "solo existe en pipelines de la rama protegida, así que una rama feature nunca puede asumir el rol de apply.", "small"),
          PageBreak(),
          P("1.2 Matriz RBAC (GitLab ↔ AWS)", "h2"),
          table(RBAC_MATRIX, [1.05 * inch, 1.9 * inch, 2.15 * inch, 2.6 * inch, 2.3 * inch]),
          Spacer(1, 8),
          P("Recomendación para producción: centralizar personas en <b>IAM Identity Center</b> (SSO con el IdP de la universidad o la empresa) "
            "y mapear grupos a permission sets equivalentes a los roles del micro lab 11. Usa una cuenta por entorno (dev/test/prod) "
            "dentro de AWS Organizations y propaga el baseline con StackSets (micro lab 10).", "small"),
          CondPageBreak(3 * inch),
          P("1.3 Capas de guardrails (defensa en profundidad)", "h2"),
          P("El permiso efectivo es la <b>intersección</b> de todas las capas: una acción debe estar permitida en cada una y no estar denegada en ninguna.", "body"),
          Spacer(1, 4),
          table(GUARDRAIL_ROWS, [1.9 * inch, 2.5 * inch, 4.8 * inch, 0.8 * inch]),
          PageBreak(),
          P("1.4 Controles DevSecOps del pipeline", "h2"),
          table(DEVSECOPS_CHECKS, [2.0 * inch, 5.2 * inch, 2.8 * inch]),
          Spacer(1, 8),
          P("1.5 Variables a configurar en GitLab (Settings → CI/CD → Variables)", "h2"),
          table(GITLAB_VARS, [2.2 * inch, 1.3 * inch, 0.9 * inch, 1.0 * inch, 4.6 * inch]),
          Spacer(1, 6),
          P("CI/CD configuration file: <b>08-terraform-aws/.gitlab-ci.yml</b> · Protected branch: <b>main</b> (merge: Maintainers, push: nadie) · "
            "Protected environments: <b>dev/*</b>, <b>prod/*</b> · Pipeline must succeed + 1 aprobación + CODEOWNERS.", "small"),
          PageBreak()]

    # Parte 2: micro labs
    s.append(P("Parte 2 · Arquitecturas e implementación por micro lab", "h1"))
    s.append(P("Cada lab muestra el diagrama (colores por categoría, fronteras punteadas = cuenta / VPC / subnet), "
               "la tabla de cómo se implementa con Terraform y los datos de operación.", "lead"))
    for i, lab in enumerate(LABS):
        if i > 0:
            s.append(PageBreak())
        s.append(KeepTogether([
            P(f"Micro lab {lab['id']} · {lab['title']}", "h1"),
            P(lab["goal"], "lead"),
            Diagram(lab["nodes"], lab["edges"], lab["groups"], height=3.25 * inch),
        ]))
        s.append(Spacer(1, 6))
        s.append(table([TF_HEAD] + [list(r) for r in lab["rows"]], TF_COLS))
        s.append(Spacer(1, 4))
        s.append(facts_table(lab["facts"] + [("Prueba automatizada", f"bash scripts/lab.sh test {LAB_DIRS[i]} → {SMOKE[i]}")]))

    # Anexo
    s += [PageBreak(), P("Anexo · Matriz Well-Architected por micro lab", "h1"),
          P("Resumen de cómo cada lab aterriza los seis pilares. El detalle está en la sección Well-Architected de cada README.", "lead"),
          table(WA_MATRIX, [0.45 * inch] + [1.59 * inch] * 6),
          Spacer(1, 10),
          P("Orden recomendado: 00 → 11 → 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10. "
            "Destruye los labs 06 (~USD 95/mes) y 08 (~USD 115/mes) al terminar cada sesión.", "body")]

    doc.build(s, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF generado: {OUT}")


if __name__ == "__main__":
    build()
