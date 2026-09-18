# Instrucciones — Lab 5 (Kubernetes local)

Guía paso a paso para levantar el clúster local, desplegar los
manifiestos, verificarlos, probar cada mecanismo (self-healing, rolling
update, Ingress) y limpiar todo. Para entender el *porqué* de cada
objeto, ver [CONCEPTOS.md](CONCEPTOS.md); para el resumen de qué hace
cada archivo, ver [README.md](README.md).

Todos los comandos son `kubectl` puro — funcionan igual en PowerShell,
Git Bash/WSL o macOS/Linux.

---

## 1. Habilitar un clúster de Kubernetes local

Elige **una** de estas tres opciones.

### Opción A — Docker Desktop (recomendado si ya tienes Docker Desktop)

1. Abrir Docker Desktop → **Settings** → **Kubernetes**.
2. Marcar **Enable Kubernetes** → **Apply & Restart**.
3. Esperar a que el ícono de Kubernetes (abajo a la izquierda) quede en
   verde ("Kubernetes is running"). La primera vez descarga varias
   imágenes, puede tardar unos minutos.

### Opción B — minikube

```bash
# Instalar (Windows, con choco o winget)
winget install minikube

# Levantar el clúster
minikube start --driver=docker
```

### Opción C — kind (Kubernetes in Docker)

```bash
winget install kind
kind create cluster --name lab5
```

### Verificar que el clúster quedó activo

```bash
kubectl config get-contexts      # debe mostrar un contexto marcado con *
kubectl cluster-info             # debe responder con URLs, no un error de conexión
kubectl get nodes                # debe mostrar al menos 1 nodo en estado Ready
```

Si `kubectl cluster-info` responde `dial tcp [::1]:8080: connectex:
No connection could be made` es que ningún clúster está corriendo
todavía (o el contexto activo de `kubectl` apunta a otro) — revisar el
paso anterior.

---

## 2. Aplicar los manifiestos

Desde la carpeta `lab5/`:

```bash
# (opcional) validar sintaxis del render final sin necesidad de clúster activo
kubectl kustomize manifests/

# aplicar todo (namespace, configmaps, deployment, replicaset, services, ingress)
kubectl apply -k manifests/
```

`kubectl apply -k` aplica los objetos en el orden correcto
automáticamente (Kustomize resuelve dependencias como el Namespace
antes que los objetos que lo usan).

---

## 3. Verificar que todo quedó desplegado

```bash
# vista general
kubectl get all -n lab5-k8s

# uno por uno
kubectl get pods -n lab5-k8s -o wide
kubectl get deployments -n lab5-k8s
kubectl get replicasets -n lab5-k8s
kubectl get services -n lab5-k8s
kubectl get ingress -n lab5-k8s
kubectl get configmaps -n lab5-k8s
```

Deberías ver:

- `nginx-deployment` con `3/3` réplicas listas
- Dos ReplicaSets: uno con nombre `nginx-deployment-xxxxxxxxxx`
  (creado por el Deployment) y otro `nginx-rs-standalone` (el suelto)
- Dos Services: `nginx-clusterip` (`TYPE=ClusterIP`) y
  `nginx-nodeport` (`TYPE=NodePort`, con `80:30080/TCP` en la columna
  `PORT(S)`)
- Un Ingress `nginx-ingress` con `HOSTS=lab5.local`

Si algún Pod no llega a `Running`/`1/1 Ready`:

```bash
kubectl describe pod <nombre-del-pod> -n lab5-k8s   # eventos: ImagePullBackOff, CrashLoop, etc.
kubectl logs <nombre-del-pod> -n lab5-k8s
```

Atajo para no repetir `-n lab5-k8s` en cada comando:

```bash
kubectl config set-context --current --namespace=lab5-k8s
```

---

## 4. Probar el Service ClusterIP

Un ClusterIP no es accesible desde fuera del clúster directamente —
se prueba con `port-forward`:

```bash
kubectl port-forward -n lab5-k8s svc/nginx-clusterip 8080:80
```

Dejar corriendo esa terminal y, en otra, o desde el navegador:

```bash
curl http://localhost:8080
```

