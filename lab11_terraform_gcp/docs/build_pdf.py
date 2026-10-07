"""Genera docs/lab11-arquitecturas-gcp.pdf: guía RBAC/DevSecOps en GCP + diagrama y tabla Terraform por micro lab.

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
ACCENT = colors.HexColor("#174EA6")  # azul Google
HILITE = colors.HexColor("#34A853")  # verde Google

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

OUT = Path(__file__).parent / "lab11-arquitecturas-gcp.pdf"

# ---------------------------------------------------------------------------
# Contenido de los micro labs (GCP)
# ---------------------------------------------------------------------------
LABS = [
    {
        "id": "00", "dir": "00-bootstrap", "title": "Bootstrap: estado remoto, Workload Identity Federation y presupuesto",
        "goal": "Prepara el proyecto para desplegar desde GitLab sin llaves JSON: estado en GCS, federación OIDC, SAs separadas de plan y apply, builder de Cloud Build y presupuesto.",
        "groups": [("GitLab", 1, 4, 22, 88), ("Proyecto GCP", 27, 4, 72, 88)],
        "nodes": [
            ("dev", "Desarrollador\nMR / merge a main", "ext", 4, 10, 16, 14),
            ("ci", "Job de GitLab CI\nid_token (JWT)", "ops", 4, 46, 16, 16),
            ("wif", "WIF pool + provider\ncondición project_path", "sec", 31, 46, 18, 16),
            ("plan", "SA tf-plan\nviewer + securityReviewer", "sec", 55, 16, 19, 15),
            ("apply", "SA tf-apply\nsolo deploy_ref ...:main", "sec", 55, 66, 19, 15),
            ("gcs", "GCS tfstate\nversionado · lock nativo", "data", 80, 40, 18, 15),
            ("build", "SA builder\nCloud Build", "compute", 80, 8, 18, 13),
            ("ar", "Artifact Registry\ncleanup policies", "data", 80, 72, 18, 13),
            ("bud", "Billing budget\n50 / 80 / 100 %", "ops", 31, 76, 18, 13),
        ],
        "edges": [("dev", "ci", "pipeline"), ("ci", "wif", "STS token exchange"), ("wif", "plan", "project_id"),
                  ("wif", "apply", "branch:main"), ("plan", "gcs", "lee/lock"), ("apply", "gcs", "escribe"),
                  ("apply", "build", "actAs", "dash")],
        "rows": [
            ("Estado", "module.state_bucket → modules/gcs-secure-bucket", "force_destroy = false; versionado; soft delete 30 d; UBLA; public access prevention"),
            ("Federación", "google_iam_workload_identity_pool(_provider)", "issuer https://gitlab.com; attribute_mapping (project_id, ref, deploy_ref); attribute_condition project_path"),
            ("SA plan", "module.plan_sa + google_service_account_iam_member.plan_wif", "principalSet .../attribute.project_id/&lt;id&gt;; roles viewer + securityReviewer"),
            ("SA apply", "module.apply_sa + apply_wif", "principalSet .../attribute.deploy_ref/&lt;id&gt;:branch:main; apply_roles"),
            ("Builder", "module.builder_sa", "cloudbuild.builds.builder, logWriter, artifactregistry.writer"),
            ("Imágenes", "google_artifact_registry_repository", "keep 10 versiones; borra untagged > 7 días"),
            ("Costo", "google_billing_budget (count)", "billing_account; monthly_budget; notificación por email"),
        ],
        "facts": [("Variables GitLab", "TF_STATE_BUCKET, GCP_WIF_PROVIDER, GCP_PLAN_SA, GCP_APPLY_SA (protegida), GCP_PROJECT_ID"),
                  ("Storage mínimo", "GCS < 1 MB por lab"), ("Architecture Framework", "SEC: sin llaves, apply solo en main · OPS: GitOps · COST: budget")],
        "smoke": "bucket seguro, provider ACTIVE, SA apply sin llaves y solo desde main",
    },
    {
        "id": "01", "dir": "01-api-gateway-functions", "title": "API serverless: API Gateway + Cloud Run functions + Firestore",
        "goal": "API REST con contrato OpenAPI, API keys con cuota por consumidor, backend privado (solo el gateway lo invoca) e IAM condicionado a una base de Firestore.",
        "groups": [("Región us-central1", 16, 3, 83, 92)],
        "nodes": [
            ("cli", "Cliente\nx-api-key", "ext", 1, 40, 12, 15),
            ("gw", "API Gateway\nOpenAPI 2.0 · cuota", "int", 20, 40, 16, 15),
            ("key", "API key\nrestringida al API", "sec", 20, 8, 16, 13),
            ("gsa", "SA del gateway\nID token", "sec", 20, 74, 16, 13),
            ("fn", "Cloud Run function\nitems · max 5", "compute", 44, 40, 17, 15),
            ("fsa", "SA de la función\ndatastore.user cond.", "sec", 44, 74, 17, 13),
            ("fs", "Firestore Native\nbase nombrada · PITR", "data", 70, 40, 17, 15),
            ("cb", "Cloud Build\nbuild desde source", "ops", 70, 8, 17, 13),
        ],
        "edges": [("cli", "gw", "HTTPS"), ("key", "gw", "valida", "dash"), ("gw", "fn", "ID token"), ("gsa", "gw", "", "dash"),
                  ("fn", "fs", "IAM condicionado"), ("fsa", "fn", "", "dash"), ("cb", "fn", "zip → imagen", "dash")],
        "rows": [
            ("Contrato", "openapi.yaml.tpl → base64encode(templatefile())", "x-google-backend (APPEND_PATH), securityDefinitions api_key, x-google-management (quota_per_minute)"),
            ("Gateway", "google_api_gateway_api / _api_config / _gateway (google-beta)", "api_config_id_prefix + create_before_destroy; backend_config con el SA del gateway"),
            ("API key", "google_apikeys_key + google_project_service.managed_api", "restrictions.api_targets = servicio administrado del API"),
            ("Función", "module.items_fn → modules/cloud-function", "python313; invoker_members = [SA del gateway] → llamada directa 403"),
            ("Datos", "google_firestore_database", "FIRESTORE_NATIVE; PITR; IAM condition resource.name.startsWith(base)"),
            ("Fallas (lab 07)", "var.enable_fault_injection", "Header x-fault-injection → 500 solo si está habilitado"),
        ],
        "facts": [("Variables GitLab", "GCP01_TFVARS (File)"), ("Storage mínimo", "Firestore por operación; zips con expiración de 30 días"),
                  ("Architecture Framework", "SEC: key + cuota + backend privado · REL: PITR · COST: free tier")],
        "smoke": "401/400, 403 backend privado, CRUD 201→200→204→404, 429 por cuota",
    },
    {
        "id": "02", "dir": "02-pubsub-event-driven", "title": "Orientado a eventos con Pub/Sub: schema, push OIDC, DLQ, filtros y BigQuery",
        "goal": "Contrato AVRO validado al publicar, push autenticado con reintentos y dead letter, suscripción filtrada, auditoría directa en BigQuery y Cloud Scheduler.",
        "groups": [("Pub/Sub", 20, 3, 34, 92)],
        "nodes": [
            ("prod", "Productores\npublish JSON", "ext", 1, 24, 15, 14),
            ("sch", "Cloud Scheduler\ncron + OIDC", "int", 1, 66, 15, 14),
            ("topic", "Topic orders\nschema AVRO · 7 d", "int", 24, 24, 16, 15),
            ("dlq", "Topic dead-letter\n+ sub inspect", "int", 24, 66, 16, 14),
            ("push", "Sub push\nOIDC · retry · DLQ 5", "int", 42, 8, 11, 16),
            ("hv", "Sub high-value\ntier = high", "int", 42, 40, 11, 14),
            ("bqs", "Sub BigQuery\nwrite_metadata", "int", 42, 70, 11, 14),
            ("fn", "Function processor\n500 ⇒ reintento", "compute", 62, 8, 17, 15),
            ("rep", "Function reporter", "compute", 62, 40, 17, 12),
            ("bq", "BigQuery\norder_events", "data", 84, 70, 14, 14),
            ("al", "Alerta\ndead letters > 0", "ops", 84, 32, 14, 14),
        ],
        "edges": [("prod", "topic"), ("topic", "push"), ("topic", "hv"), ("topic", "bqs"), ("push", "fn", "HTTPS"),
                  ("push", "dlq", "5 intentos", "dash"), ("bqs", "bq"), ("sch", "rep", "OIDC"), ("dlq", "al", "", "dash")],
        "rows": [
            ("Contrato", "google_pubsub_schema + schemas/order.avsc", "AVRO con encoding JSON; uniones como {\"double\": 250}"),
            ("Topic", "google_pubsub_topic.orders", "message_retention_duration 7 d → seek para replay"),
            ("Push + DLQ", "google_pubsub_subscription.processor", "oidc_token (SA push); retry 10-60 s; dead_letter_policy max_delivery_attempts = 5"),
            ("Agente Pub/Sub", "topic/subscription IAM + tokenCreator", "publisher en DLQ, subscriber en la sub, firma OIDC"),
            ("Filtro", "google_pubsub_subscription.high_value", "filter = attributes.tier = \"high\""),
            ("Auditoría", "bigquery_config + google_bigquery_table.events", "write_metadata; partición diaria; audit_retention_days"),
            ("Programación", "google_cloud_scheduler_job.report", "report_schedule, schedule_timezone, oidc_token"),
        ],
        "facts": [("Variables GitLab", "GCP02_TFVARS (File)"), ("Storage mínimo", "Retención Pub/Sub 7/14 d; BigQuery 30 d"),
                  ("Architecture Framework", "REL: retry + DLQ + replay · SEC: push OIDC · COST: sin código para auditar")],
        "smoke": "schema rechaza inválidos, filtro, DLQ tras 5 intentos, BigQuery, Scheduler",
    },
    {
        "id": "03", "dir": "03-vertex-ai-chatbot", "title": "Chatbot de IA generativa con Vertex AI Gemini",
        "goal": "Chatbot privado con Gemini (SDK google-genai), historial en Firestore con TTL nativo, guardrails en capas y métricas de tokens en Logging.",
        "groups": [("Proyecto GCP", 18, 3, 81, 92)],
        "nodes": [
            ("u", "Usuario\nidentity token", "ext", 1, 40, 14, 15),
            ("fn", "Function chat\nprivada · conc. 8", "compute", 22, 40, 16, 15),
            ("g1", "Guardrail de entrada\ntemas · injection", "sec", 22, 8, 16, 14),
            ("fs", "Firestore\nmessages · TTL 24 h", "data", 22, 74, 16, 14),
            ("vx", "Vertex AI\nGemini 2.5 Flash", "ai", 46, 40, 16, 15),
            ("sf", "Safety settings\n+ system instruction", "sec", 46, 8, 16, 14),
            ("lg", "Cloud Logging\ntokens in/out", "ops", 72, 40, 16, 15),
            ("m", "Métricas de logs\noutput_tokens · bloqueos", "ops", 72, 74, 16, 14),
        ],
        "edges": [("u", "fn", "Bearer"), ("fn", "g1", "", "dash"), ("fn", "fs", "historial"),
                  ("fn", "vx", "generate_content"), ("sf", "vx", "", "dash"), ("fn", "lg", "JSON"), ("lg", "m")],
        "rows": [
            ("Código", "src/chat/main.py", "genai.Client(vertexai=True); historial por email#session; finish_reason / prompt_feedback"),
            ("Historial", "google_firestore_database + _index + _field (ttl_config)", "Índice session_id + ts; TTL sobre expires_at"),
            ("Identidad", "module.chat_sa", "aiplatform.user + datastore.user condicionado a la base"),
            ("Función", "module.chat_fn", "512 Mi, 1 vCPU, concurrencia 8; invoker_members; max_instances = tope de gasto"),
            ("Parámetros IA", "model, vertex_location, system_instruction", "max_output_tokens = 512; history_turns = 6; blocked_topics"),
            ("Observabilidad", "google_logging_metric x2", "Distribución de output_tokens; conteo de guardrail_blocks"),
        ],
        "facts": [("Variables GitLab", "GCP03_TFVARS (File), TF_VAR_system_instruction"), ("Storage mínimo", "Firestore con TTL 24 h"),
                  ("Architecture Framework", "SEC: función privada + 3 capas de guardrails · COST: tokens e instancias acotados")],
        "smoke": "403 sin token, STOP + tokens, memoria, tema e injection bloqueados",
    },
    {
        "id": "04", "dir": "04-document-ai-workflows", "title": "Pipeline de IA para documentos con Cloud Workflows",
        "goal": "Orquestar APIs de IA con conectores de Workflows, sin funciones propias: OCR, entidades y resumen en paralelo, con try/except y resultados en BigQuery.",
        "groups": [("Cloud Workflows", 36, 3, 63, 92)],
        "nodes": [
            ("u", "Usuario\ngcloud storage cp", "ext", 1, 8, 14, 13),
            ("gcs", "GCS docs/incoming\nexpira 30 d", "data", 1, 40, 15, 16),
            ("ea", "Eventarc\nobject.finalized", "int", 19, 40, 13, 16),
            ("rt", "route por extensión\n.txt · imagen · otro", "compute", 40, 40, 15, 16),
            ("ocr", "Vision OCR\nTEXT_DETECTION", "ai", 40, 8, 15, 13),
            ("nl", "Natural Language\nanalyzeEntities", "ai", 61, 18, 15, 14),
            ("gm", "Vertex AI Gemini\ngenerateContent", "ai", 61, 62, 15, 14),
            ("bq", "BigQuery\ninsertAll (JSON)", "data", 84, 40, 14, 16),
            ("al", "except → log ERROR\nalerta FAILED", "ops", 40, 78, 15, 14),
        ],
        "edges": [("u", "gcs"), ("gcs", "ea"), ("ea", "rt", "ejecuta"), ("rt", "ocr", "imagen", "dash"), ("rt", "nl", "parallel"),
                  ("rt", "gm", "parallel"), ("nl", "bq"), ("gm", "bq"), ("rt", "al", "falla", "dash")],
        "rows": [
            ("Definición", "workflow.yaml → file()", "Expresiones con ':' entre comillas; switch con next; parallel shared [entities, summary]"),
            ("Workflow", "google_workflows_workflow", "user_env_vars (MODEL, VERTEX_LOCATION, LANGUAGE, DATASET, TABLE); call_log_level LOG_ERRORS_ONLY"),
            ("Disparador", "google_eventarc_trigger + IAM del agente GCS", "type + bucket; SA con workflows.invoker y eventarc.eventReceiver"),
            ("Identidad", "module.workflow_sa", "aiplatform.user, serviceUsageConsumer; objectViewer en el bucket; dataEditor en el dataset"),
            ("Resultados", "google_bigquery_table.documents", "entities tipo JSON; partición diaria por processed_at"),
            ("Alerta", "google_monitoring_alert_policy.failed", "finished_execution_count{status=FAILED} > 0"),
        ],
        "facts": [("Variables GitLab", "GCP04_TFVARS (File)"), ("Storage mínimo", "GCS 30 d; 1 fila por documento"),
                  ("Architecture Framework", "OPS: historial visual por paso · COST: sin servidores · PERF: paralelismo")],
        "smoke": "SUCCEEDED con entidades + resumen; .docx FAILED; otros/ ignorado",
    },
    {
        "id": "05", "dir": "05-three-tier-web", "title": "Arquitectura web de 3 niveles: Load Balancer + MIG + Cloud SQL HA",
        "goal": "LB global con Cloud Armor, MIG regional sin IPs públicas con autohealing, y Cloud SQL PostgreSQL HA solo por IP privada con TLS y Secret Manager.",
        "groups": [("VPC lab11-dev-3t", 14, 2, 85, 94, "#6A3FB5", "#FBFAFE"),
                   ("Borde global", 17, 8, 24, 84, "#8A97A3", "#F7F9FB"),
                   ("Subnet app (sin IPs públicas)", 44, 8, 26, 84, "#8A97A3", "#F7F9FB"),
                   ("Servicios administrados (PSA)", 73, 8, 24, 84, "#8A97A3", "#F7F9FB")],
        "nodes": [
            ("inet", "Internet", "ext", 0, 42, 11, 13),
            ("armor", "Cloud Armor\nSQLi · XSS · rate", "sec", 20, 14, 18, 14),
            ("lb", "External App LB\nIP global", "net", 20, 42, 18, 15),
            ("nat", "Cloud NAT\nsalida", "net", 20, 72, 18, 12),
            ("vma", "VM zona a\nOS Login · Shielded", "compute", 48, 18, 18, 14),
            ("vmb", "VM zona c\nMIG 2..4 · autoheal", "compute", 48, 46, 18, 14),
            ("sm", "Secret Manager\npassword", "sec", 48, 74, 18, 12),
            ("sqlp", "Cloud SQL PG 16\nprimaria", "data", 76, 18, 18, 14),
            ("sqls", "Standby HA\notra zona", "data", 76, 46, 18, 14),
        ],
        "edges": [("inet", "lb", "HTTP(S)"), ("armor", "lb", "política", "dash"), ("lb", "vma"), ("lb", "vmb"),
                  ("vma", "sqlp", "IP privada TLS"), ("vmb", "sqlp"), ("sqlp", "sqls", "sync"), ("vmb", "sm", "REST"),
                  ("vmb", "nat", "apt", "dash")],
        "rows": [
            ("Red", "module.vpc", "subnet app; Cloud NAT; Private Service Access; health checks 130.211/22 y 35.191/16; IAP"),
            ("Datos", "google_sql_database_instance.db", "REGIONAL; ipv4_enabled = false; ssl_mode ENCRYPTED_ONLY; PITR; backups 7; Query Insights"),
            ("Credenciales", "random_password + google_secret_manager_secret", "La VM la lee con el token del SA (sin llaves)"),
            ("App", "google_compute_instance_template + startup.sh.tpl", "Debian 12; app Python stdlib (/, /health, /db); Shielded VM; OS Login"),
            ("Cómputo", "region_instance_group_manager + region_autoscaler", "autohealing 180 s; update PROACTIVE max_unavailable 0; CPU 60 %"),
            ("WAF", "google_compute_security_policy.waf", "sqli-v33-stable, xss-v33-stable, rate_based_ban rate_limit_per_minute"),
            ("Borde", "backend_service / url_map / http(s) proxy / forwarding_rule", "EXTERNAL_MANAGED; HTTPS con certificado administrado si domain != null"),
        ],
        "facts": [("Variables GitLab", "GCP05_TFVARS (File); timeout 1 h"), ("Storage mínimo", "10 GB por VM; Cloud SQL 10 GB SSD con autoresize"),
                  ("Architecture Framework", "REL: MIG regional + SQL HA · SEC: Armor, sin IPs públicas · COST: ~USD 120/mes")],
        "smoke": "2 zonas sanas, /db TLS, SQL REGIONAL + PITR, Armor SQLi/XSS; CHAOS=1",
    },
    {
        "id": "06", "dir": "06-gke-autopilot", "title": "GKE Autopilot privado con workload endurecido",
        "goal": "Kubernetes administrado con seguridad por defecto: nodos privados, Workload Identity, Pod Security restricted, NetworkPolicy, HPA y PDB, todo en Terraform.",
        "groups": [("GKE Autopilot regional (nodos privados)", 22, 3, 77, 92, "#6A3FB5", "#FBFAFE"),
                   ("namespace lab11-app · PSA restricted", 26, 22, 70, 70, "#8A97A3", "#F7F9FB")],
        "nodes": [
            ("adm", "Admin\nkubectl (IP autorizada)", "ext", 1, 10, 17, 14),
            ("usr", "Usuario\nHTTP", "ext", 1, 56, 17, 13),
            ("cp", "Control plane\nauthorized networks", "net", 28, 6, 18, 12),
            ("svc", "Service\nLoadBalancer :80", "net", 30, 52, 16, 14),
            ("dep", "Deployment web\nnon-root · read-only", "compute", 52, 36, 18, 15),
            ("hpa", "HPA 2–6\nPDB minAvailable 1", "ops", 52, 70, 18, 14),
            ("np", "NetworkPolicy\ndeny + allow 8080", "sec", 76, 70, 18, 14),
            ("ksa", "KSA app\n→ GSA (WI)", "sec", 76, 36, 18, 15),
            ("gsa", "GSA\nlogWriter · metricWriter", "sec", 76, 6, 18, 12),
        ],
        "edges": [("adm", "cp"), ("usr", "svc"), ("svc", "dep", "8080"), ("hpa", "dep", "escala", "dash"),
                  ("np", "dep", "", "dash"), ("dep", "ksa"), ("ksa", "gsa", "workloadIdentityUser")],
        "rows": [
            ("Red", "module.vpc (secondary_ranges pods/services)", "nodes_cidr, pods_cidr, services_cidr; Cloud NAT para imágenes externas"),
            ("Cluster", "google_container_cluster", "enable_autopilot; enable_private_nodes; master_authorized_networks; release REGULAR; maintenance window"),
            ("Identidad", "google_service_account_iam_member.workload_identity", "&lt;project&gt;.svc.id.goog[lab11-app/app] → GSA"),
            ("Provider k8s", "provider \"kubernetes\" (token de google_client_config)", "Despliega en el mismo apply (repite apply si el cluster es nuevo)"),
            ("Workload", "kubernetes_deployment_v1", "runAsNonRoot, seccomp RuntimeDefault, drop ALL, readOnlyRootFilesystem, probes, topology spread"),
            ("Resiliencia", "HPA v2 + PDB + Service LoadBalancer", "min/max_replicas; CPU 60 %; minAvailable 1"),
            ("Zero-trust", "kubernetes_network_policy_v1 x2", "default-deny-ingress + allow-web-8080"),
        ],
        "facts": [("Variables GitLab", "GCP06_TFVARS (File)"), ("Storage mínimo", "emptyDir /tmp; sin volúmenes persistentes"),
                  ("Architecture Framework", "SEC: PSA + WI + nodos privados · REL: regional + PDB · COST: ~USD 95/mes")],
        "smoke": "nodos privados, WI, pod privilegiado rechazado, LB 200, PDB/NetPol; LOAD=1",
    },
    {
        "id": "07", "dir": "07-sre-observability", "title": "SRE con Cloud Monitoring: SLOs, burn rate, uptime y dashboard",
        "goal": "SLOs request-based sobre la función del lab 01 y alertas por consumo del presupuesto de error (multi-window, multi-burn-rate), con uptime checks y señales doradas.",
        "groups": [("Cloud Monitoring", 22, 3, 56, 92)],
        "nodes": [
            ("run", "Cloud Run\nfunción items (lab 01)", "ext", 1, 20, 17, 15),
            ("gw", "Gateway /health\n(lab 01)", "ext", 1, 66, 17, 14),
            ("svc", "Custom service\n+ SLO 99.5 % · p95", "ops", 26, 20, 18, 16),
            ("fast", "Alerta fast 14.4x\n1 h AND 5 min", "ops", 50, 8, 20, 14),
            ("slow", "Alerta slow 6x\n6 h AND 30 min", "ops", 50, 34, 20, 14),
            ("up", "Uptime check\n3 regiones", "ops", 26, 66, 18, 14),
            ("ua", "Alerta uptime\nfalla en 2+", "ops", 50, 66, 20, 14),
            ("dash", "Dashboard\ngolden signals", "ops", 26, 44, 18, 12),
            ("mail", "Email\non-call", "ext", 84, 40, 14, 14),
        ],
        "edges": [("run", "svc", "request_count"), ("svc", "fast", "burn rate"), ("svc", "slow"), ("gw", "up", "", "dash"),
                  ("up", "ua"), ("fast", "mail"), ("slow", "mail"), ("ua", "mail"), ("svc", "dash", "", "dash")],
        "rows": [
            ("Integración", "data.terraform_remote_state.lab01 (gcs)", "lab01_state_bucket → servicio y host sin copiarlos a mano"),
            ("Servicio", "google_monitoring_custom_service", "Agrupa los SLOs del API"),
            ("SLO disponibilidad", "google_monitoring_slo.availability", "request_based_sli.good_total_ratio: bad = 5xx, total = request_count; availability_goal"),
            ("SLO latencia", "google_monitoring_slo.latency", "distribution_cut request_latencies < latency_threshold_ms; latency_goal"),
            ("Burn rate", "google_monitoring_alert_policy.burn (for_each)", "select_slo_burn_rate(slo, ventana) > tasa; combiner AND; severidad"),
            ("Caja negra", "google_monitoring_uptime_check_config + alerta", "SSL validado; REDUCE_COUNT_FALSE > 1"),
            ("Dashboard", "google_monitoring_dashboard + dashboard.json.tpl", "Tráfico por clase, p50/p95/p99, instancias, burn rate, uptime"),
        ],
        "facts": [("Variables GitLab", "GCP07_TFVARS (File)"), ("Storage mínimo", "Métricas retenidas 6 semanas sin costo"),
                  ("Architecture Framework", "OPS: SLOs + runbooks · REL: alertas por presupuesto de error")],
        "smoke": "2 SLOs, alertas; GENERATE_ERRORS=1 → burn rate 5 min > 14.4",
    },
    {
        "id": "08", "dir": "08-bigquery-analytics", "title": "Analítica con BigQuery: ingesta streaming, capas y vista autorizada",
        "goal": "Data platform mínima: ingesta sin código desde Pub/Sub, partición + clustering con filtro obligatorio, MERGE programado y analistas solo sobre vistas sin PII.",
        "groups": [("BigQuery", 34, 3, 65, 92)],
        "nodes": [
            ("p", "Productores\neventos JSON", "ext", 1, 30, 14, 14),
            ("t", "Topic events", "int", 18, 30, 13, 14),
            ("dlq", "Ingest DLQ\n5 intentos", "int", 18, 66, 13, 14),
            ("raw", "_raw.events\npartición + cluster", "data", 38, 30, 17, 16),
            ("sq", "Scheduled query\nMERGE diario (SA)", "ops", 38, 66, 17, 14),
            ("cur", "_curated.daily_kpis", "data", 60, 30, 16, 16),
            ("view", "_shared.v_kpis\nvista autorizada", "data", 80, 30, 18, 16),
            ("an", "Analistas\ndataViewer (shared)", "ext", 80, 66, 18, 14),
        ],
        "edges": [("p", "t"), ("t", "raw", "BigQuery sub"), ("t", "dlq", "inválidos", "dash"), ("raw", "sq", "", "dash"),
                  ("sq", "cur", "MERGE"), ("cur", "view", "autoriza"), ("an", "view", "SELECT")],
        "rows": [
            ("Capas", "google_bigquery_dataset x3", "_raw (PII, expiración de particiones), _curated, _shared"),
            ("Tabla cruda", "google_bigquery_table.events + schemas/events.json", "partición DAY event_ts; clustering country, event_type; require_partition_filter"),
            ("Ingesta", "google_pubsub_subscription.to_bigquery", "use_table_schema; drop_unknown_fields; dead_letter_policy"),
            ("Transformación", "google_bigquery_data_transfer_config + sql/merge_daily_kpis.sql.tpl", "scheduled_query; kpi_schedule; service_account_name dedicada"),
            ("Acceso", "google_bigquery_dataset_access.authorized_view", "curated autoriza la vista; analistas sin acceso a raw/curated"),
            ("Analistas", "dataset IAM + jobUser", "analyst_members"),
        ],
        "facts": [("Variables GitLab", "GCP08_TFVARS (File)"), ("Storage mínimo", "Particiones crudas 90 d; KPIs en KB/día"),
                  ("Architecture Framework", "COST: filtro de partición + dry run · SEC: vista sin PII")],
        "smoke": "30 filas, consulta sin partición rechazada, DLQ, MERGE, vista sin PII",
    },
    {
        "id": "09", "dir": "09-dms-migration", "title": "Migración con Database Migration Service (dump + CDC)",
        "goal": "Migrar PostgreSQL a Cloud SQL con DMS continuo: origen on-prem simulado con pglogical, conectividad privada por VPC peering y cutover controlado (promote).",
        "groups": [("Red corporativa simulada (VPC)", 1, 4, 40, 90, "#7A8691", "#F7F7F7"),
                   ("Servicios administrados", 46, 4, 53, 90, "#6A3FB5", "#FBFAFE")],
        "nodes": [
            ("vm", "VM onprem-pg\nPostgreSQL 15 + pglogical", "compute", 4, 30, 20, 17),
            ("sec", "Secret Manager\npassword migration", "sec", 4, 70, 20, 13),
            ("op", "Operador\nscripts/migrate.sh", "ext", 26, 70, 13, 13),
            ("src", "Perfil origen\npostgresql", "int", 50, 12, 16, 14),
            ("job", "Migration job\nCONTINUOUS", "ops", 50, 42, 16, 16),
            ("dst", "Perfil destino\ncloudsql", "int", 50, 74, 16, 13),
            ("sql", "Cloud SQL PG 15\nsolo IP privada", "data", 78, 42, 19, 16),
        ],
        "edges": [("vm", "src", "5432", "dash"), ("sec", "vm", "lee", "dash"), ("src", "job"), ("job", "sql", "dump + CDC"),
                  ("dst", "sql", "crea", "dash"), ("op", "job", "verify/start/promote")],
        "rows": [
            ("Origen", "google_compute_instance.source + source-startup.sh.tpl", "wal_level logical; pglogical en todas las bases; usuario REPLICATION; tablas con PK"),
            ("Red", "module.vpc (PSA) + firewall allow-dms-5432", "VPC peering para DMS y Cloud SQL; sin IPs públicas"),
            ("Credenciales", "random_password + Secret Manager", "La VM lee su contraseña con el token del SA"),
            ("Perfiles", "google_database_migration_service_connection_profile x2", "postgresql (host/puerto/usuario) y cloudsql.settings (POSTGRES_15, ip_config privada)"),
            ("Job", "google_database_migration_service_migration_job", "type CONTINUOUS; vpc_peering_connectivity"),
            ("Operación", "scripts/migrate.sh", "verify → start → status → promote (cutover) → delete"),
        ],
        "facts": [("Variables GitLab", "GCP09_TFVARS (File)"), ("Storage mínimo", "VM 20 GB; Cloud SQL 20 GB SSD"),
                  ("Architecture Framework", "REL: CDC, RPO de segundos · SEC: todo privado · VMs: Migrate to Virtual Machines")],
        "smoke": "origen 500/5000 filas, verify; RUN_MIGRATION=1 → fase CDC",
    },
    {
        "id": "10", "dir": "10-org-governance", "title": "Gobernanza de organización: Org Policies, tags y fábrica de proyectos",
        "goal": "El equivalente de StackSets + SCPs: guardrails heredados por carpeta, firewall jerárquico, políticas condicionadas por tag y N proyectos con el mismo baseline.",
        "groups": [("Organización → carpeta sandbox → lab11-dev", 1, 3, 98, 50, "#232F3E", "#F7F9FB"),
                   ("Proyectos creados por la fábrica", 1, 60, 98, 36, "#8A97A3", "#FAFBFC")],
        "nodes": [
            ("tf", "Terraform\n(SA de org)", "ops", 4, 14, 13, 15),
            ("op", "Org Policies\nsin llaves, sin IP ext.", "sec", 22, 14, 17, 15),
            ("fw", "Firewall jerárquico\nIAP sí · Internet no", "sec", 44, 14, 17, 15),
            ("tag", "Tags\nlab11-environment", "sec", 66, 14, 15, 15),
            ("dev", "Carpeta dev", "net", 30, 36, 13, 11),
            ("prod", "Carpeta prod", "net", 62, 36, 13, 11),
            ("p1", "ventas-dev\nbaseline", "compute", 18, 72, 18, 15),
            ("p2", "ventas-prod\nbaseline", "compute", 56, 72, 18, 15),
            ("bl", "Baseline\nsin red default · audit · budget", "ops", 80, 72, 17, 15),
        ],
        "edges": [("tf", "op"), ("op", "dev", "hereda", "dash"), ("op", "prod", "", "dash"), ("fw", "dev", "", "dash"),
                  ("tag", "prod", "binding", "dash"), ("dev", "p1"), ("prod", "p2"), ("bl", "p2", "", "dash")],
        "rows": [
            ("Jerarquía", "google_folder root + env (for_each)", "parent_folder_id (sandbox) u organización"),
            ("Guardrails", "google_org_policy_policy (boolean)", "disableServiceAccountKeyCreation, uniformBucketLevelAccess, publicAccessPrevention, requireOsLogin, restrictPublicIp"),
            ("Listas", "vmExternalIpAccess deny_all; gcp.resourceLocations", "allowed_locations = in:us-locations"),
            ("Condicional", "gcp.restrictServiceUsage + tags", "resource.matchTag(org/lab11-environment, dev) → allow_all; resto deny"),
            ("Red", "google_compute_firewall_policy + rules + association", "allow IAP 22/3389; deny 22/3389 desde 0.0.0.0/0"),
            ("Fábrica", "module.projects (modules/project-baseline)", "auto_create_network = false; APIs; audit config; operadores; budget por proyecto"),
        ],
        "facts": [("Variables GitLab", "GCP10_TFVARS (File); SA con permisos de organización"), ("Storage mínimo", "Ninguno"),
                  ("Architecture Framework", "SEC: guardrails preventivos heredados · OPS: baseline idéntico")],
        "smoke": "políticas efectivas por proyecto, sin red default, llave de SA bloqueada",
    },
    {
        "id": "11", "dir": "11-security-governance", "title": "Seguridad del proyecto: auditoría, IAM Deny, RBAC y alertas",
        "goal": "Controles detectivos y preventivos: Data Access logs, archivo con CMEK, alertas sobre eventos de alto riesgo, deny policy, RBAC por equipo y break-glass con caducidad.",
        "groups": [("Preventivos", 1, 3, 30, 92, "#C62828", "#FFFBFB"), ("Detectivos", 35, 3, 34, 92, "#2E7D32", "#FAFDFA"),
                   ("Respuesta", 73, 3, 26, 92, "#C2185B", "#FFFAFC")],
        "nodes": [
            ("deny", "IAM Deny Policy\nllaves de SA (+sinks)", "sec", 4, 10, 24, 14),
            ("rbac", "RBAC por equipo\n+ rol custom deployer", "sec", 4, 32, 24, 14),
            ("bg", "Break-glass owner\nIAM Condition de tiempo", "sec", 4, 54, 24, 14),
            ("vpcsc", "VPC-SC dry-run\n(opcional)", "sec", 4, 76, 24, 13),
            ("audit", "Audit logs\nAdmin + Data Access", "ops", 38, 10, 28, 14),
            ("lb", "Log bucket 365 d\nLog Analytics", "data", 38, 34, 28, 14),
            ("gcs", "GCS archivo\nCMEK · Nearline 30 d", "data", 38, 58, 28, 14),
            ("scc", "SCC → Pub/Sub\n(opcional)", "ops", 38, 80, 28, 12),
            ("la", "Alertas de logs\nowner · llaves · sinks · FW", "int", 76, 30, 21, 16),
            ("mail", "Email seguridad\nrate limit 5 min", "int", 76, 64, 21, 14),
        ],
        "edges": [("audit", "lb", "sink"), ("audit", "gcs", "sink"), ("audit", "la", "match"), ("la", "mail")],
        "rows": [
            ("Auditoría", "google_project_iam_audit_config (for_each)", "ADMIN_READ, DATA_READ, DATA_WRITE en data_access_audit_services"),
            ("Retención", "google_logging_project_bucket_config + sinks", "log_retention_days = 365; enable_analytics; lock_log_bucket (irreversible)"),
            ("Archivo", "module.kms + module.archive + sink GCS", "CMEK; Nearline a 30 d; retention_days; writer_identity objectCreator"),
            ("Alertas", "google_monitoring_alert_policy.log_alerts", "condition_matched_log; notification_rate_limit 5 min; auto_close 30 min"),
            ("Deny", "google_iam_deny_policy.guardrails", "denied_principals public:all; exception_principals; protect_audit_sinks"),
            ("RBAC", "google_project_iam_custom_role + google_project_iam_member.rbac", "developer, sre, auditor, finops (rbac_members)"),
            ("Break-glass", "google_project_iam_member.break_glass", "condition request.time < timestamp(break_glass_until)"),
        ],
        "facts": [("Variables GitLab", "GCP11_TFVARS (File); aplicar primero"), ("Storage mínimo", "Log bucket 365 d; GCS Nearline"),
                  ("Architecture Framework", "SEC: deny + RBAC + auditoría inmutable · COST: Data Access selectivo")],
        "smoke": "auditoría y sinks, deny bloquea llaves, evento en el log bucket, RBAC",
    },
]

PIPELINE_DIAGRAM = dict(
    groups=[("GitLab (proyecto Claude-Dev)", 1, 3, 46, 92), ("Google Cloud", 52, 3, 47, 92)],
    nodes=[
        ("dev", "Developer\nrama feature", "ext", 3, 10, 13, 14),
        ("mr", "Merge request\nCODEOWNERS + 1 aprobación", "ops", 19, 10, 25, 14),
        ("val", "validate · tflint\nfmt + validate", "ops", 3, 40, 13, 15),
        ("chk", "checkov\nSAST de IaC", "sec", 18, 40, 12, 15),
        ("pl", "plan\nartifact plan.txt", "ops", 32, 40, 13, 15),
        ("main", "main protegida\nmerge Maintainer", "ops", 3, 74, 18, 14),
        ("ap", "apply MANUAL → smoke\nprotected env", "ops", 25, 74, 20, 14),
        ("sts", "STS + WIF\ncondición project_path", "sec", 55, 40, 15, 15),
        ("rp", "SA tf-plan\nviewer", "sec", 75, 16, 14, 14),
        ("ra", "SA tf-apply\nroles de despliegue", "sec", 75, 64, 14, 14),
        ("op", "Org Policies + Deny\ntope organizacional", "sec", 55, 78, 15, 14),
        ("st", "GCS tfstate\nlock nativo", "data", 75, 40, 14, 14),
        ("ws", "Labs\n01–11", "compute", 92, 40, 7, 16),
    ],
    edges=[("dev", "mr"), ("mr", "val"), ("val", "chk"), ("chk", "pl"), ("pl", "sts", "token project_id"),
           ("main", "ap"), ("ap", "sts", "token branch:main"), ("sts", "rp"), ("sts", "ra"), ("rp", "st", "lee"),
           ("ra", "ws", "despliega"), ("op", "ra", "limita", "dash")],
)

GUARDRAIL_ROWS = [
    ["Capa (de afuera hacia adentro)", "Dónde se define", "Qué limita", "Micro lab"],
    ["1. Organization Policies", "google_org_policy_policy (carpeta/organización)", "Configuraciones prohibidas para TODOS: llaves de SA, IPs externas, ubicaciones, SQL público", "10"],
    ["2. IAM Deny Policies", "google_iam_deny_policy", "Permisos denegados aunque un rol los otorgue (incluso a Owner), con excepciones explícitas", "11"],
    ["3. IAM allow (RBAC)", "roles predefinidos + custom role + bindings por grupo", "Lo que cada función necesita: developer, sre, auditor, finops", "11"],
    ["4. IAM Conditions", "condition { expression }", "Acceso acotado por recurso (Firestore de una base) o por tiempo (break-glass)", "01 / 03 / 11"],
    ["5. Políticas de recurso", "IAM de bucket / dataset / función / topic", "Quién usa cada recurso: invoker explícito, vista autorizada, agente de servicio", "01–08"],
    ["6. Red", "Firewall jerárquico + VPC deny-all + PSA + VPC-SC", "Sin IPs públicas; IAP; datos privados; perímetro de exfiltración", "05 / 06 / 09 / 10 / 11"],
]

RBAC_MATRIX = [
    ["Rol", "GitLab (proyecto)", "Google Cloud (grupo → roles)", "Puede hacer", "No puede hacer"],
    ["Developer", "Developer: ramas, MR, ver plan", "group:devs → run.developer, datastore.user, logging/monitoring.viewer, rol custom deployer", "Desplegar y depurar funciones y servicios", "Administrar IAM; crear llaves de SA (deny); merge a main"],
    ["SRE / Platform", "Maintainer: merge, apply/destroy", "group:sre → monitoring.editor, logging.viewer, compute.viewer, run.viewer", "SLOs, alertas, runbooks, operar pipelines", "Desactivar auditoría (deny opcional)"],
    ["Security", "Owner del grupo; CODEOWNER de labs 10/11", "Org: orgpolicy.policyAdmin, iam.denyAdmin, securitycenter.admin", "Org Policies, deny policies, SCC, VPC-SC", "Desplegar workloads"],
    ["Auditor", "Reporter", "group:auditoria → iam.securityReviewer, logging.privateLogViewer, cloudasset.viewer", "Leer IAM, logs (incl. Data Access) e inventario", "Cualquier escritura"],
    ["FinOps", "Reporter", "group:finops → recommender.viewer, billing.projectManager", "Costos, recomendaciones de rightsizing", "Cambios de infraestructura"],
    ["CI plan", "Job plan (cualquier rama/MR)", "SA tf-plan ← principalSet attribute.project_id", "Leer el proyecto y el estado", "Modificar recursos"],
    ["CI apply", "Job apply (main, manual, protected env)", "SA tf-apply ← principalSet attribute.deploy_ref …:branch:main", "Aplicar planes aprobados", "Lo que niegan las Org/Deny policies"],
    ["Break-glass", "N/A (fuera del pipeline)", "user:oncall → roles/owner con condición request.time < fecha", "Recuperación de emergencia", "Seguir teniendo acceso después de la fecha"],
]

DEVSECOPS_CHECKS = [
    ["Control", "Implementación en lab11", "Dónde"],
    ["Sin secretos de larga duración", "Workload Identity Federation: id_token → STS → impersonación; Org Policy bloquea llaves", ".gitlab-ci.yml (.gcp_auth), labs 00 y 10"],
    ["Separación de funciones", "SA plan (viewer) ≠ SA apply (solo deploy_ref main); apply manual", "lab 00, ci.yml de cada lab"],
    ["Revisión obligatoria", "main protegida, approvals, CODEOWNERS en modules/ y labs 10/11", "Settings → Repository / Merge requests"],
    ["Escaneo de IaC", "fmt, validate, tflint, checkov (JUnit en el MR)", "Etapas validate y security"],
    ["Plan inmutable", "apply usa el plan.tfplan del job plan", ".tf_plan → .tf_apply"],
    ["Verificación post-deploy", "smoke test automático con outputs.json después del apply", "Etapa smoke"],
    ["Concurrencia segura", "resource_group por lab + lock nativo de GCS", ".tf_apply / .tf_destroy"],
    ["Estado protegido", "GCS versionado, soft delete, UBLA, PAP; acceso solo de SAs de CI", "lab 00"],
    ["Mínimo privilegio en runtime", "Una SA por carga; IAM condicionado; invoker explícito", "módulos service-account y cloud-function"],
    ["Trazabilidad", "default_labels (project, owner, microlab, cost_center) + audit logs", "versions.tf, lab 11"],
    ["Detección continua", "Alertas de logs, SCC, burn rate, uptime", "labs 07 y 11"],
    ["Costo como control", "Budgets, max_instances, require_partition_filter, destroy manual", "labs 00, 01, 03, 08"],
]

GITLAB_VARS = [
    ["Variable", "Tipo", "Protegida", "Enmascarada", "Valor / origen"],
    ["GCP_PROJECT_ID", "Variable", "No", "No", "ID del proyecto"],
    ["TF_STATE_BUCKET", "Variable", "No", "No", "output tf_state_bucket (lab 00)"],
    ["GCP_WIF_PROVIDER", "Variable", "No", "No", "output wif_provider"],
    ["GCP_PLAN_SA", "Variable", "No", "Sí", "output plan_service_account"],
    ["GCP_APPLY_SA", "Variable", "Sí", "Sí", "output apply_service_account"],
    ["GCP01_TFVARS … GCP11_TFVARS", "File", "Sí", "No", "terraform.tfvars de cada lab"],
    ["DESTROY_LAB", "Variable (al ejecutar)", "No", "No", "Nombre del lab a destruir"],
]

WA_MATRIX = [
    ["Lab", "Excelencia operativa", "Seguridad", "Confiabilidad", "Rendimiento", "Costos", "Sostenibilidad"],
    ["00", "GitOps + estado versionado", "WIF sin llaves", "Soft delete del estado", "N/A", "Budget", "Solo administrados"],
    ["01", "Contrato OpenAPI", "Backend privado + cuota", "PITR Firestore", "Escala a cero", "Free tier", "Sin cómputo ocioso"],
    ["02", "Schema + replay", "Push OIDC", "Retry + DLQ", "Filtro en broker", "Auditoría sin código", "Por evento"],
    ["03", "Métricas de tokens", "Privada + guardrails", "Tope de instancias", "Concurrencia 8", "Tokens acotados", "Modelo flash"],
    ["04", "Historial por paso", "SA mínima", "try/except + alerta", "Parallel", "Sin servidores", "Datos expiran"],
    ["05", "Rolling proactivo", "Armor, sin IPs", "MIG regional + SQL HA", "LB global", "HA opcional", "Autoscaling"],
    ["06", "Workload en TF", "PSA + WI + NetPol", "PDB + regional", "HPA", "Pago por pod", "Bin packing"],
    ["07", "SLOs + runbooks", "Sin datos sensibles", "Burn rate", "SLO p95", "Gratis", "Menos ruido"],
    ["08", "SQL versionado", "Vista sin PII", "DLQ de ingesta", "Partición + cluster", "Filtro obligatorio", "Menos bytes"],
    ["09", "verify + promote", "Todo privado", "CDC", "Dump paralelo", "DMS sin costo", "Apagar origen"],
    ["10", "Baseline idéntico", "Org Policies", "Aislamiento", "N/A", "Budget por proyecto", "Ubicaciones"],
    ["11", "Log Analytics", "Deny + RBAC", "Doble destino", "N/A", "Data Access selectivo", "Retención acotada"],
]


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------
def on_page(canvas, doc):
    canvas.saveState()
    w, h = landscape(letter)
    canvas.setFillColor(colors.HexColor("#1A73E8"))
    canvas.rect(0, h - 6, w, 6, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#34A853"))
    canvas.rect(0, h - 6, 90, 6, stroke=0, fill=1)
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.5 * inch, 0.32 * inch, "Lab 11 · Micro labs Google Cloud con Terraform · Architecture Framework · GitLab CI")
    canvas.drawRightString(w - 0.5 * inch, 0.32 * inch, f"{doc.page}")
    canvas.restoreState()


def facts_table(facts):
    rows = [[Paragraph(k, styles["cellb"]), Paragraph(v, styles["cell"])] for k, v in facts]
    t = Table(rows, colWidths=[1.75 * inch, 8.25 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F0FE")),
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
        title="Lab 11 - Arquitecturas Google Cloud con Terraform", author="Axel Valenzuela",
        subject="Micro labs GCP: serverless, SRE, IA, 3 niveles, GKE, datos, migración y gobernanza",
    )
    s = []
    s += [Spacer(1, 0.6 * inch), P("Lab 11: Micro labs de Google Cloud con Terraform", "title"), Spacer(1, 6),
          P("Diagramas de arquitectura, implementación con Terraform, RBAC y seguridad DevOps con Workload Identity Federation "
            "sobre GitLab CI, alineados con el Google Cloud Architecture Framework.", "subtitle"), Spacer(1, 18)]
    idx = [["#", "Micro lab", "Servicios principales", "Equivalente AWS (lab10)"]]
    names = ["Bootstrap", "API Gateway + functions", "Pub/Sub event-driven", "Chatbot Vertex AI", "Pipeline IA con Workflows",
             "Web de 3 niveles", "GKE Autopilot", "SRE observabilidad", "BigQuery analítica", "Migración DMS",
             "Gobernanza de organización", "Seguridad y gobernanza"]
    services = ["GCS state, WIF, SAs, Artifact Registry, Budget", "API Gateway, Cloud Run functions, Firestore, API keys",
                "Pub/Sub schema/push/DLQ/filtros, BigQuery sub, Scheduler", "Vertex AI Gemini, Firestore TTL",
                "Eventarc, Workflows, Vision, Natural Language, Gemini, BigQuery", "LB global, Cloud Armor, MIG, Cloud SQL HA",
                "GKE Autopilot, Workload Identity, HPA, PDB, NetworkPolicy", "Cloud Monitoring SLO, burn rate, uptime",
                "BigQuery capas, partición, vista autorizada, scheduled query", "Database Migration Service, Cloud SQL",
                "Carpetas, Org Policies, tags, firewall jerárquico", "Audit logs, sinks, IAM Deny, RBAC, break-glass"]
    equiv = ["S3 + OIDC (00)", "API GW + Lambda (01)", "EventBridge (03)", "Bedrock (04)", "Step Functions (05)", "ALB + RDS (06)",
             "— (nuevo)", "CloudWatch SLO (07)", "— (nuevo)", "MGN (09)", "StackSets + SCP (10)", "CloudTrail + GuardDuty (11)"]
    for lab, n, sv, eq in zip(LABS, names, services, equiv):
        idx.append([lab["id"], n, sv, eq])
    s.append(table(idx, [0.4 * inch, 2.4 * inch, 5.0 * inch, 2.2 * inch]))
    s += [Spacer(1, 10), P("Código fuente: <b>lab11/</b> (módulos en <b>modules/</b>, labs en <b>microlabs/NN-nombre/</b>). "
                           "Cada lab incluye README, terraform.tfvars.example, ci.yml y scripts/smoke-test.sh. "
                           "Todos pasan terraform validate (Terraform 1.13 · google 7.x); no se han desplegado en un proyecto real.", "small"),
          PageBreak()]

    s += [P("Parte 1 · RBAC y seguridad DevOps en Google Cloud", "h1"),
          P("Dos planos que se refuerzan: <b>quién puede cambiar el código</b> (roles de GitLab, ramas y entornos protegidos) y "
            "<b>con qué identidad se despliega</b> (service accounts impersonadas con Workload Identity Federation, nunca llaves JSON). "
            "Las Organization Policies y las IAM Deny Policies ponen un techo que ningún rol puede superar.", "lead"),
          P("1.1 Flujo GitOps con Workload Identity Federation", "h2"),
          Diagram(PIPELINE_DIAGRAM["nodes"], PIPELINE_DIAGRAM["edges"], PIPELINE_DIAGRAM["groups"], height=3.3 * inch),
          Spacer(1, 4),
          P("El provider de WIF mapea los claims del token (project_id, ref_type, ref) a atributos. La SA de apply solo acepta el "
            "<i>principalSet</i> con <i>deploy_ref = &lt;project_id&gt;:branch:main</i>: una rama feature no puede impersonarla.", "small"),
          PageBreak(),
          P("1.2 Matriz RBAC (GitLab ↔ Google Cloud)", "h2"),
          table(RBAC_MATRIX, [1.0 * inch, 1.8 * inch, 2.8 * inch, 2.2 * inch, 2.2 * inch]),
          Spacer(1, 6),
          P("Asigna roles a <b>grupos</b> de Cloud Identity / Google Workspace, nunca a usuarios individuales; usa IAM Conditions para "
            "acotar por recurso o por tiempo y revisa periódicamente con IAM Recommender (permisos no usados).", "small"),
          CondPageBreak(3 * inch),
          P("1.3 Capas de guardrails (defensa en profundidad)", "h2"),
          P("Una acción solo se permite si ninguna Org Policy ni Deny Policy la bloquea y algún binding de IAM la concede.", "body"),
          Spacer(1, 4),
          table(GUARDRAIL_ROWS, [1.8 * inch, 2.6 * inch, 4.6 * inch, 1.0 * inch]),
          PageBreak(),
          P("1.4 Controles DevSecOps del pipeline", "h2"),
          table(DEVSECOPS_CHECKS, [2.0 * inch, 5.2 * inch, 2.8 * inch]),
          Spacer(1, 8),
          P("1.5 Variables a configurar en GitLab", "h2"),
          table(GITLAB_VARS, [2.2 * inch, 1.3 * inch, 0.9 * inch, 1.0 * inch, 4.6 * inch]),
          PageBreak()]

    s.append(P("Parte 2 · Arquitecturas e implementación por micro lab", "h1"))
    s.append(P("Cada lab muestra el diagrama (colores por categoría; fronteras punteadas = organización / VPC / servicio), "
               "la tabla de implementación con Terraform y los datos de operación.", "lead"))
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
        s.append(facts_table(lab["facts"] + [("Prueba automatizada", f"bash scripts/lab.sh test {lab['dir']} → {lab['smoke']}")]))

    s += [PageBreak(), P("Anexo · Matriz del Architecture Framework por micro lab", "h1"),
          P("Resumen por pilar; el detalle está en la sección correspondiente de cada README.", "lead"),
          table(WA_MATRIX, [0.45 * inch] + [1.59 * inch] * 6),
          Spacer(1, 10),
          P("Orden recomendado: 00 → 11 → 01 → 02 → 03 → 04 → 07 → 08 → 05 → 06 → 09 → 10. "
            "Destruye los labs 05 (~USD 120/mes), 06 (~USD 95/mes) y 09 (~USD 2/día) al terminar cada sesión.", "body")]

    doc.build(s, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF generado: {OUT}")


if __name__ == "__main__":
    build()
