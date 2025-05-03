# Add Hosts Entry Script for Windows PowerShell

# Ask for domain name
$domain = Read-Host "Enter your domain name (e.g., shopee-scraper.example.com)"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if ($isAdmin) {
    # Add entry to hosts file
    Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "`n127.0.0.1 $domain"
    Write-Host "Entry added to hosts file." -ForegroundColor Green
    Write-Host "You can now access your application at: http://$domain" -ForegroundColor Cyan
} else {
    Write-Host "You need to run this script as Administrator to modify the hosts file." -ForegroundColor Red
    Write-Host "Please add the following entry manually to your hosts file:" -ForegroundColor Yellow
    Write-Host "127.0.0.1 $domain" -ForegroundColor Yellow
    Write-Host "To edit your hosts file, run:" -ForegroundColor Yellow
    Write-Host "notepad C:\Windows\System32\drivers\etc\hosts" -ForegroundColor Yellow
}
