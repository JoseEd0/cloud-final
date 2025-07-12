import json
import os
import logging
from datetime import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection
from decimal import Decimal

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuración Elasticsearch
es_host = os.environ.get("ELASTICSEARCH_HOST", "http://localhost:9200")
es_client = None


def get_elasticsearch_client(tenant_id):
    """Obtener cliente de Elasticsearch para un tenant específico"""
    global es_client
    try:
        if not es_client:
            # En un ambiente real, cada tenant tendría su propio índice/cluster
            es_client = Elasticsearch(
                hosts=[es_host],
                connection_class=RequestsHttpConnection,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True,
            )
        return es_client
    except Exception as e:
        logger.error(f"Error conectando a Elasticsearch: {str(e)}")
        return None


def decimal_to_float(obj):
    """Convertir Decimal a float para Elasticsearch"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj


def process_book_insert(record):
    """Procesar inserción de libro nuevo"""
    try:
        book_data = record["dynamodb"]["NewImage"]

        # Extraer datos del libro
        book_doc = {
            "book_id": book_data.get("book_id", {}).get("S", ""),
            "tenant_id": book_data.get("tenant_id", {}).get("S", ""),
            "isbn": book_data.get("isbn", {}).get("S", ""),
            "title": book_data.get("title", {}).get("S", ""),
            "author": book_data.get("author", {}).get("S", ""),
            "editorial": book_data.get("editorial", {}).get("S", ""),
            "category": book_data.get("category", {}).get("S", ""),
            "price": float(book_data.get("price", {}).get("N", "0")),
            "description": book_data.get("description", {}).get("S", ""),
            "cover_image_url": book_data.get("cover_image_url", {}).get("S", ""),
            "stock_quantity": int(book_data.get("stock_quantity", {}).get("N", "0")),
            "publication_year": int(
                book_data.get("publication_year", {}).get("N", "0")
            ),
            "language": book_data.get("language", {}).get("S", "es"),
            "pages": int(book_data.get("pages", {}).get("N", "0")),
            "rating": float(book_data.get("rating", {}).get("N", "0")),
            "created_at": book_data.get("created_at", {}).get("S", ""),
            "updated_at": book_data.get("updated_at", {}).get("S", ""),
            "is_active": book_data.get("is_active", {}).get("BOOL", True),
            "suggest": {
                "input": [
                    book_data.get("title", {}).get("S", ""),
                    book_data.get("author", {}).get("S", ""),
                    book_data.get("category", {}).get("S", ""),
                ]
            },
        }

        tenant_id = book_doc["tenant_id"]
        es_client = get_elasticsearch_client(tenant_id)

        if es_client:
            # Crear índice si no existe
            index_name = f"books_{tenant_id}"

            if not es_client.indices.exists(index=index_name):
                # Configuración del índice
                index_config = {
                    "mappings": {
                        "properties": {
                            "book_id": {"type": "keyword"},
                            "tenant_id": {"type": "keyword"},
                            "title": {"type": "text", "analyzer": "spanish"},
                            "author": {"type": "text", "analyzer": "spanish"},
                            "description": {"type": "text", "analyzer": "spanish"},
                            "category": {"type": "keyword"},
                            "price": {"type": "double"},
                            "rating": {"type": "double"},
                            "publication_year": {"type": "integer"},
                            "stock_quantity": {"type": "integer"},
                            "suggest": {"type": "completion", "analyzer": "simple"},
                        }
                    },
                    "settings": {
                        "analysis": {"analyzer": {"spanish": {"type": "spanish"}}}
                    },
                }

                es_client.indices.create(index=index_name, body=index_config)
                logger.info(f"Índice creado: {index_name}")

            # Indexar documento
            es_client.index(index=index_name, id=book_doc["book_id"], body=book_doc)

            logger.info(f"Libro indexado: {book_doc['book_id']} en {index_name}")
        else:
            logger.warning("No se pudo conectar a Elasticsearch, saltando indexación")

    except Exception as e:
        logger.error(f"Error procesando inserción de libro: {str(e)}")


def process_book_modify(record):
    """Procesar modificación de libro"""
    try:
        book_data = record["dynamodb"]["NewImage"]
        tenant_id = book_data.get("tenant_id", {}).get("S", "")
        book_id = book_data.get("book_id", {}).get("S", "")

        es_client = get_elasticsearch_client(tenant_id)

        if es_client:
            index_name = f"books_{tenant_id}"

            # Actualizar documento
            book_doc = {
                "book_id": book_id,
                "tenant_id": tenant_id,
                "isbn": book_data.get("isbn", {}).get("S", ""),
                "title": book_data.get("title", {}).get("S", ""),
                "author": book_data.get("author", {}).get("S", ""),
                "editorial": book_data.get("editorial", {}).get("S", ""),
                "category": book_data.get("category", {}).get("S", ""),
                "price": float(book_data.get("price", {}).get("N", "0")),
                "description": book_data.get("description", {}).get("S", ""),
                "cover_image_url": book_data.get("cover_image_url", {}).get("S", ""),
                "stock_quantity": int(
                    book_data.get("stock_quantity", {}).get("N", "0")
                ),
                "publication_year": int(
                    book_data.get("publication_year", {}).get("N", "0")
                ),
                "language": book_data.get("language", {}).get("S", "es"),
                "pages": int(book_data.get("pages", {}).get("N", "0")),
                "rating": float(book_data.get("rating", {}).get("N", "0")),
                "created_at": book_data.get("created_at", {}).get("S", ""),
                "updated_at": book_data.get("updated_at", {}).get("S", ""),
                "is_active": book_data.get("is_active", {}).get("BOOL", True),
                "suggest": {
                    "input": [
                        book_data.get("title", {}).get("S", ""),
                        book_data.get("author", {}).get("S", ""),
                        book_data.get("category", {}).get("S", ""),
                    ]
                },
            }

            es_client.index(index=index_name, id=book_id, body=book_doc)

            logger.info(f"Libro actualizado en ES: {book_id}")
        else:
            logger.warning("No se pudo conectar a Elasticsearch")

    except Exception as e:
        logger.error(f"Error procesando modificación de libro: {str(e)}")


def process_book_remove(record):
    """Procesar eliminación de libro"""
    try:
        book_data = record["dynamodb"]["OldImage"]
        tenant_id = book_data.get("tenant_id", {}).get("S", "")
        book_id = book_data.get("book_id", {}).get("S", "")

        es_client = get_elasticsearch_client(tenant_id)

        if es_client:
            index_name = f"books_{tenant_id}"

            try:
                es_client.delete(index=index_name, id=book_id)
                logger.info(f"Libro eliminado de ES: {book_id}")
            except Exception as e:
                if "not_found" not in str(e):
                    raise e
                logger.info(f"Libro no encontrado en ES (ya eliminado): {book_id}")
        else:
            logger.warning("No se pudo conectar a Elasticsearch")

    except Exception as e:
        logger.error(f"Error procesando eliminación de libro: {str(e)}")


def handler(event, context):
    """Handler principal para procesar streams de DynamoDB"""
    logger.info(f"Procesando {len(event['Records'])} registros del stream")

    for record in event["Records"]:
        event_name = record["eventName"]

        try:
            if event_name == "INSERT":
                process_book_insert(record)
            elif event_name == "MODIFY":
                process_book_modify(record)
            elif event_name == "REMOVE":
                process_book_remove(record)
            else:
                logger.warning(f"Evento no manejado: {event_name}")

        except Exception as e:
            logger.error(f"Error procesando registro {event_name}: {str(e)}")
            # Continuar con el siguiente registro en lugar de fallar completamente
            continue

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f'Procesados {len(event["Records"])} registros',
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }
