swagger: "2.0"
info:
  title: ${api_id}
  description: API de items del lab11 (API Gateway -> Cloud Run functions -> Firestore)
  version: "1.0.0"
schemes:
  - https
produces:
  - application/json

# Backend: la función solo acepta llamadas con ID token del SA del gateway (no es pública).
x-google-backend:
  address: ${function_uri}
  path_translation: APPEND_PATH_TO_ADDRESS
  deadline: 30.0

# Cuota por API key (consumidor)
x-google-management:
  metrics:
    - name: "read-requests"
      displayName: "Read requests"
      valueType: INT64
      metricKind: DELTA
  quota:
    limits:
      - name: "read-limit"
        metric: "read-requests"
        unit: "1/min/{project}"
        values:
          STANDARD: ${quota_per_minute}

securityDefinitions:
  api_key:
    type: apiKey
    name: x-api-key
    in: header

paths:
  /health:
    get:
      operationId: health
      summary: Health check sin autenticación
      responses:
        "200":
          description: OK
  /items:
    get:
      operationId: listItems
      security:
        - api_key: []
      x-google-quota:
        metricCosts:
          read-requests: 1
      responses:
        "200":
          description: Lista de items
    post:
      operationId: createItem
      security:
        - api_key: []
      x-google-quota:
        metricCosts:
          read-requests: 1
      parameters:
        - in: body
          name: item
          required: true
          schema:
            $ref: "#/definitions/Item"
      responses:
        "201":
          description: Creado
        "400":
          description: Cuerpo inválido
  /items/{id}:
    parameters:
      - in: path
        name: id
        required: true
        type: string
    get:
      operationId: getItem
      security:
        - api_key: []
      x-google-quota:
        metricCosts:
          read-requests: 1
      responses:
        "200":
          description: Item
        "404":
          description: No existe
    delete:
      operationId: deleteItem
      security:
        - api_key: []
      x-google-quota:
        metricCosts:
          read-requests: 1
      responses:
        "204":
          description: Eliminado

definitions:
  Item:
    type: object
    required: [name]
    properties:
      name:
        type: string
        maxLength: 100
      description:
        type: string
        maxLength: 500
      price:
        type: number
        minimum: 0
