import json
import os
import boto3
import logging
from datetime import datetime
from decimal import Decimal

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuración S3
s3_client = boto3.client("s3")
ANALYTICS_BUCKET = os.environ.get("ANALYTICS_BUCKET", "bookstore-analytics-dev")


def decimal_to_float(obj):
    """Convertir Decimal a float para JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj


def process_purchase_insert(record):
    """Procesar nueva compra para analytics"""
    try:
        purchase_data = record["dynamodb"]["NewImage"]

        # Extraer datos de la compra
        purchase_doc = {
            "purchase_id": purchase_data.get("purchase_id", {}).get("S", ""),
            "tenant_id": purchase_data.get("tenant_id", {}).get("S", ""),
            "user_id": purchase_data.get("user_id", {}).get("S", ""),
            "total_amount": float(purchase_data.get("total_amount", {}).get("N", "0")),
            "status": purchase_data.get("status", {}).get("S", ""),
            "payment_method": purchase_data.get("payment_method", {}).get("S", ""),
            "created_at": purchase_data.get("created_at", {}).get("S", ""),
            "updated_at": purchase_data.get("updated_at", {}).get("S", ""),
            "items": [],
        }

        # Procesar items si existen
        if "items" in purchase_data:
            items_list = purchase_data["items"].get("L", [])
            for item in items_list:
                item_data = item.get("M", {})
                purchase_doc["items"].append(
                    {
                        "book_id": item_data.get("book_id", {}).get("S", ""),
                        "quantity": int(item_data.get("quantity", {}).get("N", "0")),
                        "unit_price": float(
                            item_data.get("unit_price", {}).get("N", "0")
                        ),
                        "subtotal": float(item_data.get("subtotal", {}).get("N", "0")),
                        "title": item_data.get("title", {}).get("S", ""),
                        "author": item_data.get("author", {}).get("S", ""),
                    }
                )

        # Crear estructura de particiones por fecha
        created_at = datetime.fromisoformat(
            purchase_doc["created_at"].replace("Z", "+00:00")
        )
        year = created_at.strftime("%Y")
        month = created_at.strftime("%m")
        day = created_at.strftime("%d")

        # Construir clave S3
        s3_key = f"{purchase_doc['tenant_id']}/purchases/year={year}/month={month}/day={day}/{purchase_doc['purchase_id']}.json"

        # Subir a S3
        s3_client.put_object(
            Bucket=ANALYTICS_BUCKET,
            Key=s3_key,
            Body=json.dumps(purchase_doc, default=str),
            ContentType="application/json",
        )

        logger.info(f"Compra exportada a S3: {s3_key}")

        # También crear un registro agregado para analytics rápidos
        daily_summary_key = f"{purchase_doc['tenant_id']}/daily_summary/year={year}/month={month}/day={day}/summary.json"

        try:
            # Intentar obtener resumen existente
            response = s3_client.get_object(
                Bucket=ANALYTICS_BUCKET, Key=daily_summary_key
            )
            daily_summary = json.loads(response["Body"].read())
        except s3_client.exceptions.NoSuchKey:
            # Crear nuevo resumen
            daily_summary = {
                "date": f"{year}-{month}-{day}",
                "tenant_id": purchase_doc["tenant_id"],
                "total_purchases": 0,
                "total_revenue": 0.0,
                "total_items_sold": 0,
                "categories": {},
                "payment_methods": {},
            }

        # Actualizar resumen
        daily_summary["total_purchases"] += 1
        daily_summary["total_revenue"] += purchase_doc["total_amount"]
        daily_summary["total_items_sold"] += sum(
            item["quantity"] for item in purchase_doc["items"]
        )

        # Contar método de pago
        payment_method = purchase_doc["payment_method"]
        daily_summary["payment_methods"][payment_method] = (
            daily_summary["payment_methods"].get(payment_method, 0) + 1
        )

        # Guardar resumen actualizado
        s3_client.put_object(
            Bucket=ANALYTICS_BUCKET,
            Key=daily_summary_key,
            Body=json.dumps(daily_summary, default=str),
            ContentType="application/json",
        )

        logger.info(f"Resumen diario actualizado: {daily_summary_key}")

    except Exception as e:
        logger.error(f"Error procesando inserción de compra: {str(e)}")


def process_purchase_modify(record):
    """Procesar modificación de compra"""
    try:
        purchase_data = record["dynamodb"]["NewImage"]
        purchase_id = purchase_data.get("purchase_id", {}).get("S", "")
        tenant_id = purchase_data.get("tenant_id", {}).get("S", "")

        # Similar al insert, pero actualizando el archivo existente
        purchase_doc = {
            "purchase_id": purchase_id,
            "tenant_id": tenant_id,
            "user_id": purchase_data.get("user_id", {}).get("S", ""),
            "total_amount": float(purchase_data.get("total_amount", {}).get("N", "0")),
            "status": purchase_data.get("status", {}).get("S", ""),
            "payment_method": purchase_data.get("payment_method", {}).get("S", ""),
            "created_at": purchase_data.get("created_at", {}).get("S", ""),
            "updated_at": purchase_data.get("updated_at", {}).get("S", ""),
            "items": [],
        }

        # Procesar items si existen
        if "items" in purchase_data:
            items_list = purchase_data["items"].get("L", [])
            for item in items_list:
                item_data = item.get("M", {})
                purchase_doc["items"].append(
                    {
                        "book_id": item_data.get("book_id", {}).get("S", ""),
                        "quantity": int(item_data.get("quantity", {}).get("N", "0")),
                        "unit_price": float(
                            item_data.get("unit_price", {}).get("N", "0")
                        ),
                        "subtotal": float(item_data.get("subtotal", {}).get("N", "0")),
                        "title": item_data.get("title", {}).get("S", ""),
                        "author": item_data.get("author", {}).get("S", ""),
                    }
                )

        # Crear estructura de particiones por fecha
        created_at = datetime.fromisoformat(
            purchase_doc["created_at"].replace("Z", "+00:00")
        )
        year = created_at.strftime("%Y")
        month = created_at.strftime("%m")
        day = created_at.strftime("%d")

        # Actualizar archivo en S3
        s3_key = f"{tenant_id}/purchases/year={year}/month={month}/day={day}/{purchase_id}.json"

        s3_client.put_object(
            Bucket=ANALYTICS_BUCKET,
            Key=s3_key,
            Body=json.dumps(purchase_doc, default=str),
            ContentType="application/json",
        )

        logger.info(f"Compra actualizada en S3: {s3_key}")

    except Exception as e:
        logger.error(f"Error procesando modificación de compra: {str(e)}")


def handler(event, context):
    """Handler principal para procesar streams de compras"""
    logger.info(f"Procesando {len(event['Records'])} registros del stream de compras")

    for record in event["Records"]:
        event_name = record["eventName"]

        try:
            if event_name == "INSERT":
                process_purchase_insert(record)
            elif event_name == "MODIFY":
                process_purchase_modify(record)
            elif event_name == "REMOVE":
                # Para compras, generalmente no eliminamos, solo cambiamos el estado
                logger.info(f"Compra eliminada (soft delete): {record}")
            else:
                logger.warning(f"Evento no manejado: {event_name}")

        except Exception as e:
            logger.error(f"Error procesando registro {event_name}: {str(e)}")
            continue

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f'Procesados {len(event["Records"])} registros de compras',
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }
