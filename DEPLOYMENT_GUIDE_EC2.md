# 🚀 Guía Completa de Despliegue - AWS Academy con EC2 Cloud9

## 🎯 INICIO RÁPIDO

### ⚡ Rutina cada vez que trabajas:

1. **AWS Academy** → Start Lab → Conectar a EC2
2. **EC2 Cloud9** → Terminal Ubuntu
3. **Configurar credenciales** → Verificar conexión
4. **Desplegar** desde terminal

---

## 🖥️ CONFIGURACIÓN EC2 CLOUD9

### Paso 1: Crear instancia EC2 en AWS Academy

#### 1.1 Iniciar Lab en AWS Academy

1. Ir a AWS Academy → Learner Lab
2. Hacer clic en "Start Lab"
3. Esperar círculo VERDE (2-3 minutos)
4. Hacer clic en "AWS"

#### 1.2 Crear instancia EC2

```bash
# En la consola de AWS Academy:
1. Ir a EC2 → Launch Instance
2. Nombre: "cloud9-desarrollo"
3. AMI: "Cloud9Ubuntu-2023-*" (buscar "cloud9")
4. Instance type: t3.medium (mínimo recomendado)
5. Key pair: Crear nueva o usar existente
6. Security group: Permitir SSH (puerto 22) desde tu IP
7. Storage: 20 GB gp3
8. Launch Instance
```

#### 1.3 Conectar por SSH

```bash
# Obtener IP pública de la instancia
# Conectar desde tu terminal local:
ssh -i tu-key.pem ubuntu@[IP-PUBLICA-EC2]

# O usar EC2 Instance Connect desde la consola
```

### Paso 2: Configurar ambiente de desarrollo en Ubuntu

#### 2.1 Actualizar sistema

```bash
# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar herramientas básicas
sudo apt install -y curl wget git unzip
```

#### 2.2 Instalar Node.js

```bash
# Instalar Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verificar instalación
node --version  # Debe mostrar v18.x.x
npm --version
```

#### 2.3 Instalar Python 3.9+

```bash
# Python ya viene instalado en Ubuntu, verificar versión
python3 --version  # Debe ser 3.9+

# Instalar pip y venv
sudo apt install -y python3-pip python3-venv

# Verificar pip
pip3 --version
```

#### 2.4 Instalar AWS CLI v2

```bash
# Descargar e instalar AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verificar instalación
aws --version  # Debe mostrar aws-cli/2.x.x
```

#### 2.5 Instalar Docker

```bash
# Instalar Docker
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# IMPORTANTE: Logout y login para aplicar cambios
exit
# Volver a conectar por SSH

# Verificar Docker
docker --version
docker ps  # Debe funcionar sin sudo
```

#### 2.6 Instalar Serverless Framework

```bash
# Instalar Serverless globalmente
sudo npm install -g serverless

# Verificar instalación
serverless --version  # Debe mostrar 3.x.x
```

### Paso 3: Obtener el código del proyecto

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

### Paso 1: Configurar credenciales AWS (CADA 4 HORAS)

#### 1.1 Obtener credenciales de AWS Academy

1. Ir a AWS Academy → Learner Lab
2. Hacer clic en "Start Lab"
3. Esperar círculo VERDE
4. Hacer clic en "AWS Details"
5. Copiar las 3 credenciales

#### 1.2 Configurar en EC2 Ubuntu

```bash
# En tu terminal EC2, configurar credenciales:
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="us-east-1"

# Verificar que funciona
aws sts get-caller-identity
```

**✅ Si ves tu Account ID, ¡estás listo!**

#### 1.3 Hacer persistentes las credenciales (opcional)

```bash
# Crear archivo de credenciales
mkdir -p ~/.aws
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = ASIA...
aws_secret_access_key = ...
aws_session_token = ...
EOF

cat > ~/.aws/config << EOF
[default]
region = us-east-1
output = json
EOF
```

### Paso 2: Verificar Docker y servicios

```bash
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
cd ~/cloud-final

# 2. Infraestructura base
serverless deploy --stage dev

# 3. Stream Processors
cd services/stream-processors
serverless deploy --stage dev
cd ../..

# 4. Users API
cd services/users-api
serverless deploy --stage dev
cd ../..

# 5. Books API
cd services/books-api
serverless deploy --stage dev
cd ../..

# 6. Purchases API
cd services/purchases-api
serverless deploy --stage dev
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

# Verificar que funcionan (esperar 2-3 minutos)
curl http://localhost:9201
curl http://localhost:9202
```

---

## 🧪 VERIFICACIÓN Y PRUEBAS

### Obtener URLs de APIs

