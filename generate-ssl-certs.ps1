# PowerShell script to generate self-signed SSL certificates for development

# Create the ssl directory if it doesn't exist
$sslDir = "nginx/ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir -Force | Out-Null
    Write-Host "Created directory: $sslDir" -ForegroundColor Green
}

# Generate a self-signed certificate
Write-Host "Generating self-signed SSL certificate..." -ForegroundColor Yellow

# Use OpenSSL if available
$openssl = Get-Command openssl -ErrorAction SilentlyContinue
if ($openssl) {
    # Generate private key
    openssl genrsa -out "$sslDir/key.pem" 2048
    
    # Generate certificate
    openssl req -new -x509 -key "$sslDir/key.pem" -out "$sslDir/cert.pem" -days 365 -subj "/CN=localhost"
    
    Write-Host "SSL certificate generated successfully!" -ForegroundColor Green
    Write-Host "Certificate location: $sslDir/cert.pem" -ForegroundColor Cyan
    Write-Host "Private key location: $sslDir/key.pem" -ForegroundColor Cyan
} else {
    # Use New-SelfSignedCertificate if OpenSSL is not available
    Write-Host "OpenSSL not found. Using PowerShell's New-SelfSignedCertificate..." -ForegroundColor Yellow
    
    $cert = New-SelfSignedCertificate -DnsName "localhost" -CertStoreLocation "Cert:\LocalMachine\My"
    
    # Export certificate
    Export-Certificate -Cert $cert -FilePath "$sslDir/cert.pem" -Type CERT
    
    # Export private key
    $certPath = "Cert:\LocalMachine\My\$($cert.Thumbprint)"
    $keyPath = "$sslDir/key.pem"
    $pwd = ConvertTo-SecureString -String "password" -Force -AsPlainText
    Export-PfxCertificate -Cert $certPath -FilePath "$sslDir/temp.pfx" -Password $pwd
    
    # Convert PFX to PEM
    Write-Host "Please manually convert the PFX file to PEM format using OpenSSL:" -ForegroundColor Yellow
    Write-Host "openssl pkcs12 -in $sslDir/temp.pfx -out $keyPath -nodes -password pass:password" -ForegroundColor Cyan
    
    Write-Host "Certificate generated at: $sslDir/cert.pem" -ForegroundColor Green
    Write-Host "Temporary PFX file: $sslDir/temp.pfx" -ForegroundColor Yellow
}

Write-Host "`nNOTE: This is a self-signed certificate for development only." -ForegroundColor Red
Write-Host "For production, use a certificate from a trusted certificate authority." -ForegroundColor Red
