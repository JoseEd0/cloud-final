# 📋 INFORME COMPLETO DE ENDPOINTS - DOCUMENTACIÓN PARA FRONTEND

**Fecha:** 13 de julio de 2025  
**Versión:** 1.0 - Sistema Completo  
**Estado:** Todos los endpoints verificados y funcionando

---

## 🌐 URLs BASE DE LAS APIS

```
USERS_API     = https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev
BOOKS_API     = https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev
PURCHASES_API = https://fikf4a274g.execute-api.us-east-1.amazonaws.com/dev
IMAGES_API    = https://tn43twlsd7.execute-api.us-east-1.amazonaws.com/dev
ELASTICSEARCH = http://44.222.79.51:9201 (tenant1) / http://44.222.79.51:9202 (tenant2)
```

---

## 🔐 1. AUTENTICACIÓN Y USUARIOS (USERS API)

### 1.1 CREAR USUARIO

```
POST {USERS_API}/api/v1/register?tenant_id=tenant1
Content-Type: application/json

BODY (JSON):
{
    "email": "string",           // REQUERIDO - Email válido
    "password": "string",        // REQUERIDO - Mín 8 caracteres, 1 mayúscula, 1 número, 1 especial
    "first_name": "string",      // REQUERIDO - Nombre
    "last_name": "string",       // REQUERIDO - Apellido
    "phone": "string"           // OPCIONAL - Teléfono
}

RESPUESTA EXITOSA (201):
{
    "message": "Usuario creado exitosamente",
    "user_id": "uuid-string",
    "user": {
        "user_id": "uuid-string",
        "email": "user@example.com",
        "first_name": "Nombre",
        "last_name": "Apellido",
        "phone": "123456789",
        "created_at": "2025-07-13T10:00:00Z",
        "is_active": true
    }
}

ERRORES POSIBLES:
400 - Email ya existe
400 - Password no cumple requisitos
400 - Campos requeridos faltantes
```

### 1.2 LOGIN DE USUARIO

```
POST {USERS_API}/api/v1/login?tenant_id=tenant1
Content-Type: application/json

BODY (JSON):
{
    "email": "string",           // REQUERIDO - Email registrado
    "password": "string"         // REQUERIDO - Password del usuario
}

RESPUESTA EXITOSA (200):
{
    "message": "Login exitoso",
    "token": "simple_token_xxxxxxxx",     // TOKEN DE 1 HORA DE VALIDEZ
    "user": {
        "user_id": "uuid-string",
        "email": "user@example.com",
        "first_name": "Nombre",
        "last_name": "Apellido"
    }
}

ERRORES POSIBLES:
401 - Credenciales inválidas
400 - Campos requeridos faltantes
```

### 1.3 VALIDAR TOKEN

```
GET {USERS_API}/api/v1/validate-token?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

RESPUESTA EXITOSA (200):
{
    "valid": true,
    "user_id": "uuid-string",
    "email": "user@example.com"
}

ERRORES POSIBLES:
401 - Token inválido o expirado
```

### 1.4 ACTUALIZAR IMAGEN DE PERFIL

```
PUT {USERS_API}/api/v1/profile/image?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

BODY (JSON):
{
    "image_url": "string"        // REQUERIDO - URL de imagen en S3
}

RESPUESTA EXITOSA (200):
{
    "message": "Imagen de perfil actualizada",
    "image_url": "https://s3-url-de-imagen"
}
```

---

## 📚 2. GESTIÓN DE LIBROS (BOOKS API)

### 2.1 LISTAR TODOS LOS LIBROS (CON PAGINACIÓN)

