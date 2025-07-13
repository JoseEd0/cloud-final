import json
import os
import uuid
import hashlib
import time
from datetime import datetime
from decimal import Decimal
import boto3


def lambda_handler(event, context):
    """
    Handler para AWS Lambda que maneja requests HTTP para compras
    Usa el esquema de DynamoDB con pk/sk
    """

    # Configuración básica
    dynamodb = boto3.resource(
        "dynamodb", region_name=os.environ.get("DYNAMODB_REGION", "us-east-1")
    )
    cart_table = dynamodb.Table(
        os.environ.get("CART_TABLE", "bookstore-shopping-cart-dev")
    )
    purchases_table = dynamodb.Table(
        os.environ.get("PURCHASES_TABLE", "bookstore-purchases-dev")
    )
    books_table = dynamodb.Table(os.environ.get("BOOKS_TABLE", "bookstore-books-dev"))

    # Obtener información del request
    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    body = event.get("body", "{}")

    # Parsear body si existe
    try:
        if body:
            request_body = json.loads(body)
        else:
            request_body = {}
    except:
        request_body = {}

    # Headers de respuesta básicos
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT,DELETE",
    }

    # Función para extraer user_id del token simple
    def extract_user_from_token(auth_header):
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        if not token.startswith("simple_token_"):
            return None

        try:
            token_parts = token.replace("simple_token_", "").split("_")
            if len(token_parts) < 2:
                return None
            return {"user_id": token_parts[0], "tenant_id": token_parts[1]}
        except:
            return None

    try:
        # Endpoint básico de salud
        if path == "/" or path == "/health":
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(
                    {
                        "message": "Purchases API is running",
                        "status": "healthy",
                        "timestamp": datetime.utcnow().isoformat(),
                        "method": method,
                        "path": path,
                    }
                ),
            }

        # Endpoint para obtener carrito
        elif path == "/cart" and method == "GET":
            auth_header = event.get("headers", {}).get(
                "authorization", ""
            ) or event.get("headers", {}).get("Authorization", "")
            user = extract_user_from_token(auth_header)

            if not user:
                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps({"error": "Unauthorized"}),
                }

            try:
                # Buscar items del carrito
                response = cart_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq(
                        f"CART#{user['tenant_id']}#{user['user_id']}"
                    )
                )

                cart_items = []
                total = 0

                for item in response["Items"]:
                    if item["sk"].startswith("ITEM#"):
                        cart_items.append(
                            {
                                "cart_item_id": item.get("cart_item_id"),
                                "book_id": item.get("book_id"),
                                "title": item.get("title", "Unknown"),
                                "price": float(item.get("price", 0)),
                                "quantity": int(item.get("quantity", 1)),
                            }
                        )
                        total += float(item.get("price", 0)) * int(
                            item.get("quantity", 1)
                        )

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "cart_items": cart_items,
                            "total": total,
                            "item_count": len(cart_items),
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # Endpoint para agregar al carrito
        elif path == "/cart" and method == "POST":
            auth_header = event.get("headers", {}).get(
                "authorization", ""
            ) or event.get("headers", {}).get("Authorization", "")
            user = extract_user_from_token(auth_header)

            if not user:
                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps({"error": "Unauthorized"}),
                }

            book_id = request_body.get("book_id")
            quantity = request_body.get("quantity", 1)

            if not book_id:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "book_id is required"}),
                }

            try:
                # Buscar información del libro
                book_response = books_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq(
                        f"BOOK#{user['tenant_id']}#{book_id}"
                    )
                )

                if not book_response["Items"]:
                    return {
                        "statusCode": 404,
                        "headers": headers,
                        "body": json.dumps({"error": "Book not found"}),
                    }

                book = book_response["Items"][0]
                cart_item_id = str(uuid.uuid4())

                # Agregar al carrito
                cart_item = {
                    "pk": f"CART#{user['tenant_id']}#{user['user_id']}",
                    "sk": f"ITEM#{cart_item_id}",
                    "cart_item_id": cart_item_id,
                    "book_id": book_id,
                    "title": book.get("title", "Unknown"),
                    "price": book.get("price", 0),
                    "quantity": quantity,
                    "added_at": datetime.utcnow().isoformat(),
                }

                cart_table.put_item(Item=cart_item)

                return {
                    "statusCode": 201,
                    "headers": headers,
                    "body": json.dumps(
                        {"message": "Item added to cart", "cart_item_id": cart_item_id}
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # Endpoint para obtener compras del usuario
        elif path == "/purchases" and method == "GET":
            auth_header = event.get("headers", {}).get(
                "authorization", ""
            ) or event.get("headers", {}).get("Authorization", "")
            user = extract_user_from_token(auth_header)

            if not user:
                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps({"error": "Unauthorized"}),
                }

            try:
                # Buscar compras del usuario
                response = purchases_table.query(
                    IndexName="GSI1",
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("gsi1pk").eq(
                        f"USER#{user['tenant_id']}#{user['user_id']}"
                    ),
                )

                purchases = []
                for item in response["Items"]:
                    purchases.append(
                        {
                            "purchase_id": item.get("purchase_id"),
                            "total": float(item.get("total", 0)),
                            "status": item.get("status", "pending"),
                            "created_at": item.get("created_at"),
                            "items_count": item.get("items_count", 0),
                        }
                    )

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {"purchases": purchases, "total_purchases": len(purchases)}
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # Endpoint no encontrado
        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps(
                    {
                        "error": "Endpoint not found",
                        "path": path,
                        "method": method,
                        "available_endpoints": ["/", "/health", "/cart", "/purchases"],
                    }
                ),
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal server error", "details": str(e)}),
        }


# Alias para compatibilidad
handler = lambda_handler
