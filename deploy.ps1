# PowerShell deployment script for NagrikSathi Grievance System

Write-Host "🚀 Starting deployment process..." -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: .env file not found" -ForegroundColor Red
    Write-Host "Please copy .env.production.example to .env and configure it"
    exit 1
}

Write-Host "✓ Environment file found" -ForegroundColor Green

# Check if Docker is installed
try {
    docker --version | Out-Null
    docker-compose --version | Out-Null
    Write-Host "✓ Docker and Docker Compose are installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker or Docker Compose is not installed" -ForegroundColor Red
    exit 1
}

# Build and start containers
Write-Host "📦 Building Docker images..." -ForegroundColor Yellow
docker-compose build

Write-Host "🚀 Starting containers..." -ForegroundColor Yellow
docker-compose up -d

# Wait for database to be ready
Write-Host "⏳ Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Run database migrations
Write-Host "🗄️  Running database migrations..." -ForegroundColor Yellow
docker-compose exec -T backend flask db upgrade 2>$null

# Check if ML models exist
Write-Host "🤖 Checking ML models..." -ForegroundColor Yellow
if (-not (Test-Path backend/ml_models/classifier.pkl)) {
    Write-Host "⚠️  ML models not found. Training models..." -ForegroundColor Yellow
    docker-compose exec -T backend python ml_models/train_classifier.py
}

Write-Host "✓ ML models ready" -ForegroundColor Green

# Show running containers
Write-Host "📊 Container status:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Application URLs:"
Write-Host "   Frontend: http://localhost"
Write-Host "   Backend API: http://localhost:5000/api"
Write-Host ""
Write-Host "📝 Useful commands:"
Write-Host "   View logs: docker-compose logs -f"
Write-Host "   Stop: docker-compose down"
Write-Host "   Restart: docker-compose restart"
Write-Host ""