Debe devolver el HTML de `01-configmap-html.yaml` ("Lab 5 - Kubernetes
local"), confirmando que el ConfigMap se montó correctamente como
volumen. `Ctrl+C` para cortar el port-forward.

---

## 5. Probar el Service NodePort

Sin necesidad de port-forward (en clúster local, el "nodo" es tu propia
máquina):

```bash
curl http://localhost:30080
```

> Si usas **minikube**, el NodePort no siempre queda expuesto
> directamente en `localhost` — usar en su lugar:
> ```bash
> minikube service nginx-nodeport -n lab5-k8s --url
> ```
> y hacer `curl` a la URL que imprima. Docker Desktop y kind (con
> `extraPortMappings` configurado) sí exponen NodePort en `localhost`
> directamente.

---

## 6. Instalar el Ingress Controller y probar el Ingress

El objeto `Ingress` (`07-ingress.yaml`) por sí solo no hace nada — hace
falta un controller que lo lea. Instalar **ingress-nginx**:

```bash
# Docker Desktop / kind (clúster genérico)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.2/deploy/static/provider/cloud/deploy.yaml

# minikube (usa su propio addon en vez del manifiesto de arriba)
minikube addons enable ingress
```

Esperar a que el controller quede listo (puede tardar 1-2 minutos):

```bash
kubectl get pods -n ingress-nginx --watch
# Ctrl+C cuando el pod ingress-nginx-controller-xxxx esté Running/1-1 Ready
```

### Apuntar `lab5.local` a tu máquina

Editar el archivo hosts como Administrador:

- **Windows**: `C:\Windows\System32\drivers\etc\hosts`
- **macOS/Linux**: `/etc/hosts`

Agregar la línea:

```
127.0.0.1  lab5.local
```

### Probar

```bash
curl http://lab5.local
# o abrir http://lab5.local en el navegador
```

Con Docker Desktop, el controller de ingress-nginx normalmente queda
expuesto en el puerto 80/443 de `localhost` directo. Con minikube, en
cambio, suele hacer falta correr `minikube tunnel` en una terminal
aparte (déjala abierta) para que el controller sea alcanzable desde
`localhost`.

---

## 7. Probar self-healing (ReplicaSet)

Borrar un Pod a mano y observar que el ReplicaSet lo vuelve a crear
automáticamente:

```bash
kubectl get pods -n lab5-k8s -l app=nginx-lab
kubectl delete pod <nombre-de-un-pod> -n lab5-k8s
kubectl get pods -n lab5-k8s -l app=nginx-lab --watch
```

En unos segundos debería aparecer un Pod nuevo con nombre distinto,
mismo ReplicaSet, volviendo a `3/3` réplicas. Lo mismo aplica al
ReplicaSet suelto (`app=nginx-rs-demo`).

---

## 8. Probar rolling update y rollback (Deployment)

```bash
# cambiar la imagen (dispara un rolling update)
kubectl set image deployment/nginx-deployment nginx=nginx:1.27 -n lab5-k8s

# ver el progreso del rollout
kubectl rollout status deployment/nginx-deployment -n lab5-k8s

# ver historial de revisiones
kubectl rollout history deployment/nginx-deployment -n lab5-k8s

# revertir a la revisión anterior
kubectl rollout undo deployment/nginx-deployment -n lab5-k8s
```

Nota: `04-replicaset-standalone.yaml` **no** tiene este comando
equivalente — un ReplicaSet suelto no tiene concepto de "rollout" ni
historial; hay que editarlo y borrar/recrear los Pods a mano, que es
justo la limitación que ese archivo busca ilustrar (ver CONCEPTOS.md,
sección 3).

---

## 9. Limpieza

```bash
# eliminar todos los objetos del lab
kubectl delete -k manifests/

# si instalaste el ingress controller y quieres quitarlo también
kubectl delete -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.2/deploy/static/provider/cloud/deploy.yaml
# o, con minikube:
minikube addons disable ingress

# quitar la línea de lab5.local del archivo hosts (edición manual)
```

Si usaste minikube o kind exclusivamente para este lab y quieres
liberar los recursos de la máquina por completo:

```bash
minikube delete       # opción B
kind delete cluster --name lab5   # opción C
```

(Con Docker Desktop no hace falta "borrar" nada — basta con
`kubectl delete -k manifests/`; el clúster se queda disponible para
otros labs.)

---

## Troubleshooting común

| Síntoma | Causa probable | Solución |
|---|---|---|
| `dial tcp [::1]:8080: connectex` en cualquier comando `kubectl` | Ningún clúster corriendo, o contexto equivocado | Repetir paso 1; revisar `kubectl config get-contexts` |
| Pod en `ImagePullBackOff` | Sin conexión a internet la primera vez (descarga `nginx:1.27-alpine`) | Verificar conexión; `kubectl describe pod` para ver el error exacto |
| `curl localhost:30080` no responde | Estás usando minikube (no expone NodePort en localhost directo) | Usar `minikube service nginx-nodeport -n lab5-k8s --url` |
| `curl lab5.local` da "connection refused" | Ingress Controller no instalado o aún no está Ready | `kubectl get pods -n ingress-nginx`; esperar a que esté Running |
| `curl lab5.local` da 404 del propio ingress-nginx | Falta la línea en el archivo hosts, o el Ingress apunta a un Service/puerto que no existe | Revisar `/etc/hosts` y `kubectl describe ingress nginx-ingress -n lab5-k8s` |
| `kubectl apply -k manifests/` falla con error de Kustomize | Typo en algún nombre de archivo dentro de `kustomization.yaml` | Correr `kubectl kustomize manifests/` para ver el error exacto sin necesidad de clúster |
| Deployment se queda en `1/3` o `2/3` Ready | `resources.requests` pide más CPU/memoria de la que tiene el nodo local disponible | `kubectl describe pod` → evento `Insufficient cpu/memory`; bajar los requests en `03-deployment.yaml` o asignarle más recursos a Docker Desktop/minikube |
