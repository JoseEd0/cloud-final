# 🚀 Guía Rápida de Despliegue - Bookstore Backend

## ⚡ COMANDOS RÁPIDOS

### Pre-requisitos de instalación

```bash
# Instalar Node.js, Python, AWS CLI, Docker

# Instalar Serverless Framework
npm install -g serverless

# Verificar instalaciones
node --version    # Debe ser v18+
python --version  # Debe ser 3.9+
aws --version     # AWS CLI v2
docker --version  # Docker Desktop
sls --version     # Serverless v3+
```

### Configurar AWS

```bash
aws configure
# Access Key ID: [tu-access-key-de-aws-academy]
# Secret Access Key: [tu-secret-key]
# Region: us-east-1
# Output: json
```

## 🔄 DESPLIEGUE PASO A PASO

### 1. Clonar y preparar proyecto

```bash
git clone https://github.com/tu-usuario/cloud-final.git
cd cloud-final

# Instalar dependencias principales
npm install

# Instalar dependencias de Books API
cd services/books-api
npm install
cd ../..
```

### 2. Desplegar infraestructura base

```bash
# Desde la raíz del proyecto
sls deploy --stage dev
```

### 3. Desplegar cada microservicio

```bash
# Stream Processors (PRIMERO)
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

### 4. Configurar Elasticsearch

```bash
# Crear red Docker
docker network create elastic-network

# Ejecutar contenedores
docker run -d --name elasticsearch_tenant1 --network elastic-network -p 9201:9200 -e "discovery.type=single-node" -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" -e "xpack.security.enabled=false" elasticsearch:7.17.9

docker run -d --name elasticsearch_tenant2 --network elastic-network -p 9202:9200 -e "discovery.type=single-node" -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" -e "xpack.security.enabled=false" elasticsearch:7.17.9
```

## 🧪 PRUEBAS RÁPIDAS

### Obtener URLs de APIs

```bash
cd services/users-api && sls info --stage dev
cd ../books-api && sls info --stage dev
cd ../purchases-api && sls info --stage dev
```

### Probar registro de usuario

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

### Probar creación de libro

```bash
curl -X POST https://[books-api-url]/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-1234567890",
    "title": "Libro Test",
    "author": "Autor Test",
    "editorial": "Editorial Test",
    "category": "Technology",
    "price": 29.99,
    "stock_quantity": 100,
    "tenant_id": "tenant1"
  }'
```

## 🚨 SOLUCIÓN DE PROBLEMAS

### Error: "Serverless command not found"

```bash
npm install -g serverless
```

### Error: "AWS credentials not configured"

```bash
aws configure
# Reintroduce tus credenciales de AWS Academy
```

### Error: "Python requirements error"

```bash
cd services/users-api
sls plugin install -n serverless-python-requirements
cd ../purchases-api
sls plugin install -n serverless-python-requirements
```

### Error: "Stack already exists"

```bash
# Eliminar y redesplegar
sls remove --stage dev
sls deploy --stage dev
```

### Error: "Docker not running"

```bash
# Iniciar Docker Desktop y ejecutar:
docker version
```

### Error: "Permission denied en scripts"

```bash
# En Git Bash o WSL:
chmod +x scripts/*.sh

# En PowerShell, ejecutar comandos manualmente
```

## 📊 VERIFICACIONES

### Verificar recursos creados

```bash
# Tablas DynamoDB
aws dynamodb list-tables

# Bucket S3
aws s3 ls

# Funciones Lambda
aws lambda list-functions --query 'Functions[?contains(FunctionName, `bookstore`)].FunctionName'

# Contenedores Elasticsearch
docker ps | grep elasticsearch
```

### Ver logs en tiempo real

```bash
# Users API
cd services/users-api && sls logs -f app --stage dev --tail

# Books API
cd services/books-api && sls logs -f app --stage dev --tail

# Purchases API
cd services/purchases-api && sls logs -f app --stage dev --tail
```

## 🔄 COMANDOS DE MANTENIMIENTO

### Redesplegar un servicio específico

```bash
cd services/users-api
sls deploy --stage dev
```

### Eliminar todo el stack

```bash
sls remove --stage dev
```

### Reiniciar Elasticsearch

```bash
docker restart elasticsearch_tenant1
docker restart elasticsearch_tenant2
```

### Actualizar configuración

```bash
# Editar config/dev.yml y redesplegar
sls deploy --stage dev
```

## 📝 NOTAS IMPORTANTES

1. **Orden de despliegue**: Infraestructura → Stream Processors → APIs
2. **Elasticsearch**: Debe configurarse DESPUÉS del despliegue
3. **URLs**: Se generan automáticamente después del despliegue
4. **Logs**: Usar CloudWatch o comando `sls logs`
5. **Errores**: Revisar logs de Lambda en CloudWatch

## 🎯 CHECKLIST DE VERIFICACIÓN

- [ ] AWS CLI configurado con credenciales válidas
- [ ] Serverless Framework instalado globalmente
- [ ] Todas las dependencias instaladas
- [ ] Infraestructura base desplegada
- [ ] Stream Processors desplegados
- [ ] APIs desplegadas (Users, Books, Purchases)
- [ ] Elasticsearch ejecutándose en Docker
- [ ] URLs de APIs obtenidas
- [ ] Pruebas básicas funcionando
- [ ] Logs accesibles

## 🆘 CONTACTO Y SOPORTE

Si encuentras problemas:

1. Revisa los logs con `sls logs -f [function] --stage dev --tail`
2. Verifica AWS CloudWatch para más detalles
3. Consulta la documentación completa en el README.md principal

¡Tu sistema de microservicios está listo para usar! 🚀
