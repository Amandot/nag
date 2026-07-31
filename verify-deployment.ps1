# Deployment Verification Script for NagrikSathi
# Run this after deployment to verify everything is working

param(
    [string]$ApiUrl = "http://localhost:5000",
    [string]$FrontendUrl = "http://localhost:3000"
)

Write-Host "🔍 NagrikSathi Deployment Verification" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# Function to test endpoint
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$ExpectedContent = ""
    )
    
    Write-Host "Testing $Name..." -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        
        if ($response.StatusCode -eq 200) {
            if ($ExpectedContent -and $response.Content -notlike "*$ExpectedContent*") {
                Write-Host " ❌ FAILED (unexpected content)" -ForegroundColor Red
                return $false
            }
            Write-Host " ✅ PASSED" -ForegroundColor Green
            return $true
        } else {
            Write-Host " ❌ FAILED (Status: $($response.StatusCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ❌ FAILED ($($_.Exception.Message))" -ForegroundColor Red
        return $false
    }
}

# Test Backend Health Endpoints
Write-Host "Backend Health Checks:" -ForegroundColor Yellow
Write-Host "---------------------" -ForegroundColor Yellow

$allPassed = $allPassed -and (Test-Endpoint "Basic Health" "$ApiUrl/api/health" "healthy")
$allPassed = $allPassed -and (Test-Endpoint "Database Health" "$ApiUrl/api/health/db" "healthy")
$allPassed = $allPassed -and (Test-Endpoint "ML Models Health" "$ApiUrl/api/health/ml")
$allPassed = $allPassed -and (Test-Endpoint "Readiness Probe" "$ApiUrl/api/health/ready")
$allPassed = $allPassed -and (Test-Endpoint "Liveness Probe" "$ApiUrl/api/health/live")

Write-Host ""

# Test Frontend
Write-Host "Frontend Check:" -ForegroundColor Yellow
Write-Host "--------------" -ForegroundColor Yellow

$allPassed = $allPassed -and (Test-Endpoint "Frontend Accessible" $FrontendUrl)

Write-Host ""

# Check Docker Containers (if using Docker)
Write-Host "Docker Containers:" -ForegroundColor Yellow
Write-Host "-----------------" -ForegroundColor Yellow

try {
    $containers = docker-compose ps --services 2>$null
    if ($containers) {
        foreach ($container in $containers) {
            $status = docker-compose ps $container 2>$null | Select-String "Up"
            if ($status) {
                Write-Host "  $container : ✅ Running" -ForegroundColor Green
            } else {
                Write-Host "  $container : ❌ Not Running" -ForegroundColor Red
                $allPassed = $false
            }
        }
    } else {
        Write-Host "  Docker Compose not detected or not running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Could not check Docker containers" -ForegroundColor Yellow
}

Write-Host ""

# Check Required Files
Write-Host "Required Files:" -ForegroundColor Yellow
Write-Host "--------------" -ForegroundColor Yellow

$requiredFiles = @(
    "backend/ml_models/classifier.pkl",
    "backend/ml_models/vectorizer.pkl",
    ".env"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  $file : ✅ Found" -ForegroundColor Green
    } else {
        Write-Host "  $file : ❌ Missing" -ForegroundColor Red
        $allPassed = $false
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan

if ($allPassed) {
    Write-Host "✅ All checks passed! Deployment is successful." -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Your application is ready:" -ForegroundColor Cyan
    Write-Host "   Frontend: $FrontendUrl"
    Write-Host "   Backend API: $ApiUrl/api"
    Write-Host ""
    Write-Host "📝 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Create an admin user: docker-compose exec backend python create_admin.py"
    Write-Host "   2. Configure SSL/TLS for production"
    Write-Host "   3. Set up monitoring and backups"
    Write-Host "   4. Review SECURITY_CHECKLIST.md"
    exit 0
} else {
    Write-Host "❌ Some checks failed. Please review the errors above." -ForegroundColor Red
    Write-Host ""
    Write-Host "📚 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   - Check logs: docker-compose logs -f"
    Write-Host "   - Verify .env configuration"
    Write-Host "   - Ensure all services are running"
    Write-Host "   - Review PRODUCTION_DEPLOYMENT.md"
    exit 1
}
