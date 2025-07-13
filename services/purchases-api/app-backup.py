import os
import json
import uuid
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import JWTError, jwt
import boto3
from boto3.dynamodb.conditions import Key
from mangum import Mangum

# Configuración
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"

# DynamoDB
dynamodb = boto3.resource(
    "dynamodb", region_name=os.environ.get("DYNAMODB_REGION", "us-east-1")
)
cart_table = dynamodb.Table(os.environ.get("CART_TABLE", "bookstore-shopping-cart-dev"))
purchases_table = dynamodb.Table(
    os.environ.get("PURCHASES_TABLE", "bookstore-purchases-dev")
)
books_table = dynamodb.Table(os.environ.get("BOOKS_TABLE", "bookstore-books-dev"))

# S3
s3_client = boto3.client("s3", region_name=os.environ.get("REGION", "us-east-1"))
ANALYTICS_BUCKET = os.environ.get("ANALYTICS_BUCKET", "bookstore-analytics-dev")

# FastAPI App
app = FastAPI(title="Purchases API", version="1.0.0")

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
class CartItem(BaseModel):
    book_id: str
    quantity: int


class CartUpdate(BaseModel):
    quantity: int


class CheckoutRequest(BaseModel):
    payment_method: str
    shipping_address: dict


class PurchaseItem(BaseModel):
    book_id: str
    quantity: int
    unit_price: float
    subtotal: float


# Utilidades
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


