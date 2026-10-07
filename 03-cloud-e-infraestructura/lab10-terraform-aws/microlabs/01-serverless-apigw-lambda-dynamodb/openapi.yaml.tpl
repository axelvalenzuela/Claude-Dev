openapi: "3.0.1"
info:
  title: "${api_name}"
  description: "API REST de items - micro lab 01 (contrato OpenAPI como fuente de verdad)"
  version: "1.0.0"

# Validación de requests en el borde (reduce invocaciones inválidas a Lambda)
x-amazon-apigateway-request-validators:
  all:
    validateRequestBody: true
    validateRequestParameters: true
x-amazon-apigateway-request-validator: all
x-amazon-apigateway-api-key-source: HEADER

paths:
  /health:
    get:
      summary: Health check sin backend (integración MOCK)
      responses:
        "200":
          description: OK
      x-amazon-apigateway-integration:
        type: mock
        requestTemplates:
          application/json: '{"statusCode": 200}'
        responses:
          default:
            statusCode: "200"
            responseTemplates:
              application/json: '{"status": "ok"}'

  /items:
    get:
      summary: Lista items
      security:
        - cognito: []
          api_key: []
      responses:
        "200":
          description: OK
      x-amazon-apigateway-integration:
        type: aws_proxy
        httpMethod: POST
        uri: "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"
    post:
      summary: Crea un item
      security:
        - cognito: []
          api_key: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Item"
      responses:
        "201":
          description: Creado
      x-amazon-apigateway-integration:
        type: aws_proxy
        httpMethod: POST
        uri: "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"

  /items/{id}:
    parameters:
      - name: id
        in: path
        required: true
        schema:
          type: string
    get:
      summary: Obtiene un item
      security:
        - cognito: []
          api_key: []
      responses:
        "200":
          description: OK
      x-amazon-apigateway-integration:
        type: aws_proxy
        httpMethod: POST
        uri: "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"
    delete:
      summary: Elimina un item
      security:
        - cognito: []
          api_key: []
      responses:
        "204":
          description: Eliminado
      x-amazon-apigateway-integration:
        type: aws_proxy
        httpMethod: POST
        uri: "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${lambda_arn}/invocations"

components:
  schemas:
    Item:
      type: object
      required: [name]
      additionalProperties: false
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
        description:
          type: string
          maxLength: 500
        price:
          type: number
          minimum: 0

  securitySchemes:
    cognito:
      type: apiKey
      name: Authorization
      in: header
      x-amazon-apigateway-authtype: cognito_user_pools
      x-amazon-apigateway-authorizer:
        type: cognito_user_pools
        providerARNs:
          - "${user_pool_arn}"
    api_key:
      type: apiKey
      name: x-api-key
      in: header
