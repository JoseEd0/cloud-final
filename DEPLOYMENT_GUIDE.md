# Bookstore Backend - Guía de Despliegue

# 🚀 Guía Completa de Despliegue - AWS Academy

## 🎯 INICIO RÁPIDO

### ⚡ Rutina cada vez que trabajas:

1. **AWS Academy** → Start Lab → Copiar credenciales
2. **PowerShell** → Configurar variables de entorno
3. **Verificar** Docker y Elasticsearch
4. **Desplegar** o trabajar en tu código

---

## �️ PRIMERA VEZ: Configuración Inicial

### Pre-requisitos (instalar una sola vez)

#### Windows - PowerShell como Administrador:

```powershell
# 1. Instalar Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# 2. Instalar herramientas
choco install nodejs python awscli git docker-desktop -y
```

#### Verificar instalaciones:

```bash
node --version    # v18+
python --version  # 3.9+
aws --version     # AWS CLI v2
docker --version  # Docker Desktop
```

#### Instalar Serverless Framework:

```bash
npm install -g serverless
sls --version  # 3.x+
```

### Obtener el código

```bash
# Clonar repositorio
git clone https://github.com/JoseEd0/cloud-final.git
cd cloud-final

# Instalar dependencias
npm install
cd services/books-api && npm install && cd ../..
```

---

## 🔄 RUTINA DIARIA

### Paso 1: Configurar AWS Academy (CADA 4 HORAS)

#### 1.1 Iniciar Lab

1. Ir a AWS Academy → Learner Lab
2. Hacer clic en "Start Lab"
3. Esperar círculo VERDE (2-3 minutos)
4. Hacer clic en "AWS Details"

#### 1.2 Copiar credenciales

Verás algo como:

```
aws_access_key_id=ASIA...
aws_secret_access_key=...
aws_session_token=...
```

#### 1.3 Configurar en PowerShell

```powershell
$env:AWS_ACCESS_KEY_ID="ASIA..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_SESSION_TOKEN="..."
$env:AWS_DEFAULT_REGION="us-east-1"

# Verificar
aws sts get-caller-identity
```

**✅ Si ves tu Account ID, ¡estás listo!**

### Paso 2: Verificar Docker

```powershell
# Ver si Docker está ejecutándose
docker ps

# Ver contenedores Elasticsearch
docker ps | grep elasticsearch

# Si no están corriendo, iniciar
docker start elasticsearch_tenant1
docker start elasticsearch_tenant2
```

---

## 🚀 DESPLIEGUE COMPLETO

### Comandos de despliegue (en orden)

```bash
# 1. Ir al proyecto
cd cloud-final

# 2. Infraestructura base
sls deploy --stage dev

# 3. Stream Processors
cd services/stream-processors
sls deploy --stage dev
cd ../..

# 4. Users API
cd services/users-api
sls deploy --stage dev
cd ../..

# 5. Books API
cd services/books-api
sls deploy --stage dev
cd ../..

# 6. Purchases API
cd services/purchases-api
sls deploy --stage dev
cd ../..
```

**⏱️ Tiempo total: 10-15 minutos**

### Configurar Elasticsearch (solo primera vez)

```bash
# Crear red Docker
docker network create elastic-network

# Contenedor tenant1
docker run -d --name elasticsearch_tenant1 \
  --network elastic-network \
  -p 9201:9200 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -e "xpack.security.enabled=false" \
  elasticsearch:7.17.9

# Contenedor tenant2
docker run -d --name elasticsearch_tenant2 \
  --network elastic-network \
  -p 9202:9200 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -e "xpack.security.enabled=false" \
  elasticsearch:7.17.9
```

---

## 🧪 VERIFICACIÓN Y PRUEBAS

### Obtener URLs de APIs

```bash
cd services/users-api && sls info --stage dev
cd ../books-api && sls info --stage dev
cd ../purchases-api && sls info --stage dev
cd ../..
```

