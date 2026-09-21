#!/usr/bin/env node
// Genera el inventario de Ansible a partir de `terraform output -json`.
//   terraform -chdir=terraform output -json > /tmp/tf-out.json
//   node tools/tf-to-inventory.js /tmp/tf-out.json > ansible/inventory.generated.yml
// Los hosts se identifican por ID de instancia y se alcanzan por SSM (sin SSH).
"use strict";

const fs = require("fs");

const file = process.argv[2];
if (!file) {
  console.error("uso: node tools/tf-to-inventory.js <terraform-output.json>");
  process.exit(1);
}

const raw = JSON.parse(fs.readFileSync(file, "utf8"));
const out = (k) => {
  if (!(k in raw)) {
    console.error(`ERROR: falta el output '${k}' en ${file}`);
    process.exit(1);
  }
  return raw[k].value;
};

const hanaIds = out("hana_instance_ids");
const hanaVols = out("hana_volume_ids");
const appIds = out("app_instance_ids");
const appVols = out("app_usr_sap_volume_ids");
const bucket = out("backup_bucket");
const region = out("region");
const nn = out("sap_instance_number");

const lines = [];
const push = (s = "") => lines.push(s);

push("# Generado por tools/tf-to-inventory.js - no editar a mano.");
push("all:");
push("  vars:");
push("    ansible_connection: community.aws.aws_ssm");
push(`    ansible_aws_ssm_region: ${region}`);
push(`    ansible_aws_ssm_bucket_name: ${bucket}`);
push("    ansible_python_interpreter: /usr/bin/python3");
push(`    sap_instance_number: "${nn}"`);
push("  children:");

push("    hana_primary:");
push("      hosts:");
if (hanaIds.primary) {
  push(`        ${hanaIds.primary}:`);
  push("          hana_role: primary");
  push("          sap_volume_ids:");
  for (const [vol, id] of Object.entries(hanaVols.primary)) push(`            ${vol}: ${id}`);
}

push("    hana_secondary:");
if (hanaIds.secondary) {
  push("      hosts:");
  push(`        ${hanaIds.secondary}:`);
  push("          hana_role: secondary");
  push("          sap_volume_ids:");
  for (const [vol, id] of Object.entries(hanaVols.secondary)) push(`            ${vol}: ${id}`);
} else {
  push("      hosts: {}");
}

push("    hana:");
push("      children:");
push("        hana_primary:");
push("        hana_secondary:");

push("    app:");
push("      hosts:");
for (const [name, id] of Object.entries(appIds)) {
  push(`        ${id}:`);
  push(`          app_name: ${name}`);
  push("          sap_volume_ids:");
  push(`            usr_sap: ${appVols[name]}`);
}

process.stdout.write(lines.join("\n") + "\n");
