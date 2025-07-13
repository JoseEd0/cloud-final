import json
import os
import uuid
import hashlib
import time
from datetime import datetime, timedelta
import boto3
from decimal import Decimal
import re


def lambda_handler(event, context):
    """
    Handler mejorado para AWS Lambda que maneja requests HTTP para usuarios
    Incluye funcionalidades completas para un sistema robusto
    """

    # Configuración básica
    dynamodb = boto3.resource(
        "dynamodb", region_name=os.environ.get("DYNAMODB_REGION", "us-east-1")
    )
    users_table = dynamodb.Table(os.environ.get("USERS_TABLE", "bookstore-users-dev"))
    favorites_table = dynamodb.Table(
        os.environ.get("FAVORITES_TABLE", "bookstore-user-favorites-dev")
    )
    wishlist_table = dynamodb.Table(
        os.environ.get("WISHLIST_TABLE", "bookstore-user-wishlist-dev")
    )

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

    # Función para validar email
    def validate_email(email):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    # Función para validar password
    def validate_password(password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r"[A-Za-z]", password):
            return False, "Password must contain letters"
        if not re.search(r"\d", password):
            return False, "Password must contain numbers"
        return True, "Valid password"

    # Función para extraer user_id del token
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
                        "message": "Users API v2.0.0 - Enhanced",
                        "status": "healthy",
                        "timestamp": datetime.utcnow().isoformat(),
                        "method": method,
                        "path": path,
                        "features": [
                            "User Registration & Authentication",
                            "Profile Management",
                            "Favorites & Wishlist",
                            "User Management (Admin)",
                            "Enhanced Security",
                        ],
                    }
                ),
            }

        # ===========================================
        # USER REGISTRATION
        # ===========================================
        elif path == "/api/v1/register" and method == "POST":
            username = request_body.get("username", "").strip()
            email = request_body.get("email", "").strip().lower()
            password = request_body.get("password", "")
            tenant_id = request_body.get("tenant_id", "default")
            first_name = request_body.get("first_name", "").strip()
            last_name = request_body.get("last_name", "").strip()

            # Validaciones
            if not username or not email or not password:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": "Missing required fields: username, email, password"}
                    ),
                }

            if not validate_email(email):
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Invalid email format"}),
                }

            is_valid, password_msg = validate_password(password)
            if not is_valid:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": password_msg}),
                }

            # Hash de la contraseña
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # Crear usuario
            user_id = str(uuid.uuid4())
            user_item = {
                "pk": f"USER#{tenant_id}#{user_id}",
                "sk": "PROFILE",
                "gsi1pk": f"EMAIL#{tenant_id}#{email}",
                "gsi1sk": f"USER#{user_id}",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "username": username,
                "email": email,
                "password": password_hash,
                "first_name": first_name,
                "last_name": last_name,
                "role": "user",
                "is_active": True,
                "email_verified": False,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "entity_type": "USER",
            }

            try:
                # Verificar si el usuario ya existe
                response = users_table.query(
                    IndexName="GSI1",
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("gsi1pk").eq(
                        f"EMAIL#{tenant_id}#{email}"
                    ),
                )

                if response["Items"]:
                    return {
                        "statusCode": 400,
                        "headers": headers,
                        "body": json.dumps(
                            {"error": "User already exists with this email"}
                        ),
                    }

                users_table.put_item(Item=user_item)

                return {
                    "statusCode": 201,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "User created successfully",
                            "user": {
                                "user_id": user_id,
                                "username": username,
                                "email": email,
                                "first_name": first_name,
                                "last_name": last_name,
                                "tenant_id": tenant_id,
                                "role": "user",
                                "created_at": user_item["created_at"],
                            },
                            "token": f"simple_token_{user_id}_{tenant_id}",
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
        # USER LOGIN
        # ===========================================
        elif path == "/api/v1/login" and method == "POST":
            email = request_body.get("email", "").strip().lower()
            password = request_body.get("password", "")
            tenant_id = request_body.get("tenant_id", "default")

            if not email or not password:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Missing email or password"}),
                }

            password_hash = hashlib.sha256(password.encode()).hexdigest()

            try:
                response = users_table.query(
                    IndexName="GSI1",
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("gsi1pk").eq(
                        f"EMAIL#{tenant_id}#{email}"
                    ),
                )

                if response["Items"]:
                    user = response["Items"][0]
                    if not user.get("is_active", True):
                        return {
                            "statusCode": 401,
                            "headers": headers,
                            "body": json.dumps({"error": "Account is deactivated"}),
                        }

                    if user["password"] == password_hash:
                        return {
                            "statusCode": 200,
                            "headers": headers,
                            "body": json.dumps(
                                {
                                    "message": "Login successful",
                                    "user": {
                                        "user_id": user["user_id"],
                                        "username": user["username"],
                                        "email": user["email"],
                                        "first_name": user.get("first_name", ""),
                                        "last_name": user.get("last_name", ""),
                                        "role": user.get("role", "user"),
                                        "tenant_id": user["tenant_id"],
                                    },
                                    "token": f'simple_token_{user["user_id"]}_{tenant_id}',
                                }
                            ),
                        }

                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps({"error": "Invalid credentials"}),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # GET USER PROFILE
        # ===========================================
        elif path == "/api/v1/profile" and method == "GET":
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
                response = users_table.get_item(
                    Key={
                        "pk": f'USER#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": "PROFILE",
                    }
                )

                if "Item" not in response:
                    return {
                        "statusCode": 404,
                        "headers": headers,
                        "body": json.dumps({"error": "User not found"}),
                    }

                user_data = response["Item"]
                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "user": {
                                "user_id": user_data["user_id"],
                                "username": user_data["username"],
                                "email": user_data["email"],
                                "first_name": user_data.get("first_name", ""),
                                "last_name": user_data.get("last_name", ""),
                                "role": user_data.get("role", "user"),
                                "tenant_id": user_data["tenant_id"],
                                "is_active": user_data.get("is_active", True),
                                "email_verified": user_data.get(
                                    "email_verified", False
                                ),
                                "created_at": user_data["created_at"],
                                "updated_at": user_data.get(
                                    "updated_at", user_data["created_at"]
                                ),
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
        # UPDATE USER PROFILE
        # ===========================================
        elif path == "/api/v1/profile" and method == "PUT":
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

            username = request_body.get("username", "").strip()
            first_name = request_body.get("first_name", "").strip()
            last_name = request_body.get("last_name", "").strip()

            if not username:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Username is required"}),
                }

            try:
                # Actualizar perfil
                response = users_table.update_item(
                    Key={
                        "pk": f'USER#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": "PROFILE",
                    },
                    UpdateExpression="SET username = :username, first_name = :first_name, last_name = :last_name, updated_at = :updated_at",
                    ExpressionAttributeValues={
                        ":username": username,
                        ":first_name": first_name,
                        ":last_name": last_name,
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                    ReturnValues="ALL_NEW",
                )

                user_data = response["Attributes"]
                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "Profile updated successfully",
                            "user": {
                                "user_id": user_data["user_id"],
                                "username": user_data["username"],
                                "email": user_data["email"],
                                "first_name": user_data.get("first_name", ""),
                                "last_name": user_data.get("last_name", ""),
                                "updated_at": user_data["updated_at"],
                            },
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
        # CHANGE PASSWORD
        # ===========================================
        elif path == "/api/v1/change-password" and method == "POST":
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

            current_password = request_body.get("current_password", "")
            new_password = request_body.get("new_password", "")

            if not current_password or not new_password:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": "Current password and new password are required"}
                    ),
                }

            is_valid, password_msg = validate_password(new_password)
            if not is_valid:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": password_msg}),
                }

            try:
                # Verificar contraseña actual
                response = users_table.get_item(
                    Key={
                        "pk": f'USER#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": "PROFILE",
                    }
                )

                if "Item" not in response:
                    return {
                        "statusCode": 404,
                        "headers": headers,
                        "body": json.dumps({"error": "User not found"}),
                    }

                user_data = response["Item"]
                current_password_hash = hashlib.sha256(
                    current_password.encode()
                ).hexdigest()

                if user_data["password"] != current_password_hash:
                    return {
                        "statusCode": 401,
                        "headers": headers,
                        "body": json.dumps({"error": "Current password is incorrect"}),
                    }

                # Actualizar contraseña
                new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                users_table.update_item(
                    Key={
                        "pk": f'USER#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": "PROFILE",
                    },
                    UpdateExpression="SET password = :password, updated_at = :updated_at",
                    ExpressionAttributeValues={
                        ":password": new_password_hash,
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps({"message": "Password changed successfully"}),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # LIST USERS (Admin Only)
        # ===========================================
        elif path == "/api/v1/users" and method == "GET":
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

            # Verificar si es admin
            try:
                response = users_table.get_item(
                    Key={
                        "pk": f'USER#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": "PROFILE",
                    }
                )

                if "Item" not in response or response["Item"].get("role") != "admin":
                    return {
                        "statusCode": 403,
                        "headers": headers,
                        "body": json.dumps({"error": "Admin access required"}),
                    }

                # Parámetros de paginación
                page = int(query_params.get("page", 1))
                limit = min(int(query_params.get("limit", 10)), 100)
                search = query_params.get("search", "").strip()

                # Scan usuarios del tenant
                scan_params = {
                    "FilterExpression": boto3.dynamodb.conditions.Attr("tenant_id").eq(
                        user["tenant_id"]
                    )
                    & boto3.dynamodb.conditions.Attr("sk").eq("PROFILE")
                }

                if search:
                    scan_params["FilterExpression"] = scan_params[
                        "FilterExpression"
                    ] & (
                        boto3.dynamodb.conditions.Attr("username").contains(search)
                        | boto3.dynamodb.conditions.Attr("email").contains(search)
                        | boto3.dynamodb.conditions.Attr("first_name").contains(search)
                        | boto3.dynamodb.conditions.Attr("last_name").contains(search)
                    )

                response = users_table.scan(**scan_params)
                all_users = response["Items"]

                # Paginación manual
                total_items = len(all_users)
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                paginated_users = all_users[start_idx:end_idx]

                # Formatear usuarios
                users_list = []
                for user_item in paginated_users:
                    users_list.append(
                        {
                            "user_id": user_item["user_id"],
                            "username": user_item["username"],
                            "email": user_item["email"],
                            "first_name": user_item.get("first_name", ""),
                            "last_name": user_item.get("last_name", ""),
                            "role": user_item.get("role", "user"),
                            "is_active": user_item.get("is_active", True),
                            "created_at": user_item["created_at"],
                        }
                    )

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        create_pagination_response(users_list, page, limit, total_items)
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # FAVORITES MANAGEMENT
        # ===========================================
        elif path == "/api/v1/favorites" and method == "GET":
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

                response = favorites_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq(
                        f'FAVORITES#{user["tenant_id"]}#{user["user_id"]}'
                    )
                )

                favorites = []
                for item in response["Items"]:
                    if item["sk"].startswith("BOOK#"):
                        favorites.append(
                            {
                                "book_id": item.get("book_id"),
                                "title": item.get("title", "Unknown"),
                                "author": item.get("author", "Unknown"),
                                "price": float(item.get("price", 0)),
                                "added_at": item.get("added_at"),
                            }
                        )

                # Paginación manual
                total_items = len(favorites)
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                paginated_favorites = favorites[start_idx:end_idx]

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        create_pagination_response(
                            paginated_favorites, page, limit, total_items
                        )
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        elif path == "/api/v1/favorites" and method == "POST":
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
            if not book_id:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "book_id is required"}),
                }

            try:
                # Agregar a favoritos
                favorite_item = {
                    "pk": f'FAVORITES#{user["tenant_id"]}#{user["user_id"]}',
                    "sk": f"BOOK#{book_id}",
                    "book_id": book_id,
                    "title": request_body.get("title", "Unknown"),
                    "author": request_body.get("author", "Unknown"),
                    "price": request_body.get("price", 0),
                    "added_at": datetime.utcnow().isoformat(),
                }

                favorites_table.put_item(Item=favorite_item)

                return {
                    "statusCode": 201,
                    "headers": headers,
                    "body": json.dumps({"message": "Book added to favorites"}),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        elif path.startswith("/api/v1/favorites/") and method == "DELETE":
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

            book_id = path.split("/")[-1]

            try:
                favorites_table.delete_item(
                    Key={
                        "pk": f'FAVORITES#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": f"BOOK#{book_id}",
                    }
                )

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps({"message": "Book removed from favorites"}),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # WISHLIST MANAGEMENT (Similar to Favorites)
        # ===========================================
        elif path == "/api/v1/wishlist" and method == "GET":
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

                response = wishlist_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq(
                        f'WISHLIST#{user["tenant_id"]}#{user["user_id"]}'
                    )
                )

                wishlist = []
                for item in response["Items"]:
                    if item["sk"].startswith("BOOK#"):
                        wishlist.append(
                            {
                                "book_id": item.get("book_id"),
                                "title": item.get("title", "Unknown"),
                                "author": item.get("author", "Unknown"),
                                "price": float(item.get("price", 0)),
                                "priority": item.get("priority", "medium"),
                                "added_at": item.get("added_at"),
                            }
                        )

                # Paginación manual
                total_items = len(wishlist)
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                paginated_wishlist = wishlist[start_idx:end_idx]

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        create_pagination_response(
                            paginated_wishlist, page, limit, total_items
                        )
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # ADD TO WISHLIST
        # ===========================================
        elif path == "/api/v1/wishlist" and method == "POST":
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

            book_id = request_body.get("book_id", "").strip()
            title = request_body.get("title", "").strip()
            author = request_body.get("author", "").strip()
            price = request_body.get("price", 0)
            priority = request_body.get("priority", "medium").strip()

            # Validaciones
            if not all([book_id, title, author]):
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": "book_id, title, and author are required"}
                    ),
                }

            if priority not in ["low", "medium", "high"]:
                priority = "medium"

            try:
                # Convertir price a Decimal para DynamoDB
                from decimal import Decimal

                if isinstance(price, (int, float)):
                    price = Decimal(str(price))
                elif isinstance(price, str):
                    price = Decimal(price)

                # Verificar si ya está en wishlist
                existing_response = wishlist_table.get_item(
                    Key={
                        "pk": f'WISHLIST#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": f"BOOK#{book_id}",
                    }
                )

                if "Item" in existing_response:
                    return {
                        "statusCode": 400,
                        "headers": headers,
                        "body": json.dumps({"error": "Book already in wishlist"}),
                    }

                # Agregar a wishlist
                wishlist_item = {
                    "pk": f'WISHLIST#{user["tenant_id"]}#{user["user_id"]}',
                    "sk": f"BOOK#{book_id}",
                    "book_id": book_id,
                    "title": title,
                    "author": author,
                    "price": price,
                    "priority": priority,
                    "added_at": datetime.utcnow().isoformat(),
                    "tenant_id": user["tenant_id"],
                    "user_id": user["user_id"],
                }

                wishlist_table.put_item(Item=wishlist_item)

                return {
                    "statusCode": 201,
                    "headers": headers,
                    "body": json.dumps({"message": "Book added to wishlist"}),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # REMOVE FROM WISHLIST
        # ===========================================
        elif path.startswith("/api/v1/wishlist/") and method == "DELETE":
            book_id = path.split("/")[-1]
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
                # Eliminar de wishlist
                wishlist_table.delete_item(
                    Key={
                        "pk": f'WISHLIST#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": f"BOOK#{book_id}",
                    }
                )

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps({"message": "Book removed from wishlist"}),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Database error: {str(e)}"}),
                }

        # ===========================================
        # TOKEN VALIDATION
        # ===========================================
        elif path == "/api/v1/validate-token" and method == "GET":
            auth_header = event.get("headers", {}).get(
                "authorization", ""
            ) or event.get("headers", {}).get("Authorization", "")
            user = extract_user_from_token(auth_header)

            if not user:
                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps({"error": "Invalid token", "valid": False}),
                }

            try:
                response = users_table.get_item(
                    Key={
                        "pk": f'USER#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": "PROFILE",
                    }
                )

                if "Item" not in response:
                    return {
                        "statusCode": 401,
                        "headers": headers,
                        "body": json.dumps({"error": "User not found", "valid": False}),
                    }

                user_data = response["Item"]
                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "valid": True,
                            "user": {
                                "user_id": user_data["user_id"],
                                "username": user_data["username"],
                                "email": user_data["email"],
                                "role": user_data.get("role", "user"),
                                "tenant_id": user_data["tenant_id"],
                            },
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
        # UPDATE PROFILE IMAGE
        # ===========================================
        elif path == "/api/v1/profile/image" and method == "PUT":
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

            image_url = request_body.get("image_url", "").strip()

            if not image_url:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "image_url is required"}),
                }

            try:
                # Actualizar imagen de perfil
                response = users_table.update_item(
                    Key={
                        "pk": f'USER#{user["tenant_id"]}#{user["user_id"]}',
                        "sk": "PROFILE",
                    },
                    UpdateExpression="SET profile_image_url = :image_url, updated_at = :updated_at",
                    ExpressionAttributeValues={
                        ":image_url": image_url,
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                    ReturnValues="ALL_NEW",
                )

                user_data = response["Attributes"]
                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "Profile image updated successfully",
                            "profile_image_url": image_url,
                            "user": {
                                "user_id": user_data["user_id"],
                                "username": user_data["username"],
                                "email": user_data["email"],
                                "profile_image_url": user_data.get(
                                    "profile_image_url", ""
                                ),
                                "updated_at": user_data["updated_at"],
                            },
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
                            "POST /api/v1/register",
                            "POST /api/v1/login",
                            "GET /api/v1/profile",
                            "PUT /api/v1/profile",
                            "PUT /api/v1/profile/image",
                            "POST /api/v1/change-password",
                            "GET /api/v1/users",
                            "GET /api/v1/favorites",
                            "POST /api/v1/favorites",
                            "DELETE /api/v1/favorites/{book_id}",
                            "GET /api/v1/wishlist",
                            "POST /api/v1/wishlist",
                            "DELETE /api/v1/wishlist/{book_id}",
                            "GET /api/v1/validate-token",
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
