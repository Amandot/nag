# PowerShell script to start the backend server
Write-Host "Starting NagrikSathi Backend Server..." -ForegroundColor Green
Write-Host ""

# Navigate to backend directory
Set-Location backend

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Warning: Virtual environment not found at backend\venv" -ForegroundColor Yellow
    Write-Host "Using global Python installation..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting Flask application on http://localhost:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan
Write-Host ""

# Start the Flask app
python app.py
