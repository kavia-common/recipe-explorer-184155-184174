# Recipe Explorer Backend API

FastAPI backend implementing users, auth (opaque token), recipes CRUD with ratings, and search, using a layered architecture and in-memory storage.

## Features
- Health check `/`
- Users:
  - `POST /users/register` (rejects duplicate email/username)
  - `POST /users/login` (OAuth2 password flow; returns bearer token and expiry)
  - `GET /users/me` (requires Authorization)
- Recipes:
  - `GET /recipes` with pagination and filters (`tags`, `cuisine`, `time_max`)
  - `POST /recipes` (auth required)
  - `GET /recipes/{id}`
  - `PUT /recipes/{id}` (owner only)
  - `DELETE /recipes/{id}` (owner only)
  - `POST /recipes/{id}/rate` (auth required, 1..5, per-user upsert)
- Search:
  - `GET /search` with pagination and filters

## Error format
All errors return:
```json
{ "error": { "code": "string", "message": "string", "details": {} } }
```

## Auth
- OAuth2PasswordBearer advertised, backed by an HMAC-signed opaque token with in-memory store and expiry.
- Password hashing uses salted SHA-256 (non-production).

## Run
```bash
uvicorn src.api.main:app --reload --port 3001
```

## Environment
Copy `.env.example` to `.env` and update:
- SECRET_KEY
- TOKEN_EXP_MINUTES
- CORS_ALLOW_ORIGINS
- SITE_URL

## Dev Notes
- Pydantic v2 schemas.
- Thread-safe in-memory repos with locks.
- Request/response logging with method, path, status, duration, and user_id.
- No external DB dependencies; suitable for CI/demo. 