```
GET {BOOKS_API}/api/v1/books?tenant_id=tenant1&page=1&limit=10&category=Technology&author=Autor
Authorization: Bearer {token}
Content-Type: application/json

PARÁMETROS QUERY:
- tenant_id: string (REQUERIDO)
- page: number (OPCIONAL, default: 1)
- limit: number (OPCIONAL, default: 10, máx: 100)
- category: string (OPCIONAL - filtro por categoría)
- author: string (OPCIONAL - filtro por autor)

RESPUESTA EXITOSA (200):
{
    "books": [
        {
            "book_id": "uuid-string",
            "isbn": "978-0-123456-78-9",
            "title": "Título del Libro",
            "author": "Autor del Libro",
            "editorial": "Editorial",
            "category": "Categoría",
            "price": 29.99,
            "description": "Descripción del libro",
            "cover_image_url": "https://s3-url",
            "stock_quantity": 50,
            "publication_year": 2024,
            "language": "es",
            "pages": 300,
            "rating": 4.5,
            "is_active": true,
            "created_at": "2025-07-13T10:00:00Z",
            "updated_at": "2025-07-13T10:00:00Z"
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 47,
        "items_per_page": 10
    }
}
```

### 2.2 OBTENER UN LIBRO POR ID

```
GET {BOOKS_API}/api/v1/books/{book_id}?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

RESPUESTA EXITOSA (200):
{
    "book_id": "uuid-string",
    "isbn": "978-0-123456-78-9",
    "title": "Título del Libro",
    "author": "Autor del Libro",
    "editorial": "Editorial",
    "category": "Categoría",
    "price": 29.99,
    "description": "Descripción completa",
    "cover_image_url": "https://s3-url",
    "stock_quantity": 50,
    "publication_year": 2024,
    "language": "es",
    "pages": 300,
    "rating": 4.5,
    "tenant_id": "tenant1",
    "is_active": true,
    "created_at": "2025-07-13T10:00:00Z",
    "updated_at": "2025-07-13T10:00:00Z"
}

ERRORES POSIBLES:
404 - Libro no encontrado
```

### 2.3 CREAR NUEVO LIBRO

```
POST {BOOKS_API}/api/v1/books?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

BODY (JSON):
{
    "isbn": "string",                    // REQUERIDO - ISBN único
    "title": "string",                   // REQUERIDO - Título del libro
    "author": "string",                  // REQUERIDO - Autor
    "editorial": "string",               // REQUERIDO - Editorial
    "category": "string",                // REQUERIDO - Categoría
    "price": 29.99,                     // REQUERIDO - Precio (number)
    "stock_quantity": 50,               // REQUERIDO - Stock (number)
    "description": "string",            // OPCIONAL - Descripción
    "cover_image_url": "string",        // OPCIONAL - URL imagen
    "publication_year": 2024,           // OPCIONAL - Año (number)
    "language": "es",                   // OPCIONAL - Idioma (default: "es")
    "pages": 300,                       // OPCIONAL - Páginas (number)
    "tenant_id": "tenant1"              // REQUERIDO - Tenant
}

RESPUESTA EXITOSA (201):
{
    "message": "Libro creado exitosamente",
    "book_id": "uuid-string",
    "book": { /* objeto libro completo */ }
}

ERRORES POSIBLES:
400 - ISBN ya existe
400 - Campos requeridos faltantes
400 - Tipos de datos incorrectos
```

### 2.4 ACTUALIZAR LIBRO

```
PUT {BOOKS_API}/api/v1/books/{book_id}?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

BODY (JSON): // Todos los campos son OPCIONALES
{
    "title": "string",
    "author": "string",
    "editorial": "string",
    "category": "string",
    "price": 35.99,
    "description": "string",
    "cover_image_url": "string",
    "stock_quantity": 25,
    "publication_year": 2025,
    "language": "en",
    "pages": 350
}

RESPUESTA EXITOSA (200):
{
    "message": "Libro actualizado exitosamente",
    "book": { /* objeto libro actualizado */ }
}
```

### 2.5 ACTUALIZAR IMAGEN DE LIBRO

```
PUT {BOOKS_API}/api/v1/books/{book_id}/image?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

BODY (JSON):
{
    "cover_image_url": "string"         // REQUERIDO - URL de imagen
}

RESPUESTA EXITOSA (200):
{
    "message": "Imagen actualizada exitosamente"
}
```

### 2.6 ELIMINAR LIBRO (SOFT DELETE)

