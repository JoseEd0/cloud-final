# 📚 Bookstore Backend - Sistema Completo de Microservicios

[![AWS](https://img.shields.io/badge/AWS-Cloud-orange)](https://aws.amazon.com/)
[![Serverless](https://img.shields.io/badge/Serverless-Framework-red)](https://www.serverless.com/)
[![Python](https://img.shields.io/badge/Python-3.9-blue)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18-green)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)](https://fastapi.tiangolo.com/)
[![DynamoDB](https://img.shields.io/badge/DynamoDB-NoSQL-purple)](https://aws.amazon.com/dynamodb/)

## 🏗️ Descripción del Proyecto

Sistema completo de backend para una librería online construido con arquitectura de microservicios serverless en AWS. Incluye gestión de usuarios, catálogo de libros, sistema de compras, ingesta de datos en tiempo real y analytics avanzados.

### ✨ Características Principales

- **🔐 Autenticación JWT** con multi-tenancy
- **📖 Gestión completa de libros** con búsqueda avanzada
- **🛒 Sistema de carrito y compras**
- **⭐ Favoritos y lista de deseos**
- **📊 Analytics en tiempo real** con S3 + Glue + Athena
- **🔍 Búsqueda semántica** con Elasticsearch
- **⚡ Ingesta en tiempo real** con DynamoDB Streams
- **🏢 Multi-tenant** por diseño

---

## 🏛️ Arquitectura del Sistema

### Stack Tecnológico

| Componente        | Tecnología                | Propósito                 |
| ----------------- | ------------------------- | ------------------------- |
| **APIs**          | FastAPI + Node.js Express | Microservicios REST       |
| **Base de Datos** | DynamoDB                  | NoSQL escalable           |
| **Búsqueda**      | Elasticsearch             | Búsqueda semántica        |
| **Analytics**     | S3 + Glue + Athena        | Data Lake y consultas SQL |
| **Streaming**     | DynamoDB Streams + Lambda | Ingesta tiempo real       |
| **Autenticación** | JWT                       | Seguridad stateless       |
| **Orquestación**  | Serverless Framework      | IaC y despliegue          |

### Diagrama de Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Users API     │    │   Books API     │    │ Purchases API   │
│   (FastAPI)     │    │   (Node.js)     │    │   (FastAPI)     │
│   Port: 443     │    │   Port: 443     │    │   Port: 443     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │       DynamoDB            │
                    │  ┌─────────────────────┐  │
                    │  │ Tables:             │  │
                    │  │ • users             │  │
                    │  │ • books             │  │
                    │  │ • user_favorites    │  │
                    │  │ • user_wishlist     │  │
                    │  │ • shopping_cart     │  │
                    │  │ • purchases         │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │ Streams
                    ┌─────────────┴─────────────┐
                    │     Lambda Processors     │
                    │ ┌─────────┐ ┌───────────┐ │
                    │ │ Books   │ │ Purchases │ │
                    │ │ Stream  │ │ Stream    │ │
                    │ └─────────┘ └───────────┘ │
                    └─────┬─────────────┬───────┘
                          │             │
              ┌───────────┴──┐     ┌────┴─────┐
              │ Elasticsearch│     │    S3    │
              │ Multi-tenant │     │Analytics │
              │    Docker    │     │  Bucket  │
              └──────────────┘     └──────────┘
```

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

## 📊 Modelo de Datos

### Estructura DynamoDB

El sistema utiliza DynamoDB con patrones de acceso optimizados y Global Secondary Indexes (GSI).

#### Tabla: users

```
PK: tenant_id#user_id
SK: USER#email
GSI1: tenant_id#EMAIL -> email
```

#### Tabla: books

```
PK: tenant_id#book_id
SK: BOOK#isbn
GSI1: tenant_id#CATEGORY -> category#book_id
GSI2: tenant_id#AUTHOR -> author#book_id
```

#### Tabla: purchases

```
PK: tenant_id#user_id
SK: PURCHASE#purchase_id
GSI1: tenant_id#PURCHASES -> created_at
```

### Particionado y Multi-tenancy

Cada tabla utiliza `tenant_id` como prefijo de la partition key, garantizando:

- **Aislamiento completo** entre tenants
- **Escalabilidad horizontal** automática
- **Consultas eficientes** por tenant

---

## 🚀 Microservicios

### 1. Users API (FastAPI)

**Función**: Gestión de usuarios, autenticación y preferencias

**Endpoints principales**:

- `POST /api/v1/users/register` - Registro de usuarios
- `POST /api/v1/users/login` - Autenticación
- `GET /api/v1/users/profile` - Perfil de usuario
- `GET /api/v1/users/favorites` - Gestión de favoritos
- `GET /api/v1/users/wishlist` - Lista de deseos

**Características**:

- JWT con expiración configurable
- Hashing seguro de contraseñas con bcrypt
- Middleware de autenticación
- Validación con Pydantic

### 2. Books API (Node.js + Express)

**Función**: Catálogo de libros y búsqueda

**Endpoints principales**:

- `GET /api/v1/books` - Listar libros con filtros
- `POST /api/v1/books` - Crear libro
- `GET /api/v1/books/search` - Búsqueda avanzada
- `GET /api/v1/books/categories` - Categorías disponibles
- `GET /api/v1/books/recommendations/:user_id` - Recomendaciones

**Características**:

- Paginación inteligente con cursors
- Búsqueda fuzzy con Elasticsearch
- Filtros por categoría, autor, precio
- Sistema de recomendaciones

### 3. Purchases API (FastAPI)

**Función**: Carrito de compras y gestión de pedidos

**Endpoints principales**:

- `GET /api/v1/cart` - Ver carrito
- `POST /api/v1/cart/add` - Agregar al carrito
- `POST /api/v1/purchases/checkout` - Procesar compra
- `GET /api/v1/purchases` - Historial de compras
- `GET /api/v1/purchases/analytics/summary` - Analytics de usuario

**Características**:

- Validación de stock en tiempo real
- Proceso de checkout transaccional
- Cálculo automático de totales
- Persistencia del carrito por usuario

---

## ⚡ Ingesta en Tiempo Real

### DynamoDB Streams + Lambda

El sistema captura cambios en DynamoDB y los procesa automáticamente:

#### Books Stream Processor

- **Trigger**: Cambios en tabla `books`
- **Función**: Sincronizar con Elasticsearch
- **Eventos**: INSERT, MODIFY, REMOVE

#### Purchases Stream Processor

- **Trigger**: Cambios en tabla `purchases`
- **Función**: Exportar a S3 para analytics
- **Particionado**: `tenant_id/purchases/year=YYYY/month=MM/day=DD/`

### Elasticsearch Multi-tenant

Cada tenant tiene su propio índice de Elasticsearch:

```bash
# Contenedores separados por tenant
elasticsearch_tenant1:9201
elasticsearch_tenant2:9202
elasticsearch_tenantN:920N
```

**Configuración del índice**:

```json
{
  "mappings": {
    "properties": {
      "title": { "type": "text", "analyzer": "spanish" },
      "author": { "type": "text", "analyzer": "spanish" },
      "description": { "type": "text", "analyzer": "spanish" },
      "suggest": { "type": "completion" }
    }
  }
}
```

---

## 📈 Analytics y Data Lake

### S3 + Glue + Athena

Los datos de compras se exportan automáticamente a S3 en formato particionado:

```
s3://bookstore-analytics-{stage}/
├── tenant1/
│   ├── purchases/year=2025/month=07/day=12/
│   └── daily_summary/year=2025/month=07/day=12/
├── tenant2/
│   └── purchases/year=2025/month=07/day=12/
```

### Consultas SQL de Ejemplo

```sql
-- Top libros más vendidos
SELECT book_id, title, COUNT(*) as sales
FROM purchases_table
WHERE year = '2025' AND month = '07'
GROUP BY book_id, title
ORDER BY sales DESC;

-- Ingresos por categoría
SELECT category, SUM(total_amount) as revenue
FROM purchases_table p
JOIN books_table b ON p.book_id = b.book_id
GROUP BY category;
```

---

## 🛠️ Instalación y Despliegue

### Pre-requisitos

- **Node.js** v18+
- **Python** 3.9+
- **AWS CLI** configurado
- **Docker** para Elasticsearch
- **Serverless Framework** v3+

### 1. Clonar y Configurar

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/cloud-final.git
cd cloud-final

# Instalar dependencias globales
npm install -g serverless
npm install

# Instalar dependencias de Node.js
cd services/books-api
npm install
cd ../..
```

### 2. Configurar AWS

```bash
# Configurar credenciales AWS Academy
aws configure
```

**Introduce**:

- Access Key ID: `[tu-access-key]`
- Secret Access Key: `[tu-secret-key]`
- Region: `us-east-1`
- Output: `json`

### 3. Desplegar Infraestructura

```bash
# Desplegar DynamoDB, S3 y recursos base
sls deploy --stage dev
```

### 4. Desplegar Microservicios

```bash
# Stream Processors
cd services/stream-processors
sls deploy --stage dev
cd ../..

# Users API
cd services/users-api
sls deploy --stage dev
cd ../..

# Books API
cd services/books-api
sls deploy --stage dev
cd ../..

# Purchases API
cd services/purchases-api
sls deploy --stage dev
cd ../..
```

### 5. Configurar Elasticsearch

```bash
# Crear red Docker
docker network create elastic-network

# Ejecutar contenedores
docker run -d --name elasticsearch_tenant1 \
  --network elastic-network \
  -p 9201:9200 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  elasticsearch:7.17.9

docker run -d --name elasticsearch_tenant2 \
  --network elastic-network \
  -p 9202:9200 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  elasticsearch:7.17.9
```

---

## 🧪 Pruebas y Validación

### Obtener URLs de APIs

```bash
# Ver información de despliegue
cd services/users-api && sls info --stage dev
cd services/books-api && sls info --stage dev
cd services/purchases-api && sls info --stage dev
```

### Pruebas de API

#### 1. Registrar Usuario

```bash
curl -X POST https://[users-api-url]/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456",
    "first_name": "Test",
    "last_name": "User",
    "tenant_id": "tenant1"
  }'
```

#### 2. Login y Obtener Token

```bash
curl -X POST https://[users-api-url]/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456",
    "tenant_id": "tenant1"
  }'
```

#### 3. Crear Libro

```bash
curl -X POST https://[books-api-url]/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-1234567890",
    "title": "Clean Code",
    "author": "Robert Martin",
    "editorial": "Prentice Hall",
    "category": "Programming",
    "price": 49.99,
    "stock_quantity": 50,
    "tenant_id": "tenant1"
  }'
```

#### 4. Buscar Libros

```bash
curl "https://[books-api-url]/api/v1/books/search?q=clean&tenant_id=tenant1"
```

#### 5. Agregar al Carrito

```bash
curl -X POST https://[purchases-api-url]/api/v1/cart/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [token]" \
  -d '{
    "book_id": "[book-id]",
    "quantity": 1
  }'
```

---

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real

```bash
# Logs de Users API
cd services/users-api
sls logs -f app --stage dev --tail

# Logs de Books API
cd services/books-api
sls logs -f app --stage dev --tail

# Logs de Stream Processors
cd services/stream-processors
sls logs -f booksStreamProcessor --stage dev --tail
```

### Verificar Recursos AWS

```bash
# Verificar tablas DynamoDB
aws dynamodb list-tables

# Verificar bucket S3
aws s3 ls

# Verificar funciones Lambda
aws lambda list-functions --query 'Functions[?contains(FunctionName, `bookstore`)].FunctionName'
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno por Stage

Los archivos de configuración están en `config/`:

- `dev.yml` - Desarrollo
- `test.yml` - Testing
- `prod.yml` - Producción

### Escalamiento

El sistema está diseñado para escalar automáticamente:

- **DynamoDB**: On-demand billing
- **Lambda**: Concurrencia automática
- **Elasticsearch**: Escalamiento horizontal con más contenedores

### Seguridad

- **JWT tokens** con expiración configurable
- **Tenant isolation** a nivel de datos
- **CORS** configurado por environment
- **Rate limiting** por tenant
- **Encryption** en tránsito y reposo

---

## 📁 Estructura del Proyecto

```
cloud-final/
├── config/                     # Configuración por environment
│   ├── dev.yml
│   ├── test.yml
│   └── prod.yml
├── infrastructure/             # Infraestructura como código
│   ├── dynamodb.yml
│   └── s3-glue-athena.yml
├── services/                   # Microservicios
│   ├── users-api/             # API de usuarios (FastAPI)
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── serverless.yml
│   ├── books-api/             # API de libros (Node.js)
│   │   ├── app.js
│   │   ├── package.json
│   │   └── serverless.yml
│   ├── purchases-api/         # API de compras (FastAPI)
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── serverless.yml
│   └── stream-processors/     # Procesadores de streams
│       ├── books_stream_processor.py
│       ├── purchases_stream_processor.py
│       └── serverless.yml
├── scripts/                   # Scripts de automatización
│   ├── deploy-all.sh
│   └── setup-elasticsearch.sh
├── serverless.yml            # Configuración principal
├── package.json             # Dependencias Node.js
└── README.md               # Esta documentación
```

---

## 🚨 Solución de Problemas

### Error: "Serverless command not found"

```bash
npm install -g serverless
```

### Error: "AWS credentials not configured"

```bash
aws configure
```

### Error: "Python requirements not found"

```bash
cd services/users-api
sls plugin install -n serverless-python-requirements
```

### Error: "DynamoDB table already exists"

```bash
# Eliminar stack y redesplegar
sls remove --stage dev
sls deploy --stage dev
```

### Error: "Elasticsearch connection failed"

```bash
# Verificar contenedores Docker
docker ps | grep elasticsearch

# Reiniciar contenedor
docker restart elasticsearch_tenant1
```

---

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

---

## 📄 Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

---

## 👨‍💻 Autor

**Tu Nombre**

- GitHub: [@tu-usuario](https://github.com/tu-usuario)
- LinkedIn: [Tu Perfil](https://linkedin.com/in/tu-perfil)

---

## 🙏 Agradecimientos

- AWS Academy por proporcionar el entorno de desarrollo
- Serverless Framework por simplificar el despliegue
- La comunidad open source por las herramientas utilizadas

---

⭐ **Si este proyecto te fue útil, ¡no olvides darle una estrella!** ⭐
