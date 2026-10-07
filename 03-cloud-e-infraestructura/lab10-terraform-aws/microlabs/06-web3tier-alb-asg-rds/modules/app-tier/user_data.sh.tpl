#!/bin/bash
# Bootstrap de la capa app (Amazon Linux 2023). Instala una app mínima en Python (solo stdlib)
# que demuestra las 3 capas: ALB -> instancia -> RDS PostgreSQL (credenciales desde Secrets Manager).
# En producción: hornea una AMI con Packer/EC2 Image Builder o usa contenedores.
set -euxo pipefail
dnf install -y postgresql16 python3

mkdir -p /opt/app
cat > /opt/app/app.py <<'PY'
import json, os, socket, subprocess, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REGION = os.environ["APP_REGION"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
SECRET_ARN = os.environ["DB_SECRET_ARN"]


def imds(path):
    token = urllib.request.urlopen(urllib.request.Request(
        "http://169.254.169.254/latest/api/token", method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"}), timeout=2).read().decode()
    return urllib.request.urlopen(urllib.request.Request(
        "http://169.254.169.254/latest/meta-data/" + path,
        headers={"X-aws-ec2-metadata-token": token}), timeout=2).read().decode()


INSTANCE = imds("instance-id")
AZ = imds("placement/availability-zone")


def db_credentials():
    # Se lee en cada request: si RDS rota la contraseña, la app la toma sin reiniciar.
    raw = subprocess.run(["aws", "secretsmanager", "get-secret-value", "--region", REGION,
                          "--secret-id", SECRET_ARN, "--query", "SecretString", "--output", "text"],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(raw)


def psql(sql):
    creds = db_credentials()
    env = dict(os.environ, PGPASSWORD=creds["password"], PGSSLMODE="require", PGCONNECT_TIMEOUT="5")
    out = subprocess.run(["psql", "-h", DB_HOST, "-U", creds["username"], "-d", DB_NAME,
                          "-At", "-v", "ON_ERROR_STOP=1", "-c", sql],
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
                psql("CREATE TABLE IF NOT EXISTS visits (id serial PRIMARY KEY, instance text, az text, at timestamptz DEFAULT now())")
                psql(f"INSERT INTO visits (instance, az) VALUES ('{INSTANCE}', '{AZ}')")
                total = int(psql("SELECT count(*) FROM visits"))
                version = psql("SHOW server_version")
                ssl = psql("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
                return self._send(200, {"status": "ok", "instance": INSTANCE, "az": AZ, "visits": total,
                                        "postgres": version, "ssl": ssl == "t"})
            except subprocess.CalledProcessError as e:
                return self._send(500, {"status": "error", "detail": (e.stderr or str(e))[-300:]})
        return self._send(200, f"<h1>03-cloud-e-infraestructura/lab10-terraform-aws · 3 niveles</h1><p>Instancia <b>{INSTANCE}</b> en <b>{AZ}</b></p>"
                               f"<p><a href='/db'>/db</a> prueba la conexión a PostgreSQL ({DB_HOST})</p>", "text/html")

    def log_message(self, fmt, *args):
        print(json.dumps({"client": self.client_address[0], "request": fmt % args}), flush=True)


ThreadingHTTPServer(("0.0.0.0", int(os.environ["APP_PORT"])), Handler).serve_forever()
PY

cat > /etc/systemd/system/lab10-app.service <<UNIT
[Unit]
Description=03-cloud-e-infraestructura/lab10-terraform-aws three-tier demo app
After=network-online.target
Wants=network-online.target

[Service]
Environment=APP_PORT=${app_port}
Environment=APP_REGION=${region}
Environment=DB_HOST=${db_endpoint}
Environment=DB_NAME=${db_name}
Environment=DB_SECRET_ARN=${db_secret_arn}
ExecStart=/usr/bin/python3 /opt/app/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now lab10-app
