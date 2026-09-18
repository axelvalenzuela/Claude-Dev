# Conceptos y buenas prácticas — Lab 5 (Kubernetes)

Este documento explica el *porqué* detrás de cada decisión tomada en
los manifiestos de `manifests/`, y las buenas prácticas para dejar un
ambiente de Kubernetes local configurado de forma funcional y
mantenible. Es el complemento conceptual de [README.md](README.md)
(qué hace cada archivo) e [INSTRUCCIONES.md](INSTRUCCIONES.md) (cómo
ejecutarlo paso a paso).

## Índice

1. [Labels vs. Annotations](#1-labels-vs-annotations)
2. [Namespaces](#2-namespaces)
3. [Pods, ReplicaSets y Deployments](#3-pods-replicasets-y-deployments)
4. [Services: ClusterIP, NodePort, LoadBalancer, ExternalName](#4-services-clusterip-nodeport-loadbalancer-externalname)
5. [Ingress e Ingress Controller](#5-ingress-e-ingress-controller)
6. [ConfigMaps vs. Secrets](#6-configmaps-vs-secrets)
7. [Probes: readiness, liveness, startup](#7-probes-readiness-liveness-startup)
8. [Resources: requests, limits y QoS](#8-resources-requests-limits-y-qos)
9. [Checklist de buenas prácticas](#9-checklist-de-buenas-prácticas)

---

## 1. Labels vs. Annotations

Ambos son pares clave-valor en `metadata`, pero cumplen roles distintos
y **no son intercambiables**:

| | **Labels** | **Annotations** |
|---|---|---|
| Propósito | Identificar y **agrupar/seleccionar** objetos | Adjuntar **metadata no identificadora** |
| ¿Quién las lee? | Kubernetes mismo (selectors de Service, Deployment, NetworkPolicy...) | Herramientas externas, controllers, humanos |
| ¿Se puede filtrar por ellas? | Sí — `kubectl get pods -l app=nginx-lab` | No (no hay selectors por annotation) |
| Formato de valor | Restringido: máx 63 caracteres, `[a-z0-9A-Z]` con `-_.` internos | Libre: puede ser texto largo, JSON, URLs |
| Ejemplo en este lab | `app: nginx-lab` (selector del Service y del Deployment) | `nginx.ingress.kubernetes.io/rewrite-target: /` (config del Ingress Controller) |

**Regla práctica:** si necesitas que Kubernetes *seleccione* un
conjunto de objetos por ese valor (un Service que enruta a Pods, un
Deployment que administra un ReplicaSet), es un **label**. Si es
información que solo un humano o un controller externo va a leer, sin
que el propio scheduler/selector de Kubernetes la use, es una
**annotation**.

En este lab:

- `app: nginx-lab` es un **label** compartido por el Deployment, sus
  Pods y ambos Services (`05-service-clusterip.yaml`,
  `06-service-nodeport.yaml`) — es el mecanismo real de conexión entre
  Service → Pod. Si cambias este label en un archivo sin cambiarlo en
  el otro, el Service deja de encontrar Pods.
- `nginx.ingress.kubernetes.io/rewrite-target: /` en
  `07-ingress.yaml` es una **annotation**: el objeto `Ingress` genérico
  de Kubernetes no sabe qué es "rewrite-target"; es el *Ingress
  Controller* (ingress-nginx) el que la lee al traducir el `Ingress` a
  configuración real de Nginx. Cada Ingress Controller (nginx, Traefik,
  HAProxy...) define sus propias annotations con su propio prefijo.

### Buena práctica: labels estándar

Kubernetes define un set de labels "recomendadas"
(`app.kubernetes.io/*`) para que herramientas como Helm, Lens o
dashboards de observabilidad puedan interpretar objetos de cualquier
proyecto de forma uniforme:

```yaml
labels:
  app.kubernetes.io/name: nginx
  app.kubernetes.io/instance: nginx-lab5
  app.kubernetes.io/component: web
  app.kubernetes.io/part-of: lab5-k8s
  app.kubernetes.io/managed-by: kubectl
```

Este lab usa el label simplificado `app: nginx-lab` para que los
manifiestos sean cortos y fáciles de leer en un ejercicio educativo,
pero en un proyecto real conviene adoptar el set `app.kubernetes.io/*`
desde el día uno.

---

## 2. Namespaces

Un Namespace es una partición **lógica** del clúster: aísla nombres
(dos Pods pueden llamarse igual en namespaces distintos) y sirve como
límite para `ResourceQuota`, `NetworkPolicy` y RBAC. **No aísla red por
sí solo** — por defecto todos los Pods de todos los namespaces pueden
hablar entre sí; para bloquearlo hace falta una `NetworkPolicy`
explícita (fuera del alcance de este lab).

Buenas prácticas:

- Un namespace por entorno/proyecto (`lab5-k8s` aquí), nunca todo en
  `default`.
- Fijar el namespace en cada manifiesto (`metadata.namespace: lab5-k8s`
  como en este lab) en vez de depender del contexto activo de
  `kubectl` — evita aplicar algo al namespace equivocado por error.
- Alternativa cómoda: `kubectl config set-context --current
  --namespace=lab5-k8s` para no repetir `-n lab5-k8s` en cada comando
  (ver INSTRUCCIONES.md).

---

## 3. Pods, ReplicaSets y Deployments

Jerarquía de control (cada nivel es administrado por el de arriba):

```
Deployment  →  ReplicaSet  →  Pod(s)
```

- **Pod**: la unidad mínima ejecutable (uno o más contenedores que
  comparten red y storage). Casi nunca se crea un Pod suelto: si muere,
  nadie lo vuelve a crear.
- **ReplicaSet**: garantiza que siempre haya `N` Pods vivos que
  cumplan su `selector`. Es el mecanismo de *self-healing*. Por sí
  solo no sabe hacer rolling update ni rollback.
- **Deployment**: administra ReplicaSets. Al cambiar la imagen o el
  spec del Pod, crea un ReplicaSet nuevo y hace *rolling update*
  (apaga viejos Pods / prende nuevos gradualmente), manteniendo
  historial para poder hacer `kubectl rollout undo`.

Por eso `03-deployment.yaml` es el objeto "de producción" real, y
`04-replicaset-standalone.yaml` existe solo para que se vea, en un
`kubectl get replicasets`, la diferencia entre un RS que **pertenece**
a un Deployment (tiene un `ownerReference` hacia él) y uno que no.

**Buena práctica:** nunca editar un ReplicaSet creado por un Deployment
directamente (por ejemplo, cambiarle `replicas`) — el Deployment lo va
a revertir en el siguiente reconcile. El punto de entrada siempre es el
Deployment.

---

## 4. Services: ClusterIP, NodePort, LoadBalancer, ExternalName

Un Service es una IP virtual + balanceo de carga estable hacia un
conjunto de Pods (definido por `selector`, no por nombre — si los Pods
mueren y nacen otros con las mismas labels, el Service los sigue
encontrando).

| Tipo | Alcance | Cuándo usarlo |
|---|---|---|
| `ClusterIP` (default) | Solo dentro del clúster | Comunicación interna entre servicios (backend↔DB, o backend del Ingress). Es lo que usa `05-service-clusterip.yaml`. |
| `NodePort` | Puerto fijo (30000-32767) en cada nodo | Acceso externo simple en clúster local/dev, sin instalar nada más. `06-service-nodeport.yaml` usa `30080`. En producción rara vez se expone así directo. |
| `LoadBalancer` | IP pública asignada por el proveedor de nube | Producción en la nube (AWS/GCP/Azure aprovisionan un balanceador real). No funciona "de fábrica" en clúster local — se queda en `<pending>` salvo que instales algo como MetalLB. |
| `ExternalName` | Alias DNS hacia un nombre externo | Referenciar un servicio fuera del clúster (ej. una base de datos gestionada) con un nombre interno de Kubernetes. No se usa en este lab. |
| *(headless)* `clusterIP: None` | Sin IP virtual, DNS resuelve directo a cada Pod | Cuando el cliente necesita conectarse a un Pod específico (ej. StatefulSets como bases de datos en clúster). No se usa en este lab. |

**Por qué el lab incluye ClusterIP *y* NodePort a la vez:** son
complementarios, no mutuamente excluyentes. El `NodePort` en realidad
*incluye* el comportamiento de ClusterIP (también obtiene una IP
interna) y además abre el puerto en el nodo. Se muestran los dos
Services por separado para que quede claro cuándo usar cada patrón:
ClusterIP para el Ingress (tráfico ya llegó al clúster, se enruta
internamente) y NodePort para probar acceso externo sin depender de un
Ingress Controller instalado.

**Buena práctica:** en producción, evitar exponer NodePort
directamente a internet. Preferir `LoadBalancer` (en la nube) o
`Ingress` (para enrutar múltiples servicios HTTP/HTTPS bajo un mismo
punto de entrada) — NodePort queda para debugging o clústeres on-prem
sin balanceador.

---

## 5. Ingress e Ingress Controller

Son **dos objetos distintos** y hace falta instalar ambos:

- **`Ingress`** (`07-ingress.yaml`): solo declara *reglas* de
  enrutamiento (host/path → Service). Es un objeto pasivo, como un
  archivo de configuración.
- **Ingress Controller**: el proceso real (un Pod, típicamente
  `ingress-nginx`, Traefik o similar) que *lee* esas reglas y configura
  un proxy reverso de verdad. Sin un controller corriendo, el objeto
  `Ingress` no tiene ningún efecto — por eso `kubectl get ingress`
  puede mostrar el objeto creado pero `curl` seguir fallando si el
  controller no está instalado (ver INSTRUCCIONES.md para instalarlo).

Campos clave de `07-ingress.yaml`:

- `spec.ingressClassName: nginx` — le dice a Kubernetes *cuál*
  Ingress Controller debe atender esta regla (un clúster puede tener
  varios controllers instalados a la vez, cada uno con su propia
  `IngressClass`).
- `spec.rules[].host` — enrutamiento por nombre de dominio (aquí
  `lab5.local`, ficticio, resuelto vía archivo `hosts` local).
- `annotations` con prefijo `nginx.ingress.kubernetes.io/*` — config
  específica de ese controller (rewrite, SSL redirect, rate limiting,
  tamaño máximo de body, etc.). Cada Ingress Controller define su
  propio set de annotations soportadas; no son parte del estándar de
  Kubernetes.

**Buena práctica:** usar Ingress (con un solo Ingress Controller
compartido) en vez de un `Service LoadBalancer` por cada aplicación —
consolida TLS, logging y reglas de enrutamiento en un solo punto, y es
mucho más barato en la nube (un balanceador en vez de N).

---

## 6. ConfigMaps vs. Secrets

Ambos separan configuración del código de la imagen (principio de
[12-factor apps](https://12factor.net/config)), pero:

- **ConfigMap** (`01-configmap-html.yaml`, `02-configmap-env.yaml`):
  para configuración **no sensible** — nombres de host, flags,
  archivos estáticos, niveles de log.
- **Secret**: mismo mecanismo pero pensado para datos sensibles
  (passwords, tokens, certificados). Por defecto solo está codificado
  en base64 (no cifrado) — para cifrado real en reposo hace falta
  habilitar *encryption at rest* en el clúster o usar una herramienta
  externa (Sealed Secrets, External Secrets Operator, Vault). **No
  incluido en este lab** porque no hay credenciales que manejar, pero
  es el paso natural siguiente si el contenedor necesitara, por
  ejemplo, una contraseña de base de datos.

Dos formas de consumir un ConfigMap (ambas usadas en este lab, a
propósito, para comparar):

1. **Como volumen** (`01-configmap-html.yaml` → `volumes` +
   `volumeMounts` en `03-deployment.yaml`): cada key se vuelve un
   archivo. Útil para archivos de configuración completos (nginx.conf,
   index.html, application.yaml...).
2. **Como variables de entorno** (`02-configmap-env.yaml` →
   `envFrom.configMapRef`): cada key se vuelve una env var. Útil para
   flags sueltos que la app lee de `process.env` / `os.environ`.

**Buena práctica:** un ConfigMap montado como volumen **no se
actualiza automáticamente dentro del Pod** de forma instantánea al
hacer `kubectl edit configmap` (kubelet lo sincroniza cada cierto
intervalo, y la app rara vez recarga sola el archivo). Para forzar que
un cambio de ConfigMap dispare un rollout, una técnica común es incluir
un hash del contenido del ConfigMap en una annotation del `template`
del Deployment (patrón que Helm/Kustomize automatizan) — así cualquier
cambio de config genera un Pod nuevo.

---

## 7. Probes: readiness, liveness, startup

Tres sondas distintas, cada una con un propósito y una consecuencia
distinta si fallan:

| Probe | Pregunta que responde | Si falla |
|---|---|---|
| `readinessProbe` | ¿Este Pod está listo para **recibir tráfico** ahora mismo? | El Pod se saca temporalmente de los endpoints del Service (deja de recibir tráfico) pero **no se reinicia**. |
| `livenessProbe` | ¿Este Pod sigue **vivo** (no colgado en deadlock)? | Kubernetes **mata y reinicia** el contenedor. |
| `startupProbe` | ¿Ya terminó de **arrancar**? (para apps con boot lento) | Bloquea liveness/readiness hasta que pasa, evitando que un arranque lento se confunda con un liveness fallido. No usado en este lab porque Nginx arranca casi instantáneo. |

En `03-deployment.yaml` ambas sondas apuntan a `GET /` puerto 80 (algo
que Nginx siempre puede responder), con `readinessProbe` con
`initialDelaySeconds` más corto (entra al balanceo antes) y
`livenessProbe` más conservador (evita reinicios innecesarios por un
pico de latencia momentáneo).

**Buena práctica:** siempre definir al menos `readinessProbe` en
producción — sin ella, un Service puede enviar tráfico a un Pod que
todavía no terminó de inicializar, causando errores intermitentes justo
después de cada deploy.

---

## 8. Resources: requests, limits y QoS

- `requests`: lo que el Pod **reserva** — el scheduler solo coloca el
  Pod en un nodo que tenga al menos esa cantidad libre. Es lo que
  *garantiza* que tendrá disponible.
- `limits`: el **tope máximo**. Si se pasa de `memory` limit, el
  contenedor es matado (`OOMKilled`); si se pasa de `cpu` limit, se le
  hace *throttling* (no lo matan, pero lo frenan).

Kubernetes deriva una clase de QoS (*Quality of Service*) de esta
relación, que decide qué Pods se matan primero si el nodo se queda sin
recursos:

- **Guaranteed**: `requests == limits` en CPU y memoria (máxima
  prioridad, se matan de último).
- **Burstable**: `requests < limits` (lo que usa este lab: `50m/200m`
  CPU, `64Mi/128Mi` memoria) — prioridad media.
- **BestEffort**: sin `requests` ni `limits` definidos — primeros en
  ser matados bajo presión de recursos.

**Buena práctica:** nunca dejar un contenedor sin `requests`/`limits`
en un clúster compartido — un solo Pod sin límites puede acaparar toda
la memoria del nodo y tumbar a los demás. Los valores de este lab
(`50m`-`200m` CPU, `64Mi`-`128Mi` memoria) son deliberadamente bajos:
alcanzan para un Nginx sirviendo HTML estático en un laptop, pero
deberían medirse con carga real antes de llevarlos a producción.

---

## 9. Checklist de buenas prácticas

Para dejar un ambiente de Kubernetes local (o cualquier clúster)
configurado de forma funcional y fácil de mantener:

- [ ] **Namespace propio** por proyecto/entorno, nunca todo en `default`.
- [ ] **Labels consistentes** (`app`, idealmente `app.kubernetes.io/*`)
      compartidas entre Deployment, Pods y Services — son el pegamento
      real entre objetos.
- [ ] **Annotations solo para lo que no es selector**: config de
      Ingress Controller, checksums de ConfigMap, metadata para
      herramientas externas (Prometheus scrape, etc.).
- [ ] **Nunca editar a mano** un ReplicaSet o Pod administrado por un
      Deployment — editar el Deployment.
- [ ] **`requests` y `limits` siempre definidos** en cada contenedor.
- [ ] **`readinessProbe` siempre**, `livenessProbe` casi siempre
      (con cuidado de no hacerla demasiado agresiva).
- [ ] **Nunca usar el tag `:latest`** en producción — fija versiones
      (`nginx:1.27-alpine` en este lab) para que un rollout sea
      reproducible y el rollback tenga sentido.
- [ ] **Secrets, nunca ConfigMaps, para datos sensibles.**
- [ ] **Declarativo sobre imperativo**: manifiestos versionados en Git
      (`kubectl apply -f`/`-k`) en vez de `kubectl create`/`kubectl
      edit` sueltos — así el estado del clúster queda reproducible y
      auditable (lo que este lab hace guardando todo en `manifests/`).
- [ ] **Kustomize o Helm** para no repetir boilerplate entre
      entornos (este lab usa Kustomize, ya integrado en `kubectl`, por
      ser un solo entorno; Helm conviene cuando hay que parametrizar
      varios entornos con el mismo chart).
- [ ] **`NodePort` solo para dev/debug local**; `LoadBalancer` o
      `Ingress` para exponer tráfico real.
- [ ] **Un Ingress Controller único compartido** por el clúster en vez
      de un `LoadBalancer` por servicio.
- [ ] Antes de aplicar, revisar el render final con `kubectl kustomize
      manifests/` (no requiere clúster activo) para detectar errores
      de sintaxis sin necesidad de tener Kubernetes corriendo.
