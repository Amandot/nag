# AI-Based Public Grievance Prioritization & Resolution System - Backend

## Overview

This is the backend API for the Grievance Prioritization System, built with Flask and Python. It provides intelligent complaint processing using NLP and ML to automatically categorize, prioritize, and route citizen grievances.

**Local development:** the app runs on port 5000 by default so that the React front‑end (which uses
`REACT_APP_API_URL=http://localhost:5000/api` from `.env`) can reach it without additional
configuration.  Set the `PORT` environment variable to `7860` when deploying to Hugging Face
Spaces or any environment that requires a specific port.


## Project Structure

```
backend/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── models/                # Database models
├── routes/                # API endpoints
├── services/              # Business logic
├── utils/                 # Utility functions
├── tests/                 # Test suite
├── ml_models/             # Trained ML models
├── logs/                  # Application logs
└── uploads/               # User uploaded files
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

### 4. Initialize Database

```bash
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 5. Run the Application

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login

### Complaints
- `POST /api/complaints` - Submit new complaint
- `GET /api/complaints/:id` - Get complaint details
- `GET /api/complaints/:id/history` - Get complaint history
- `GET /api/users/:id/complaints` - Get user's complaints
- `POST /api/complaints/:id/feedback` - Submit feedback

### Admin
- `GET /api/admin/heatmap` - Get complaint heatmap data
- `GET /api/admin/analytics/trends` - Get category trends
- `GET /api/admin/analytics/departments` - Get department performance
- `GET /api/admin/analytics/resolution-times` - Get resolution time analytics
- `GET /api/admin/alerts` - Get critical alerts

## Testing

Run tests with pytest:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=. --cov-report=html
```

## Development

- Use Python 3.9 or higher
- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation as needed

## License

Government Project - Internal Use Only
