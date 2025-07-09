# Attendance System API

A FastAPI-based enterprise backend for an attendance system with face recognition capabilities.

## Features

- User authentication with JWT tokens
- Face recognition-based attendance verification
- Comprehensive attendance tracking and reporting
- Role-based access control
- API versioning
- Detailed logging
- Database migrations with Alembic
- Unit and integration testing

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy ORM with MySQL
- **Authentication**: JWT with OAuth2
- **Face Recognition**: DeepFace
- **Image Processing**: OpenCV
- **Validation**: Pydantic
- **Testing**: Pytest
- **Migrations**: Alembic
- **Caching**: Redis (optional)
- **Background Tasks**: Celery (optional)

## Project Structure

```
absen_backend/
├── alembic/                 # Database migrations
├── app/
│   ├── api/                 # API endpoints
│   │   └── v1/              # API version 1
│   │       └── endpoints/   # API endpoint modules
│   ├── core/                # Core application modules
│   ├── database/            # Database configuration
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic services
│   ├── tests/               # Unit and integration tests
│   └── utils/               # Utility functions
├── logs/                    # Application logs
├── static/                  # Static files
└── uploads/                 # Uploaded files
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- MySQL
- Redis (optional, for caching and background tasks)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/absen_backend.git
   cd absen_backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirement.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your configuration settings.

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

### Running the Application

For development:
```bash
uvicorn app.main:app --reload
```

For production:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Testing

Run tests with pytest:
```bash
pytest
```

Run tests with coverage report:
```bash
pytest --cov=app
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migrations:
```bash
alembic downgrade -1  # Rollback one migration
```

## License

[MIT](LICENSE) 