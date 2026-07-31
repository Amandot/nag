# PowerShell script to start both backend and frontend servers
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NagrikSathi - Starting All Services  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running in PowerShell
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Host "Error: This script requires PowerShell 5.0 or higher" -ForegroundColor Red
    exit 1
}

# Function to start a process in a new window
function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory
    )
    
    Write-Host "Starting $Title..." -ForegroundColor Green
    
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = "powershell.exe"
    $startInfo.Arguments = "-NoExit -Command `"cd '$WorkingDirectory'; $Command`""
    $startInfo.UseShellExecute = $true
    $startInfo.CreateNoWindow = $false
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    $process.Start() | Out-Null
    
    return $process
}

# Get the current directory
$rootDir = Get-Location

# Start Backend Server
Write-Host ""
Write-Host "1. Starting Backend Server..." -ForegroundColor Yellow
$backendDir = Join-Path $rootDir "backend"
$backendProcess = Start-ServiceWindow -Title "Backend Server" -Command "python app.py" -WorkingDirectory $backendDir

Start-Sleep -Seconds 3

# Start Frontend Server
Write-Host ""
Write-Host "2. Starting Frontend Server..." -ForegroundColor Yellow
$frontendDir = Join-Path $rootDir "frontend"
$frontendProcess = Start-ServiceWindow -Title "Frontend Server" -Command "npm start" -WorkingDirectory $frontendDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Services Started Successfully!       " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:5000" -ForegroundColor White
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Two new windows have been opened:" -ForegroundColor Yellow
Write-Host "  1. Backend Server (Flask)" -ForegroundColor White
Write-Host "  2. Frontend Server (React)" -ForegroundColor White
Write-Host ""
Write-Host "To stop the servers:" -ForegroundColor Yellow
Write-Host "  - Close the PowerShell windows" -ForegroundColor White
Write-Host "  - Or press Ctrl+C in each window" -ForegroundColor White
Write-Host ""
Write-Host "Waiting 10 seconds for servers to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Run diagnostic
Write-Host ""
Write-Host "Running diagnostic check..." -ForegroundColor Yellow
python diagnose_login.py

Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
