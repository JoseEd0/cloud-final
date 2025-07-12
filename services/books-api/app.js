const express = require('express');
const cors = require('cors');
const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');
const Joi = require('joi');
const serverless = require('serverless-http');
const { Client } = require('elasticsearch');

// Configuración
const app = express();
const dynamodb = new AWS.DynamoDB.DocumentClient({
    region: process.env.DYNAMODB_REGION || 'us-east-1'
});

const elasticsearch = new Client({
    host: process.env.ELASTICSEARCH_HOST || 'http://localhost:9200'
});

const BOOKS_TABLE = process.env.BOOKS_TABLE || 'bookstore-books-dev';

// Middleware
app.use(cors());
app.use(express.json());

// Schemas de validación
const bookSchema = Joi.object({
    isbn: Joi.string().required(),
    title: Joi.string().required(),
    author: Joi.string().required(),
    editorial: Joi.string().required(),
    category: Joi.string().required(),
    price: Joi.number().positive().required(),
    description: Joi.string().allow(''),
    cover_image_url: Joi.string().uri().allow(''),
    stock_quantity: Joi.number().integer().min(0).required(),
    publication_year: Joi.number().integer().min(1000).max(new Date().getFullYear()),
    language: Joi.string().default('es'),
    pages: Joi.number().integer().positive(),
    rating: Joi.number().min(0).max(5).default(0),
    tenant_id: Joi.string().required()
});

const updateBookSchema = Joi.object({
    title: Joi.string(),
    author: Joi.string(),
    editorial: Joi.string(),
    category: Joi.string(),
    price: Joi.number().positive(),
    description: Joi.string().allow(''),
    cover_image_url: Joi.string().uri().allow(''),
    stock_quantity: Joi.number().integer().min(0),
    publication_year: Joi.number().integer().min(1000).max(new Date().getFullYear()),
    language: Joi.string(),
    pages: Joi.number().integer().positive(),
    rating: Joi.number().min(0).max(5)
});

// Utilidades
const createPaginationResponse = (items, page, limit, totalItems = null) => {
    const totalPages = totalItems ? Math.ceil(totalItems / limit) : Math.ceil(items.length / limit);
    return {
        data: items,
        pagination: {
            current_page: page,
            total_pages: totalPages,
            total_items: totalItems || items.length,
            items_per_page: limit,
            has_next: page < totalPages,
            has_previous: page > 1
        }
    };
};

const generateBookId = () => uuidv4();

// Rutas

// Health check
app.get('/', (req, res) => {
    res.json({ 
        message: 'Books API v1.0.0', 
        status: 'running',
        timestamp: new Date().toISOString()
    });
});

