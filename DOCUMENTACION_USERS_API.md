# 🔐 DOCUMENTACIÓN COMPLETA - USERS API

**Fecha:** 13 de julio de 2025  
**Base URL:** `https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev`  
**Pruebas:** Realizadas en tiempo real  
**Nueva IP EC2:** 35.170.54.115

---

## 📋 **ENDPOINTS PROBADOS Y DOCUMENTADOS**

### ✅ **1. HEALTH CHECK**

**Endpoint:** `GET /`

**Request:**

```bash
curl -X GET "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/"
```

**Response exitosa (200):**

```json
{
  "message": "Users API v2.0.0 - Enhanced",
  "status": "healthy",
  "timestamp": "2025-07-13T13:10:27.891643",
  "method": "GET",
  "path": "/",
  "features": [
    "User Registration & Authentication",
    "Profile Management",
    "Favorites & Wishlist",
    "User Management (Admin)",
    "Enhanced Security"
  ]
}
```

---

### ✅ **2. REGISTRO DE USUARIO**

**Endpoint:** `POST /api/v1/register?tenant_id={tenant_id}`

**Request exitoso:**

```bash
curl -X POST "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/register?tenant_id=tenant1" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_prueba_2",
    "email": "usuario2@test.com",
    "password": "MiPassword123!",
    "first_name": "Carlos",
    "last_name": "Mendez",
    "phone": "555-0002"
  }'
```

**Response exitosa (201):**

```json
{
  "message": "User created successfully",
  "user": {
    "user_id": "d780c13c-60f6-48bd-95b5-6d57a05e56a4",
    "username": "usuario_prueba_2",
    "email": "usuario2@test.com",
    "first_name": "Carlos",
    "last_name": "Mendez",
    "tenant_id": "default",
    "role": "user",
    "created_at": "2025-07-13T13:11:00.125101"
  },
  "token": "simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default"
}
```

**Casos de error:**

_Email duplicado (409):_

```json
{ "error": "User already exists with this email" }
```

_Campos faltantes (400):_

```json
{ "error": "Missing required fields: username, email, password" }
```

_Password débil (400):_

```json
{ "error": "Password must be at least 8 characters long" }
```

---

### ✅ **3. LOGIN DE USUARIO**

**Endpoint:** `POST /api/v1/login?tenant_id={tenant_id}`

**Request exitoso:**

```bash
curl -X POST "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/login?tenant_id=tenant1" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario2@test.com",
    "password": "MiPassword123!"
  }'
```

**Response exitosa (200):**

```json
{
  "message": "Login successful",
  "user": {
    "user_id": "d780c13c-60f6-48bd-95b5-6d57a05e56a4",
    "username": "usuario_prueba_2",
    "email": "usuario2@test.com",
    "first_name": "Carlos",
    "last_name": "Mendez",
    "role": "user",
    "tenant_id": "default"
  },
  "token": "simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default"
}
```

**Casos de error:**

_Credenciales inválidas (401):_

```json
{ "error": "Invalid credentials" }
```

_Campos faltantes (400):_

```json
{ "error": "Missing email or password" }
```

---

### ✅ **4. VALIDAR TOKEN**

**Endpoint:** `GET /api/v1/validate-token?tenant_id={tenant_id}`

**Request exitoso:**

```bash
curl -X GET "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/validate-token?tenant_id=tenant1" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default"
```

**Response exitosa (200):**

```json
{
  "valid": true,
  "user": {
    "user_id": "d780c13c-60f6-48bd-95b5-6d57a05e56a4",
    "username": "usuario_prueba_2",
    "email": "usuario2@test.com",
    "role": "user",
    "tenant_id": "default"
  }
}
```

**Casos de error:**

_Token inválido (401):_

```json
{ "error": "Invalid token", "valid": false }
```

---

### ✅ **5. OBTENER PERFIL**

**Endpoint:** `GET /api/v1/profile?tenant_id={tenant_id}`

**Request:**

```bash
curl -X GET "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/profile?tenant_id=tenant1" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default"
```

**Response exitosa (200):**

```json
{
  "user": {
    "user_id": "d780c13c-60f6-48bd-95b5-6d57a05e56a4",
    "username": "usuario_prueba_2",
    "email": "usuario2@test.com",
    "first_name": "Carlos",
    "last_name": "Mendez",
    "role": "user",
    "tenant_id": "default",
    "is_active": true,
    "email_verified": false,
    "created_at": "2025-07-13T13:11:00.125101",
    "updated_at": "2025-07-13T13:11:00.125110"
  }
}
```

---

### ✅ **6. ACTUALIZAR PERFIL**

**Endpoint:** `PUT /api/v1/profile?tenant_id={tenant_id}`

**Request:**

```bash
curl -X PUT "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/profile?tenant_id=tenant1" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_prueba_2_updated",
    "first_name": "Carlos Eduardo",
    "last_name": "Mendez García",
    "phone": "555-0002-Updated"
  }'
```

**Response exitosa (200):**

