# 🏗️ Arquitectura Técnica Detallada - Bookstore Backend

## 📋 Resumen Ejecutivo

Este documento describe la arquitectura técnica completa del sistema de backend para bookstore, implementado con microservicios serverless en AWS, incluyendo patrones de diseño, decisiones arquitectónicas y consideraciones de escalabilidad.

---

## 🎯 Objetivos de Arquitectura

### Objetivos Funcionales

- ✅ **Gestión completa de usuarios** con autenticación JWT
- ✅ **Catálogo de libros** con búsqueda avanzada
- ✅ **Sistema de compras** con carrito persistente
- ✅ **Analytics en tiempo real** para business intelligence
- ✅ **Multi-tenancy** para múltiples clientes

### Objetivos No Funcionales

- 🚀 **Escalabilidad**: Manejo de 10K+ usuarios concurrentes
- ⚡ **Performance**: Latencia < 200ms en 95% de requests
- 🔒 **Seguridad**: Aislamiento por tenant + JWT
- 💰 **Costo-efectividad**: Pay-per-use con serverless
- 🌍 **Disponibilidad**: 99.9% uptime

---

## 🏛️ Patrones Arquitectónicos Implementados

### 1. Microservicios Serverless

```
┌─────────────────┐
│  API Gateway    │ ← Entry point único
└─────────┬───────┘
          │
    ┌─────┴─────┐
    │  Lambda   │ ← Lógica de negocio
    └─────┬─────┘
          │
    ┌─────┴─────┐
    │ DynamoDB  │ ← Persistencia
    └───────────┘
```

**Ventajas**:

- Independencia de desarrollo y despliegue
- Escalamiento automático por servicio
- Fault tolerance por aislamiento

### 2. Event-Driven Architecture

```
DynamoDB → Streams → Lambda → [Elasticsearch | S3]
```

**Implementación**:

- **DynamoDB Streams**: Captura cambios en tiempo real
- **Lambda Processors**: Procesan eventos de manera asíncrona
- **Fan-out Pattern**: Un evento puede triggerear múltiples acciones

### 3. Multi-Tenant SaaS Pattern

```
Tenant1: tenant1#user_123 → Aislamiento por prefijo
Tenant2: tenant2#user_456 → Datos completamente separados
```

**Implementación**:

- **Partition Key**: Prefijo con tenant_id
- **Row Level Security**: Filtros automáticos por tenant
- **Elasticsearch**: Índices separados por tenant

---

## 🗄️ Diseño de Base de Datos

### Modelo de Datos DynamoDB

#### Patrones de Acceso Identificados

| Patrón                | Descripción                  | Implementación                         |
| --------------------- | ---------------------------- | -------------------------------------- |
| **User by ID**        | Obtener usuario por ID       | PK: tenant_id#user_id                  |
| **User by Email**     | Login por email              | GSI1: tenant_id#EMAIL → email          |
| **Books by Category** | Filtrar libros por categoría | GSI1: tenant_id#CATEGORY → category    |
| **Books by Author**   | Filtrar libros por autor     | GSI2: tenant_id#AUTHOR → author        |
| **User Purchases**    | Historial de compras         | PK: tenant_id#user_id                  |
| **Analytics by Date** | Reportes por fecha           | GSI1: tenant_id#PURCHASES → created_at |

#### Estructura de Claves

```javascript
// Users Table
{
  pk: "tenant1#user_123",
  sk: "USER#john@example.com",
  gsi1pk: "tenant1#EMAIL",
  gsi1sk: "john@example.com",
  // ... datos del usuario
}

// Books Table
{
  pk: "tenant1#book_456",
  sk: "BOOK#978-1234567890",
  gsi1pk: "tenant1#CATEGORY",
  gsi1sk: "Programming#book_456",
  gsi2pk: "tenant1#AUTHOR",
  gsi2sk: "Robert Martin#book_456",
  // ... datos del libro
}
```

### Consideraciones de Performance

#### Read/Write Capacity

- **Mode**: On-Demand para manejo automático de spikes
- **Hot Partitions**: Evitadas con distribución uniforme de tenant_id
- **GSI Projections**: ALL para flexibilidad vs. costo

#### Query Optimization

