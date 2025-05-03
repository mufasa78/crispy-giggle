# Check Application Status Script for Windows PowerShell

Write-Host "Checking application status..." -ForegroundColor Green

# Check Docker containers
Write-Host "`nDocker Containers:" -ForegroundColor Cyan
docker ps

# Check Docker networks
Write-Host "`nDocker Networks:" -ForegroundColor Cyan
docker network ls

# Check application logs
Write-Host "`nApplication Logs:" -ForegroundColor Cyan
docker-compose logs --tail=20 api

# Check database logs
Write-Host "`nDatabase Logs:" -ForegroundColor Cyan
docker-compose logs --tail=20 db

# Check if application is accessible
Write-Host "`nChecking if application is accessible..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 5
    Write-Host "Application is accessible at http://localhost:5000" -ForegroundColor Green
    Write-Host "Status code: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Application is not accessible at http://localhost:5000" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

# Provide troubleshooting tips
Write-Host "`nTroubleshooting Tips:" -ForegroundColor Yellow
Write-Host "1. If containers are not running, try restarting them:" -ForegroundColor Yellow
Write-Host "   docker-compose down" -ForegroundColor Yellow
Write-Host "   docker-compose up -d" -ForegroundColor Yellow
Write-Host "2. If database connection issues, check the DATABASE_URL in docker-compose.yml" -ForegroundColor Yellow
Write-Host "3. For external access issues, check nginx.conf and docker-compose.nginx.yml" -ForegroundColor Yellow
Write-Host "4. For more detailed logs, run:" -ForegroundColor Yellow
Write-Host "   docker-compose logs" -ForegroundColor Yellow
