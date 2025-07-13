# Instrucciones para desplegar Stream Processors

Los Stream Processors se deben desplegar DESPUÉS de que las tablas DynamoDB estén creadas.

## Orden correcto de despliegue:

1. Infraestructura principal (crea las tablas)
2. APIs (users, books, purchases)
3. Stream Processors (último, depende de las tablas)

## Comando para verificar que las tablas existen:

```bash
aws dynamodb list-tables
```

Debe mostrar:

- bookstore-users-dev
- bookstore-books-dev
- bookstore-purchases-dev
- bookstore-user-favorites-dev
- bookstore-user-wishlist-dev

Solo después de confirmar que las tablas existen, desplegar:

```bash
cd services/stream-processors
serverless deploy --stage dev
```
