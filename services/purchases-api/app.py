import json
import os
import uuid
import hashlib
import time
from datetime import datetime, timedelta
from decimal import Decimal
import boto3


def lambda_handler(event, context):
    """
    Handler mejorado para AWS Lambda que mane                # Verificar stock_quantity disponible
                if book.get('stock_quantity_quantity', 0) < quantity: requests HTTP para compras
    Incluye funcionalidades completas para carrito, checkout, órdenes y analytics
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
    query_params = event.get("queryStringParameters") or {}

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

    # Función para crear respuesta de paginación
    def create_pagination_response(items, page, limit, total_items):
        total_pages = (total_items + limit - 1) // limit
        has_next = page < total_pages
        has_previous = page > 1

        return {
            "items": items,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "items_per_page": limit,
                "has_next": has_next,
                "has_previous": has_previous,
            },
        }

    # Función para obtener información del libro
    def get_book_info(tenant_id, book_id):
        try:
            response = books_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr("tenant_id").eq(
                    tenant_id
                )
                & boto3.dynamodb.conditions.Attr("book_id").eq(book_id)
                & boto3.dynamodb.conditions.Attr("is_active").eq(True)
            )
            return response["Items"][0] if response["Items"] else None
        except:
            return None

    try:
        # ===========================================
        # HEALTH CHECK ENDPOINT
        # ===========================================
        if path == "/" or path == "/health":
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(
                    {
                        "message": "Purchases API v2.0.0 - Enhanced",
                        "status": "healthy",
                        "timestamp": datetime.utcnow().isoformat(),
                        "method": method,
                        "path": path,
                        "features": [
                            "Shopping Cart Management",
                            "Order Processing & Checkout",
                            "Purchase History & Analytics",
                            "Inventory Management",
                            "Payment Processing Integration",
                        ],
                    }
                ),
            }

        # ===========================================
        # SHOPPING CART ENDPOINTS
        # ===========================================

        # GET CART
        elif path == "/api/v1/cart" and method == "GET":
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
                response = cart_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq(
                        f"CART#{user['tenant_id']}#{user['user_id']}"
                    )
                )

                cart_items = []
                total = 0

                for item in response["Items"]:
                    if item["sk"].startswith("ITEM#"):
                        item_total = float(item.get("price", 0)) * int(
                            item.get("quantity", 1)
                        )
                        cart_items.append(
                            {
                                "cart_item_id": item.get("cart_item_id"),
                                "book_id": item.get("book_id"),
                                "title": item.get("title", "Unknown"),
                                "author": item.get("author", "Unknown"),
                                "price": float(item.get("price", 0)),
                                "quantity": int(item.get("quantity", 1)),
                                "subtotal": item_total,
                                "added_at": item.get("added_at"),
                                "isbn": item.get("isbn", ""),
                                "image_url": item.get("image_url", ""),
                            }
                        )
                        total += item_total

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "cart_items": cart_items,
                            "summary": {
                                "subtotal": total,
                                "tax": round(total * 0.08, 2),  # 8% tax
                                "shipping": (
                                    5.99 if total < 50 else 0
                                ),  # Free shipping over $50
                                "total": round(
                                    total
                                    + (total * 0.08)
                                    + (5.99 if total < 50 else 0),
                                    2,
                                ),
                            },
                            "item_count": len(cart_items),
                            "updated_at": datetime.utcnow().isoformat(),
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ADD TO CART
        elif path == "/api/v1/cart" and method == "POST":
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
            quantity = int(request_body.get("quantity", 1))

            if not book_id or quantity <= 0:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": "Valid book_id and quantity are required"}
                    ),
                }

            try:
                # Obtener información del libro
                book = get_book_info(user["tenant_id"], book_id)

                if not book:
                    return {
                        "statusCode": 404,
                        "headers": headers,
                        "body": json.dumps(
                            {"error": "Book not found or not available"}
                        ),
                    }

                # Verificar stock_quantity disponible
                if book.get("stock_quantity", 0) < quantity:
                    return {
                        "statusCode": 400,
                        "headers": headers,
                        "body": json.dumps(
                            {
                                "error": "Insufficient stock_quantity",
                                "available_stock_quantity": book.get(
                                    "stock_quantity", 0
                                ),
                            }
                        ),
                    }

                # Verificar si el item ya existe en el carrito
                existing_response = cart_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq(
                        f"CART#{user['tenant_id']}#{user['user_id']}"
                    ),
                    FilterExpression=boto3.dynamodb.conditions.Attr("book_id").eq(
                        book_id
                    ),
                )

                if existing_response["Items"]:
                    # Actualizar cantidad existente
                    existing_item = existing_response["Items"][0]
                    new_quantity = int(existing_item.get("quantity", 0)) + quantity

                    if book.get("stock_quantity", 0) < new_quantity:
                        return {
                            "statusCode": 400,
                            "headers": headers,
                            "body": json.dumps(
                                {
                                    "error": "Insufficient stock_quantity for total quantity",
                                    "available_stock_quantity": book.get(
                                        "stock_quantity", 0
                                    ),
                                    "current_in_cart": existing_item.get("quantity", 0),
                                }
                            ),
                        }

                    cart_table.update_item(
                        Key={"pk": existing_item["pk"], "sk": existing_item["sk"]},
                        UpdateExpression="SET quantity = :quantity, updated_at = :updated_at",
                        ExpressionAttributeValues={
                            ":quantity": new_quantity,
                            ":updated_at": datetime.utcnow().isoformat(),
                        },
                    )

                    return {
                        "statusCode": 200,
                        "headers": headers,
                        "body": json.dumps(
                            {
                                "message": "Cart item updated",
                                "cart_item_id": existing_item["cart_item_id"],
                                "new_quantity": new_quantity,
                            }
                        ),
                    }
                else:
                    # Crear nuevo item en el carrito
                    cart_item_id = str(uuid.uuid4())

                    cart_item = {
                        "pk": f"CART#{user['tenant_id']}#{user['user_id']}",
                        "sk": f"ITEM#{cart_item_id}",
                        "cart_item_id": cart_item_id,
                        "book_id": book_id,
                        "title": book.get("title", "Unknown"),
                        "author": book.get("author", "Unknown"),
                        "price": book.get("price", 0),
                        "quantity": quantity,
                        "isbn": book.get("isbn", ""),
                        "image_url": book.get("image_url", ""),
                        "added_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }

                    cart_table.put_item(Item=cart_item)

                    return {
                        "statusCode": 201,
                        "headers": headers,
                        "body": json.dumps(
                            {
                                "message": "Item added to cart",
                                "cart_item_id": cart_item_id,
                                "quantity": quantity,
                            }
                        ),
                    }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # UPDATE CART ITEM
        elif path.startswith("/api/v1/cart/") and method == "PUT":
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

            cart_item_id = path.split("/")[-1]
            quantity = int(request_body.get("quantity", 1))

            if quantity <= 0:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Quantity must be greater than 0"}),
                }

            try:
                # Obtener item del carrito
                response = cart_table.get_item(
                    Key={
                        "pk": f"CART#{user['tenant_id']}#{user['user_id']}",
                        "sk": f"ITEM#{cart_item_id}",
                    }
                )

                if "Item" not in response:
                    return {
                        "statusCode": 404,
                        "headers": headers,
                        "body": json.dumps({"error": "Cart item not found"}),
                    }

                cart_item = response["Item"]

                # Verificar stock_quantity disponible
                book = get_book_info(user["tenant_id"], cart_item["book_id"])
                if not book or book.get("stock_quantity", 0) < quantity:
                    return {
                        "statusCode": 400,
                        "headers": headers,
                        "body": json.dumps(
                            {
                                "error": "Insufficient stock_quantity",
                                "available_stock_quantity": (
                                    book.get("stock_quantity", 0) if book else 0
                                ),
                            }
                        ),
                    }

                # Actualizar cantidad
                cart_table.update_item(
                    Key={"pk": cart_item["pk"], "sk": cart_item["sk"]},
                    UpdateExpression="SET quantity = :quantity, updated_at = :updated_at",
                    ExpressionAttributeValues={
                        ":quantity": quantity,
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "Cart item updated",
                            "cart_item_id": cart_item_id,
                            "new_quantity": quantity,
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # REMOVE FROM CART
        elif path.startswith("/api/v1/cart/") and method == "DELETE":
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

            cart_item_id = path.split("/")[-1]

            try:
                cart_table.delete_item(
                    Key={
                        "pk": f"CART#{user['tenant_id']}#{user['user_id']}",
                        "sk": f"ITEM#{cart_item_id}",
                    }
                )

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps({"message": "Item removed from cart"}),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # CLEAR CART
        elif path == "/api/v1/cart/clear" and method == "POST":
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
                # Obtener todos los items del carrito
                response = cart_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq(
                        f"CART#{user['tenant_id']}#{user['user_id']}"
                    )
                )

                # Eliminar cada item
                with cart_table.batch_writer() as batch:
                    for item in response["Items"]:
                        batch.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "Cart cleared successfully",
                            "items_removed": len(response["Items"]),
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # CHECKOUT & ORDERS
        # ===========================================

        # CHECKOUT PROCESS
        elif path == "/api/v1/checkout" and method == "POST":
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

            payment_method = request_body.get("payment_method", "credit_card")
            shipping_address = request_body.get("shipping_address", {})
            billing_address = request_body.get("billing_address", {})

            if not shipping_address or not billing_address:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": "Shipping and billing addresses are required"}
                    ),
                }

            try:
                # Obtener items del carrito
                cart_response = cart_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq(
                        f"CART#{user['tenant_id']}#{user['user_id']}"
                    )
                )

                if not cart_response["Items"]:
                    return {
                        "statusCode": 400,
                        "headers": headers,
                        "body": json.dumps({"error": "Cart is empty"}),
                    }

                # Validar inventario y calcular total
                order_items = []
                subtotal = 0

                for cart_item in cart_response["Items"]:
                    if cart_item["sk"].startswith("ITEM#"):
                        book = get_book_info(user["tenant_id"], cart_item["book_id"])

                        if not book:
                            return {
                                "statusCode": 400,
                                "headers": headers,
                                "body": json.dumps(
                                    {
                                        "error": f'Book {cart_item.get("title", "Unknown")} is no longer available'
                                    }
                                ),
                            }

                        quantity = int(cart_item.get("quantity", 1))
                        if book.get("stock_quantity", 0) < quantity:
                            return {
                                "statusCode": 400,
                                "headers": headers,
                                "body": json.dumps(
                                    {
                                        "error": f'Insufficient stock_quantity for {cart_item.get("title", "Unknown")}',
                                        "available_stock_quantity": book.get(
                                            "stock_quantity", 0
                                        ),
                                    }
                                ),
                            }

                        item_total = float(cart_item.get("price", 0)) * quantity
                        subtotal += item_total

                        order_items.append(
                            {
                                "book_id": cart_item["book_id"],
                                "title": cart_item.get("title", "Unknown"),
                                "author": cart_item.get("author", "Unknown"),
                                "price": float(cart_item.get("price", 0)),
                                "quantity": quantity,
                                "subtotal": item_total,
                                "isbn": cart_item.get("isbn", ""),
                            }
                        )

                # Calcular totales
                tax = round(subtotal * 0.08, 2)
                shipping = 5.99 if subtotal < 50 else 0
                total = round(subtotal + tax + shipping, 2)

                # Crear orden
                order_id = str(uuid.uuid4())
                order_item = {
                    "pk": f'ORDER#{user["tenant_id"]}#{order_id}',
                    "sk": "DETAILS",
                    "gsi1pk": f'USER#{user["tenant_id"]}#{user["user_id"]}',
                    "gsi1sk": f"ORDER#{order_id}",
                    "order_id": order_id,
                    "user_id": user["user_id"],
                    "tenant_id": user["tenant_id"],
                    "status": "processing",
                    "payment_method": payment_method,
                    "payment_status": "pending",
                    "subtotal": subtotal,
                    "tax": tax,
                    "shipping": shipping,
                    "total": total,
                    "items": order_items,
                    "items_count": len(order_items),
                    "shipping_address": shipping_address,
                    "billing_address": billing_address,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }

                # Guardar orden
                purchases_table.put_item(Item=order_item)

                # Actualizar inventario (decrementar stock_quantity)
                for item in order_items:
                    book = get_book_info(user["tenant_id"], item["book_id"])
                    new_stock_quantity = (
                        book.get("stock_quantity", 0) - item["quantity"]
                    )

                    books_table.update_item(
                        Key={"pk": book["pk"], "sk": book["sk"]},
                        UpdateExpression="SET stock_quantity = :stock_quantity, updated_at = :updated_at",
                        ExpressionAttributeValues={
                            ":stock_quantity": max(0, new_stock_quantity),
                            ":updated_at": datetime.utcnow().isoformat(),
                        },
                    )

                # Limpiar carrito
                with cart_table.batch_writer() as batch:
                    for item in cart_response["Items"]:
                        batch.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})

                return {
                    "statusCode": 201,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "Order created successfully",
                            "order": {
                                "order_id": order_id,
                                "status": "processing",
                                "total": total,
                                "items_count": len(order_items),
                                "estimated_delivery": (
                                    datetime.utcnow() + timedelta(days=7)
                                ).isoformat(),
                            },
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Checkout error: {str(e)}"}),
                }

        # ===========================================
        # ORDERS & PURCHASE HISTORY
        # ===========================================

        # GET USER ORDERS
        elif path == "/api/v1/orders" and method == "GET":
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
                page = int(query_params.get("page", 1))
                limit = min(int(query_params.get("limit", 10)), 100)
                status = query_params.get("status", "")

                # Query usando GSI1
                scan_params = {
                    "IndexName": "GSI1",
                    "KeyConditionExpression": boto3.dynamodb.conditions.Key(
                        "gsi1pk"
                    ).eq(f'USER#{user["tenant_id"]}#{user["user_id"]}'),
                }

                if status:
                    scan_params["FilterExpression"] = boto3.dynamodb.conditions.Attr(
                        "status"
                    ).eq(status)

                response = purchases_table.query(**scan_params)
                orders = []

                for item in response["Items"]:
                    orders.append(
                        {
                            "order_id": item.get("order_id"),
                            "status": item.get("status", "unknown"),
                            "payment_status": item.get("payment_status", "pending"),
                            "total": float(item.get("total", 0)),
                            "items_count": item.get("items_count", 0),
                            "created_at": item.get("created_at"),
                            "updated_at": item.get("updated_at"),
                        }
                    )

                # Ordenar por fecha de creación (más reciente primero)
                orders.sort(key=lambda x: x["created_at"], reverse=True)

                # Paginación manual
                total_items = len(orders)
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                paginated_orders = orders[start_idx:end_idx]

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        create_pagination_response(
                            paginated_orders, page, limit, total_items
                        )
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # GET ORDER DETAILS
        elif path.startswith("/api/v1/orders/") and method == "GET":
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

            order_id = path.split("/")[-1]

            try:
                response = purchases_table.get_item(
                    Key={"pk": f'ORDER#{user["tenant_id"]}#{order_id}', "sk": "DETAILS"}
                )

                if "Item" not in response:
                    return {
                        "statusCode": 404,
                        "headers": headers,
                        "body": json.dumps({"error": "Order not found"}),
                    }

                order = response["Item"]

                # Verificar que la orden pertenece al usuario
                if order.get("user_id") != user["user_id"]:
                    return {
                        "statusCode": 403,
                        "headers": headers,
                        "body": json.dumps({"error": "Access denied"}),
                    }

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "order": {
                                "order_id": order.get("order_id"),
                                "status": order.get("status"),
                                "payment_status": order.get("payment_status"),
                                "payment_method": order.get("payment_method"),
                                "subtotal": float(order.get("subtotal", 0)),
                                "tax": float(order.get("tax", 0)),
                                "shipping": float(order.get("shipping", 0)),
                                "total": float(order.get("total", 0)),
                                "items": order.get("items", []),
                                "items_count": order.get("items_count", 0),
                                "shipping_address": order.get("shipping_address", {}),
                                "billing_address": order.get("billing_address", {}),
                                "created_at": order.get("created_at"),
                                "updated_at": order.get("updated_at"),
                            }
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # ANALYTICS & REPORTS
        # ===========================================

        # GET PURCHASE ANALYTICS
        elif path == "/api/v1/analytics/purchases" and method == "GET":
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
                # Obtener todas las órdenes del usuario
                response = purchases_table.query(
                    IndexName="GSI1",
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("gsi1pk").eq(
                        f'USER#{user["tenant_id"]}#{user["user_id"]}'
                    ),
                )

                orders = response["Items"]

                # Calcular estadísticas
                total_orders = len(orders)
                total_spent = sum(float(order.get("total", 0)) for order in orders)
                completed_orders = [
                    order for order in orders if order.get("status") == "completed"
                ]
                pending_orders = [
                    order
                    for order in orders
                    if order.get("status") in ["processing", "pending"]
                ]

                # Estadísticas por mes (últimos 12 meses)
                monthly_stats = {}
                for order in orders:
                    if order.get("created_at"):
                        month_key = order["created_at"][:7]  # YYYY-MM
                        if month_key not in monthly_stats:
                            monthly_stats[month_key] = {"orders": 0, "total": 0}
                        monthly_stats[month_key]["orders"] += 1
                        monthly_stats[month_key]["total"] += float(
                            order.get("total", 0)
                        )

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "analytics": {
                                "summary": {
                                    "total_orders": total_orders,
                                    "total_spent": round(total_spent, 2),
                                    "average_order_value": (
                                        round(total_spent / total_orders, 2)
                                        if total_orders > 0
                                        else 0
                                    ),
                                    "completed_orders": len(completed_orders),
                                    "pending_orders": len(pending_orders),
                                },
                                "monthly_stats": monthly_stats,
                                "generated_at": datetime.utcnow().isoformat(),
                            }
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # ENDPOINT NOT FOUND
        # ===========================================
        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps(
                    {
                        "error": "Endpoint not found",
                        "path": path,
                        "method": method,
                        "available_endpoints": [
                            "GET /",
                            "GET /api/v1/cart",
                            "POST /api/v1/cart",
                            "PUT /api/v1/cart/{cart_item_id}",
                            "DELETE /api/v1/cart/{cart_item_id}",
                            "POST /api/v1/cart/clear",
                            "POST /api/v1/checkout",
                            "GET /api/v1/orders",
                            "GET /api/v1/orders/{order_id}",
                            "GET /api/v1/analytics/purchases",
                        ],
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
