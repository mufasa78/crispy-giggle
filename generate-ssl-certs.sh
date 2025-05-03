#!/bin/bash

# Bash script to generate self-signed SSL certificates for development

# Create the ssl directory if it doesn't exist
SSL_DIR="nginx/ssl"
mkdir -p $SSL_DIR
echo "Created directory: $SSL_DIR"

# Generate a self-signed certificate
echo "Generating self-signed SSL certificate..."

# Generate private key
openssl genrsa -out "$SSL_DIR/key.pem" 2048

# Generate certificate
openssl req -new -x509 -key "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem" -days 365 -subj "/CN=localhost"

echo "SSL certificate generated successfully!"
echo "Certificate location: $SSL_DIR/cert.pem"
echo "Private key location: $SSL_DIR/key.pem"

echo ""
echo "NOTE: This is a self-signed certificate for development only."
echo "For production, use a certificate from a trusted certificate authority."
