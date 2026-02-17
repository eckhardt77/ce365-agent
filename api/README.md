# TechCare Bot - API Backend

FastAPI-basiertes Backend für TechCare Bot.

## Features

✅ **Async PostgreSQL** - SQLAlchemy + asyncpg
✅ **JWT Authentication** - Secure user auth
✅ **SSE Streaming** - Real-time chat responses
✅ **Tool Use API** - Anthropic Claude Tool Use
✅ **Shared Learning** - Team-Wissensdatenbank
✅ **Rate Limiting** - API protection
✅ **Health Checks** - Docker-ready

## Quick Start

### Development

```bash
# Erstelle Virtual Environment
cd api/
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installiere Dependencies
pip install -r requirements.txt

# Spacy Modell
python -m spacy download de_core_news_md

# .env erstellen
cp ../.env.docker.example ../.env
nano ../.env  # API Keys ausfüllen

# Database initialisieren
alembic upgrade head

# Server starten
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API läuft auf: **http://localhost:8000**
Docs: **http://localhost:8000/api/docs**

### Docker

```bash
# Aus root directory
docker build -t techcare-api:latest -f api/Dockerfile .

# Run
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e REDIS_URL=redis://... \
  -e ANTHROPIC_API_KEY=... \
  techcare-api:latest
```

## API Endpoints

### Authentication

```
POST   /api/auth/register    # Register new user
POST   /api/auth/login       # Login user
GET    /api/auth/me          # Get current user
POST   /api/auth/logout      # Logout
```

### Chat

```
POST   /api/chat/conversations                        # Create conversation
GET    /api/chat/conversations                        # List conversations
GET    /api/chat/conversations/{id}                   # Get conversation
GET    /api/chat/conversations/{id}/messages          # Get messages
POST   /api/chat/conversations/{id}/messages/stream   # Chat (SSE)
DELETE /api/chat/conversations/{id}                   # Delete conversation
```

### Tools

```
GET    /api/tools/list           # List all tools
GET    /api/tools/{tool_name}    # Get tool definition
```

### Learning

```
POST   /api/learning/cases              # Save case
GET    /api/learning/cases              # List cases
POST   /api/learning/cases/search       # Search similar cases
GET    /api/learning/cases/{id}         # Get case
POST   /api/learning/cases/{id}/reuse   # Mark reused
```

### Users (Admin)

```
GET    /api/users           # List users
GET    /api/users/{id}      # Get user
PATCH  /api/users/{id}      # Update user
DELETE /api/users/{id}      # Delete user
```

### Health

```
GET    /api/health          # Health check
GET    /api/version         # Version info
```

## Architecture

```
api/
├── main.py                  # FastAPI App
├── config.py                # Settings
├── dependencies.py          # FastAPI Dependencies
├── models/                  # SQLAlchemy Models
│   ├── database.py         # DB Connection
│   ├── user.py
│   ├── conversation.py
│   ├── message.py
│   ├── tool_call.py
│   └── case.py
├── schemas/                 # Pydantic Schemas
│   ├── user.py
│   ├── conversation.py
│   ├── message.py
│   ├── tool_call.py
│   └── case.py
├── routers/                 # API Routes
│   ├── health.py
│   ├── auth.py
│   ├── users.py
│   ├── chat.py
│   ├── tools.py
│   └── learning.py
├── services/                # Business Logic
│   ├── auth_service.py     # JWT, Password Hashing
│   ├── chat_service.py     # Anthropic Tool Use Loop
│   └── license_service.py  # License Validation
└── middleware/              # Custom Middleware
    ├── logging.py          # Request Logging
    └── rate_limit.py       # Rate Limiting
```

## Database Models

### User
- JWT Authentication
- Edition-basierte Repair Limits
- Admin Rolle

### Conversation
- State Machine (IDLE → AUDIT → PLAN → LOCKED → EXECUTING → COMPLETED)
- OS Detection
- User Ownership

### Message
- Chat History
- Token Tracking (Cost)
- Sequence Number

### ToolCall
- Audit Trail für alle Tool-Aufrufe
- Success/Error Tracking
- Approval Flow (Repair Tools)

### Case (Learning System)
- Problem + Solution
- Keyword-basierte Suche
- Reuse Tracking

## Environment Variables

Siehe `.env.docker.example` für alle verfügbaren Variablen.

**Wichtigste:**
- `DATABASE_URL` - PostgreSQL Connection
- `REDIS_URL` - Redis Connection
- `ANTHROPIC_API_KEY` - Claude API Key
- `SECRET_KEY` - App Secret (generiert)
- `JWT_SECRET` - JWT Secret (generiert)

## Testing

```bash
# Unit Tests (TODO)
pytest tests/

# Integration Tests (TODO)
pytest tests/integration/

# Coverage (TODO)
pytest --cov=api tests/
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Upgrade
alembic upgrade head

# Downgrade
alembic downgrade -1
```

## Production Considerations

### Performance
- ✅ Connection pooling (SQLAlchemy)
- ✅ Async I/O (FastAPI + asyncpg)
- ✅ Redis caching
- ✅ Gzip compression

### Security
- ✅ JWT Authentication
- ✅ Rate Limiting
- ✅ Password hashing (bcrypt)
- ✅ PII Detection (Presidio)
- ⚠️ HTTPS (via nginx reverse proxy)

### Monitoring
- ✅ Health checks
- ✅ Request logging
- ✅ Error tracking
- ⚠️ Metrics (TODO: Prometheus)
- ⚠️ Tracing (TODO: OpenTelemetry)

## License

Proprietary - Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
