#!/bin/bash

# Script para configurar Elasticsearch en EC2 con Docker
# Ejecutar después del despliegue principal

echo "==================================="
echo "CONFIGURANDO ELASTICSEARCH"
echo "==================================="

# Función para verificar comandos
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 no está instalado"
        return 1
    fi
    return 0
}

# Verificar Docker
if ! check_command docker; then
    echo "Instala Docker desde: https://www.docker.com/get-started"
    exit 1
fi

echo "🐳 Docker encontrado"

# Crear red para Elasticsearch
echo "📡 Creando red Docker para Elasticsearch..."
docker network create elastic-network 2>/dev/null || echo "Red ya existe"

# Función para crear contenedor de Elasticsearch para un tenant
create_elasticsearch_container() {
    local tenant_id=$1
    local port=$2
    local container_name="elasticsearch_${tenant_id}"
    
    echo "🔍 Creando Elasticsearch para tenant: $tenant_id en puerto $port"
    
    # Crear directorio de datos
    mkdir -p "./elasticsearch_data/${tenant_id}"
    
    # Ejecutar contenedor
    docker run -d \
        --name $container_name \
        --network elastic-network \
        -p $port:9200 \
        -e "discovery.type=single-node" \
        -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
        -e "xpack.security.enabled=false" \
        -v "$(pwd)/elasticsearch_data/${tenant_id}:/usr/share/elasticsearch/data" \
        elasticsearch:7.17.9
    
    if [ $? -eq 0 ]; then
        echo "✅ Elasticsearch para $tenant_id iniciado en puerto $port"
    else
        echo "❌ Error iniciando Elasticsearch para $tenant_id"
    fi
}

# Crear contenedores para diferentes tenants
echo "🚀 Iniciando contenedores de Elasticsearch..."

# Tenant 1
create_elasticsearch_container "tenant1" 9201

# Tenant 2  
create_elasticsearch_container "tenant2" 9202

# Tenant 3 (ejemplo)
create_elasticsearch_container "tenant3" 9203

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que Elasticsearch esté listo..."
sleep 30

# Verificar que los servicios estén funcionando
echo "🔍 Verificando servicios..."

for port in 9201 9202 9203; do
    echo "Verificando puerto $port..."
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port)
    if [ "$response" = "200" ]; then
        echo "✅ Elasticsearch en puerto $port está funcionando"
    else
        echo "⚠️  Elasticsearch en puerto $port no responde aún"
    fi
done

echo ""
echo "==================================="
echo "✅ ELASTICSEARCH CONFIGURADO"
echo "==================================="
echo ""
echo "📊 Estado de los contenedores:"
docker ps | grep elasticsearch

echo ""
echo "🔗 URLs de Elasticsearch:"
echo "Tenant1: http://localhost:9201"
echo "Tenant2: http://localhost:9202"
echo "Tenant3: http://localhost:9203"

echo ""
echo "📝 Comandos útiles:"
echo "Ver logs: docker logs elasticsearch_tenant1"
echo "Parar: docker stop elasticsearch_tenant1"
echo "Iniciar: docker start elasticsearch_tenant1"
echo "Eliminar: docker rm -f elasticsearch_tenant1"

echo ""
echo "🔧 Para agregar más tenants:"
echo "docker run -d --name elasticsearch_[tenant_id] --network elastic-network -p [puerto]:9200 -e \"discovery.type=single-node\" elasticsearch:7.17.9"
