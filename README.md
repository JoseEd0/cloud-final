# cloud-final

# DOCUMENTACIÓN TÉCNICA - BACKEND & INGESTA DE DATOS

## Proyecto Final Cloud Computing - Sistema de Libros

---

## 🏗️ ARQUITECTURA GENERAL

### Stack Tecnológico

- **Framework**: Serverless Framework (3 stages: dev/test/prod)
- **Backend APIs**: Python (Flask) + Node.js (Express)
- **Base de Datos**: DynamoDB con Global Secondary Indexes
- **Ingesta**: DynamoDB Streams + AWS Lambda
- **Búsqueda**: ElasticSearch en EC2 con Docker (multi-tenant)
- **Analytics**: S3 + AWS Glue + Amazon Athena

---

## 📊 ESTRUCTURA DE BASE DE DATOS

### Tabla: users

```
PK: tenant_id#user_id
SK: USER#email
Atributos:
- user_id (UUID)
- tenant_id (string)
- email (string)
- password_hash (string)
- first_name, last_name (string)
- created_at, updated_at (timestamp)
- is_active (boolean)
- preferences (map): {categories: [], language: 'es'}
```

### Tabla: books

```
PK: tenant_id#book_id
SK: BOOK#isbn
GSI1: tenant_id#category
GSI2: tenant_id#author
Atributos:
- book_id (UUID)
- tenant_id (string)
- isbn (string)
- title (string)
- author (string)
- editorial (string)
- category (string)
- price (decimal)
- description (text)
- cover_image_url (string)
- stock_quantity (number)
- publication_year (number)
- language (string)
- pages (number)
- rating (decimal 0-5)
- created_at, updated_at (timestamp)
- is_active (boolean)
```

### Tabla: user_favorites

```
PK: tenant_id#user_id
SK: FAVORITE#book_id
Atributos:
- user_id (UUID)
- tenant_id (string)
- book_id (UUID)
- added_at (timestamp)
```

### Tabla: user_wishlist

```
PK: tenant_id#user_id
SK: WISHLIST#book_id
Atributos:
- user_id (UUID)
- tenant_id (string)
- book_id (UUID)
- added_at (timestamp)
- priority (number 1-5)
```

### Tabla: shopping_cart

```
PK: tenant_id#user_id
SK: CART#book_id
Atributos:
- user_id (UUID)
- tenant_id (string)
- book_id (UUID)
- quantity (number)
- added_at (timestamp)
- updated_at (timestamp)
```

### Tabla: purchases

```
PK: tenant_id#user_id
SK: PURCHASE#purchase_id
GSI1: tenant_id#created_at (para analytics)
Atributos:
- purchase_id (UUID)
- tenant_id (string)
- user_id (UUID)
- total_amount (decimal)
- status (string): pending/completed/cancelled
- payment_method (string)
- shipping_address (map)
- created_at, updated_at (timestamp)
- items (list): [{book_id, quantity, unit_price, subtotal}]
```

---

## 🔗 MICROSERVICIO 1: API USUARIOS (Python)

### Endpoints Principales

```
POST   /api/v1/users/register
POST   /api/v1/users/login
POST   /api/v1/users/validate-token
GET    /api/v1/users/profile
PUT    /api/v1/users/profile
PUT    /api/v1/users/preferences
GET    /api/v1/users/favorites?page=1&limit=20
POST   /api/v1/users/favorites/{book_id}
DELETE /api/v1/users/favorites/{book_id}
GET    /api/v1/users/wishlist?page=1&limit=20
POST   /api/v1/users/wishlist/{book_id}
DELETE /api/v1/users/wishlist/{book_id}
```

### Funcionalidades Avanzadas

- **JWT Tokens** con expiración de 1 hora
- **Middleware de autenticación** para todas las rutas protegidas
- **Gestión de favoritos** con paginación
- **Lista de deseos** con sistema de prioridades
- **Preferencias de usuario** (categorías favoritas, idioma)
- **Rate limiting** por tenant

---

## 📚 MICROSERVICIO 2: API PRODUCTOS (Node.js)

### Endpoints Principales

```
GET    /api/v1/books?page=1&limit=20&category=&author=&sort=
POST   /api/v1/books
GET    /api/v1/books/{book_id}
PUT    /api/v1/books/{book_id}
DELETE /api/v1/books/{book_id}
GET    /api/v1/books/search?q=&fuzzy=true&page=1&limit=20
GET    /api/v1/books/by-isbn/{isbn}
GET    /api/v1/books/categories
GET    /api/v1/books/authors?page=1&limit=50
GET    /api/v1/books/recommendations/{user_id}
```

### Sistema de Paginación Avanzado

```javascript
// Respuesta estándar con paginación
{
  "data": [...],
  "pagination": {
    "current_page": 1,
    "total_pages": 15,
    "total_items": 298,
    "items_per_page": 20,
    "has_next": true,
    "has_previous": false,
    "next_cursor": "eyJ0ZW5hbnRfaWQi...",
    "previous_cursor": null
  }
}
```

### Funcionalidades Avanzadas

- **Búsqueda multi-criterio** (título, autor, categoría, descripción)
- **Filtros avanzados** (precio, año, rating, stock)
- **Sistema de recomendaciones** basado en historial y favoritos
- **Gestión de stock** en tiempo real
- **Categorización inteligente** con subcategorías

---

## 🛒 MICROSERVICIO 3: API COMPRAS (Python)

### Endpoints Principales

