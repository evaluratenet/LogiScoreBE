# LogiScore Backend API

FastAPI backend for the LogiScore freight forwarder review platform.

## Features

- **Authentication**: GitHub OAuth with JWT tokens
- **Database**: PostgreSQL with Supabase
- **API**: RESTful API with automatic documentation
- **Security**: JWT authentication, CORS, rate limiting
- **Payment**: Stripe integration for subscriptions

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database (Supabase)
- GitHub OAuth app
- Stripe account

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/LogiScore/backend.git
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `SUPABASE_SERVICE_KEY` | Supabase service key | Yes |
| `JWT_SECRET_KEY` | Secret for JWT tokens | Yes |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | Yes |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret | Yes |
| `STRIPE_SECRET_KEY` | Stripe secret key | Yes |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | Yes |

## API Endpoints

### Authentication
- `POST /api/users/auth/github` - GitHub OAuth authentication
- `GET /api/users/me` - Get current user info
- `GET /api/users/{user_id}` - Get user by ID

### Freight Forwarders
- `GET /api/freight-forwarders/` - List freight forwarders
- `GET /api/freight-forwarders/{id}` - Get specific freight forwarder
- `GET /api/freight-forwarders/{id}/branches` - Get branches

### Reviews
- `GET /api/reviews/` - List reviews
- `POST /api/reviews/` - Create new review
- `GET /api/reviews/{id}` - Get specific review

### Search
- `GET /api/search/freight-forwarders` - Search freight forwarders
- `GET /api/search/suggestions` - Get search suggestions

## Development

### Project Structure

```
logiscore-backend/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── database/              # Database configuration
│   ├── database.py        # Database connection
│   └── models.py          # SQLAlchemy models
├── auth/                  # Authentication
│   └── auth.py           # JWT and OAuth logic
├── routes/               # API routes
│   ├── users.py          # User endpoints
│   ├── freight_forwarders.py
│   ├── reviews.py        # Review endpoints
│   └── search.py         # Search endpoints
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Database Migrations

The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations.

## Deployment

### Render Deployment

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render dashboard

### Environment Variables for Production

Make sure to set all required environment variables in your deployment platform.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary software for LogiScore. # Database initialization fix
# Database initialization fix
# Database initialization fix
# Trigger redeploy
# Trigger redeploy
# Force redeploy Fri Aug  1 01:38:37 +08 2025