```json
{
  "message": "Profile updated successfully",
  "user": {
    "user_id": "d780c13c-60f6-48bd-95b5-6d57a05e56a4",
    "username": "usuario_prueba_2_updated",
    "email": "usuario2@test.com",
    "first_name": "Carlos Eduardo",
    "last_name": "Mendez García",
    "updated_at": "2025-07-13T13:13:00.469404"
  }
}
```

**Casos de error:**

_Campo requerido faltante (400):_

```json
{ "error": "Username is required" }
```

---

### ✅ **7. CAMBIAR PASSWORD**

**Endpoint:** `POST /api/v1/change-password?tenant_id={tenant_id}`

**Request:**

```bash
curl -X POST "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/change-password?tenant_id=tenant1" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "MiPassword123!",
    "new_password": "NuevoPassword456!"
  }'
```

**Response exitosa (200):**

```json
{ "message": "Password changed successfully" }
```

---

### ✅ **8. GESTIÓN DE FAVORITOS**

#### **8.1 Obtener Favoritos**

**Endpoint:** `GET /api/v1/favorites?tenant_id={tenant_id}`

**Request:**

```bash
curl -X GET "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/favorites?tenant_id=tenant1" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default"
```

**Response exitosa (200):**

```json
{
  "items": [
    {
      "book_id": "ec259537-0979-4152-8512-d5d13eb658a6",
      "title": "Unknown",
      "author": "Unknown",
      "price": 0.0,
      "added_at": "2025-07-13T13:13:26.882591"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 1,
    "items_per_page": 10,
    "has_next": false,
    "has_previous": false
  }
}
```

#### **8.2 Agregar a Favoritos**

**Endpoint:** `POST /api/v1/favorites?tenant_id={tenant_id}`

**Request:**

```bash
curl -X POST "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/favorites?tenant_id=tenant1" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "ec259537-0979-4152-8512-d5d13eb658a6"}'
```

**Response exitosa (201):**

```json
{ "message": "Book added to favorites" }
```

---

### ✅ **9. GESTIÓN DE WISHLIST**

#### **9.1 Obtener Wishlist**

**Endpoint:** `GET /api/v1/wishlist?tenant_id={tenant_id}`

**Request:**

```bash
curl -X GET "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/wishlist?tenant_id=tenant1" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default"
```

**Response exitosa (200):**

```json
{
  "items": [],
  "pagination": {
    "current_page": 1,
    "total_pages": 0,
    "total_items": 0,
    "items_per_page": 10,
    "has_next": false,
    "has_previous": false
  }
}
```

#### **9.2 Agregar a Wishlist**

**Endpoint:** `POST /api/v1/wishlist?tenant_id={tenant_id}`

**Request:**

```bash
curl -X POST "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/wishlist?tenant_id=tenant1" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": "3a467af1-ab97-4e70-a1e2-8dcae68675fd",
    "title": "AWS Serverless Guide",
    "author": "Tech Expert"
  }'
```

**Response exitosa (201):**

```json
{ "message": "Book added to wishlist" }
```

**Casos de error:**

_Campos requeridos faltantes (400):_

```json
{ "error": "book_id, title, and author are required" }
```

---

### ✅ **10. OBTENER USUARIOS (Admin)**

**Endpoint:** `GET /api/v1/users?tenant_id={tenant_id}`

**Request:**

```bash
curl -X GET "https://tf6775wga9.execute-api.us-east-1.amazonaws.com/dev/api/v1/users?tenant_id=tenant1" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default"
```

**Response de error (403):**

```json
{ "error": "Admin access required" }
```

---

## 🔧 **NOTAS TÉCNICAS**

### **Autenticación:**

- Todos los endpoints protegidos requieren el header: `Authorization: Bearer {token}`
- Los tokens tienen el formato: `simple_token_{user_id}_{tenant_id}`
- Los tokens se obtienen en register y login

### **Parámetros comunes:**

- `tenant_id`: Requerido en query string para multi-tenancy
- Todos los requests con body requieren: `Content-Type: application/json`

### **Códigos de respuesta:**

- `200`: Operación exitosa
- `201`: Recurso creado exitosamente
- `400`: Error en request (campos faltantes, validación)
- `401`: No autorizado (token inválido)
- `403`: Acceso denegado (permisos insuficientes)
- `409`: Conflicto (recurso ya existe)

### **Campos de validación:**

- **Password**: Mínimo 8 caracteres
- **Email**: Debe ser válido y único
- **Username**: Requerido para registro y actualización
- **tenant_id**: Requerido en todos los endpoints

## 🎯 **RESUMEN DE FUNCIONALIDADES PROBADAS**

✅ Health Check  
✅ Registro de usuario  
✅ Login con token  
✅ Validación de token  
✅ Obtener perfil  
✅ Actualizar perfil  
✅ Cambiar password  
✅ Gestión de favoritos (get/post)  
✅ Gestión de wishlist (get/post)  
✅ Control de acceso admin

**Total endpoints funcionales:** 10 endpoint principales con sub-funcionalidades  
**Estado general:** ✅ COMPLETAMENTE FUNCIONAL
