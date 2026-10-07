#!/bin/bash
# Startup script de la capa app (Debian 12). App mínima en Python (solo stdlib) que demuestra las 3 capas:
# Load Balancer -> VM del MIG -> Cloud SQL (IP privada, TLS) con contraseña desde Secret Manager.
set -euxo pipefail
apt-get update -y
apt-get install -y python3 postgresql-client

mkdir -p /opt/app
cat > /opt/app/app.py <<'PY'
import base64, json, os, subprocess, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROJECT = os.environ["PROJECT"]
SECRET = os.environ["DB_SECRET"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
MD = "http://metadata.google.internal/computeMetadata/v1/"


def metadata(path):
    req = urllib.request.Request(MD + path, headers={"Metadata-Flavor": "Google"})
    return urllib.request.urlopen(req, timeout=2).read().decode()


INSTANCE = metadata("instance/name")
ZONE = metadata("instance/zone").rsplit("/", 1)[-1]


def db_password():
    # Token del SA adjunto (sin llaves) -> Secret Manager REST
    token = json.loads(metadata("instance/service-accounts/default/token"))["access_token"]
    url = f"https://secretmanager.googleapis.com/v1/projects/{PROJECT}/secrets/{SECRET}/versions/latest:access"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    payload = json.loads(urllib.request.urlopen(req, timeout=5).read())["payload"]["data"]
    return base64.b64decode(payload).decode()


def psql(sql):
    env = dict(os.environ, PGPASSWORD=db_password(), PGSSLMODE="require", PGCONNECT_TIMEOUT="5")
    out = subprocess.run(["psql", "-h", DB_HOST, "-U", DB_USER, "-d", DB_NAME, "-At", "-v", "ON_ERROR_STOP=1", "-c", sql],
                         check=True, capture_output=True, text=True, env=env)
    return out.stdout.strip()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, "ok", "text/plain")
        if self.path == "/db":
            try:
                psql("CREATE TABLE IF NOT EXISTS visits (id serial PRIMARY KEY, instance text, zone text, at timestamptz DEFAULT now())")
                psql(f"INSERT INTO visits (instance, zone) VALUES ('{INSTANCE}', '{ZONE}')")
                return self._send(200, {
                    "status": "ok", "instance": INSTANCE, "zone": ZONE,
                    "visits": int(psql("SELECT count(*) FROM visits")),
                    "postgres": psql("SHOW server_version"),
                    "ssl": psql("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()") == "t",
                })
            except Exception as e:  # noqa: BLE001 - se reporta el error al cliente del lab
                return self._send(500, {"status": "error", "detail": str(getattr(e, "stderr", e))[-300:]})
        return self._send(200, f"<h1>03-cloud-e-infraestructura/lab11-terraform-gcp · 3 niveles (GCP)</h1><p>VM <b>{INSTANCE}</b> en <b>{ZONE}</b></p>"
                               f"<p><a href='/db'>/db</a> prueba Cloud SQL por IP privada</p>", "text/html")

    def log_message(self, fmt, *args):
        print(json.dumps({"severity": "INFO", "httpRequest": fmt % args}), flush=True)


ThreadingHTTPServer(("0.0.0.0", int(os.environ["APP_PORT"])), Handler).serve_forever()
PY

cat > /etc/systemd/system/lab11-app.service <<UNIT
[Unit]
Description=03-cloud-e-infraestructura/lab11-terraform-gcp three-tier demo app
After=network-online.target
Wants=network-online.target

[Service]
Environment=APP_PORT=${app_port}
Environment=PROJECT=${project_id}
Environment=DB_SECRET=${db_secret}
Environment=DB_HOST=${db_host}
Environment=DB_NAME=${db_name}
Environment=DB_USER=${db_user}
ExecStart=/usr/bin/python3 /opt/app/app.py
Restart=always
RestartSec=3
DynamicUser=yes

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now lab11-app
