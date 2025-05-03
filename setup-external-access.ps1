# Setup External Access Script for Windows PowerShell

# Ask for domain name
$domain = Read-Host "Enter your domain name (e.g., shopee-scraper.example.com)"

# Update Nginx configuration with the domain
Write-Host "Updating Nginx configuration with domain: $domain" -ForegroundColor Green
(Get-Content -Path nginx.conf) -replace 'server_name shopee-scraper.example.com;', "server_name $domain;" | Set-Content -Path nginx.conf

# Start Nginx container
Write-Host "Starting Nginx container..." -ForegroundColor Green
docker-compose -f docker-compose.nginx.yml up -d

# Display information
Write-Host "External access setup completed!" -ForegroundColor Green
Write-Host "Your application is now accessible at: http://$domain" -ForegroundColor Cyan
Write-Host "Make sure to add the following entry to your hosts file:" -ForegroundColor Yellow
Write-Host "127.0.0.1 $domain" -ForegroundColor Yellow
Write-Host "To edit your hosts file, run:" -ForegroundColor Yellow
Write-Host "notepad C:\Windows\System32\drivers\etc\hosts" -ForegroundColor Yellow

# Ask if user wants to add the entry to hosts file
$addToHosts = Read-Host "Do you want to add the entry to your hosts file? (y/n)"
if ($addToHosts -eq "y") {
    # Check if running as administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    
    if ($isAdmin) {
        # Add entry to hosts file
        Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "`n127.0.0.1 $domain"
        Write-Host "Entry added to hosts file." -ForegroundColor Green
    } else {
        Write-Host "You need to run this script as Administrator to modify the hosts file." -ForegroundColor Red
        Write-Host "Please add the entry manually or restart the script as Administrator." -ForegroundColor Red
    }
}
