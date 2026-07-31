# Grievance System - Frontend

React-based frontend for the AI-Based Public Grievance Prioritization & Resolution System.

## Features

- User registration and authentication with JWT
- Complaint submission with location detection
- Real-time complaint tracking
- Priority and status visualization
- Feedback submission for resolved complaints
- Responsive design

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your backend API URL:
```
REACT_APP_API_URL=http://localhost:5000/api
```

4. Start development server:
```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

## Available Scripts

- `npm start` - Run development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App (one-way operation)

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios configuration
│   │   ├── auth.ts            # Authentication API
│   │   └── complaints.ts      # Complaints API
│   ├── components/
│   │   ├── Navigation.tsx     # Navigation bar
│   │   └── FeedbackForm.tsx   # Feedback form component
│   ├── pages/
│   │   ├── Register.tsx       # Registration page
│   │   ├── Login.tsx          # Login page
│   │   ├── Dashboard.tsx      # User dashboard
│   │   ├── SubmitComplaint.tsx # Complaint submission
│   │   └── ComplaintDetails.tsx # Complaint tracking
│   ├── App.tsx                # Main app component
│   └── index.tsx              # Entry point
└── package.json
```

## API Integration

The frontend communicates with the backend API using Axios. All API calls include JWT authentication tokens stored in localStorage.

### Authentication Flow

1. User registers or logs in
2. Backend returns JWT token
3. Token stored in localStorage
4. Token included in all subsequent API requests
5. Automatic redirect to login on 401 errors

### Protected Routes

All routes except `/register` and `/login` require authentication. Unauthenticated users are redirected to the login page.

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 1.1**: User registration with name, phone, email, password
- **Requirement 1.3**: User authentication with JWT tokens
- **Requirement 2.1**: Complaint submission with text description
- **Requirement 2.2**: Voice complaint support (transcription handled by backend)
- **Requirement 2.3**: Image/video upload support
- **Requirement 2.4**: Location detection and GPS coordinates
- **Requirement 9.1**: Complaint status display
- **Requirement 9.2**: Priority level and explanation display
- **Requirement 9.3**: Status history display
- **Requirement 13.1**: Feedback submission with rating and comments

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Production Build

To create a production build:

```bash
npm run build
```

The optimized files will be in the `build/` directory, ready for deployment.