```javascript
// ✅ Eficiente: Query específico por tenant
const params = {
  KeyConditionExpression: "pk = :pk",
  ExpressionAttributeValues: { ":pk": "tenant1#user_123" },
};

// ❌ Ineficiente: Scan cross-tenant
const badParams = {
  FilterExpression: "email = :email", // Requiere scan completo
};
```

---

## 🔍 Sistema de Búsqueda con Elasticsearch

### Arquitectura Multi-Tenant

```bash
# Contenedores separados por tenant
elasticsearch_tenant1:9201
elasticsearch_tenant2:9202
elasticsearch_tenant3:9203
```

### Configuración de Índices

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "spanish_custom": {
          "type": "spanish",
          "stopwords": ["el", "la", "de", "que", "y", "a"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "spanish_custom",
        "fields": {
          "keyword": { "type": "keyword" },
          "suggest": { "type": "completion" }
        }
      },
      "author": {
        "type": "text",
        "analyzer": "spanish_custom"
      },
      "description": {
        "type": "text",
        "analyzer": "spanish_custom"
      },
      "category": { "type": "keyword" },
      "price": { "type": "double" },
      "rating": { "type": "double" },
      "publication_year": { "type": "integer" }
    }
  }
}
```

### Queries de Búsqueda Avanzada

```json
{
  "query": {
    "bool": {
      "must": [{ "term": { "tenant_id": "tenant1" } }],
      "should": [
        { "match": { "title": { "query": "clean code", "boost": 3 } } },
        { "match": { "author": { "query": "clean code", "boost": 2 } } },
        { "match": { "description": { "query": "clean code" } } }
      ],
      "filter": [
        { "range": { "price": { "gte": 10, "lte": 100 } } },
        { "term": { "category": "Programming" } }
      ]
    }
  },
  "sort": [{ "_score": { "order": "desc" } }, { "rating": { "order": "desc" } }]
}
```

---

## ⚡ Procesamiento de Streams

### DynamoDB Streams Configuration

```yaml
StreamSpecification:
  StreamViewType: NEW_AND_OLD_IMAGES
```

**StreamViewType Options**:

- `KEYS_ONLY`: Solo claves (mínimo overhead)
- `NEW_IMAGE`: Solo datos nuevos
- `OLD_IMAGE`: Solo datos anteriores
- `NEW_AND_OLD_IMAGES`: Datos completos (usado para sync completo)

### Lambda Stream Processors

#### Books Stream Processor

```python
def process_record(record):
    event_name = record['eventName']

    if event_name == 'INSERT':
        # Indexar nuevo libro en Elasticsearch
        book_data = extract_book_data(record['dynamodb']['NewImage'])
        elasticsearch_client.index(
            index=f"books_{book_data['tenant_id']}",
            body=book_data
        )

    elif event_name == 'MODIFY':
        # Actualizar índice existente
        old_data = record['dynamodb']['OldImage']
        new_data = record['dynamodb']['NewImage']
        # ... lógica de sincronización

    elif event_name == 'REMOVE':
        # Eliminar del índice
        book_id = record['dynamodb']['OldImage']['book_id']['S']
        elasticsearch_client.delete(
            index=f"books_{tenant_id}",
            id=book_id
        )
```

#### Purchases Stream Processor

```python
def process_purchase(record):
    purchase_data = extract_purchase_data(record['dynamodb']['NewImage'])

    # Estructura particionada por fecha
    date_partition = create_date_partition(purchase_data['created_at'])
    s3_key = f"{purchase_data['tenant_id']}/purchases/{date_partition}/{purchase_data['purchase_id']}.json"

    # Subir a S3 para analytics
    s3_client.put_object(
        Bucket=ANALYTICS_BUCKET,
        Key=s3_key,
        Body=json.dumps(purchase_data)
    )

    # Actualizar métricas en tiempo real
    update_daily_summary(purchase_data)
```

---

## 📊 Data Lake y Analytics

### Estructura S3 Particionada

```
s3://bookstore-analytics-dev/
├── tenant1/
│   ├── purchases/
│   │   ├── year=2025/
│   │   │   ├── month=01/
│   │   │   │   ├── day=01/
│   │   │   │   │   ├── purchase_123.json
│   │   │   │   │   └── purchase_124.json
│   │   │   │   └── day=02/
│   │   │   └── month=02/
│   │   └── year=2024/
│   └── daily_summary/
│       └── year=2025/month=01/day=01/summary.json
├── tenant2/
│   └── purchases/...
└── tenant3/
    └── purchases/...
