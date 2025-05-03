# Deployment Script for Windows PowerShell

# Check if environment variables are set
if (-not $env:DATABASE_URL) {
    Write-Host "ERROR: DATABASE_URL environment variable is not set." -ForegroundColor Red
    Write-Host "Please set it using: `$env:DATABASE_URL='your-database-url'" -ForegroundColor Yellow
    exit 1
}

if (-not $env:SESSION_SECRET) {
    Write-Host "ERROR: SESSION_SECRET environment variable is not set." -ForegroundColor Red
    Write-Host "Please set it using: `$env:SESSION_SECRET='your-secret-key'" -ForegroundColor Yellow
    exit 1
}

# Check if SSL certificates exist, generate if not
$sslDir = "nginx/ssl"
if (-not (Test-Path "$sslDir/cert.pem") -or -not (Test-Path "$sslDir/key.pem")) {
    Write-Host "SSL certificates not found. Generating self-signed certificates..." -ForegroundColor Yellow

    # Run the certificate generation script
    if (Test-Path "generate-ssl-certs.ps1") {
        & .\generate-ssl-certs.ps1
    } else {
        Write-Host "Certificate generation script not found. Please run generate-ssl-certs.ps1 manually." -ForegroundColor Red
        Write-Host "Continuing without SSL certificates..." -ForegroundColor Yellow
    }
}

# Stop any running containers
Write-Host "Stopping any running containers..." -ForegroundColor Yellow
docker-compose down

# Build and start the containers
Write-Host "Building and starting containers..." -ForegroundColor Green
docker-compose up -d --build

# Wait for the application to start
Write-Host "Waiting for the application to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if the application is running
Write-Host "Checking if the application is running..." -ForegroundColor Yellow
$response = $null
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -ErrorAction SilentlyContinue
} catch {
    Write-Host "Could not connect to the application. Retrying..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -ErrorAction SilentlyContinue
    } catch {
        Write-Host "Still could not connect to the application." -ForegroundColor Red
    }
}

if ($response -and $response.StatusCode -eq 200) {
    Write-Host "Application is running successfully!" -ForegroundColor Green
    Write-Host "You can access the application at:" -ForegroundColor Cyan
    Write-Host "  - HTTP: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "  - HTTPS: https://localhost" -ForegroundColor Cyan
    Write-Host "To create an admin account, visit: http://localhost:5000/setup-admin" -ForegroundColor Cyan
} else {
    Write-Host "Application may not be running properly. Please check the logs." -ForegroundColor Red
    Write-Host "You can view the logs with: docker-compose logs" -ForegroundColor Yellow
}

# Display the environment variables being used
Write-Host "`nEnvironment Variables:" -ForegroundColor Magenta
Write-Host "DATABASE_URL: [HIDDEN - Using NeonDB PostgreSQL]" -ForegroundColor Magenta
Write-Host "SESSION_SECRET: [HIDDEN]" -ForegroundColor Magenta

Write-Host "`nDeployment completed!" -ForegroundColor Green
Write-Host "For production deployment, make sure to:" -ForegroundColor Yellow
Write-Host "1. Use a proper SSL certificate from a trusted CA" -ForegroundColor Yellow
Write-Host "2. Configure proper firewall rules" -ForegroundColor Yellow
Write-Host "3. Set up regular database backups" -ForegroundColor Yellow
