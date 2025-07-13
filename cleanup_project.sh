#!/bin/bash

echo "🧹 LIMPIEZA COMPLETA DEL PROYECTO"
echo "================================="
echo ""

echo "📋 ARCHIVOS A ELIMINAR (obsoletos/duplicados):"
echo "=============================================="

# Arrays de archivos a eliminar
declare -a ARCHIVOS_OBSOLETOS=(
    # Tests duplicados/obsoletos
    "activate_purchases_stream.py"
    "activate_streams.py"
    "test_books_final.py"
    "test_completo_final.py"
    "test_final_con_libro.py"
    "test_final_endpoints.py"
    "test_image_updates.py"
    "test_images_complete_final.py"
    "test_images_quick.py"
    "test_lambda.py"
    "test_sistema_completo.py"
    "test_sistema_final.py"
    "test_system_python.py"
    "test-apis.sh"
    "test-images-complete.sh"
    "test_complete_flow.sh"
    
    # Scripts de testing duplicados
    "test_elasticsearch_complete.sh"
    "verify_infrastructure.sh"
    "setup_athena.sh"
    
    # Reportes duplicados/obsoletos
    "REPORTE_COMPLETO_APIS_MEJORADAS.md"
    "REPORTE_FINAL_BOOKS_API.md"
    "reporte_final_actualizado.sh"
    "reporte_final_completo.sh"
    "ENDPOINTS_CORREGIDOS.md"
    "INFORME_ENDPOINTS_Y_FLUJO.md"
    
    # Documentación duplicada
    "API_TESTS.md"
    "GUIA_POSTMAN.md"
    "SISTEMA_COMPLETO.md"
    "DEPLOYMENT_GUIDE.md"
    "DEPLOYMENT_GUIDE_EC2.md"
    "COMANDOS_EC2.md"
    
    # Archivos de configuración obsoletos
    "deploy-manual.sh"
    "diagnose.sh"
    "test-payload.json"
    
    # Collections obsoletas de Postman
    "Bookstore_API_Collection.postman_collection.json"
    "Bookstore_API_CORRECTED.postman_collection.json"
)

echo "📝 Lista de archivos a eliminar:"
for archivo in "${ARCHIVOS_OBSOLETOS[@]}"; do
    if [ -f "$archivo" ]; then
        echo "   ❌ $archivo"
    fi
done

echo ""
echo "🔍 ¿Proceder con la eliminación? (y/N): "
read -r confirmacion

if [[ $confirmacion == "y" || $confirmacion == "Y" ]]; then
    echo ""
    echo "🗑️ ELIMINANDO ARCHIVOS..."
    echo "========================"
    
    for archivo in "${ARCHIVOS_OBSOLETOS[@]}"; do
        if [ -f "$archivo" ]; then
            rm "$archivo"
            echo "   ✅ Eliminado: $archivo"
        fi
    done
    
    echo ""
    echo "🧹 LIMPIANDO DIRECTORIOS VACÍOS..."
    echo "=================================="
    
    # Limpiar node_modules si no se necesita
    if [ -d "node_modules" ]; then
        echo "   🗑️ Eliminando node_modules..."
        rm -rf node_modules
        rm -f package-lock.json
        echo "   ✅ node_modules eliminado"
    fi
    
    # Limpiar .venv si no se necesita
    if [ -d ".venv" ]; then
        echo "   🗑️ Eliminando .venv..."
        rm -rf .venv
        echo "   ✅ .venv eliminado"
    fi
    
    # Limpiar scripts directory si está vacío
    if [ -d "scripts" ] && [ -z "$(ls -A scripts)" ]; then
        rmdir scripts
        echo "   ✅ Directorio scripts vacío eliminado"
    fi
    
    echo ""
    echo "🎯 ARCHIVOS QUE SE MANTIENEN (ESENCIALES):"
    echo "=========================================="
    echo "   ✅ informe_endpoints.md - Documentación completa para frontend"
    echo "   ✅ verificacion_final_completa.sh - Script de verificación final"
    echo "   ✅ test_elasticsearch_final.sh - Test final de ElasticSearch"
    echo "   ✅ contexto.txt - Información del proyecto"
    echo "   ✅ README.md - Documentación principal"
    echo "   ✅ RESUMEN_EJECUTIVO_EVALUACION.md - Evaluación del proyecto"
    echo "   ✅ TECHNICAL_ARCHITECTURE.md - Arquitectura técnica"
    echo "   ✅ serverless.yml - Configuración principal"
    echo "   ✅ services/ - Código fuente de las APIs"
    echo "   ✅ infrastructure/ - Configuración de infraestructura"
    echo "   ✅ config/ - Archivos de configuración"
    echo "   ✅ bucket-policy.json - Política de S3"
    echo "   ✅ cors-config.json - Configuración CORS"
    echo "   ✅ labsuser.pem - Clave EC2"
    echo "   ✅ requirements.txt - Dependencias Python"
    echo "   ✅ package.json - Configuración Node.js"
    
    echo ""
    echo "🏆 LIMPIEZA COMPLETADA"
    echo "====================="
    echo "✅ Archivos obsoletos eliminados"
    echo "✅ Proyecto organizado y limpio"
    echo "✅ Solo archivos esenciales mantenidos"
    
else
    echo ""
    echo "❌ Limpieza cancelada"
fi

echo ""
echo "📊 ESTADO FINAL DEL PROYECTO:"
echo "============================"
ls -la | grep -E "\.(py|sh|md|json|yml)$" | wc -l | sed 's/^/   📁 Total archivos: /'