```

### AWS Glue Table Definition

```yaml
TableInput:
  Name: purchases
  StorageDescriptor:
    Columns:
      - Name: purchase_id
        Type: string
      - Name: tenant_id
        Type: string
      - Name: user_id
        Type: string
      - Name: total_amount
        Type: double
      - Name: created_at
        Type: timestamp
      - Name: items
        Type: array<struct<
          book_id:string,
          quantity:int,
          unit_price:double,
          subtotal:double
        >>
    Location: s3://bookstore-analytics-dev/purchases/
    InputFormat: org.apache.hadoop.mapred.TextInputFormat
    OutputFormat: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
    SerdeInfo:
      SerializationLibrary: org.openx.data.jsonserde.JsonSerDe
  PartitionKeys:
    - Name: year
      Type: string
    - Name: month
      Type: string
    - Name: day
      Type: string
```

### Queries Athena Optimizadas

```sql
-- Query optimizada con particiones
SELECT
    tenant_id,
    COUNT(*) as total_purchases,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value
FROM purchases_table
WHERE year = '2025'
  AND month = '01'
  AND tenant_id = 'tenant1'
GROUP BY tenant_id;

-- Top productos por categoría
WITH book_sales AS (
    SELECT
        p.tenant_id,
        i.book_id,
        i.title,
        b.category,
        SUM(i.quantity) as total_sold,
        SUM(i.subtotal) as total_revenue
    FROM purchases_table p
    CROSS JOIN UNNEST(p.items) AS t(i)
    JOIN books_table b ON i.book_id = b.book_id
    WHERE p.year = '2025' AND p.month = '01'
    GROUP BY p.tenant_id, i.book_id, i.title, b.category
)
SELECT
    category,
    title,
    total_sold,
    total_revenue,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY total_sold DESC) as rank
FROM book_sales
WHERE rank <= 5;
```

---

## 🔒 Seguridad y Compliance

### Autenticación JWT

```javascript
// Token Structure
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "user_123",
    "tenant_id": "tenant1",
    "exp": 1640995200,
    "iat": 1640991600
  }
}
```

### Middleware de Autenticación

```python
async def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Verificar expiración
        if payload['exp'] < datetime.utcnow().timestamp():
            raise HTTPException(401, "Token expirado")

        # Verificar tenant
        tenant_id = payload.get('tenant_id')
        if not tenant_id:
            raise HTTPException(401, "Token inválido: sin tenant")

        return payload

    except JWTError:
        raise HTTPException(401, "Token inválido")
```

### Tenant Isolation

```python
# Automáticamente inyectado en queries
def build_query_with_tenant_isolation(tenant_id: str, base_query: dict):
    return {
        **base_query,
        'KeyConditionExpression': f'begins_with(pk, :tenant_prefix)',
        'ExpressionAttributeValues': {
            ':tenant_prefix': f'{tenant_id}#'
        }
    }
```

### IAM Roles y Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Query",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/bookstore-*",
        "arn:aws:dynamodb:*:*:table/bookstore-*/index/*"
      ],
      "Condition": {
        "ForAllValues:StringLike": {
          "dynamodb:Attributes": ["tenant_id", "pk", "sk"]
        }
      }
    }
  ]
}
```

---

## 📈 Métricas y Monitoreo

### CloudWatch Metrics Personalizadas

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_custom_metric(metric_name: str, value: float, tenant_id: str):
    cloudwatch.put_metric_data(
        Namespace='Bookstore/Business',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': 'Count',
                'Dimensions': [
                    {
                        'Name': 'TenantId',
                        'Value': tenant_id
                    }
                ]
            }
        ]
    )

