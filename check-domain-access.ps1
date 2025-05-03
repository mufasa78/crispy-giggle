# Check Domain Access Script for Windows PowerShell

# Ask for domain name
$domain = Read-Host "Enter your domain name (e.g., shopee-scraper.example.com)"

# Check if domain resolves to localhost
Write-Host "Checking if domain resolves to localhost..." -ForegroundColor Cyan
try {
    $ip = [System.Net.Dns]::GetHostAddresses($domain)[0].IPAddressToString
    Write-Host "Domain $domain resolves to $ip" -ForegroundColor Green
    
    if ($ip -eq "127.0.0.1") {
        Write-Host "Domain correctly resolves to localhost." -ForegroundColor Green
    } else {
        Write-Host "Domain does not resolve to localhost. You may need to add an entry to your hosts file." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Domain $domain does not resolve. You may need to add an entry to your hosts file." -ForegroundColor Red
}

# Check if Nginx is running
Write-Host "`nChecking if Nginx is running..." -ForegroundColor Cyan
try {
    $nginxContainer = docker ps --filter "name=nginx" --format "{{.Names}}"
    if ($nginxContainer) {
        Write-Host "Nginx container is running: $nginxContainer" -ForegroundColor Green
    } else {
        Write-Host "Nginx container is not running." -ForegroundColor Red
        Write-Host "Try starting it with: docker-compose -f docker-compose.nginx.yml up -d" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error checking Nginx container: $_" -ForegroundColor Red
}

# Check if domain is accessible
Write-Host "`nChecking if domain is accessible..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://$domain" -UseBasicParsing -TimeoutSec 5
    Write-Host "Domain is accessible at http://$domain" -ForegroundColor Green
    Write-Host "Status code: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Domain is not accessible at http://$domain" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

# Provide troubleshooting tips
Write-Host "`nTroubleshooting Tips:" -ForegroundColor Yellow
Write-Host "1. Make sure the domain is added to your hosts file:" -ForegroundColor Yellow
Write-Host "   127.0.0.1 $domain" -ForegroundColor Yellow
Write-Host "2. Make sure Nginx is running:" -ForegroundColor Yellow
Write-Host "   docker-compose -f docker-compose.nginx.yml up -d" -ForegroundColor Yellow
Write-Host "3. Check Nginx logs:" -ForegroundColor Yellow
Write-Host "   docker-compose -f docker-compose.nginx.yml logs" -ForegroundColor Yellow
Write-Host "4. Make sure the application is running:" -ForegroundColor Yellow
Write-Host "   docker-compose ps" -ForegroundColor Yellow
