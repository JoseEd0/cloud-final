import json
import os
import uuid
import hashlib
import time
from datetime import datetime
import boto3


def lambda_handler(event, context):
    """
    Handler para AWS Lambda que maneja requests HTTP para usuarios
    Usa el esquema de DynamoDB con pk/sk
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

    try:
        # Endpoint básico de salud
        if path == "/" or path == "/health":
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(
                    {
                        "message": "Users API is running",
                        "status": "healthy",
                        "timestamp": datetime.utcnow().isoformat(),
                        "method": method,
                        "path": path,
                    }
                ),
            }

        # Endpoint de registro
        elif path == "/register" and method == "POST":
            username = request_body.get("username", "")
            email = request_body.get("email", "")
            password = request_body.get("password", "")
            tenant_id = request_body.get("tenant_id", "default")

            if not username or not email or not password:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Missing required fields"}),
                }

            # Hash simple de la contraseña (SHA-256 para demo)
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # Crear usuario con esquema pk/sk
            user_id = str(uuid.uuid4())
            user_item = {
                "pk": f"USER#{tenant_id}#{user_id}",  # Partition key
                "sk": f"PROFILE",  # Sort key
                "gsi1pk": f"EMAIL#{tenant_id}#{email}",  # Para búsqueda por email
                "gsi1sk": f"USER#{user_id}",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "username": username,
                "email": email,
                "password": password_hash,
                "created_at": datetime.utcnow().isoformat(),
                "entity_type": "USER",
            }

            try:
                # Verificar si el usuario ya existe usando GSI1 (email index)
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
                        "body": json.dumps({"error": "User already exists"}),
                    }

                # Crear usuario
                users_table.put_item(Item=user_item)

                return {
                    "statusCode": 201,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "User created successfully",
                            "user_id": user_id,
                            "username": username,
                            "email": email,
                            "tenant_id": tenant_id,
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

        # Endpoint de login
        elif path == "/login" and method == "POST":
            email = request_body.get("email", "")
            password = request_body.get("password", "")
            tenant_id = request_body.get("tenant_id", "default")

            if not email or not password:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Missing email or password"}),
                }

            # Hash de la contraseña para comparar
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            try:
                # Buscar usuario por email usando GSI1
                response = users_table.query(
                    IndexName="GSI1",
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("gsi1pk").eq(
                        f"EMAIL#{tenant_id}#{email}"
                    ),
                )

                if response["Items"]:
                    user = response["Items"][0]
                    if user["password"] == password_hash:
                        return {
                            "statusCode": 200,
                            "headers": headers,
                            "body": json.dumps(
                                {
                                    "message": "Login successful",
                                    "user_id": user["user_id"],
                                    "username": user["username"],
                                    "email": user["email"],
                                    "tenant_id": user["tenant_id"],
                                    "token": f"simple_token_{user['user_id']}_{tenant_id}",
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

        # Endpoint de perfil
        elif path == "/profile" and method == "GET":
            # Extraer token del header Authorization
            auth_header = event.get("headers", {}).get(
                "authorization", ""
            ) or event.get("headers", {}).get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": "Missing or invalid authorization header"}
                    ),
                }

            token = auth_header.replace("Bearer ", "")

            # Extraer user_id y tenant_id del token simple
            if not token.startswith("simple_token_"):
                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps({"error": "Invalid token format"}),
                }

            try:
                token_parts = token.replace("simple_token_", "").split("_")
                if len(token_parts) < 2:
                    raise ValueError("Invalid token")

                user_id = token_parts[0]
                tenant_id = token_parts[1]

                # Buscar usuario
                response = users_table.get_item(
                    Key={"pk": f"USER#{tenant_id}#{user_id}", "sk": "PROFILE"}
                )

                if "Item" not in response:
                    return {
                        "statusCode": 404,
                        "headers": headers,
                        "body": json.dumps({"error": "User not found"}),
                    }

                user = response["Item"]
                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "user_id": user["user_id"],
                            "username": user["username"],
                            "email": user["email"],
                            "tenant_id": user["tenant_id"],
                            "created_at": user["created_at"],
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps({"error": f"Invalid token: {str(e)}"}),
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
                        "available_endpoints": [
                            "/",
                            "/health",
                            "/register",
                            "/login",
                            "/profile",
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
