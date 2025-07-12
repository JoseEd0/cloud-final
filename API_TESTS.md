# Test API Endpoints

## Users API

### Registrar usuario

```bash
curl -X POST [TU-USERS-API-URL]/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456",
    "first_name": "Test",
    "last_name": "User",
    "tenant_id": "tenant1"
  }'
```

### Login

```bash
curl -X POST [TU-USERS-API-URL]/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456",
    "tenant_id": "tenant1"
  }'
```

## Books API

### Crear libro

```bash
curl -X POST [TU-BOOKS-API-URL]/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-1234567890",
    "title": "Libro de Prueba",
    "author": "Autor Test",
    "editorial": "Editorial Test",
    "category": "Technology",
    "price": 29.99,
    "stock_quantity": 100,
    "tenant_id": "tenant1"
  }'
```

### Listar libros

```bash
curl "[TU-BOOKS-API-URL]/api/v1/books?tenant_id=tenant1&page=1&limit=10"
```

## Purchases API

### Ver carrito (necesita token)

```bash
curl -X GET [TU-PURCHASES-API-URL]/api/v1/cart \
  -H "Authorization: Bearer [TU-TOKEN]"
```

### Agregar al carrito (necesita token)

```bash
curl -X POST [TU-PURCHASES-API-URL]/api/v1/cart/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [TU-TOKEN]" \
  -d '{
    "book_id": "[BOOK-ID-OBTENIDO-ANTERIORMENTE]",
    "quantity": 2
  }'
```
