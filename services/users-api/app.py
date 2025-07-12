import os
import json
import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
import boto3
from boto3.dynamodb.conditions import Key
from mangum import Mangum

# Configuración
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1

# DynamoDB
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

# FastAPI App
app = FastAPI(title="Users API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    tenant_id: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    tenant_id: str


class UserProfile(BaseModel):
    first_name: str
    last_name: str
    preferences: Optional[dict] = {}


class UserPreferences(BaseModel):
    categories: List[str] = []
    language: str = "es"


# Utilidades
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_jwt_token(user_id: str, tenant_id: str) -> str:
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    return payload


# Endpoints
@app.get("/")
async def root():
    return {"message": "Users API v1.0.0", "status": "running"}


@app.post("/api/v1/users/register")
async def register_user(user: UserRegister):
    try:
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # Verificar si el usuario ya existe
        response = users_table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("gsi1pk").eq(f"{user.tenant_id}#EMAIL")
            & Key("gsi1sk").eq(user.email),
        )

        if response["Items"]:
            raise HTTPException(status_code=400, detail="El usuario ya existe")

        # Crear usuario
        hashed_password = hash_password(user.password)

        user_item = {
            "pk": f"{user.tenant_id}#{user_id}",
            "sk": f"USER#{user.email}",
            "gsi1pk": f"{user.tenant_id}#EMAIL",
            "gsi1sk": user.email,
            "user_id": user_id,
            "tenant_id": user.tenant_id,
            "email": user.email,
            "password_hash": hashed_password,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "preferences": {"categories": [], "language": "es"},
        }

        users_table.put_item(Item=user_item)

        # Crear token
        token = create_jwt_token(user_id, user.tenant_id)

        return {
            "message": "Usuario registrado exitosamente",
            "user_id": user_id,
            "token": token,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/users/login")
async def login_user(user: UserLogin):
    try:
        # Buscar usuario por email
        response = users_table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("gsi1pk").eq(f"{user.tenant_id}#EMAIL")
            & Key("gsi1sk").eq(user.email),
        )

        if not response["Items"]:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        user_item = response["Items"][0]

        # Verificar contraseña
        if not verify_password(user.password, user_item["password_hash"]):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        if not user_item.get("is_active", True):
            raise HTTPException(status_code=401, detail="Usuario inactivo")

        # Crear token
        token = create_jwt_token(user_item["user_id"], user.tenant_id)

        return {
            "message": "Login exitoso",
            "user_id": user_item["user_id"],
            "token": token,
            "user": {
                "first_name": user_item["first_name"],
                "last_name": user_item["last_name"],
                "email": user_item["email"],
                "preferences": user_item.get("preferences", {}),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/users/validate-token")
async def validate_token(current_user: dict = Depends(get_current_user)):
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "tenant_id": current_user["tenant_id"],
    }


@app.get("/api/v1/users/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    try:
        response = users_table.get_item(
            Key={
                "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
                "sk": f"USER#{current_user.get('email', '')}",
            }
        )

        if "Item" not in response:
            # Buscar por GSI si no se encuentra por clave primaria
            response = users_table.query(
                KeyConditionExpression=Key("pk").eq(
                    f"{current_user['tenant_id']}#{current_user['user_id']}"
                )
            )
            if not response["Items"]:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            user_item = response["Items"][0]
        else:
            user_item = response["Item"]

        return {
            "user_id": user_item["user_id"],
            "email": user_item["email"],
            "first_name": user_item["first_name"],
            "last_name": user_item["last_name"],
            "preferences": user_item.get("preferences", {}),
            "created_at": user_item["created_at"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/users/profile")
async def update_profile(
    profile: UserProfile, current_user: dict = Depends(get_current_user)
):
    try:
        now = datetime.utcnow().isoformat()

        # Buscar el usuario actual
        response = users_table.query(
            KeyConditionExpression=Key("pk").eq(
                f"{current_user['tenant_id']}#{current_user['user_id']}"
            )
        )

        if not response["Items"]:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user_item = response["Items"][0]

        # Actualizar perfil
        users_table.update_item(
            Key={"pk": user_item["pk"], "sk": user_item["sk"]},
            UpdateExpression="SET first_name = :fn, last_name = :ln, preferences = :pref, updated_at = :updated",
            ExpressionAttributeValues={
                ":fn": profile.first_name,
                ":ln": profile.last_name,
                ":pref": profile.preferences,
                ":updated": now,
            },
        )

        return {"message": "Perfil actualizado exitosamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/users/preferences")
async def update_preferences(
    preferences: UserPreferences, current_user: dict = Depends(get_current_user)
):
    try:
        now = datetime.utcnow().isoformat()

        # Buscar el usuario actual
        response = users_table.query(
            KeyConditionExpression=Key("pk").eq(
                f"{current_user['tenant_id']}#{current_user['user_id']}"
            )
        )

        if not response["Items"]:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user_item = response["Items"][0]

        # Actualizar preferencias
        users_table.update_item(
            Key={"pk": user_item["pk"], "sk": user_item["sk"]},
            UpdateExpression="SET preferences = :pref, updated_at = :updated",
            ExpressionAttributeValues={":pref": preferences.dict(), ":updated": now},
        )

        return {"message": "Preferencias actualizadas exitosamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/users/favorites")
async def get_favorites(
    page: int = 1, limit: int = 20, current_user: dict = Depends(get_current_user)
):
    try:
        response = favorites_table.query(
            KeyConditionExpression=Key("pk").eq(
                f"{current_user['tenant_id']}#{current_user['user_id']}"
            ),
            ScanIndexForward=False,  # Orden descendente
            Limit=limit,
        )

        favorites = response["Items"]

        return {
            "data": favorites,
            "pagination": {
                "current_page": page,
                "items_per_page": limit,
                "total_items": len(favorites),
                "has_next": "LastEvaluatedKey" in response,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/users/favorites/{book_id}")
async def add_favorite(book_id: str, current_user: dict = Depends(get_current_user)):
    try:
        now = datetime.utcnow().isoformat()

        favorite_item = {
            "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
            "sk": f"FAVORITE#{book_id}",
            "user_id": current_user["user_id"],
            "tenant_id": current_user["tenant_id"],
            "book_id": book_id,
            "added_at": now,
        }

        favorites_table.put_item(Item=favorite_item)

        return {"message": "Libro agregado a favoritos"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/users/favorites/{book_id}")
async def remove_favorite(book_id: str, current_user: dict = Depends(get_current_user)):
    try:
        favorites_table.delete_item(
            Key={
                "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
                "sk": f"FAVORITE#{book_id}",
            }
        )

        return {"message": "Libro removido de favoritos"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/users/wishlist")
async def get_wishlist(
    page: int = 1, limit: int = 20, current_user: dict = Depends(get_current_user)
):
    try:
        response = wishlist_table.query(
            KeyConditionExpression=Key("pk").eq(
                f"{current_user['tenant_id']}#{current_user['user_id']}"
            ),
            ScanIndexForward=False,
            Limit=limit,
        )

        wishlist = response["Items"]

        return {
            "data": wishlist,
            "pagination": {
                "current_page": page,
                "items_per_page": limit,
                "total_items": len(wishlist),
                "has_next": "LastEvaluatedKey" in response,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/users/wishlist/{book_id}")
async def add_to_wishlist(
    book_id: str, priority: int = 3, current_user: dict = Depends(get_current_user)
):
    try:
        now = datetime.utcnow().isoformat()

        wishlist_item = {
            "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
            "sk": f"WISHLIST#{book_id}",
            "user_id": current_user["user_id"],
            "tenant_id": current_user["tenant_id"],
            "book_id": book_id,
            "priority": min(max(priority, 1), 5),  # Entre 1 y 5
            "added_at": now,
        }

        wishlist_table.put_item(Item=wishlist_item)

        return {"message": "Libro agregado a lista de deseos"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/users/wishlist/{book_id}")
async def remove_from_wishlist(
    book_id: str, current_user: dict = Depends(get_current_user)
):
    try:
        wishlist_table.delete_item(
            Key={
                "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
                "sk": f"WISHLIST#{book_id}",
            }
        )

        return {"message": "Libro removido de lista de deseos"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Lambda Handler
handler = Mangum(app)