```bash
cd services/users-api && serverless info --stage dev
cd ../books-api && serverless info --stage dev
cd ../purchases-api && serverless info --stage dev
cd ../..
```

### Probar APIs

```bash
# Registrar usuario (reemplazar con TU URL real)
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
serverless deploy --stage dev
```

### Ver logs en tiempo real

```bash
cd services/users-api
serverless logs -f app --stage dev --tail
```

### Reiniciar Elasticsearch

```bash
docker restart elasticsearch_tenant1
docker restart elasticsearch_tenant2
```

### Actualizar credenciales (cada 4 horas)

```bash
# Renovar credenciales de AWS Academy → Copiar nuevas credenciales
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# Verificar
aws sts get-caller-identity
```

### Mantener la sesión EC2 activa

```bash
# Usar screen para sesiones persistentes
sudo apt install screen

# Crear sesión
screen -S desarrollo

# Separarse de la sesión: Ctrl+A, D
# Volver a la sesión:
screen -r desarrollo
```

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### "Access Denied"

**Causa**: Lab no iniciado o credenciales expiradas
**Solución**:

1. AWS Academy → Start Lab
2. Reconfigurar credenciales en EC2
3. Verificar con `aws sts get-caller-identity`

### "Port already in use" (Elasticsearch)

```bash
docker stop elasticsearch_tenant1 elasticsearch_tenant2
docker rm elasticsearch_tenant1 elasticsearch_tenant2
# Volver a crear los contenedores
```

### "Stack already exists"

```bash
serverless remove --stage dev
serverless deploy --stage dev
```

### "Cannot find module"

```bash
npm install
cd services/books-api && npm install && cd ../..
```

### "Docker permission denied"

```bash
# Asegurarse de estar en el grupo docker
sudo usermod -aG docker $USER
# Logout y login de nuevo
```

### "EC2 instance stopped"

```bash
# En AWS Console:
1. EC2 → Instances
2. Seleccionar tu instancia
3. Instance State → Start
4. Esperar que esté "running"
5. Conectar por SSH con la nueva IP
```

---

## 📋 CHECKLIST RÁPIDO

### Configuración inicial (solo primera vez):

- [ ] Instancia EC2 creada con AMI Cloud9Ubuntu
- [ ] Conectado por SSH a la instancia
- [ ] Node.js, Python, AWS CLI, Docker instalados
- [ ] Serverless Framework instalado globalmente
- [ ] Proyecto clonado y dependencias instaladas

### Cada sesión de trabajo:

- [ ] AWS Academy Lab iniciado (círculo verde)
- [ ] Conectado a EC2 por SSH
- [ ] Credenciales configuradas en terminal
- [ ] `aws sts get-caller-identity` funciona
- [ ] Docker ejecutándose
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
3. **EC2**: La instancia se puede parar automáticamente, verificar estado
4. **Orden de despliegue**: Infraestructura → Stream Processors → APIs
5. **Docker**: Debe ejecutarse en la EC2
6. **Elasticsearch**: Se ejecuta en contenedores Docker en EC2
7. **Persistencia**: Usar `screen` para mantener sesiones activas

---

## 🔧 COMANDOS DE MANTENIMIENTO EC2

### Verificar estado de servicios

```bash
# Estado de Docker
sudo systemctl status docker

# Procesos en ejecución
ps aux | grep node
ps aux | grep python

# Uso de memoria y CPU
top
htop  # sudo apt install htop
```

### Limpiar espacio en disco

```bash
# Limpiar cache de npm
npm cache clean --force

# Limpiar cache de pip
pip3 cache purge

# Limpiar contenedores Docker no utilizados
docker system prune

# Ver uso de disco
df -h
du -sh ~/cloud-final
```

### Backup de configuración

```bash
# Hacer backup de credenciales
cp ~/.aws/credentials ~/.aws/credentials.backup

# Backup del proyecto
tar -czf cloud-final-backup.tar.gz ~/cloud-final
```

---

## 🎯 RESUMEN ULTRA-RÁPIDO

**Configuración inicial:**

1. AWS Academy → EC2 → Crear instancia Cloud9Ubuntu
2. SSH a EC2 → Instalar herramientas → Clonar proyecto

**Rutina diaria:**

1. AWS Academy → Start Lab → SSH a EC2
2. Configurar credenciales → Verificar Docker
3. `cd ~/cloud-final` → Desplegar cambios
4. `serverless deploy --stage dev` → ¡Listo!

**Si algo falla:**

1. Verificar credenciales AWS
2. Verificar que EC2 esté running
3. Verificar Docker: `docker ps`
4. Revisar logs: `serverless logs -f app --stage dev --tail`

¡Tu entorno de desarrollo en EC2 está optimizado! 🚀
