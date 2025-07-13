import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
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
    username: str
    email: EmailStr
    password: str
    tenant_id: str = "default"


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    tenant_id: str = "default"


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    tenant_id: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class FavoriteRequest(BaseModel):
    book_id: str


class WishlistRequest(BaseModel):
    book_id: str


# Utilidades simplificadas (sin bcrypt)
def hash_password(password: str) -> str:
    # Usar SHA-256 para simplicidad (NO recomendado para producción)
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed


def create_jwt_token(user_id: str, tenant_id: str) -> str:
    try:
        import jwt

        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except ImportError:
        # Fallback simple sin JWT real
        return f"simple_token_{user_id}_{tenant_id}"


def decode_jwt_token(token: str) -> dict:
    try:
        import jwt

        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ImportError:
        # Fallback simple
        parts = token.replace("simple_token_", "").split("_")
        if len(parts) >= 2:
            return {"user_id": parts[0], "tenant_id": parts[1]}
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = decode_jwt_token(credentials.credentials)
        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")
        if user_id is None or tenant_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "tenant_id": tenant_id}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# Endpoints
@app.get("/")
async def root():
    return {"message": "Users API is running", "status": "healthy"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    try:
        # Verificar si el usuario ya existe
        response = users_table.query(
            IndexName="email-index",
            KeyConditionExpression=Key("email").eq(user_data.email),
        )

        if response["Items"]:
            raise HTTPException(status_code=400, detail="User already exists")

        # Crear nuevo usuario
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user_data.password)

        user_item = {
            "user_id": user_id,
            "tenant_id": user_data.tenant_id,
            "username": user_data.username,
            "email": user_data.email,
            "password": hashed_password,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        users_table.put_item(Item=user_item)

        # Crear token
        token = create_jwt_token(user_id, user_data.tenant_id)

        user_response = UserResponse(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            tenant_id=user_data.tenant_id,
            created_at=user_item["created_at"],
        )

        return TokenResponse(
            access_token=token, token_type="bearer", user=user_response
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    try:
        # Buscar usuario por email
        response = users_table.query(
            IndexName="email-index",
            KeyConditionExpression=Key("email").eq(user_data.email),
        )

        if not response["Items"]:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user = response["Items"][0]

        # Verificar tenant_id
        if user["tenant_id"] != user_data.tenant_id:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verificar contraseña
        if not verify_password(user_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Crear token
        token = create_jwt_token(user["user_id"], user["tenant_id"])

        user_response = UserResponse(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"],
            tenant_id=user["tenant_id"],
            created_at=user["created_at"],
        )

        return TokenResponse(
            access_token=token, token_type="bearer", user=user_response
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.get("/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    try:
        response = users_table.get_item(
            Key={
                "user_id": current_user["user_id"],
                "tenant_id": current_user["tenant_id"],
            }
        )

        if "Item" not in response:
            raise HTTPException(status_code=404, detail="User not found")

        user = response["Item"]
        return UserResponse(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"],
            tenant_id=user["tenant_id"],
            created_at=user["created_at"],
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@app.post("/favorites")
async def add_favorite(
    favorite_data: FavoriteRequest, current_user: dict = Depends(get_current_user)
):
    try:
        favorite_id = str(uuid.uuid4())

        favorite_item = {
            "favorite_id": favorite_id,
            "user_id": current_user["user_id"],
            "tenant_id": current_user["tenant_id"],
            "book_id": favorite_data.book_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        favorites_table.put_item(Item=favorite_item)

        return {"message": "Book added to favorites", "favorite_id": favorite_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add favorite: {str(e)}")


@app.get("/favorites")
async def get_favorites(current_user: dict = Depends(get_current_user)):
    try:
        response = favorites_table.query(
            IndexName="user-index",
            KeyConditionExpression=Key("user_id").eq(current_user["user_id"]),
        )

        return {"favorites": response["Items"]}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get favorites: {str(e)}"
        )


@app.delete("/favorites/{book_id}")
async def remove_favorite(book_id: str, current_user: dict = Depends(get_current_user)):
    try:
        # Buscar el favorito
        response = favorites_table.query(
            IndexName="user-index",
            KeyConditionExpression=Key("user_id").eq(current_user["user_id"]),
            FilterExpression=Key("book_id").eq(book_id),
        )

        if not response["Items"]:
            raise HTTPException(status_code=404, detail="Favorite not found")

        favorite = response["Items"][0]

        # Eliminar favorito
        favorites_table.delete_item(
            Key={
                "favorite_id": favorite["favorite_id"],
                "tenant_id": favorite["tenant_id"],
            }
        )

        return {"message": "Book removed from favorites"}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Failed to remove favorite: {str(e)}"
        )


@app.post("/wishlist")
async def add_to_wishlist(
    wishlist_data: WishlistRequest, current_user: dict = Depends(get_current_user)
):
    try:
        wishlist_id = str(uuid.uuid4())

        wishlist_item = {
            "wishlist_id": wishlist_id,
            "user_id": current_user["user_id"],
            "tenant_id": current_user["tenant_id"],
            "book_id": wishlist_data.book_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        wishlist_table.put_item(Item=wishlist_item)

        return {"message": "Book added to wishlist", "wishlist_id": wishlist_id}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add to wishlist: {str(e)}"
        )


@app.get("/wishlist")
async def get_wishlist(current_user: dict = Depends(get_current_user)):
    try:
        response = wishlist_table.query(
            IndexName="user-index",
            KeyConditionExpression=Key("user_id").eq(current_user["user_id"]),
        )

        return {"wishlist": response["Items"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wishlist: {str(e)}")


@app.delete("/wishlist/{book_id}")
async def remove_from_wishlist(
    book_id: str, current_user: dict = Depends(get_current_user)
):
    try:
        # Buscar el item en wishlist
        response = wishlist_table.query(
            IndexName="user-index",
            KeyConditionExpression=Key("user_id").eq(current_user["user_id"]),
            FilterExpression=Key("book_id").eq(book_id),
        )

        if not response["Items"]:
            raise HTTPException(status_code=404, detail="Wishlist item not found")

        wishlist_item = response["Items"][0]

        # Eliminar item
        wishlist_table.delete_item(
            Key={
                "wishlist_id": wishlist_item["wishlist_id"],
                "tenant_id": wishlist_item["tenant_id"],
            }
        )

        return {"message": "Book removed from wishlist"}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Failed to remove from wishlist: {str(e)}"
        )


# Handler para Lambda
handler = Mangum(app)
