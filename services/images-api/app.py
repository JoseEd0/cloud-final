import json
import boto3
import os
import base64
import uuid
from datetime import datetime
import hashlib
import re


def lambda_handler(event, context):
    """
    Handler para gestión de imágenes de libros y usuarios
    Soporta upload, update, delete y get de imágenes en S3
    """

    # Configuración
    s3_client = boto3.client("s3")
    images_bucket = os.environ.get("IMAGES_BUCKET", "bookstore-images-dev-328458381283")

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
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Tenant-ID",
        "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT,DELETE",
    }

    # Función para extraer información del token
    def extract_user_from_token(auth_header):
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        # Token simple format: simple_token_{user_id}_{tenant_id}
        if token.startswith("simple_token_"):
            parts = token.split("_")
            if len(parts) >= 3:
                user_id = parts[2]
                tenant_id = parts[3] if len(parts) > 3 else "tenant1"
                return {"user_id": user_id, "tenant_id": tenant_id}
        return None

    # Función para validar formato de imagen
    def validate_image_data(image_data):
        # Verificar que sea base64 válido
        try:
            decoded = base64.b64decode(image_data)
            # Verificar headers de imagen comunes
            if decoded.startswith(b"\xff\xd8\xff"):  # JPEG
                return "jpeg"
            elif decoded.startswith(b"\x89PNG"):  # PNG
                return "png"
            elif decoded.startswith(b"GIF"):  # GIF
                return "gif"
            elif decoded.startswith(b"\x52\x49\x46\x46"):  # WebP
                return "webp"
            else:
                return None
        except:
            return None

    # Función para generar URL pública
    def get_public_url(bucket, key):
        return f"https://{bucket}.s3.amazonaws.com/{key}"

    try:
        # ===========================================
        # HEALTH CHECK
        # ===========================================
        if path == "/health" or path == "/":
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(
                    {
                        "service": "Images API",
                        "version": "1.0.0",
                        "status": "healthy",
                        "timestamp": datetime.utcnow().isoformat(),
                        "features": [
                            "Book cover images",
                            "User profile images",
                            "Image upload/update/delete",
                            "S3 integration",
                            "Multi-tenant support",
                        ],
                    }
                ),
            }

        # ===========================================
        # UPLOAD BOOK COVER IMAGE
        # ===========================================
        elif path == "/api/v1/books/image" and method == "POST":
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
            image_data = request_body.get("image_data", "").strip()

            if not book_id or not image_data:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": "book_id and image_data are required"}
                    ),
                }

            # Procesar image_data (puede venir como data URL o base64 directo)
            if image_data.startswith("data:"):
                # Extraer solo la parte base64 del data URL
                try:
                    image_data = image_data.split(",")[1]
                except:
                    return {
                        "statusCode": 400,
                        "headers": headers,
                        "body": json.dumps({"error": "Invalid data URL format"}),
                    }

            # Validar imagen
            image_format = validate_image_data(image_data)
            if not image_format:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "error": "Invalid image format. Supported: JPEG, PNG, GIF, WebP"
                        }
                    ),
                }

            try:
                # Decodificar imagen
                decoded_image = base64.b64decode(image_data)

                # Verificar tamaño (máximo 5MB)
                if len(decoded_image) > 5 * 1024 * 1024:
                    return {
                        "statusCode": 400,
                        "headers": headers,
                        "body": json.dumps(
                            {"error": "Image too large. Maximum size: 5MB"}
                        ),
                    }

                # Generar clave S3
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                s3_key = f"{user['tenant_id']}/books/{book_id}/cover_{timestamp}.{image_format}"

                # Subir a S3
                s3_client.put_object(
                    Bucket=images_bucket,
                    Key=s3_key,
                    Body=decoded_image,
                    ContentType=f"image/{image_format}",
                    CacheControl="max-age=31536000",  # 1 año de cache
                )

                # Generar URL pública
                image_url = get_public_url(images_bucket, s3_key)

                return {
                    "statusCode": 201,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "Book cover image uploaded successfully",
                            "image_url": image_url,
                            "book_id": book_id,
                            "format": image_format,
                            "size_bytes": len(decoded_image),
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Upload failed: {str(e)}"}),
                }

        # ===========================================
        # UPLOAD USER PROFILE IMAGE
        # ===========================================
        elif path == "/api/v1/users/profile/image" and method == "POST":
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

            image_data = request_body.get("image_data", "").strip()

            if not image_data:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "image_data is required"}),
                }

            # Procesar image_data (puede venir como data URL o base64 directo)
            if image_data.startswith("data:"):
                # Extraer solo la parte base64 del data URL
                try:
                    image_data = image_data.split(",")[1]
                except:
                    return {
                        "statusCode": 400,
                        "headers": headers,
                        "body": json.dumps({"error": "Invalid data URL format"}),
                    }

            # Validar imagen
            image_format = validate_image_data(image_data)
            if not image_format:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "error": "Invalid image format. Supported: JPEG, PNG, GIF, WebP"
                        }
                    ),
                }

            try:
                # Decodificar imagen
                decoded_image = base64.b64decode(image_data)

                # Verificar tamaño (máximo 2MB para perfiles)
                if len(decoded_image) > 2 * 1024 * 1024:
                    return {
                        "statusCode": 400,
                        "headers": headers,
                        "body": json.dumps(
                            {
                                "error": "Image too large. Maximum size: 2MB for profile images"
                            }
                        ),
                    }

                # Generar clave S3
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                s3_key = f"{user['tenant_id']}/users/{user['user_id']}/profile_{timestamp}.{image_format}"

                # Subir a S3
                s3_client.put_object(
                    Bucket=images_bucket,
                    Key=s3_key,
                    Body=decoded_image,
                    ContentType=f"image/{image_format}",
                    CacheControl="max-age=31536000",  # 1 año de cache
                )

                # Generar URL pública
                image_url = get_public_url(images_bucket, s3_key)

                return {
                    "statusCode": 201,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "Profile image uploaded successfully",
                            "image_url": image_url,
                            "user_id": user["user_id"],
                            "format": image_format,
                            "size_bytes": len(decoded_image),
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Upload failed: {str(e)}"}),
                }

        # ===========================================
        # DELETE IMAGE
        # ===========================================
        elif path.startswith("/api/v1/images/") and method == "DELETE":
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

            # Extraer el path de la imagen del URL
            image_key = "/".join(path.split("/")[4:])  # Remove /api/v1/images/

            # Verificar que la imagen pertenece al tenant del usuario
            if not image_key.startswith(f"{user['tenant_id']}/"):
                return {
                    "statusCode": 403,
                    "headers": headers,
                    "body": json.dumps({"error": "Access denied to this image"}),
                }

            try:
                # Eliminar de S3
                s3_client.delete_object(Bucket=images_bucket, Key=image_key)

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "message": "Image deleted successfully",
                            "image_key": image_key,
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({"error": f"Delete failed: {str(e)}"}),
                }

        # ===========================================
        # GET PRESIGNED URL FOR UPLOAD
        # ===========================================
        elif path == "/api/v1/images/presigned-url" and method == "POST":
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

            image_type = request_body.get("image_type", "")  # "book" or "profile"
            book_id = request_body.get("book_id", "")
            content_type = request_body.get("content_type", "image/jpeg")

            if image_type not in ["book", "profile"]:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": "image_type must be 'book' or 'profile'"}
                    ),
                }

            if image_type == "book" and not book_id:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": "book_id is required for book images"}
                    ),
                }

            try:
                # Generar clave S3
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                unique_id = str(uuid.uuid4())[:8]

                if image_type == "book":
                    s3_key = f"{user['tenant_id']}/books/{book_id}/cover_{timestamp}_{unique_id}"
                else:
                    s3_key = f"{user['tenant_id']}/users/{user['user_id']}/profile_{timestamp}_{unique_id}"

                # Generar URL presignada para upload
                presigned_url = s3_client.generate_presigned_url(
                    "put_object",
                    Params={
                        "Bucket": images_bucket,
                        "Key": s3_key,
                        "ContentType": content_type,
                    },
                    ExpiresIn=3600,  # 1 hora
                )

                # URL pública final
                public_url = get_public_url(images_bucket, s3_key)

                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(
                        {
                            "presigned_url": presigned_url,
                            "public_url": public_url,
                            "s3_key": s3_key,
                            "expires_in": 3600,
                        }
                    ),
                }

            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps(
                        {"error": f"Failed to generate presigned URL: {str(e)}"}
                    ),
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
                            "GET /health",
                            "POST /api/v1/books/image",
                            "POST /api/v1/users/profile/image",
                            "DELETE /api/v1/images/{image_path}",
                            "POST /api/v1/images/presigned-url",
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