def decimal_to_float(obj):
    """Convertir Decimal a float para serialización JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj


async def get_book_details(book_id: str, tenant_id: str) -> dict:
    """Obtener detalles de un libro"""
    try:
        response = books_table.query(
            KeyConditionExpression=Key("pk").eq(f"{tenant_id}#{book_id}")
        )

        if not response["Items"]:
            return None

        return response["Items"][0]
    except Exception:
        return None


# Endpoints
@app.get("/")
async def root():
    return {"message": "Purchases API v1.0.0", "status": "running"}


@app.get("/api/v1/cart")
async def get_cart(current_user: dict = Depends(get_current_user)):
    try:
        response = cart_table.query(
            KeyConditionExpression=Key("pk").eq(
                f"{current_user['tenant_id']}#{current_user['user_id']}"
            )
        )

        cart_items = []
        total_amount = 0.0
        total_items = 0

        for item in response["Items"]:
            book_details = await get_book_details(
                item["book_id"], current_user["tenant_id"]
            )
            if book_details:
                item_total = float(book_details.get("price", 0)) * item["quantity"]
                cart_items.append(
                    {
                        "book_id": item["book_id"],
                        "quantity": item["quantity"],
                        "added_at": item["added_at"],
                        "updated_at": item["updated_at"],
                        "book_details": {
                            "title": book_details.get("title"),
                            "author": book_details.get("author"),
                            "price": decimal_to_float(book_details.get("price", 0)),
                            "cover_image_url": book_details.get("cover_image_url"),
                            "stock_quantity": book_details.get("stock_quantity", 0),
                        },
                        "unit_price": decimal_to_float(book_details.get("price", 0)),
                        "subtotal": item_total,
                    }
                )
                total_amount += item_total
                total_items += item["quantity"]

        return {
            "items": cart_items,
            "summary": {
                "total_items": total_items,
                "total_amount": total_amount,
                "currency": "USD",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cart/add")
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    try:
        # Verificar que el libro existe y tiene stock
        book_details = await get_book_details(item.book_id, current_user["tenant_id"])
        if not book_details:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        if book_details.get("stock_quantity", 0) < item.quantity:
            raise HTTPException(status_code=400, detail="Stock insuficiente")

        now = datetime.utcnow().isoformat()

        # Verificar si el item ya existe en el carrito
        existing_response = cart_table.get_item(
            Key={
                "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
                "sk": f"CART#{item.book_id}",
            }
        )

        if "Item" in existing_response:
            # Actualizar cantidad
            new_quantity = existing_response["Item"]["quantity"] + item.quantity
            if book_details.get("stock_quantity", 0) < new_quantity:
                raise HTTPException(
                    status_code=400, detail="Stock insuficiente para la cantidad total"
                )

            cart_table.update_item(
                Key={
                    "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
                    "sk": f"CART#{item.book_id}",
                },
                UpdateExpression="SET quantity = :qty, updated_at = :updated",
                ExpressionAttributeValues={":qty": new_quantity, ":updated": now},
            )
        else:
            # Crear nuevo item
            cart_item = {
                "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
                "sk": f"CART#{item.book_id}",
                "user_id": current_user["user_id"],
                "tenant_id": current_user["tenant_id"],
                "book_id": item.book_id,
                "quantity": item.quantity,
                "added_at": now,
                "updated_at": now,
            }

            cart_table.put_item(Item=cart_item)

        return {"message": "Producto agregado al carrito"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/cart/update/{book_id}")
async def update_cart_item(
    book_id: str, update: CartUpdate, current_user: dict = Depends(get_current_user)
):
    try:
        if update.quantity <= 0:
            raise HTTPException(
                status_code=400, detail="La cantidad debe ser mayor a 0"
            )

        # Verificar stock
        book_details = await get_book_details(book_id, current_user["tenant_id"])
        if not book_details:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        if book_details.get("stock_quantity", 0) < update.quantity:
            raise HTTPException(status_code=400, detail="Stock insuficiente")

        now = datetime.utcnow().isoformat()

        cart_table.update_item(
            Key={
                "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
                "sk": f"CART#{book_id}",
            },
            UpdateExpression="SET quantity = :qty, updated_at = :updated",
            ExpressionAttributeValues={":qty": update.quantity, ":updated": now},
        )

        return {"message": "Carrito actualizado"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/cart/remove/{book_id}")
async def remove_from_cart(
    book_id: str, current_user: dict = Depends(get_current_user)
):
    try:
        cart_table.delete_item(
            Key={
                "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
                "sk": f"CART#{book_id}",
            }
        )

        return {"message": "Producto removido del carrito"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/cart/clear")
async def clear_cart(current_user: dict = Depends(get_current_user)):
    try:
        # Obtener todos los items del carrito
        response = cart_table.query(
            KeyConditionExpression=Key("pk").eq(
                f"{current_user['tenant_id']}#{current_user['user_id']}"
            )
        )

        # Eliminar cada item
        for item in response["Items"]:
            cart_table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})

        return {"message": "Carrito vaciado"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/purchases/checkout")
async def checkout(
    checkout_data: CheckoutRequest, current_user: dict = Depends(get_current_user)
):
    try:
        # Obtener items del carrito
        cart_response = cart_table.query(
            KeyConditionExpression=Key("pk").eq(
                f"{current_user['tenant_id']}#{current_user['user_id']}"
            )
        )

        if not cart_response["Items"]:
            raise HTTPException(status_code=400, detail="El carrito está vacío")

        purchase_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        purchase_items = []
        total_amount = 0.0

        # Procesar cada item del carrito
        for cart_item in cart_response["Items"]:
            book_details = await get_book_details(
                cart_item["book_id"], current_user["tenant_id"]
            )
            if not book_details:
                continue

            # Verificar stock
            if book_details.get("stock_quantity", 0) < cart_item["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para {book_details.get('title', 'libro')}",
                )

            unit_price = float(book_details.get("price", 0))
            subtotal = unit_price * cart_item["quantity"]

            purchase_items.append(
                {
                    "book_id": cart_item["book_id"],
                    "quantity": cart_item["quantity"],
                    "unit_price": unit_price,
                    "subtotal": subtotal,
                    "title": book_details.get("title"),
                    "author": book_details.get("author"),
                }
            )

            total_amount += subtotal

            # Actualizar stock del libro
            books_table.update_item(
                Key={"pk": book_details["pk"], "sk": book_details["sk"]},
                UpdateExpression="SET stock_quantity = stock_quantity - :qty, updated_at = :updated",
                ExpressionAttributeValues={
                    ":qty": cart_item["quantity"],
                    ":updated": now,
                },
            )

        # Crear compra
        purchase_item = {
            "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
            "sk": f"PURCHASE#{purchase_id}",
            "gsi1pk": f"{current_user['tenant_id']}#PURCHASES",
            "gsi1sk": now,
            "purchase_id": purchase_id,
            "tenant_id": current_user["tenant_id"],
            "user_id": current_user["user_id"],
            "total_amount": Decimal(str(total_amount)),
            "status": "completed",
            "payment_method": checkout_data.payment_method,
            "shipping_address": checkout_data.shipping_address,
            "created_at": now,
            "updated_at": now,
            "items": purchase_items,
        }

        purchases_table.put_item(Item=purchase_item)

        # Limpiar carrito
        for cart_item in cart_response["Items"]:
            cart_table.delete_item(Key={"pk": cart_item["pk"], "sk": cart_item["sk"]})

        return {
            "message": "Compra procesada exitosamente",
            "purchase_id": purchase_id,
            "total_amount": total_amount,
            "items_purchased": len(purchase_items),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/purchases")
async def get_purchases(
    page: int = 1,
    limit: int = 10,
    status: str = None,
    current_user: dict = Depends(get_current_user),
):
    try:
        params = {
            "KeyConditionExpression": Key("pk").eq(
                f"{current_user['tenant_id']}#{current_user['user_id']}"
            ),
            "ScanIndexForward": False,  # Orden descendente
            "Limit": limit,
        }

        if status:
            params["FilterExpression"] = "contains(sk, :status)"
            params["ExpressionAttributeValues"] = {":status": status}

        response = purchases_table.query(**params)

        purchases = []
        for item in response["Items"]:
            purchase_data = decimal_to_float(dict(item))
            purchases.append(purchase_data)

        return {
            "data": purchases,
            "pagination": {
                "current_page": page,
                "items_per_page": limit,
                "total_items": len(purchases),
                "has_next": "LastEvaluatedKey" in response,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/purchases/{purchase_id}")
async def get_purchase(
    purchase_id: str, current_user: dict = Depends(get_current_user)
):
    try:
        response = purchases_table.get_item(
            Key={
                "pk": f"{current_user['tenant_id']}#{current_user['user_id']}",
                "sk": f"PURCHASE#{purchase_id}",
            }
        )

        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Compra no encontrada")

        purchase_data = decimal_to_float(dict(response["Item"]))
        return purchase_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/purchases/analytics/summary")
async def get_purchase_analytics(current_user: dict = Depends(get_current_user)):
    try:
        # Obtener todas las compras del usuario
        response = purchases_table.query(
            KeyConditionExpression=Key("pk").eq(
                f"{current_user['tenant_id']}#{current_user['user_id']}"
            )
        )

        total_purchases = len(response["Items"])
        total_spent = sum(
            float(item.get("total_amount", 0)) for item in response["Items"]
        )

        # Calcular estadísticas
        if total_purchases > 0:
            avg_order_value = total_spent / total_purchases

            # Categorías más compradas (simplificado)
            category_stats = {}
            for purchase in response["Items"]:
                for item in purchase.get("items", []):
                    # Esta es una simplificación, en producción necesitarías más datos
                    category = "General"  # Necesitarías obtener la categoría del libro
                    category_stats[category] = category_stats.get(
                        category, 0
                    ) + item.get("quantity", 0)
        else:
            avg_order_value = 0
            category_stats = {}

        return {
            "summary": {
                "total_purchases": total_purchases,
                "total_spent": total_spent,
                "average_order_value": avg_order_value,
                "currency": "USD",
            },
            "category_breakdown": category_stats,
            "user_id": current_user["user_id"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Lambda Handler
handler = Mangum(app)