```
GET    /api/v1/cart
POST   /api/v1/cart/add
PUT    /api/v1/cart/update/{book_id}
DELETE /api/v1/cart/remove/{book_id}
DELETE /api/v1/cart/clear
POST   /api/v1/purchases/checkout
GET    /api/v1/purchases?page=1&limit=10&status=
GET    /api/v1/purchases/{purchase_id}
GET    /api/v1/purchases/analytics/summary
```

### Funcionalidades del Carrito

- **Persistencia del carrito** por usuario
- **Validación de stock** en tiempo real
- **Cálculo automático** de totales e impuestos
- **Proceso de checkout** completo
- **Historial detallado** de compras con paginación

---

## ⚡ INGESTA EN TIEMPO REAL

### DynamoDB Streams Configuración

```yaml
# serverless.yml
resources:
  Resources:
    BooksTable:
      Type: AWS::DynamoDB::Table
      Properties:
        StreamSpecification:
          StreamViewType: NEW_AND_OLD_IMAGES
    PurchasesTable:
      Type: AWS::DynamoDB::Table
      Properties:
        StreamSpecification:
          StreamViewType: NEW_AND_OLD_IMAGES
```

### Lambda 1: Books Stream Processor

**Trigger**: DynamoDB Stream de tabla `books`
**Función**: Sincronizar con ElasticSearch en tiempo real

```
Eventos capturados:
- INSERT: Nuevo libro → Indexar en ElasticSearch
- MODIFY: Libro modificado → Actualizar índice
- REMOVE: Libro eliminado → Eliminar del índice
```

### Lambda 2: Purchases Stream Processor

**Trigger**: DynamoDB Stream de tabla `purchases`
**Función**: Exportar datos para analytics

```
Eventos capturados:
- INSERT: Nueva compra → Generar archivo JSON en S3
- MODIFY: Compra actualizada → Actualizar archivo en S3
```

### Estructura ElasticSearch (EC2 + Docker)

```
Contenedores por tenant:
- elasticsearch_tenant1:9200
- elasticsearch_tenant2:9200
- elasticsearch_tenantN:9200

Volúmenes persistentes:
- /opt/elasticsearch/tenant1/data
- /opt/elasticsearch/tenant2/data
```

### Índice ElasticSearch para Libros

```json
{
  "mappings": {
    "properties": {
      "book_id": { "type": "keyword" },
      "tenant_id": { "type": "keyword" },
      "title": { "type": "text", "analyzer": "spanish" },
      "author": { "type": "text", "analyzer": "spanish" },
      "description": { "type": "text", "analyzer": "spanish" },
      "category": { "type": "keyword" },
      "price": { "type": "double" },
      "rating": { "type": "double" },
      "suggest": {
        "type": "completion",
        "analyzer": "simple"
      }
    }
  }
}
```

---

## 📈 ANALYTICS CON AWS GLUE + ATHENA

### Estructura de Datos en S3

```
s3://bookstore-analytics/
├── tenant1/
│   ├── purchases/year=2025/month=07/day=12/
│   └── user_behavior/year=2025/month=07/day=12/
├── tenant2/
│   └── purchases/year=2025/month=07/day=12/
```

### Queries SQL de Ejemplo en Athena

```sql
-- 1. Top libros más vendidos por mes
SELECT book_id, title, COUNT(*) as total_sales
FROM purchases_table
WHERE year = '2025' AND month = '07'
GROUP BY book_id, title
ORDER BY total_sales DESC
LIMIT 10;

-- 2. Ingresos por categoría
SELECT category, SUM(total_amount) as revenue
FROM purchases_table p
JOIN books_table b ON p.book_id = b.book_id
WHERE p.year = '2025'
GROUP BY category;

-- 3. Análisis de comportamiento de usuarios
SELECT user_id, COUNT(*) as purchase_count, AVG(total_amount) as avg_order
FROM purchases_table
WHERE year = '2025'
GROUP BY user_id;
```

---

## 🔒 SEGURIDAD Y MULTI-TENANCY

### Middleware de Autenticación

- **JWT Validation** en todas las APIs protegidas
- **Tenant Isolation** a nivel de base de datos
- **Rate Limiting** por tenant y endpoint
- **CORS** configurado para dominios específicos

### Variables de Entorno por Stage

```
dev:
  DYNAMODB_REGION: us-east-1
  JWT_SECRET: dev-secret-key
  ELASTICSEARCH_HOST: dev-elasticsearch.com

test:
  DYNAMODB_REGION: us-east-1
  JWT_SECRET: test-secret-key
  ELASTICSEARCH_HOST: test-elasticsearch.com

prod:
  DYNAMODB_REGION: us-east-1
  JWT_SECRET: ${ssm:/prod/jwt-secret}
  ELASTICSEARCH_HOST: prod-elasticsearch.com
```

---

## 🚀 DESPLIEGUE SERVERLESS

### Estructura de Proyecto

```
bookstore-backend/
├── services/
│   ├── users-api/          # Python Flask
│   ├── books-api/          # Node.js Express
│   ├── purchases-api/      # Python Flask
│   └── stream-processors/  # Lambda functions
├── infrastructure/
│   ├── dynamodb.yml
│   ├── elasticsearch-ec2.yml
│   └── s3-glue-athena.yml
└── scripts/
    ├── deploy-all.sh
    └── setup-elasticsearch.sh
```

### Comandos de Despliegue

```bash
# Despliegue por stages
sls deploy --stage dev
sls deploy --stage test
sls deploy --stage prod

# Despliegue específico por servicio
sls deploy --stage dev --service users-api
sls deploy --stage dev --service books-api
```

Esta documentación cubre la arquitectura completa del backend y la ingesta de datos, enfocándose en crear un sistema robusto, escalable y con funcionalidades avanzadas que van más allá de un CRUD básico.