// Obtener todos los libros con filtros y paginación
app.get('/api/v1/books', async (req, res) => {
    try {
        const {
            page = 1,
            limit = 20,
            category,
            author,
            sort = 'created_at',
            tenant_id
        } = req.query;

        if (!tenant_id) {
            return res.status(400).json({ error: 'tenant_id es requerido' });
        }

        const pageNum = parseInt(page);
        const limitNum = parseInt(limit);

        let params = {
            TableName: BOOKS_TABLE,
            KeyConditionExpression: 'pk = :pk',
            ExpressionAttributeValues: {
                ':pk': `${tenant_id}#BOOKS`
            },
            ScanIndexForward: sort === 'created_at' ? false : true
        };

        // Aplicar filtros
        if (category) {
            params.IndexName = 'GSI1';
            params.KeyConditionExpression = 'gsi1pk = :gsi1pk AND begins_with(gsi1sk, :category)';
            params.ExpressionAttributeValues = {
                ':gsi1pk': `${tenant_id}#CATEGORY`,
                ':category': category
            };
        }

        if (author) {
            params.IndexName = 'GSI2';
            params.KeyConditionExpression = 'gsi2pk = :gsi2pk AND begins_with(gsi2sk, :author)';
            params.ExpressionAttributeValues = {
                ':gsi2pk': `${tenant_id}#AUTHOR`,
                ':author': author
            };
        }

        const result = await dynamodb.query(params).promise();
        
        // Paginación manual
        const startIndex = (pageNum - 1) * limitNum;
        const endIndex = startIndex + limitNum;
        const paginatedItems = result.Items.slice(startIndex, endIndex);

        const response = createPaginationResponse(paginatedItems, pageNum, limitNum, result.Items.length);
        res.json(response);

    } catch (error) {
        console.error('Error obteniendo libros:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Crear nuevo libro
app.post('/api/v1/books', async (req, res) => {
    try {
        const { error, value } = bookSchema.validate(req.body);
        if (error) {
            return res.status(400).json({ error: error.details[0].message });
        }

        const bookId = generateBookId();
        const now = new Date().toISOString();

        const bookItem = {
            pk: `${value.tenant_id}#${bookId}`,
            sk: `BOOK#${value.isbn}`,
            gsi1pk: `${value.tenant_id}#CATEGORY`,
            gsi1sk: `${value.category}#${bookId}`,
            gsi2pk: `${value.tenant_id}#AUTHOR`,
            gsi2sk: `${value.author}#${bookId}`,
            book_id: bookId,
            tenant_id: value.tenant_id,
            isbn: value.isbn,
            title: value.title,
            author: value.author,
            editorial: value.editorial,
            category: value.category,
            price: value.price,
            description: value.description || '',
            cover_image_url: value.cover_image_url || '',
            stock_quantity: value.stock_quantity,
            publication_year: value.publication_year,
            language: value.language || 'es',
            pages: value.pages || 0,
            rating: value.rating || 0,
            created_at: now,
            updated_at: now,
            is_active: true
        };

        await dynamodb.put({
            TableName: BOOKS_TABLE,
            Item: bookItem,
            ConditionExpression: 'attribute_not_exists(pk)'
        }).promise();

        res.status(201).json({
            message: 'Libro creado exitosamente',
            book_id: bookId,
            book: bookItem
        });

    } catch (error) {
        if (error.code === 'ConditionalCheckFailedException') {
            return res.status(409).json({ error: 'El libro ya existe' });
        }
        console.error('Error creando libro:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Obtener libro por ID
app.get('/api/v1/books/:book_id', async (req, res) => {
    try {
        const { book_id } = req.params;
        const { tenant_id } = req.query;

        if (!tenant_id) {
            return res.status(400).json({ error: 'tenant_id es requerido' });
        }

        // Primero intentamos buscar directamente
        const params = {
            TableName: BOOKS_TABLE,
            KeyConditionExpression: 'pk = :pk',
            ExpressionAttributeValues: {
                ':pk': `${tenant_id}#${book_id}`
            }
        };

        const result = await dynamodb.query(params).promise();

        if (result.Items.length === 0) {
            return res.status(404).json({ error: 'Libro no encontrado' });
        }

        res.json(result.Items[0]);

    } catch (error) {
        console.error('Error obteniendo libro:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Actualizar libro
app.put('/api/v1/books/:book_id', async (req, res) => {
    try {
        const { book_id } = req.params;
        const { tenant_id } = req.query;

        if (!tenant_id) {
            return res.status(400).json({ error: 'tenant_id es requerido' });
        }

        const { error, value } = updateBookSchema.validate(req.body);
        if (error) {
            return res.status(400).json({ error: error.details[0].message });
        }

        // Buscar el libro actual
        const getCurrentBook = await dynamodb.query({
            TableName: BOOKS_TABLE,
            KeyConditionExpression: 'pk = :pk',
            ExpressionAttributeValues: {
                ':pk': `${tenant_id}#${book_id}`
            }
        }).promise();

        if (getCurrentBook.Items.length === 0) {
            return res.status(404).json({ error: 'Libro no encontrado' });
        }

        const currentBook = getCurrentBook.Items[0];

        // Construir la expresión de actualización
        let updateExpression = 'SET updated_at = :updated_at';
        let expressionAttributeValues = {
            ':updated_at': new Date().toISOString()
        };

        Object.keys(value).forEach(key => {
            updateExpression += `, ${key} = :${key}`;
            expressionAttributeValues[`:${key}`] = value[key];
        });

        await dynamodb.update({
            TableName: BOOKS_TABLE,
            Key: {
                pk: currentBook.pk,
                sk: currentBook.sk
            },
            UpdateExpression: updateExpression,
            ExpressionAttributeValues: expressionAttributeValues
        }).promise();

        res.json({ message: 'Libro actualizado exitosamente' });

    } catch (error) {
        console.error('Error actualizando libro:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Eliminar libro
app.delete('/api/v1/books/:book_id', async (req, res) => {
    try {
        const { book_id } = req.params;
        const { tenant_id } = req.query;

        if (!tenant_id) {
            return res.status(400).json({ error: 'tenant_id es requerido' });
        }

        // Buscar el libro actual
        const getCurrentBook = await dynamodb.query({
            TableName: BOOKS_TABLE,
            KeyConditionExpression: 'pk = :pk',
            ExpressionAttributeValues: {
                ':pk': `${tenant_id}#${book_id}`
            }
        }).promise();

        if (getCurrentBook.Items.length === 0) {
            return res.status(404).json({ error: 'Libro no encontrado' });
        }

        const currentBook = getCurrentBook.Items[0];

        // Soft delete
        await dynamodb.update({
            TableName: BOOKS_TABLE,
            Key: {
                pk: currentBook.pk,
                sk: currentBook.sk
            },
            UpdateExpression: 'SET is_active = :is_active, updated_at = :updated_at',
            ExpressionAttributeValues: {
                ':is_active': false,
                ':updated_at': new Date().toISOString()
            }
        }).promise();

        res.json({ message: 'Libro eliminado exitosamente' });

    } catch (error) {
        console.error('Error eliminando libro:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Buscar libros
app.get('/api/v1/books/search', async (req, res) => {
    try {
        const {
            q,
            fuzzy = 'true',
            page = 1,
            limit = 20,
            tenant_id
        } = req.query;

        if (!tenant_id) {
            return res.status(400).json({ error: 'tenant_id es requerido' });
        }

        if (!q) {
            return res.status(400).json({ error: 'Parámetro de búsqueda "q" es requerido' });
        }

        const pageNum = parseInt(page);
        const limitNum = parseInt(limit);

        try {
            // Intentar búsqueda en Elasticsearch
            const searchBody = {
                query: {
                    bool: {
                        must: [
                            {
                                term: {
                                    tenant_id: tenant_id
                                }
                            },
                            {
                                multi_match: {
                                    query: q,
                                    fields: ['title^3', 'author^2', 'description', 'category'],
                                    fuzziness: fuzzy === 'true' ? 'AUTO' : '0'
                                }
                            }
                        ]
                    }
                },
                from: (pageNum - 1) * limitNum,
                size: limitNum,
                sort: [
                    { _score: { order: 'desc' } },
                    { created_at: { order: 'desc' } }
                ]
            };

            const searchResult = await elasticsearch.search({
                index: `books_${tenant_id}`,
                body: searchBody
            });

            const books = searchResult.body.hits.hits.map(hit => hit._source);
            const totalItems = searchResult.body.hits.total.value || searchResult.body.hits.total;

            const response = createPaginationResponse(books, pageNum, limitNum, totalItems);
            res.json(response);

        } catch (esError) {
            console.log('Elasticsearch no disponible, usando DynamoDB scan:', esError.message);
            
            // Fallback a DynamoDB scan
            const params = {
                TableName: BOOKS_TABLE,
                FilterExpression: 'contains(title, :q) OR contains(author, :q) OR contains(description, :q) OR contains(category, :q)',
                ExpressionAttributeValues: {
                    ':q': q
                }
            };

            const result = await dynamodb.scan(params).promise();
            
            // Filtrar por tenant_id
            const filteredItems = result.Items.filter(item => item.tenant_id === tenant_id);
            
            // Paginación manual
            const startIndex = (pageNum - 1) * limitNum;
            const endIndex = startIndex + limitNum;
            const paginatedItems = filteredItems.slice(startIndex, endIndex);

            const response = createPaginationResponse(paginatedItems, pageNum, limitNum, filteredItems.length);
            res.json(response);
        }

    } catch (error) {
        console.error('Error en búsqueda:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Obtener libro por ISBN
app.get('/api/v1/books/by-isbn/:isbn', async (req, res) => {
    try {
        const { isbn } = req.params;
        const { tenant_id } = req.query;

        if (!tenant_id) {
            return res.status(400).json({ error: 'tenant_id es requerido' });
        }

        const params = {
            TableName: BOOKS_TABLE,
            FilterExpression: 'isbn = :isbn AND tenant_id = :tenant_id',
            ExpressionAttributeValues: {
                ':isbn': isbn,
                ':tenant_id': tenant_id
            }
        };

        const result = await dynamodb.scan(params).promise();

        if (result.Items.length === 0) {
            return res.status(404).json({ error: 'Libro no encontrado' });
        }

        res.json(result.Items[0]);

    } catch (error) {
        console.error('Error obteniendo libro por ISBN:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Obtener categorías
app.get('/api/v1/books/categories', async (req, res) => {
    try {
        const { tenant_id } = req.query;

        if (!tenant_id) {
            return res.status(400).json({ error: 'tenant_id es requerido' });
        }

        const params = {
            TableName: BOOKS_TABLE,
            IndexName: 'GSI1',
            KeyConditionExpression: 'gsi1pk = :gsi1pk',
            ExpressionAttributeValues: {
                ':gsi1pk': `${tenant_id}#CATEGORY`
            },
            ProjectionExpression: 'category'
        };

        const result = await dynamodb.query(params).promise();
        
        // Extraer categorías únicas
        const categories = [...new Set(result.Items.map(item => item.category))];

        res.json({ categories });

    } catch (error) {
        console.error('Error obteniendo categorías:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Obtener autores
app.get('/api/v1/books/authors', async (req, res) => {
    try {
        const { page = 1, limit = 50, tenant_id } = req.query;

        if (!tenant_id) {
            return res.status(400).json({ error: 'tenant_id es requerido' });
        }

        const pageNum = parseInt(page);
        const limitNum = parseInt(limit);

        const params = {
            TableName: BOOKS_TABLE,
            IndexName: 'GSI2',
            KeyConditionExpression: 'gsi2pk = :gsi2pk',
            ExpressionAttributeValues: {
                ':gsi2pk': `${tenant_id}#AUTHOR`
            },
            ProjectionExpression: 'author'
        };

        const result = await dynamodb.query(params).promise();
        
        // Extraer autores únicos
        const authors = [...new Set(result.Items.map(item => item.author))];
        
        // Paginación
        const startIndex = (pageNum - 1) * limitNum;
        const endIndex = startIndex + limitNum;
        const paginatedAuthors = authors.slice(startIndex, endIndex);

        const response = createPaginationResponse(paginatedAuthors, pageNum, limitNum, authors.length);
        res.json(response);

    } catch (error) {
        console.error('Error obteniendo autores:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Recomendaciones (simplificado)
app.get('/api/v1/books/recommendations/:user_id', async (req, res) => {
    try {
        const { user_id } = req.params;
        const { tenant_id, limit = 10 } = req.query;

        if (!tenant_id) {
            return res.status(400).json({ error: 'tenant_id es requerido' });
        }

        // Por ahora, retornamos libros aleatorios con mejor rating
        const params = {
            TableName: BOOKS_TABLE,
            KeyConditionExpression: 'begins_with(pk, :pk_prefix)',
            ExpressionAttributeValues: {
                ':pk_prefix': `${tenant_id}#`
            },
            FilterExpression: 'rating >= :min_rating',
            ExpressionAttributeValues: {
                ...{ ':pk_prefix': `${tenant_id}#` },
                ':min_rating': 4.0
            },
            Limit: parseInt(limit)
        };

        const result = await dynamodb.query(params).promise();

        res.json({
            recommendations: result.Items,
            user_id: user_id,
            based_on: 'rating'
        });

    } catch (error) {
        console.error('Error obteniendo recomendaciones:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Error handler
app.use((error, req, res, next) => {
    console.error('Error no manejado:', error);
    res.status(500).json({ error: 'Error interno del servidor' });
});

// Export para Lambda
module.exports.handler = serverless(app);
