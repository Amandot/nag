# 🏛️ NagrikSathi - AI-Based Public Grievance Prioritization & Resolution System

A comprehensive web-based platform that leverages Artificial Intelligence and Natural Language Processing to intelligently prioritize, categorize, and route citizen grievances to appropriate government departments for efficient resolution.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![React](https://img.shields.io/badge/React-18.2.0-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-4.9.5-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [ML Models](#-ml-models)
- [Security Features](#-security-features)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### Core Functionality
- **Intelligent Complaint Submission**: Citizens can submit grievances with location, description, and media attachments
- **AI-Powered Categorization**: Automatic classification of complaints into relevant government departments
- **Smart Prioritization**: ML-based priority scoring considering severity, location sensitivity, and impact
- **Duplicate Detection**: Identifies and clusters similar complaints to prevent redundancy
- **Real-time Tracking**: Citizens can track complaint status and resolution progress
- **Multi-language Support**: Language detection and translation capabilities
- **Feedback System**: Post-resolution feedback collection for continuous improvement

### Advanced Features
- **SLA Monitoring**: Automated tracking of Service Level Agreement deadlines
- **Escalation Management**: Automatic escalation of overdue complaints
- **Analytics Dashboard**: Comprehensive insights for administrators
- **Heatmap Visualization**: Geographic visualization of complaint hotspots
- **Critical Alerts**: Real-time notifications for high-priority issues
- **Trust Score System**: User credibility scoring based on complaint history

### Security & Compliance
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Citizen, Officer, and Admin roles
- **Data Encryption**: Secure handling of sensitive information
- **HTTPS Support**: SSL/TLS configuration for production
- **Input Validation**: Comprehensive validation and sanitization
- **CORS Protection**: Configured Cross-Origin Resource Sharing

## 🏗️ System Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  React Frontend │◄───────►│  Flask Backend  │◄───────►│   SQLite DB     │
│   (Port 3000)   │         │   (Port 5000)   │         │                 │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
            │              │  │           │  │             │
            │  ML Models   │  │    NLP    │  │ Notification│
            │  (sklearn)   │  │  (NLTK)   │  │  Services   │
            │              │  │           │  │             │
            └──────────────┘  └───────────┘  └─────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 3.0.0
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **ORM**: SQLAlchemy 2.0.23
- **Authentication**: Flask-JWT-Extended 4.6.0
- **ML/AI**: 
  - scikit-learn 1.3.2 (Classification)
  - NLTK 3.8.1 (Text Processing)
  - spaCy 3.7.2 (NLP)
  - langdetect 1.0.9 (Language Detection)
- **Data Processing**: pandas 2.1.4, numpy 1.26.2
- **Task Scheduling**: APScheduler 3.10.4

### Frontend
- **Framework**: React 18.2.0
- **Language**: TypeScript 4.9.5
- **Routing**: React Router DOM 6.20.0
- **HTTP Client**: Axios 1.6.0
- **Maps**: Leaflet 1.9.4 + React Leaflet 4.2.1
- **Charts**: Recharts 3.7.0
- **Build Tool**: React Scripts 5.0.1

### External Services (Optional)
- **Maps**: Google Maps API
- **Translation**: Google Cloud Translate API
- **SMS**: Twilio
- **Email**: SendGrid

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: 3.8 or higher
- **Node.js**: 14 or higher
- **npm**: 6 or higher
- **Git**: Latest version

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd nagriksathi
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

# Create environment file
copy .env.example .env  # Windows
# OR
cp .env.example .env    # macOS/Linux

# Initialize database
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create environment file
copy .env.example .env  # Windows
# OR
cp .env.example .env    # macOS/Linux
```

## ⚙️ Configuration

### Backend Configuration (backend/.env)

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DATABASE_URL=sqlite:///grievance.db
# For production: postgresql://user:password@localhost:5432/grievance

# External APIs (Optional)
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
GOOGLE_TRANSLATE_API_KEY=your-translate-api-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-phone
SENDGRID_API_KEY=your-sendgrid-key
SENDER_EMAIL=noreply@yourdomain.com

# SSL/TLS (Production)
SSL_CERT_FILE=/path/to/certificate.crt
SSL_KEY_FILE=/path/to/private.key
```

### Frontend Configuration (frontend/.env)

```env
REACT_APP_API_URL=http://localhost:5000/api
```

### Generate Secret Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

## 🎯 Running the Application

### Development Mode

#### Start Backend Server

```bash
cd backend
python app.py
```

Backend will run on: http://localhost:5000

#### Start Frontend Server

```bash
cd frontend
npm start
```

Frontend will run on: http://localhost:3000

### Access the Application

Open your browser and navigate to: http://localhost:3000

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "phone": "1234567890",
  "email": "john@example.com",
  "password": "securepassword"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "credential": "john@example.com",  // Email or phone
  "password": "securepassword"
}
```

### Complaint Endpoints

#### Submit Complaint
```http
POST /api/complaints
Authorization: Bearer <token>
Content-Type: application/json

{
  "description": "Street light not working",
  "location": {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "address": "Connaught Place, New Delhi"
  },
  "media_urls": []
}
```

#### Get User Complaints
```http
GET /api/complaints/user/<user_id>
Authorization: Bearer <token>
```

#### Get Complaint Details
```http
GET /api/complaints/<complaint_id>
Authorization: Bearer <token>
```

#### Submit Feedback
```http
POST /api/complaints/<complaint_id>/feedback
Authorization: Bearer <token>
Content-Type: application/json

{
  "rating": 5,
  "comments": "Issue resolved quickly"
}
```

### Admin Endpoints

#### Get Heatmap Data
```http
GET /api/admin/heatmap
Authorization: Bearer <token>
```

#### Get Analytics
```http
GET /api/admin/analytics/trends
GET /api/admin/analytics/departments
GET /api/admin/analytics/resolution-times
Authorization: Bearer <token>
```

## 📁 Project Structure

```
nagriksathi/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── config.py              # Configuration settings
│   ├── requirements.txt       # Python dependencies
│   ├── models/                # Database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── complaint.py
│   │   ├── officer.py
│   │   └── feedback.py
│   ├── routes/                # API endpoints
│   │   ├── auth.py
│   │   ├── complaints.py
│   │   └── admin.py
│   ├── services/              # Business logic
│   │   ├── ml_classifier.py
│   │   ├── nlp_engine.py
│   │   ├── priority_scoring.py
│   │   ├── duplicate_detection.py
│   │   ├── routing_service.py
│   │   ├── notification_service.py
│   │   └── monitoring_service.py
│   ├── utils/                 # Utility functions
│   │   ├── authorization.py
│   │   ├── anonymization.py
│   │   └── https_config.py
│   ├── ml_models/             # Trained ML models
│   │   ├── classifier.pkl
│   │   ├── vectorizer.pkl
│   │   └── train_classifier.py
│   ├── migrations/            # Database migrations
│   ├── tests/                 # Unit and integration tests
│   └── logs/                  # Application logs
│
├── frontend/
│   ├── package.json           # Node dependencies
│   ├── tsconfig.json          # TypeScript configuration
│   ├── public/                # Static files
│   └── src/
│       ├── App.tsx            # Main application component
│       ├── index.tsx          # Entry point
│       ├── api/               # API client
│       │   ├── client.ts
│       │   ├── auth.ts
│       │   ├── complaints.ts
│       │   └── admin.ts
│       ├── components/        # Reusable components
│       │   ├── Navigation.tsx
│       │   ├── FeedbackForm.tsx
│       │   ├── ComplaintHeatmap.tsx
│       │   ├── AnalyticsCharts.tsx
│       │   └── CriticalAlerts.tsx
│       └── pages/             # Page components
│           ├── Login.tsx
│           ├── Register.tsx
│           ├── Dashboard.tsx
│           ├── SubmitComplaint.tsx
│           ├── ComplaintDetails.tsx
│           └── AdminDashboard.tsx
│
├── .gitignore
└── README.md
```

## 🤖 ML Models

### Complaint Classification Model

The system uses a trained scikit-learn classifier to automatically categorize complaints:

- **Algorithm**: TF-IDF Vectorization + Multinomial Naive Bayes
- **Categories**: Water Supply, Electricity, Roads & Infrastructure, Healthcare, Public Safety, Sanitation
- **Training Data**: Located in `backend/ml_models/training_data.csv`

### Training the Model

```bash
cd backend/ml_models
python train_classifier.py
```

This generates:
- `classifier.pkl` - Trained classification model
- `vectorizer.pkl` - TF-IDF vectorizer

### Priority Scoring Algorithm

Priority is calculated based on:
1. **Severity Terms** (40%): Presence of critical keywords
2. **Location Sensitivity** (30%): Proximity to sensitive locations
3. **User Trust Score** (20%): Historical user credibility
4. **Duplicate Count** (10%): Number of similar complaints

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication with secure token generation
- Role-based access control (RBAC) for Citizens, Officers, and Admins
- Password hashing using bcrypt
- Token expiration and refresh mechanisms

### Data Protection
- Input validation and sanitization
- SQL injection prevention via SQLAlchemy ORM
- XSS protection with Content Security Policy headers
- CSRF protection for state-changing operations
- Secure file upload handling

### HTTPS/TLS
- SSL/TLS support for production deployments
- Configurable certificate paths
- Automatic HTTPS redirection
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## 🚀 Deployment

### Production Deployment

The system is production-ready with comprehensive deployment options:

#### Quick Deploy with Docker (Recommended)

```bash
# 1. Configure environment
cp .env.production.example .env
# Edit .env with your settings

# 2. Deploy
./deploy.sh  # Linux/Mac
# OR
.\deploy.ps1  # Windows

# 3. Create admin user
docker-compose exec backend python create_admin.py
```

#### Deployment Options

- **Docker Compose**: Containerized deployment with PostgreSQL, backend, and frontend
- **Kubernetes**: Scalable deployment with auto-scaling and load balancing
- **Cloud Platforms**: AWS, Heroku, DigitalOcean, Google Cloud
- **Manual**: Traditional server deployment with Nginx and Gunicorn

#### Deployment Features

✅ Health check endpoints for monitoring  
✅ Automated deployment scripts  
✅ CI/CD pipeline (GitHub Actions)  
✅ SSL/TLS configuration  
✅ Database migrations  
✅ Backup and recovery procedures  
✅ Security hardening  
✅ Performance optimization  

#### Quick Links

- [DEPLOYMENT_README.md](DEPLOYMENT_README.md) - Quick deployment guide
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Comprehensive deployment guide
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Step-by-step checklist
- [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) - Security hardening guide

### Health Check Endpoints

```bash
# Basic health check
curl http://localhost:5000/api/health

# Database connection
curl http://localhost:5000/api/health/db

# ML models status
curl http://localhost:5000/api/health/ml

# Readiness probe (Kubernetes)
curl http://localhost:5000/api/health/ready

# Liveness probe (Kubernetes)
curl http://localhost:5000/api/health/live
```

### Production Environment

For production deployment:
- Use PostgreSQL instead of SQLite
- Configure SSL/TLS certificates
- Set up proper firewall rules
- Enable monitoring and logging
- Configure automated backups
- Use strong secret keys
- Set up external API services (optional)

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for detailed instructions.

## 👥 User Roles

### Citizen
- Submit complaints
- Track complaint status
- Provide feedback
- View personal complaint history

### Officer
- View assigned complaints
- Update complaint status
- Resolve complaints
- Access department-specific analytics

### Admin
- Full system access
- View analytics dashboard
- Monitor SLA compliance
- Manage users and officers
- Access heatmap and critical alerts

## 📊 Key Metrics

The system tracks:
- **Response Time**: Time from submission to first response
- **Resolution Time**: Time from submission to resolution
- **SLA Compliance**: Percentage of complaints resolved within deadline
- **User Satisfaction**: Average feedback ratings
- **Category Distribution**: Complaints by department
- **Priority Distribution**: Complaints by priority level
- **Geographic Hotspots**: Areas with high complaint density

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards
- Follow PEP 8 for Python code
- Use ESLint and Prettier for TypeScript/React code
- Write unit tests for new features
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Support

For support and queries:
- **Email**: support@grievance.gov
- **Documentation**: Full API documentation available in `API_DOCUMENTATION.md`
- **Issues**: Report bugs via GitHub Issues

## 🙏 Acknowledgments

- Built with Flask and React
- ML models powered by scikit-learn
- Maps powered by Leaflet and OpenStreetMap
- Icons and UI components from various open-source libraries

---

**Made with ❤️ for better citizen services**
