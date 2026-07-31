#!/bin/bash
# Health check script for NagrikSathi Grievance System

set -e

API_URL="${API_URL:-http://localhost:5000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "🏥 Running health checks..."
echo ""

# Check backend API
echo "Checking Backend API..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/api/health 2>/dev/null || echo "000")

if [ "$BACKEND_STATUS" = "200" ]; then
    echo "✅ Backend API is healthy"
else
    echo "❌ Backend API is not responding (Status: $BACKEND_STATUS)"
    exit 1
fi

# Check database connection
echo "Checking Database connection..."
DB_STATUS=$(curl -s $API_URL/api/health/db 2>/dev/null | grep -o "healthy" || echo "unhealthy")

if [ "$DB_STATUS" = "healthy" ]; then
    echo "✅ Database connection is healthy"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Check ML models
echo "Checking ML models..."
ML_STATUS=$(curl -s $API_URL/api/health/ml 2>/dev/null | grep -o "loaded" || echo "not loaded")

if [ "$ML_STATUS" = "loaded" ]; then
    echo "✅ ML models are loaded"
else
    echo "⚠️  ML models are not loaded"
fi

# Check frontend
echo "Checking Frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL 2>/dev/null || echo "000")

if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ Frontend is accessible"
else
    echo "⚠️  Frontend is not responding (Status: $FRONTEND_STATUS)"
fi

echo ""
echo "✅ Health check completed"
