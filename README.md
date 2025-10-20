# MojDom API

Backend API for a mobile real estate rental application. Built with FastAPI, SQLAlchemy (async), and PostgreSQL. Docker setup and detailed documentation are included.

## Table of contents

- Overview
- Features
- Architecture
- Tech stack
- Project structure
- Getting started
  - Prerequisites
  - Local setup
  - Run with Docker
- Environment variables
- API documentation
- Deployment
- Contact

## Overview

MojDom API provides REST endpoints for:
- User lifecycle: registration and device info
- Search and pagination of rental listings (via external listings service)
- User filters and settings persistence
- Districts and partner adverts retrieval


## Features

- FastAPI async application with lifespan hooks
- Centralized error handling middleware
- CORS configured (tighten for production)
- Async SQLAlchemy + PostgreSQL with data-access helpers
- External HTTP integrations with timeouts
- Containerized with Docker and Compose

## Architecture

- Entry point: `app/main.py`
- Routers: `app/routers/api.py`, `app/routers/public.py`
- Schemas: `app/schemas/api_schemas.py`
- Models: `app/models/db_models.py`
- Services: `app/services/` (email, external listings, user)
- Config: `app/config.py` using `pydantic-settings`
- Error middleware: `app/middleware/error_handler.py`

See `Architecture.md` for diagrams and detailed interactions.

## Tech stack

- Python 3.11
- FastAPI, Uvicorn
- PostgreSQL 17, SQLAlchemy 2 (async), asyncpg
- httpx, aiohttp
- pydantic v2, pydantic-settings
- structlog, python-dotenv

Full pinned versions in `requirements.txt`. Details in `TechStack.md`.

## Project structure

```
MojDom/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ database.py
│  ├─ pg_data_acces.py
│  ├─ models/
│  │  └─ db_models.py
│  ├─ schemas/
│  │  └─ api_schemas.py
│  ├─ routers/
│  │  ├─ api.py
│  │  └─ public.py
│  ├─ services/
│  │  ├─ database_service.py
│  │  ├─ district_mapping_service.py
│  │  ├─ email_service.py
│  │  └─ external_listings_service.py
│  └─ middleware/
│     └─ error_handler.py
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ env.example
├─ Makefile
├─ nginx.conf
└─ run.py

```

## Getting started

### Prerequisites

- Python 3.11+
- PostgreSQL 17 recommended
- Docker and Docker Compose (optional)
- Git

### Local setup

```
# Clone repository
git clone <repository-url>
cd MojDom

# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env to set DATABASE_URL and other settings

# Run API
python run.py
# or
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

API will be available at `http://localhost:8081`. Swagger UI at `/docs`.

### Run with Docker

```
cp env.example .env
# Adjust variables as needed

docker-compose up -d
# Check logs
docker-compose logs -f mojdom-api
```

The service/container name defaults to `mojdom-api` (see `docker-compose.yml`).

## Environment variables

Key variables (see `env.example` for full list):

- `DEBUG` — enable debug mode
- `DATABASE_URL` — e.g. `postgresql+asyncpg://user:pass@host:5432/db`
- `PUBLIC_TOKEN` — public API token for public routes
- `EXTERNAL_LISTINGS_URL`, `EXTERNAL_LISTINGS_ENDPOINT`, `EXTERNAL_LISTINGS_TIMEOUT`
- `POSTGRES_*` — Database settings
- `SENDGRID_API_KEY`

Configuration is loaded via `pydantic-settings` from `.env`.


## API documentation

- Swagger UI: `http://localhost:8081/docs`
- ReDoc: `http://localhost:8081/redoc`
- OpenAPI schema: `http://localhost:8081/openapi.json`


## Deployment

- Dockerfile and `docker-compose.yml` included
- Example Nginx reverse proxy in `nginx.conf`

## Contact

- Email: info@rentme.group