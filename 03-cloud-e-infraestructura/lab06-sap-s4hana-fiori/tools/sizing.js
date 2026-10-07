#!/usr/bin/env node
// Convierte assessment/<archivo>.json en tfvars de Terraform + un reporte de
// dimensionamiento. Sin dependencias (solo Node.js >= 18).
//   node tools/sizing.js assessment/assessment.example.json
// Salida: terraform/environments/<env>.generated.tfvars.json y
//         assessment/<env>.sizing-report.md
"use strict";

const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");

function fail(msg) {
  console.error(`ERROR: ${msg}`);
  process.exit(1);
}

function num(obj, key, { min = 0, integer = false } = {}) {
  const v = obj?.[key];
  if (typeof v !== "number" || Number.isNaN(v) || v < min || (integer && !Number.isInteger(v))) {
    fail(`'${key}' debe ser un numero${integer ? " entero" : ""} >= ${min} (recibido: ${JSON.stringify(v)})`);
  }
  return v;
}

function loadAssessment(file) {
  let a;
  try {
    a = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (e) {
    fail(`no se pudo leer ${file}: ${e.message}`);
  }
  if (!["dev", "qas", "prd"].includes(a.environment)) fail("'environment' debe ser dev, qas o prd");
  if (!/^[0-9]{2}$/.test(a.sap_instance_number ?? "")) fail("'sap_instance_number' debe tener dos digitos");
  const s = a.sizing ?? {};
  num(s, "hana_ram_gb_from_quicksizer", { min: 1 });
  num(s, "growth_percent_per_year", { min: 0 });
  num(s, "planning_years", { min: 0, integer: true });
  num(s, "concurrent_users", { min: 1, integer: true });
  const c = a.continuity ?? {};
  num(c, "rpo_minutes", { min: 0 });
  num(c, "rto_minutes", { min: 0 });
  if (typeof c.dr_region_required !== "boolean") fail("'continuity.dr_region_required' debe ser true/false");
  num(a.backup ?? {}, "retention_days", { min: 1, integer: true });
  const cidrs = a.network?.admin_cidrs;
  if (!Array.isArray(cidrs)) fail("'network.admin_cidrs' debe ser una lista");
  if (cidrs.includes("0.0.0.0/0")) fail("'network.admin_cidrs' no puede incluir 0.0.0.0/0");
  return a;
}

function tfvarsVpcCidr(a) {
  return a.network.vpc_cidr ?? "10.60.0.0/16";
}

function chooseHana(catalog, requiredGb) {
  const sorted = [...catalog.hana].sort((x, y) => x.ram_gb - y.ram_gb);
  const pick = sorted.find((i) => i.ram_gb >= requiredGb);
  if (!pick) {
    fail(`ningun tipo del catalogo cubre ${Math.ceil(requiredGb)} GB de RAM; ampliar tools/instance-catalog.json`);
  }
  return pick;
}

function volumesFor(ramGb) {
  const tier =
    ramGb <= 256
      ? { di: 6000, dt: 400, li: 6000, lt: 300 }
      : ramGb <= 512
        ? { di: 10000, dt: 600, li: 10000, lt: 500 }
        : { di: 16000, dt: 1000, li: 16000, lt: 1000 };
  return {
    data_gb: Math.ceil(ramGb * 1.2),
    log_gb: Math.ceil(Math.min(512, ramGb * 0.5)),
    shared_gb: Math.ceil(Math.min(1024, ramGb)),
    backup_gb: Math.ceil(ramGb * 2),
    data_iops: tier.di,
    data_throughput: tier.dt,
    log_iops: tier.li,
    log_throughput: tier.lt,
  };
}

function chooseApp(catalog, users) {
  const sorted = [...catalog.app].sort((x, y) => x.max_concurrent_users_per_server - y.max_concurrent_users_per_server);
  const largest = sorted[sorted.length - 1];
  const single = sorted.find((i) => i.max_concurrent_users_per_server >= users);
  if (single) return { type: single.type, count: 1 };
  return { type: largest.type, count: Math.ceil(users / largest.max_concurrent_users_per_server) };
}

function main() {
  const file = process.argv[2];
  if (!file) fail("uso: node tools/sizing.js <assessment.json>");
  const a = loadAssessment(path.resolve(file));
  const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, "instance-catalog.json"), "utf8"));

  const s = a.sizing;
  const required = s.hana_ram_gb_from_quicksizer * Math.pow(1 + s.growth_percent_per_year / 100, s.planning_years);
  const hana = chooseHana(catalog, required);
  const volumes = volumesFor(hana.ram_gb);
  const app = chooseApp(catalog, s.concurrent_users);

  const c = a.continuity;
  const haEnabled = c.rpo_minutes === 0 || c.rto_minutes <= 30;
  const appServers = ["ascs-pas", ...Array.from({ length: app.count - 1 }, (_, i) => `aas${i + 1}`)];

  const warnings = [];
  if (!hana.certified_verified) {
    warnings.push(`El tipo ${hana.type} NO esta verificado en el directorio de plataformas certificadas de SAP.`);
  }
  if (c.dr_region_required) {
    warnings.push("Se requiere DR en otra region: la plantilla no lo crea (replica ASYNC + backup cross-region a construir aparte).");
  }
  if (a.environment === "prd" && !haEnabled) {
    warnings.push("Productivo sin HA (RPO/RTO no lo exigen): confirmar que el negocio acepta restauracion desde backup.");
  }

  const m = /^(\d+)\.(\d+)\.0\.0\/16$/.exec(tfvarsVpcCidr(a));
  if (!m) fail("'network.vpc_cidr' debe ser un /16 con formato A.B.0.0/16 (las subredes se derivan de el)");
  const [, oct1, oct2] = m;

  const tfvars = {
    environment: a.environment,
    region: a.region ?? "us-east-1",
    project: a.project ?? "s4hana",
    sap_instance_number: a.sap_instance_number,
    vpc_cidr: tfvarsVpcCidr(a),
    private_subnet_cidrs: [`${oct1}.${oct2}.1.0/24`, `${oct1}.${oct2}.2.0/24`],
    public_subnet_cidr: `${oct1}.${oct2}.100.0/24`,
    admin_cidrs: a.network.admin_cidrs,
    ha_enabled: haEnabled,
    hana_instance_type: hana.type,
    hana_volumes: volumes,
    app_instance_type: app.type,
    app_servers: appServers,
    backup_retention_days: a.backup.retention_days,
    backup_force_destroy: a.environment === "dev",
    delete_volumes_on_termination: a.environment === "dev",
  };
  if (a.os?.ami_id) tfvars.ami_id = a.os.ami_id;

  const outTf = path.join(root, "terraform", "environments", `${a.environment}.generated.tfvars.json`);
  fs.writeFileSync(outTf, JSON.stringify(tfvars, null, 2) + "\n");

  const report = [
    `# Reporte de dimensionamiento — ${a.environment}`,
    "",
    "| Concepto | Valor |",
    "|---|---|",
    `| RAM segun Quick Sizer | ${s.hana_ram_gb_from_quicksizer} GB |`,
    `| Crecimiento | ${s.growth_percent_per_year} %/anio x ${s.planning_years} anios |`,
    `| RAM requerida proyectada | ${Math.ceil(required)} GB |`,
    `| Instancia HANA elegida | ${hana.type} (${hana.ram_gb} GB) |`,
    `| Discos HANA | data ${volumes.data_gb} / log ${volumes.log_gb} / shared ${volumes.shared_gb} / backup ${volumes.backup_gb} GB |`,
    `| Rendimiento data / log | ${volumes.data_iops} IOPS, ${volumes.data_throughput} MB/s / ${volumes.log_iops} IOPS, ${volumes.log_throughput} MB/s |`,
    `| Usuarios concurrentes | ${s.concurrent_users} |`,
    `| Servidores de aplicacion | ${app.count} x ${app.type} (${appServers.join(", ")}) |`,
    `| RPO / RTO objetivo | ${c.rpo_minutes} min / ${c.rto_minutes} min |`,
    `| Alta disponibilidad (HSR) | ${haEnabled ? "Si (segundo nodo en otra AZ)" : "No"} |`,
    "",
    "## Advertencias",
    "",
    ...(warnings.length ? warnings.map((w) => `- ${w}`) : ["- Ninguna."]),
    "",
    `Archivo generado: \`terraform/environments/${a.environment}.generated.tfvars.json\``,
    "",
  ].join("\n");
  const outReport = path.join(root, "assessment", `${a.environment}.sizing-report.md`);
  fs.writeFileSync(outReport, report);

  console.log(report);
}

main();