```
DELETE {BOOKS_API}/api/v1/books/{book_id}?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

RESPUESTA EXITOSA (200):
{
    "message": "Libro eliminado exitosamente"
}
```

---

## 🛒 3. SISTEMA DE COMPRAS (PURCHASES API)

### 3.1 OBTENER CARRITO

```
GET {PURCHASES_API}/api/v1/cart?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

RESPUESTA EXITOSA (200):
{
    "cart_items": [
        {
            "cart_item_id": "uuid-string",
            "book_id": "uuid-string",
            "title": "Título del Libro",
            "author": "Autor",
            "price": 29.99,
            "quantity": 2,
            "subtotal": 59.98,
            "cover_image_url": "https://s3-url"
        }
    ],
    "total_items": 2,
    "total_amount": 59.98
}
```

### 3.2 AGREGAR AL CARRITO

```
POST {PURCHASES_API}/api/v1/cart?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

BODY (JSON):
{
    "book_id": "string",                // REQUERIDO - ID del libro
    "quantity": 2,                      // REQUERIDO - Cantidad (number)
    "price": 29.99                      // REQUERIDO - Precio (number)
}

RESPUESTA EXITOSA (201):
{
    "message": "Producto agregado al carrito",
    "cart_item_id": "uuid-string",
    "cart_item": {
        "cart_item_id": "uuid-string",
        "book_id": "uuid-string",
        "quantity": 2,
        "price": 29.99,
        "subtotal": 59.98
    }
}

ERRORES POSIBLES:
404 - Libro no encontrado o no disponible
400 - Stock insuficiente
```

### 3.3 ACTUALIZAR CANTIDAD EN CARRITO

```
PUT {PURCHASES_API}/api/v1/cart/{cart_item_id}?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

BODY (JSON):
{
    "quantity": 3                       // REQUERIDO - Nueva cantidad
}

RESPUESTA EXITOSA (200):
{
    "message": "Cantidad actualizada",
    "cart_item": { /* item actualizado */ }
}
```

### 3.4 ELIMINAR DEL CARRITO

```
DELETE {PURCHASES_API}/api/v1/cart/{cart_item_id}?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

RESPUESTA EXITOSA (200):
{
    "message": "Producto eliminado del carrito"
}
```

### 3.5 LIMPIAR CARRITO

```
POST {PURCHASES_API}/api/v1/cart/clear?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

RESPUESTA EXITOSA (200):
{
    "message": "Carrito limpiado exitosamente"
}
```

### 3.6 REALIZAR CHECKOUT

```
POST {PURCHASES_API}/api/v1/checkout?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

BODY (JSON):
{
    "payment_method": "string",         // REQUERIDO - "credit_card", "debit_card", "paypal"
    "shipping_address": "string"        // REQUERIDO - Dirección de envío
}

RESPUESTA EXITOSA (201):
{
    "message": "Compra realizada exitosamente",
    "order_id": "uuid-string",
    "order": {
        "order_id": "uuid-string",
        "user_id": "uuid-string",
        "total_amount": 129.97,
        "payment_method": "credit_card",
        "shipping_address": "123 Main St",
        "order_status": "confirmed",
        "created_at": "2025-07-13T10:00:00Z",
        "items": [
            {
                "book_id": "uuid-string",
                "title": "Título",
                "quantity": 2,
                "price": 29.99,
                "subtotal": 59.98
            }
        ]
    }
}

ERRORES POSIBLES:
400 - Carrito vacío
400 - Stock insuficiente
```

### 3.7 OBTENER HISTORIAL DE ÓRDENES

```
GET {PURCHASES_API}/api/v1/orders?tenant_id=tenant1&page=1&limit=10
Authorization: Bearer {token}
Content-Type: application/json

RESPUESTA EXITOSA (200):
{
    "orders": [
        {
            "order_id": "uuid-string",
            "total_amount": 129.97,
            "order_status": "confirmed",
            "payment_method": "credit_card",
            "created_at": "2025-07-13T10:00:00Z",
            "items_count": 3
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 2,
        "total_items": 15
    }
}
```

