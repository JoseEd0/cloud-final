import json
import os
import uuid
import hashlib
import time
from datetime import datetime
import boto3


def lambda_handler(event, context):
    """
    Handler simple para AWS Lambda que maneja requests HTTP básicos
    """

    # Configuración básica
    dynamodb = boto3.resource(
        "dynamodb", region_name=os.environ.get("DYNAMODB_REGION", "us-east-1")
    )
    users_table = dynamodb.Table(os.environ.get("USERS_TABLE", "bookstore-users-dev"))

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

            # Crear usuario
            user_id = str(uuid.uuid4())
            user_item = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "username": username,
                "email": email,
                "password": password_hash,
                "created_at": datetime.utcnow().isoformat(),
            }

            try:
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

            # Buscar usuario (esto es una búsqueda simple, en producción se necesitaría un índice)
            try:
                response = users_table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr("email").eq(email)
                    & boto3.dynamodb.conditions.Attr("tenant_id").eq(tenant_id)
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
                        "available_endpoints": ["/", "/health", "/register", "/login"],
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
