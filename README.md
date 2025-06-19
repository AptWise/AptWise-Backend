# AptWise Backend API

This project is a FastAPI backend for the AptWise application with authentication and PostgreSQL DB integration.

## Features

- FastAPI for high-performance REST API
- JWT-based authentication with cookie storage
- User registration, login, and account management
- PostgreSQL integration for persistent data storage

## Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- PostgreSQL (local installation or Docker)

## Getting Started with PostgreSQL

### Option 1: Using Docker

```bash
# Pull the PostgreSQL image
docker pull postgres:latest

# Run the PostgreSQL container
docker run --name aptwisedb-postgres -e POSTGRES_USER=aptwise -e POSTGRES_PASSWORD=aptwise -e POSTGRES_DB=aptwisedb -p 5432:5432 -d postgres:latest

# Check the container status
docker ps
```

### Option 2: Local Installation

Follow the installation guide for your operating system from the [PostgreSQL website](https://www.postgresql.org/download/).

## Environment Variables

Set the following environment variables or configure them in your deployment:

- `SECRET_KEY`: JWT secret key
- `DB_HOST`: PostgreSQL host (default: 127.0.0.1)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_NAME`: PostgreSQL database name (default: aptwisedb)
- `DB_USER`: PostgreSQL username (default: aptwise)
- `DB_PASSWORD`: PostgreSQL password (default: aptwise)

## Installation and Setup

```bash
# Clone the repository
git clone https://github.com/your-username/aptwisedb.git
cd aptwisedb

# Install dependencies with poetry
poetry install

# Run the FastAPI server
poetry run python -m src.test_poetry_cicd.main
```

The API will be available at http://localhost:8000.

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc