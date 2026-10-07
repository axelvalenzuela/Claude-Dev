#!/bin/bash
# Simula una base PostgreSQL "on-premises" lista para Database Migration Service (replicación lógica con pglogical).
set -euxo pipefail

if [ -f /var/lib/lab11-source-ready ]; then exit 0; fi

apt-get update -y
apt-get install -y postgresql-15 postgresql-15-pglogical curl jq

# Contraseña del usuario de migración desde Secret Manager (token del SA adjunto, sin llaves)
TOKEN=$(curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" | jq -r .access_token)
MIGRATION_PASSWORD=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://secretmanager.googleapis.com/v1/projects/${project_id}/secrets/${secret_id}/versions/latest:access" | jq -r .payload.data | base64 -d)

CONF=/etc/postgresql/15/main
cat >> $CONF/postgresql.conf <<CONFEOF
listen_addresses = '*'
wal_level = logical
shared_preload_libraries = 'pglogical'
max_replication_slots = 10
max_wal_senders = 10
max_worker_processes = 10
wal_sender_timeout = 0
CONFEOF

# Solo la red privada de la VPC (incluye el rango de peering de DMS/Cloud SQL)
echo "host all migration ${allowed_cidr} scram-sha-256" >> $CONF/pg_hba.conf
echo "host replication migration ${allowed_cidr} scram-sha-256" >> $CONF/pg_hba.conf
systemctl restart postgresql

sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
CREATE ROLE migration WITH LOGIN REPLICATION PASSWORD '$MIGRATION_PASSWORD';
CREATE DATABASE ventas;
SQL

# pglogical debe existir en TODAS las bases (incluida postgres) y el usuario de migración leer todo
for DB in postgres ventas; do
  sudo -u postgres psql -d "$DB" -v ON_ERROR_STOP=1 <<SQL
CREATE EXTENSION IF NOT EXISTS pglogical;
GRANT USAGE ON SCHEMA pglogical TO migration;
GRANT SELECT ON ALL TABLES IN SCHEMA pglogical TO migration;
GRANT USAGE ON SCHEMA public TO migration;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO migration;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO migration;
SQL
done

# Datos de ejemplo (todas las tablas con PRIMARY KEY: requisito para replicar UPDATE/DELETE)
sudo -u postgres psql -d ventas -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE clientes (id serial PRIMARY KEY, nombre text NOT NULL, ciudad text, creado timestamptz DEFAULT now());
CREATE TABLE pedidos  (id serial PRIMARY KEY, cliente_id int REFERENCES clientes(id), total numeric(10,2), creado timestamptz DEFAULT now());
INSERT INTO clientes (nombre, ciudad)
  SELECT 'Cliente ' || g, (ARRAY['Tijuana','Mexicali','Ensenada'])[1 + g % 3] FROM generate_series(1, 500) g;
INSERT INTO pedidos (cliente_id, total)
  SELECT 1 + (g % 500), round((random() * 2000)::numeric, 2) FROM generate_series(1, 5000) g;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO migration;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO migration;
SQL

touch /var/lib/lab11-source-ready
