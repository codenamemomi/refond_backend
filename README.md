# REE-FOND API

A comprehensive FastAPI-based backend system for tax management and compliance in Nigeria. Built with modern Python technologies to handle taxpayer registration, organization management, audit logging, and role-based access control.

## 🚀 Features

### Core Functionality
- **User Management**: Multi-role user system (Admin, Accountant, Employer, Organization)
- **Organization Management**: Support for accounting firms, employers, and fintech companies
- **Taxpayer Management**: Comprehensive taxpayer profiles for individuals and businesses
- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **Audit Logging**: Complete audit trail for all system actions
- **Tax Compliance**: Support for various Nigerian tax types (PAYE, VAT, CIT, WHT, PIT)

### Technical Features
- **Asynchronous Database**: PostgreSQL with async SQLAlchemy
- **Auto-generated API Docs**: Interactive Swagger UI at `/docs`
- **CORS Support**: Configurable cross-origin resource sharing
- **Data Validation**: Pydantic schemas with comprehensive validation
- **Migration Support**: Alembic for database schema management
- **Security**: Argon2 password hashing, JWT tokens, secure configurations

## 🛠 Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with async SQLAlchemy
- **ORM**: SQLAlchemy 2.0 (async)
- **Migration**: Alembic
- **Authentication**: JWT (jose)
- **Password Hashing**: Argon2 (passlib)
- **Validation**: Pydantic
- **ASGI Server**: Uvicorn
- **Testing**: pytest
- **Environment**: python-dotenv

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 12+
- pip (Python package manager)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/codenamemomi/refond_backend
   cd refond_backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Database
   DATABASE_URL=postgresql+asyncpg://username:password@localhost/dbname
   DATABASE_SYNC_URL=postgresql://username:password@localhost/dbname

   # Security
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

   # API
   DEBUG=True
   PROJECT_NAME="REE-FOND API"
   VERSION="1.0.0"

   # CORS
   # Add your frontend URLs
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🏗 Project Structure

```
refond_backend/
├── alembic/                 # Database migrations
├── api/
│   ├── db/
│   │   └── session.py       # Database session management
│   ├── utils/
│   │   └── exceptions.py    # Custom exceptions
│   └── v1/
│       ├── dependencies.py  # FastAPI dependencies
│       ├── models/          # SQLAlchemy models
│       │   ├── audit_log.py
│       │   ├── base.py
│       │   ├── taxpayer.py
│       │   └── user.py
│       ├── routes/          # API route handlers
│       │   ├── auth.py
│       │   └── taxpayer.py
│       ├── schemas/         # Pydantic schemas
│       │   ├── taxpayer.py
│       │   └── user.py
│       └── services/        # Business logic
│           ├── audit_service.py
│           ├── auth_service.py
│           ├── taxpayer_service.py
│           └── user_service.py
├── core/
│   ├── config.py            # Application configuration
│   └── security.py          # Security utilities
├── test/                    # Test files
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── alembic.ini             # Alembic configuration
└── README.md               # This file
```

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### User Roles & Permissions

- **ADMIN**: Full system access
- **ACCOUNTANT**: Organization-specific taxpayer management
- **EMPLOYER**: Employee taxpayer management within their organization
- **ORGANIZATION**: Limited access to organization data

## 🗄 Database Schema

### Core Tables

- **users**: System users with roles and organization associations
- **organizations**: Companies, accounting firms, employers
- **taxpayers**: Individual and business taxpayers
- **audit_logs**: Complete audit trail of all actions

### Key Relationships

- Users belong to Organizations
- Organizations have multiple Users and Taxpayers
- Taxpayers are associated with Employers (Organizations)
- All actions are logged in audit_logs

## 🧪 Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=api --cov-report=html
```

## 🚀 Deployment

### Production Setup

1. Set `DEBUG=False` in your environment
2. Use a production WSGI server like Gunicorn
3. Configure proper database credentials
4. Set up SSL/TLS certificates
5. Use environment variables for all sensitive data

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN alembic upgrade head

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints for all function parameters
- Ensure all tests pass before submitting PR

## 📝 API Endpoints Overview

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/verify` - Verify user account

### Taxpayers
- `GET /api/v1/taxpayers` - List taxpayers (with filtering/pagination)
- `POST /api/v1/taxpayers` - Create taxpayer
- `GET /api/v1/taxpayers/{id}` - Get taxpayer details
- `PUT /api/v1/taxpayers/{id}` - Update taxpayer
- `DELETE /api/v1/taxpayers/{id}` - Delete taxpayer
- `POST /api/v1/taxpayers/{id}/verify` - Verify taxpayer
- `POST /api/v1/taxpayers/bulk` - Bulk create taxpayers
- `GET /api/v1/taxpayers/stats/summary` - Taxpayer statistics

### Organizations
- Organization management endpoints (to be implemented)

## 🔍 Monitoring & Logging

- All API requests are logged with user context
- Audit logs track all data modifications
- Database queries are logged in debug mode
- Structured logging with timestamps and context

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the codebase for implementation details

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**REE-FOND API** - Empowering tax compliance through technology.
