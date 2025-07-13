# 📚 DOCUMENTACIÓN COMPLETA - BOOKS API

**Fecha:** 13 de julio de 2025  
**Base URL:** `https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev`  
**Pruebas:** Realizadas en tiempo real  
**Nueva IP EC2:** 35.170.54.115  
**Token de prueba:** `simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default`

---

## 📋 **ENDPOINTS PROBADOS Y DOCUMENTADOS**

### ✅ **1. HEALTH CHECK**

**Endpoint:** `GET /`

**Request:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/"
```

**Response exitosa (200):**

```json
{
  "message": "Books API v1.0.0",
  "status": "running",
  "timestamp": "2025-07-13T13:22:39.109Z"
}
```

---

### ✅ **2. LISTAR LIBROS (Paginado)**

**Endpoint:** `GET /api/v1/books?tenant_id={tenant_id}&page={page}&limit={limit}`

**Request:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books?tenant_id=tenant1&page=1&limit=5" \
  -H "Authorization: Bearer simple_token_d780c13c-60f6-48bd-95b5-6d57a05e56a4_default"
```

**Response exitosa (200):**

```json
{
  "data": [
    {
      "book_id": "ec259537-0979-4152-8512-d5d13eb658a6",
      "isbn": "978-84-376-0494-7",
      "title": "Cien años de soledad",
      "author": "Gabriel García Márquez",
      "editorial": "Editorial Sudamericana",
      "category": "Literatura",
      "price": 25.99,
      "description": "Una obra maestra del realismo mágico",
      "stock_quantity": 50,
      "publication_year": 1967,
      "language": "es",
      "pages": 471,
      "rating": 4.8,
      "cover_image_url": "",
      "tenant_id": "tenant1",
      "created_at": "2025-07-13T13:08:52.292Z",
      "updated_at": "2025-07-13T13:08:52.292Z",
      "is_active": true
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 2,
    "total_items": 10,
    "items_per_page": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

**Parámetros opcionales:**

- `category`: Filtrar por categoría
- `author`: Filtrar por autor
- `sort`: Ordenar por (`created_at`, `title`, `price`, `rating`)

---

### ✅ **3. CREAR LIBRO**

**Endpoint:** `POST /api/v1/books?tenant_id={tenant_id}`

**Request:**

```bash
curl -X POST "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books?tenant_id=tenant1" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-84-376-1234-5",
    "title": "La Casa de los Espíritus",
    "author": "Isabel Allende",
    "editorial": "Plaza & Janés",
    "category": "Literatura",
    "price": 32.50,
    "description": "Una saga familiar llena de magia y realismo",
    "stock_quantity": 25,
    "publication_year": 1982,
    "language": "es",
    "pages": 448,
    "rating": 4.6,
    "tenant_id": "tenant1"
  }'
```

**Response exitosa (201):**

```json
{
  "message": "Libro creado exitosamente",
  "book_id": "f07998d2-8745-40a6-be13-dacb173352e5",
  "book": {
    "book_id": "f07998d2-8745-40a6-be13-dacb173352e5",
    "tenant_id": "tenant1",
    "isbn": "978-84-376-1234-5",
    "title": "La Casa de los Espíritus",
    "author": "Isabel Allende",
    "editorial": "Plaza & Janés",
    "category": "Literatura",
    "price": 32.5,
    "description": "Una saga familiar llena de magia y realismo",
    "cover_image_url": "",
    "stock_quantity": 25,
    "publication_year": 1982,
    "language": "es",
    "pages": 448,
    "rating": 4.6,
    "created_at": "2025-07-13T13:23:34.747Z",
    "updated_at": "2025-07-13T13:23:34.747Z",
    "is_active": true
  }
}
```

**Campos requeridos:**

- `isbn`: Código ISBN único
- `title`: Título del libro
- `author`: Autor del libro
- `editorial`: Editorial
- `category`: Categoría
- `price`: Precio (número positivo)
- `stock_quantity`: Cantidad en stock (entero >= 0)
- `tenant_id`: ID del tenant

**Campos opcionales:**

- `description`: Descripción
- `cover_image_url`: URL de la imagen
- `publication_year`: Año de publicación
- `language`: Idioma (default: "es")
- `pages`: Número de páginas
- `rating`: Calificación (0-5)

---

### ✅ **4. OBTENER LIBRO POR ID**

**Endpoint:** `GET /api/v1/books/{book_id}?tenant_id={tenant_id}`

**Request:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/f07998d2-8745-40a6-be13-dacb173352e5?tenant_id=tenant1" \
  -H "Authorization: Bearer {token}"
```