### 3.8 OBTENER DETALLE DE ORDEN

```
GET {PURCHASES_API}/api/v1/orders/{order_id}?tenant_id=tenant1
Authorization: Bearer {token}
Content-Type: application/json

RESPUESTA EXITOSA (200):
{
    "order_id": "uuid-string",
    "user_id": "uuid-string",
    "total_amount": 129.97,
    "payment_method": "credit_card",
    "shipping_address": "123 Main St",
    "order_status": "confirmed",
    "created_at": "2025-07-13T10:00:00Z",
    "items": [
        {
            "book_id": "uuid-string",
            "title": "Título del Libro",
            "author": "Autor",
            "quantity": 2,
            "price": 29.99,
            "subtotal": 59.98,
            "cover_image_url": "https://s3-url"
        }
    ]
}
```

---

## 📷 4. GESTIÓN DE IMÁGENES (IMAGES API)

### 4.1 SUBIR IMAGEN PARA LIBRO

```
POST {IMAGES_API}/api/v1/books/image
Authorization: Bearer {token}
Content-Type: application/json

BODY (JSON):
{
    "book_id": "string",                // REQUERIDO - ID del libro
    "image_data": "string"              // REQUERIDO - Base64 con formato:
                                        // "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
}

RESPUESTA EXITOSA (201):
{
    "message": "Imagen subida exitosamente",
    "image_url": "https://bookstore-images-dev-328458381283.s3.amazonaws.com/default/books/{book_id}/cover_20250713_100000.png",
    "book_id": "uuid-string"
}

FORMATOS SOPORTADOS:
- PNG: "data:image/png;base64,..."
- JPEG: "data:image/jpeg;base64,..."
- JPG: "data:image/jpg;base64,..."

ERRORES POSIBLES:
400 - Formato de imagen inválido
400 - book_id requerido
413 - Imagen muy grande
```

### 4.2 SUBIR IMAGEN DE PERFIL

```
POST {IMAGES_API}/api/v1/users/image
Authorization: Bearer {token}
Content-Type: application/json

BODY (JSON):
{
    "user_id": "string",                // REQUERIDO - ID del usuario
    "image_data": "string"              // REQUERIDO - Base64 con prefijo data:
}

RESPUESTA EXITOSA (201):
{
    "message": "Imagen de perfil subida exitosamente",
    "image_url": "https://bookstore-images-dev-328458381283.s3.amazonaws.com/default/users/{user_id}/profile_20250713_100000.png",
    "user_id": "uuid-string"
}
```

---

## 🔍 5. BÚSQUEDA AVANZADA (ELASTICSEARCH)

### 5.1 BÚSQUEDA FUZZY (TOLERANTE A ERRORES)

```
POST http://44.222.79.51:9201/books/_search
Content-Type: application/json

BODY (JSON):
{
    "query": {
        "fuzzy": {
            "title": {
                "value": "Serverles",           // Busca "Serverless" aunque tenga error
                "fuzziness": "AUTO"
            }
        }
    }
}

RESPUESTA:
{
    "hits": {
        "total": { "value": 1 },
        "hits": [
            {
                "_source": {
                    "book_id": "uuid-string",
                    "title": "AWS Serverless Guide",
                    "author": "Tech Expert",
                    "description": "Complete guide...",
                    "category": "Technology",
                    "price": 35.99
                }
            }
        ]
    }
}
```

### 5.2 BÚSQUEDA POR PREFIJO

```
POST http://44.222.79.51:9201/books/_search
Content-Type: application/json

BODY (JSON):
{
    "query": {
        "prefix": {
            "title": "Java"                     // Encuentra títulos que empiecen con "Java"
        }
    }
}
```

### 5.3 BÚSQUEDA FULL-TEXT

```
POST http://44.222.79.51:9201/books/_search
Content-Type: application/json

BODY (JSON):
{
    "query": {
        "match": {
            "description": "Machine Learning"   // Busca en descripciones
        }
    }
}
```

### 5.4 BÚSQUEDA MULTI-CAMPO

