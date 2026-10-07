#!/usr/bin/env bash
# Verifica el cluster y el workload: nodos privados, réplicas en varias zonas, PSS restricted, NetworkPolicy, HPA y PDB.
# LOAD=1 genera carga para observar el escalado del HPA.
source "$(dirname "$0")/../../../scripts/lib.sh"
require gcloud kubectl curl jq

CLUSTER=$(out cluster_name)
NS=$(out namespace)
gcloud container clusters get-credentials "$CLUSTER" --region "$REGION" --project "$PROJECT" >/dev/null 2>&1

section "Cluster $CLUSTER"
C=$(gcloud container clusters describe "$CLUSTER" --region "$REGION" --format=json)
expect "Autopilot" "$(echo "$C" | jq -r .autopilot.enabled)" "true"
expect "Nodos privados" "$(echo "$C" | jq -r .privateClusterConfig.enablePrivateNodes)" "true"
expect "Workload Identity" "$(echo "$C" | jq -r .workloadIdentityConfig.workloadPool)" "$PROJECT.svc.id.goog"

section "Workload"
check "Deployment disponible" kubectl -n "$NS" rollout status deploy/web --timeout=600s
ZONES=$(kubectl -n "$NS" get pods -l app=web -o json | jq -r '.items[].spec.nodeName' |
  xargs -I{} kubectl get node {} -o jsonpath='{.metadata.labels.topology\.kubernetes\.io/zone}{"\n"}' | sort -u | wc -l | tr -d ' ')
info "Zonas con réplicas: $ZONES"
expect "Pods corren como non-root" "$(kubectl -n "$NS" get deploy web -o jsonpath='{.spec.template.spec.securityContext.runAsNonRoot}')" "true"

section "Pod Security Admission (restricted)"
if kubectl -n "$NS" run privileged-test --image=busybox --restart=Never --overrides='{"spec":{"containers":[{"name":"t","image":"busybox","securityContext":{"privileged":true}}]}}' >/dev/null 2>&1; then
  ko "Se permitió un pod privilegiado"; kubectl -n "$NS" delete pod privileged-test --now >/dev/null 2>&1
else
  ok "Pod privilegiado rechazado por la política restricted"
fi

section "Servicio público"
check "LoadBalancer con IP (hasta 3 min)" retry 18 10 bash -c "kubectl -n $NS get svc web -o jsonpath='{.status.loadBalancer.ingress[0].ip}' | grep -q ."
IP=$(kubectl -n "$NS" get svc web -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
check "HTTP 200 en http://$IP" retry 18 10 bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' http://$IP)\" = 200 ]"

section "Resiliencia"
expect "PDB minAvailable" "$(kubectl -n "$NS" get pdb web -o jsonpath='{.spec.minAvailable}')" "1"
expect "NetworkPolicies" "$(kubectl -n "$NS" get networkpolicy -o name | wc -l | tr -d ' ')" "2"
info "HPA: $(kubectl -n "$NS" get hpa web -o jsonpath='{.status.currentReplicas} réplicas, CPU {.status.currentMetrics[0].resource.current.averageUtilization}%')"

if [ "${LOAD:-0}" = "1" ]; then
  section "Carga (3 min) para disparar el HPA"
  END=$(( $(date +%s) + 180 ))
  while [ "$(date +%s)" -lt "$END" ]; do for _ in $(seq 1 50); do curl -s -o /dev/null "http://$IP" & done; wait; done
  info "Réplicas después de la carga: $(kubectl -n "$NS" get hpa web -o jsonpath='{.status.currentReplicas}')"
fi

summary