# Ejemplos de uso
put_custom_metric('NewUserRegistrations', 1, 'tenant1')
put_custom_metric('BookPurchases', 1, 'tenant1')
put_custom_metric('SearchQueries', 1, 'tenant1')
```

### Dashboards de Monitoreo

```yaml
# CloudWatch Dashboard Config
{
  "widgets":
    [
      {
        "type": "metric",
        "properties":
          {
            "metrics":
              [
                [
                  "AWS/Lambda",
                  "Duration",
                  "FunctionName",
                  "bookstore-users-api",
                ],
                ["AWS/Lambda", "Errors", "FunctionName", "bookstore-users-api"],
                [
                  "AWS/DynamoDB",
                  "ConsumedReadCapacityUnits",
                  "TableName",
                  "bookstore-users-dev",
                ],
              ],
            "period": 300,
            "stat": "Average",
            "region": "us-east-1",
            "title": "API Performance",
          },
      },
    ],
}
```

---

## 🚀 Consideraciones de Escalabilidad

### Auto-scaling Configurado

| Servicio          | Método de Escalamiento  | Configuración                   |
| ----------------- | ----------------------- | ------------------------------- |
| **Lambda**        | Concurrencia automática | 1000 ejecuciones concurrentes   |
| **DynamoDB**      | On-Demand               | Auto-scaling basado en tráfico  |
| **API Gateway**   | Ilimitado               | Rate limiting por tenant        |
| **Elasticsearch** | Manual                  | Agregar contenedores por tenant |

### Performance Optimization

```python
# Connection pooling para DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    config=Config(
        max_pool_connections=50,
        retries={'max_attempts': 3}
    )
)

# Batch operations para eficiencia
def batch_write_items(items: List[dict], table_name: str):
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)
```

### Caching Strategy

```python
# Redis/ElastiCache para sesiones
import redis

redis_client = redis.Redis(host='elasticache-endpoint')

def get_user_session(user_id: str) -> dict:
    cached = redis_client.get(f"session:{user_id}")
    if cached:
        return json.loads(cached)

    # Fallback a DynamoDB
    user_data = dynamodb_get_user(user_id)
    redis_client.setex(f"session:{user_id}", 3600, json.dumps(user_data))
    return user_data
```

---

## 🔄 CI/CD y DevOps

### Pipeline de Despliegue

```yaml
# .github/workflows/deploy.yml
name: Deploy Bookstore Backend

on:
  push:
    branches: [main, develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: "18"

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.9"

      - name: Install Serverless
        run: npm install -g serverless

      - name: Deploy to Dev
        if: github.ref == 'refs/heads/develop'
        run: sls deploy --stage dev

      - name: Deploy to Prod
        if: github.ref == 'refs/heads/main'
        run: sls deploy --stage prod
```

### Testing Strategy

```python
# Unit Tests
import pytest
from moto import mock_dynamodb

@mock_dynamodb
def test_create_user():
    # Setup mock DynamoDB
    table = create_mock_table()

    # Test user creation
    user_data = {
        "email": "test@example.com",
        "password": "123456",
        "tenant_id": "tenant1"
    }

    result = create_user(user_data)
    assert result["status"] == "success"

# Integration Tests
def test_full_user_flow():
    # Register -> Login -> Get Profile
    register_response = register_user(test_user_data)
    token = register_response["token"]

    profile_response = get_user_profile(token)
    assert profile_response["email"] == test_user_data["email"]
```

---

## 💰 Consideraciones de Costo

### Estimación de Costos Mensuales

| Servicio        | Costo Base | Costo por 10K usuarios |
| --------------- | ---------- | ---------------------- |
| **Lambda**      | $0         | ~$20                   |
| **DynamoDB**    | $0         | ~$50                   |
| **API Gateway** | $0         | ~$35                   |
| **S3**          | $0         | ~$10                   |
| **CloudWatch**  | $0         | ~$15                   |
| **Total**       | $0         | **~$130/mes**          |

### Optimización de Costos

```python
# Compresión de payloads
import gzip
import json

def compress_s3_data(data: dict) -> bytes:
    json_str = json.dumps(data)
    return gzip.compress(json_str.encode('utf-8'))

# Cleanup automático S3
def setup_s3_lifecycle():
    s3_client.put_bucket_lifecycle_configuration(
        Bucket=ANALYTICS_BUCKET,
        LifecycleConfiguration={
            'Rules': [
                {
                    'Id': 'DeleteOldData',
                    'Status': 'Enabled',
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'STANDARD_IA'
                        },
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER'
                        }
                    ]
                }
            ]
        }
    )
```

---

Este documento proporciona una visión técnica completa de la arquitectura implementada, patrones utilizados y consideraciones operacionales para el sistema de bookstore backend.
