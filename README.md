# Guesty Integration Microservice

This is a FastAPI-based microservice following DDD and SOLID principles. It manages user authentication, roles, and Guesty webhook subscriptions.

## Features

- JWT authentication
- User roles (Admin, Owner)
- Domain-driven design
- SQLAlchemy integration (SQLite by default)
- Easily extendable and testable structure

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- Pydantic
- Passlib
- python-jose
- SQLite (dev) / PostgreSQL (prod-ready)

## Setup

1. **Install dependencies**

```bash
pip install -r requirements.txt