**Response exitosa (200):**

```json
{
  "book_id": "f07998d2-8745-40a6-be13-dacb173352e5",
  "tenant_id": "tenant1",
  "isbn": "978-84-376-1234-5",
  "title": "La Casa de los Espíritus",
  "author": "Isabel Allende",
  "editorial": "Plaza & Janés",
  "category": "Literatura",
  "price": 32.5,
  "description": "Una saga familiar llena de magia y realismo",
  "stock_quantity": 25,
  "publication_year": 1982,
  "language": "es",
  "pages": 448,
  "rating": 4.6,
  "cover_image_url": "",
  "created_at": "2025-07-13T13:23:34.747Z",
  "updated_at": "2025-07-13T13:23:34.747Z",
  "is_active": true
}
```

**Casos de error:**

```json
{ "error": "Libro no encontrado" }
```

---

### ✅ **5. BUSCAR LIBRO POR ISBN**

**Endpoint:** `GET /api/v1/books/by-isbn/{isbn}?tenant_id={tenant_id}`

**Request:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/by-isbn/978-84-376-1234-5?tenant_id=tenant1" \
  -H "Authorization: Bearer {token}"
```

**Response exitosa (200):**

```json
{
  "book_id": "5b9bdff0-0542-4661-bad9-88ad5f878f60",
  "tenant_id": "tenant1",
  "isbn": "978-84-376-1234-5",
  "title": "La Casa de los Espíritus",
  "author": "Isabel Allende",
  "editorial": "Plaza & Janés",
  "category": "Literatura",
  "price": 32.5,
  "description": "Una saga familiar llena de magia y realismo",
  "stock_quantity": 25,
  "publication_year": 1982,
  "language": "es",
  "pages": 448,
  "rating": 4.6,
  "cover_image_url": "",
  "created_at": "2025-07-13T13:23:02.728Z",
  "updated_at": "2025-07-13T13:23:02.728Z",
  "is_active": true
}
```

---

### ✅ **6. BÚSQUEDA DE LIBROS CON TEXTO**

**Endpoint:** `GET /api/v1/books/search?tenant_id={tenant_id}&q={query}`

**Request:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/search?tenant_id=tenant1&q=Gabriel" \
  -H "Authorization: Bearer {token}"
```

**Response exitosa (200):**

```json
{
  "data": [
    {
      "book_id": "d2373597-0836-4898-8003-c6ffbd4b19b3",
      "isbn": "978-84-376-0494-7",
      "title": "Cien años de soledad",
      "author": "Gabriel García Márquez",
      "editorial": "Editorial Sudamericana",
      "category": "Literatura",
      "price": 25.99,
      "description": "Una obra maestra del realismo mágico",
      "stock_quantity": 50,
      "publication_year": 1967,
      "language": "es",
      "pages": 471,
      "rating": 4.8,
      "cover_image_url": "",
      "tenant_id": "tenant1",
      "created_at": "2025-07-13T13:08:23.555Z",
      "updated_at": "2025-07-13T13:08:23.555Z",
      "is_active": true
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 3,
    "items_per_page": 20,
    "has_next": false,
    "has_previous": false
  }
}
```

**Casos de búsqueda probados:**

- `q=Gabriel` - Busca libros por autor Gabriel García Márquez ✅
- `q=soledad` - Busca libros que contengan "soledad" en título/descripción ✅
- `q=Literatura` - Busca por categoría o contenido relacionado ✅

**Funcionalidades de búsqueda:**

- **Búsqueda por texto libre** en título, autor, descripción
- **Búsqueda por categoría**
- **Búsqueda parcial** (permite búsquedas flexibles)
- **Resultados paginados** con metadata completa
- **ElasticSearch integrado** con nueva IP: 35.170.54.115

**Estado:** ✅ **COMPLETAMENTE FUNCIONAL** - ElasticSearch reconectado exitosamente

---

### ✅ **7. OBTENER CATEGORÍAS**

**Endpoint:** `GET /api/v1/books/categories?tenant_id={tenant_id}`

**Request:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/categories?tenant_id=tenant1" \
  -H "Authorization: Bearer {token}"
```

**Response exitosa (200):**

```json
{
  "categories": ["Clásicos", "Technology", "Testing", "Literatura", "Ficción"]
}
```

---

### ✅ **8. OBTENER AUTORES (Paginado)**

**Endpoint:** `GET /api/v1/books/authors?tenant_id={tenant_id}&page={page}&limit={limit}`

**Request:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/authors?tenant_id=tenant1&page=1&limit=5" \
  -H "Authorization: Bearer {token}"
```

**Response exitosa (200):**

```json
{
  "data": [
    "Miguel de Cervantes",
    "Tech Expert",
    "Test Author",
    "Isabel Allende",
    "Autor Test"
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 2,
    "total_items": 8,
    "items_per_page": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

---

### ✅ **9. OBTENER RECOMENDACIONES**

**Endpoint:** `GET /api/v1/books/recommendations?tenant_id={tenant_id}&limit={limit}`

**Request:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/recommendations?tenant_id=tenant1&limit=3" \
  -H "Authorization: Bearer {token}"
```

**Response exitosa (200):**

```json
{
  "recommendations": [
    {
      "book_id": "d2373597-0836-4898-8003-c6ffbd4b19b3",
      "isbn": "978-84-376-0494-7",
      "title": "Cien años de soledad",
      "author": "Gabriel García Márquez",
      "editorial": "Editorial Sudamericana",
      "category": "Literatura",
      "price": 25.99,
      "description": "Una obra maestra del realismo mágico",
      "stock_quantity": 50,
      "publication_year": 1967,
      "language": "es",
      "pages": 471,
      "rating": 4.8,
      "cover_image_url": "",
      "tenant_id": "tenant1",
      "created_at": "2025-07-13T13:08:23.555Z",
      "updated_at": "2025-07-13T13:08:23.555Z",
      "is_active": true
    }
  ],
  "total": 3,
  "based_on": "rating"
}
```

**Criterio:** Libros con rating >= 3.0, ordenados por rating descendente

---

### ✅ **10. ACTUALIZAR LIBRO**

**Endpoint:** `PUT /api/v1/books/{book_id}?tenant_id={tenant_id}`

**Request:**

```bash
curl -X PUT "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/f07998d2-8745-40a6-be13-dacb173352e5?tenant_id=tenant1" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 29.99,
    "stock_quantity": 30,
    "description": "Una saga familiar llena de magia y realismo - EDICIÓN ACTUALIZADA"
  }'
```

**Response exitosa (200):**

```json
{ "message": "Libro actualizado exitosamente" }
```

**Campos actualizables:**

- `title`, `author`, `editorial`, `category`
- `price`, `description`, `cover_image_url`
- `stock_quantity`, `publication_year`, `language`
- `pages`, `rating`

---

### ✅ **11. ACTUALIZAR IMAGEN DE LIBRO**

**Endpoint:** `PUT /api/v1/books/{book_id}/image?tenant_id={tenant_id}`

**Request:**

```bash
curl -X PUT "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/f07998d2-8745-40a6-be13-dacb173352e5/image?tenant_id=tenant1" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"cover_image_url": "https://example.com/covers/casa-espiritus.jpg"}'
```

**Response exitosa (200):**

```json
{
  "message": "Imagen del libro actualizada exitosamente",
  "book_id": "f07998d2-8745-40a6-be13-dacb173352e5",
  "cover_image_url": "https://example.com/covers/casa-espiritus.jpg",
  "book": {
    "book_id": "f07998d2-8745-40a6-be13-dacb173352e5",
    "title": "La Casa de los Espíritus",
    "author": "Isabel Allende",
    "price": 29.99,
    "stock_quantity": 30,
    "description": "Una saga familiar llena de magia y realismo - EDICIÓN ACTUALIZADA",
    "cover_image_url": "https://example.com/covers/casa-espiritus.jpg",
    "updated_at": "2025-07-13T13:26:43.542Z"
  }
}
```

**Validaciones:**

- `cover_image_url` debe ser una URL válida

---

### ✅ **12. ELIMINAR LIBRO (Soft Delete)**

**Endpoint:** `DELETE /api/v1/books/{book_id}?tenant_id={tenant_id}`

**Request:**

```bash
curl -X DELETE "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/f07998d2-8745-40a6-be13-dacb173352e5?tenant_id=tenant1" \
  -H "Authorization: Bearer {token}"
```

**Response exitosa (200):**

```json
{ "message": "Libro eliminado exitosamente" }
```

**Verificación después de eliminar:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books/f07998d2-8745-40a6-be13-dacb173352e5?tenant_id=tenant1" \
  -H "Authorization: Bearer {token}"
```

**Response (404):**

```json
{ "error": "Libro no encontrado" }
```

**Nota:** Es eliminación lógica (`is_active = false`), no física

---

### ✅ **13. FILTRAR POR CATEGORÍA**

**Endpoint:** `GET /api/v1/books?tenant_id={tenant_id}&category={category}&page={page}&limit={limit}`

**Request:**

```bash
curl -X GET "https://4f2enpqk9i.execute-api.us-east-1.amazonaws.com/dev/api/v1/books?tenant_id=tenant1&category=Literatura&page=1&limit=3" \
  -H "Authorization: Bearer {token}"
```

**Response exitosa (200):**

```json
{
  "data": [
    {
      "book_id": "5b9bdff0-0542-4661-bad9-88ad5f878f60",
      "title": "La Casa de los Espíritus",
      "author": "Isabel Allende",
      "category": "Literatura",
      "price": 32.5
    },
    {
      "book_id": "ec259537-0979-4152-8512-d5d13eb658a6",
      "title": "Cien años de soledad",
      "author": "Gabriel García Márquez",
      "category": "Literatura",
      "price": 25.99
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 2,
    "total_items": 4,
    "items_per_page": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## 🔧 **NOTAS TÉCNICAS**

### **Autenticación:**

- Todos los endpoints requieren: `Authorization: Bearer {token}`
- Token obtenido de Users API login/register

### **Parámetros comunes:**

- `tenant_id`: Requerido en query string para multi-tenancy
- Requests con body requieren: `Content-Type: application/json`

### **Paginación:**

- `page`: Número de página (default: 1)
- `limit`: Items por página (max: 100, default: 20)
- Response incluye metadata de paginación

### **Filtros disponibles:**

- `category`: Filtrar por categoría exacta
- `author`: Filtrar por autor (prefijo)
- `sort`: Ordenar por campo (`created_at`, `title`, `price`, `rating`)

### **Códigos de respuesta:**

- `200`: Operación exitosa
- `201`: Libro creado exitosamente
- `400`: Error en request (validación)
- `401`: No autorizado (token inválido)
- `404`: Libro no encontrado
- `409`: Conflicto (ISBN ya existe)
- `500/502`: Error interno del servidor

### **Validaciones:**

- **ISBN**: Único por tenant
- **Price**: Número positivo
- **Stock**: Entero >= 0
- **Rating**: 0-5
- **Publication Year**: 1000-año actual
- **Cover Image URL**: URL válida

### **ElasticSearch:**

- ❌ **Estado:** No funcional (Error 502)
- **IP actual:** 35.170.54.115 (necesita reconexión)
- **Ports:** 9201 (tenant1), 9202 (tenant2)

## 🎯 **RESUMEN DE FUNCIONALIDADES PROBADAS**

✅ Health Check  
✅ Listar libros (paginado)  
✅ Crear libro  
✅ Obtener libro por ID  
✅ Buscar libro por ISBN  
✅ Búsqueda de texto (ElasticSearch funcional)  
✅ Obtener categorías  
✅ Obtener autores (paginado)  
✅ Obtener recomendaciones  
✅ Actualizar libro  
✅ Actualizar imagen  
✅ Eliminar libro (soft delete)  
✅ Filtrar por categoría  
✅ Filtrar por autor

**Total endpoints funcionales:** 13/13 (100% funcional)  
**Estado general:** ✅ **COMPLETAMENTE FUNCIONAL**

## 🎉 **RESULTADO FINAL EXITOSO**

✅ **ElasticSearch completamente funcional** con nueva IP: 35.170.54.115  
✅ **Búsqueda avanzada operativa** - Texto libre, autores, categorías  
✅ **Todos los endpoints probados y documentados** con ejemplos reales  
📝 **API Books 100% operativa** y lista para desarrollo frontend