### Probar APIs

```bash
# Registrar usuario
curl -X POST https://TU-USERS-API-URL/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456",
    "first_name": "Test",
    "last_name": "User",
    "tenant_id": "tenant1"
  }'

# Crear libro
curl -X POST https://TU-BOOKS-API-URL/api/v1/books \
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

### Verificar recursos AWS

```bash
aws dynamodb list-tables
aws s3 ls
aws lambda list-functions --query 'Functions[?contains(FunctionName, `bookstore`)].FunctionName'
docker ps | grep elasticsearch
```

---

## 🛠️ COMANDOS ÚTILES DIARIOS

### Redesplegar un servicio

```bash
cd services/users-api
sls deploy --stage dev
```

### Ver logs en tiempo real

```bash
cd services/users-api
sls logs -f app --stage dev --tail
```

### Reiniciar Elasticsearch

```bash
docker restart elasticsearch_tenant1
docker restart elasticsearch_tenant2
```

### Actualizar credenciales (cada 4 horas)

```powershell
# Reiniciar Lab en AWS Academy → Copiar nuevas credenciales
$env:AWS_ACCESS_KEY_ID="ASIA..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_SESSION_TOKEN="..."

# Verificar
aws sts get-caller-identity
```

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### "Access Denied"

**Causa**: Lab no iniciado o credenciales expiradas
**Solución**:

1. AWS Academy → Start Lab
2. Reconfigurar credenciales en PowerShell
3. Verificar con `aws sts get-caller-identity`

### "Port already in use" (Elasticsearch)

```bash
docker stop elasticsearch_tenant1 elasticsearch_tenant2
docker rm elasticsearch_tenant1 elasticsearch_tenant2
# Volver a crear los contenedores
```

### "Stack already exists"

```bash
sls remove --stage dev
sls deploy --stage dev
```

### "Cannot find module"

```bash
npm install
cd services/books-api && npm install && cd ../..
```

### "Docker not running"

- Abrir Docker Desktop
- Ejecutar `docker version` para verificar

---

## 📋 CHECKLIST RÁPIDO

### Pre-requisitos (solo primera vez):

- [ ] Node.js, Python, AWS CLI, Docker instalados
- [ ] Serverless Framework instalado globalmente
- [ ] Proyecto clonado y dependencias instaladas

### Cada sesión de trabajo:

- [ ] AWS Academy Lab iniciado (círculo verde)
- [ ] Credenciales configuradas en PowerShell
- [ ] `aws sts get-caller-identity` funciona
- [ ] Docker Desktop ejecutándose
- [ ] Elasticsearch containers corriendo

### Para desplegar:

- [ ] Infraestructura base desplegada
- [ ] Stream processors desplegados
- [ ] APIs desplegadas (users, books, purchases)
- [ ] URLs obtenidas y funcionando

---

## 📝 RECORDATORIOS IMPORTANTES

1. **Lab AWS Academy**: Debe estar iniciado antes de cada despliegue
2. **Credenciales**: Expiran cada 4 horas automáticamente
3. **Orden de despliegue**: Infraestructura → Stream Processors → APIs
4. **Docker Desktop**: Debe ejecutarse para Elasticsearch
5. **Elasticsearch**: Se ejecuta localmente en tu computadora
6. **Todo desde local**: No necesitas EC2, todo desde tu Windows

---

## 🎯 RESUMEN ULTRA-RÁPIDO

**Rutina diaria:**

1. AWS Academy → Start Lab → Credenciales → PowerShell
2. `docker ps` → Verificar Elasticsearch
3. `cd cloud-final` → Trabajar en tu código
4. `sls deploy --stage dev` → Desplegar cambios

**Si algo falla:**

1. Verificar credenciales AWS
2. Verificar Docker Desktop
3. Revisar logs con `sls logs -f app --stage dev --tail`

¡Tu flujo de trabajo está optimizado! 🚀
