#!/bin/bash

# Script para desplegar todos los servicios del backend
# Uso: ./deploy-all.sh [dev|test|prod]

STAGE=${1:-dev}

echo "==================================="
echo "DESPLEGANDO BACKEND BOOKSTORE"
echo "Stage: $STAGE"
echo "==================================="

# Función para verificar si el comando anterior fue exitoso
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 - Completado exitosamente"
    else
        echo "❌ $1 - Error en el despliegue"
        exit 1
    fi
}

# Verificar que Serverless Framework esté instalado
if ! command -v sls &> /dev/null; then
    echo "❌ Serverless Framework no está instalado"
    echo "Instálalo con: npm install -g serverless"
    exit 1
fi

# Verificar que AWS CLI esté configurado
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI no está configurado o las credenciales no son válidas"
    echo "Configura AWS CLI con: aws configure"
    exit 1
fi

echo "🚀 Iniciando despliegue..."

# 1. Desplegar infraestructura base (DynamoDB, S3, Glue)
echo ""
echo "📊 Desplegando infraestructura base..."
sls deploy --stage $STAGE
check_status "Infraestructura base"

# 2. Desplegar Stream Processors
echo ""
echo "⚡ Desplegando Stream Processors..."
cd services/stream-processors
sls deploy --stage $STAGE
check_status "Stream Processors"
cd ../..

# 3. Desplegar API de Usuarios
echo ""
echo "👥 Desplegando API de Usuarios..."
cd services/users-api
sls deploy --stage $STAGE
check_status "API de Usuarios"
cd ../..

# 4. Desplegar API de Libros
echo ""
echo "📚 Desplegando API de Libros..."
cd services/books-api
npm install
sls deploy --stage $STAGE
check_status "API de Libros"
cd ../..

# 5. Desplegar API de Compras
echo ""
echo "🛒 Desplegando API de Compras..."
cd services/purchases-api
sls deploy --stage $STAGE
check_status "API de Compras"
cd ../..

echo ""
echo "==================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "==================================="
echo ""
echo "🔗 URLs de las APIs:"
echo ""

# Obtener URLs de las APIs desplegadas
echo "Users API:"
cd services/users-api
sls info --stage $STAGE | grep -A 20 "endpoints:" | grep "https://"
cd ../..

echo ""
echo "Books API:"
cd services/books-api
sls info --stage $STAGE | grep -A 20 "endpoints:" | grep "https://"
cd ../..

echo ""
echo "Purchases API:"
cd services/purchases-api
sls info --stage $STAGE | grep -A 20 "endpoints:" | grep "https://"
cd ../..

echo ""
echo "📝 Próximos pasos:"
echo "1. Configurar Elasticsearch en EC2"
echo "2. Probar las APIs con las URLs mostradas arriba"
echo "3. Revisar los logs en CloudWatch"
echo ""
echo "Para ver logs en tiempo real:"
echo "sls logs -f [function-name] --stage $STAGE --tail"
