# Bookstore Backend - Guía de Despliegue

Este documento te guiará paso a paso para desplegar el backend completo.

## 🔧 Pre-requisitos

1. **Node.js** (v18 o superior)
2. **Python** (3.9 o superior)
3. **AWS CLI** configurado con tus credenciales
4. **Serverless Framework** instalado globalmente
5. **Docker** para Elasticsearch

## 🚀 Pasos de Instalación

### 1. Instalar Serverless Framework

```bash
npm install -g serverless
```

### 2. Configurar AWS CLI

```bash
aws configure
```

Ingresa tu:

- AWS Access Key ID
- AWS Secret Access Key
- Default region: us-east-1
- Default output format: json

### 3. Instalar dependencias

```bash
# En la raíz del proyecto
npm install

# Instalar dependencias de Node.js para books-api
cd services/books-api
npm install
cd ../..
```

### 4. Desplegar todo el backend

```bash
# Para desarrollo
npm run deploy-dev

# O manualmente
./scripts/deploy-all.sh dev
```

### 5. Configurar Elasticsearch

```bash
npm run setup-elasticsearch

# O manualmente
./scripts/setup-elasticsearch.sh
```

## 📊 Verificación

### Verificar despliegue

```bash
# Ver información de cada servicio
cd services/users-api && sls info --stage dev
cd services/books-api && sls info --stage dev
cd services/purchases-api && sls info --stage dev
```

### Ver logs en tiempo real

```bash
npm run logs-users
npm run logs-books
npm run logs-purchases
```

## 🧪 Pruebas

### 1. Registrar usuario

```bash
curl -X POST [USERS-API-URL]/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456",
    "first_name": "Test",
    "last_name": "User",
    "tenant_id": "tenant1"
  }'
```

### 2. Crear libro

```bash
curl -X POST [BOOKS-API-URL]/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-1234567890",
    "title": "Libro de Prueba",
    "author": "Autor Test",
    "editorial": "Editorial Test",
    "category": "Technology",
    "price": 29.99,
    "stock_quantity": 100,
    "tenant_id": "tenant1"
  }'
```

## 🛠️ Solución de Problemas

### Error de permisos AWS

```bash
# Verificar credenciales
aws sts get-caller-identity
```

### Error en despliegue de Python

```bash
# Instalar serverless-python-requirements
cd services/users-api
sls plugin install -n serverless-python-requirements
```

### Elasticsearch no responde

```bash
# Verificar contenedores
docker ps | grep elasticsearch

# Reiniciar contenedor
docker restart elasticsearch_tenant1
```

## 📱 URLs de las APIs

Después del despliegue, obtendrás URLs similares a:

- **Users API**: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
- **Books API**: https://yyyyy.execute-api.us-east-1.amazonaws.com/dev
- **Purchases API**: https://zzzzz.execute-api.us-east-1.amazonaws.com/dev

## 🔄 Comandos Útiles

```bash
# Redesplegar un servicio específico
cd services/users-api && sls deploy --stage dev

# Ver logs de una función específica
sls logs -f app --stage dev --tail

# Eliminar todo el stack
sls remove --stage dev

# Ver recursos creados
aws dynamodb list-tables
aws s3 ls
```