```
POST http://44.222.79.51:9201/books/_search
Content-Type: application/json

BODY (JSON):
{
    "query": {
        "multi_match": {
            "query": "Python",
            "fields": ["title", "description", "author"]
        }
    }
}
```

### 5.5 BÚSQUEDA CON AUTOCOMPLETADO

```
POST http://44.222.79.51:9201/books/_search
Content-Type: application/json

BODY (JSON):
{
    "query": {
        "bool": {
            "should": [
                { "prefix": { "title": "Serv" } },
                { "prefix": { "author": "Serv" } }
            ]
        }
    },
    "size": 5
}
```

---

## 🏷️ 6. CÓDIGOS DE ESTADO HTTP

```
200 - OK: Operación exitosa
201 - Created: Recurso creado exitosamente
400 - Bad Request: Error en la solicitud (campos faltantes/incorrectos)
401 - Unauthorized: Token inválido o faltante
403 - Forbidden: Sin permisos
404 - Not Found: Recurso no encontrado
409 - Conflict: Conflicto (ej: email/ISBN ya existe)
413 - Payload Too Large: Archivo muy grande
500 - Internal Server Error: Error del servidor
```

---

## 🔧 7. HEADERS OBLIGATORIOS

### Para todas las APIs:

```
Content-Type: application/json
```

### Para endpoints protegidos:

```
Authorization: Bearer {token}
```

### Nota sobre tenant_id:

- **Users API**: Se pasa como query parameter: `?tenant_id=tenant1`
- **Books API**: Se pasa como query parameter: `?tenant_id=tenant1`
- **Purchases API**: Se pasa como query parameter: `?tenant_id=tenant1`
- **Images API**: Se extrae automáticamente del token

---

## 🎯 8. FLUJO RECOMENDADO PARA EL FRONTEND

### 8.1 FLUJO DE AUTENTICACIÓN:

1. Usuario se registra → `POST /api/v1/register`
2. Usuario hace login → `POST /api/v1/login` (obtiene token)
3. Guardar token en localStorage/sessionStorage
4. Incluir token en todas las requests posteriores

### 8.2 FLUJO DE GESTIÓN DE LIBROS:

1. Listar libros → `GET /api/v1/books`
2. Ver detalle → `GET /api/v1/books/{id}`
3. Crear libro → `POST /api/v1/books`
4. Subir imagen → `POST /api/v1/books/image`
5. Actualizar libro con URL imagen → `PUT /api/v1/books/{id}/image`

### 8.3 FLUJO DE COMPRAS:

1. Agregar al carrito → `POST /api/v1/cart`
2. Ver carrito → `GET /api/v1/cart`
3. Modificar cantidades → `PUT /api/v1/cart/{item_id}`
4. Hacer checkout → `POST /api/v1/checkout`
5. Ver historial → `GET /api/v1/orders`

### 8.4 FLUJO DE BÚSQUEDA:

1. Búsqueda básica → Books API con filtros
2. Búsqueda avanzada → ElasticSearch
3. Autocompletado → ElasticSearch con prefix

---

## 💡 9. NOTAS IMPORTANTES PARA EL FRONTEND

### 9.1 Manejo de Imágenes:

- Las imágenes se suben como Base64 con prefijo: `data:image/png;base64,{data}`
- Primero subir imagen → obtener URL → luego actualizar libro
- Tamaño máximo recomendado: 5MB

### 9.2 Paginación:

- Siempre incluir page y limit en requests de listado
- Manejar el objeto pagination de la respuesta

### 9.3 Manejo de Errores:

- Siempre verificar status code
- Mostrar mensajes de error apropiados al usuario
- Manejar tokens expirados (401) redirigiendo al login

### 9.4 Multi-tenancy:

- Usar siempre `tenant1` para el proyecto
- Incluir tenant_id en todas las requests como query parameter

---

## ✅ 10. ENDPOINTS VERIFICADOS Y FUNCIONANDO

Todos estos endpoints han sido probados el **13 de julio de 2025** y están **100% funcionales**.

**🚀 ¡Listo para desarrollar el frontend sin errores!**
