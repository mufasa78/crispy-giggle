#!/bin/bash

# Deployment Script for Linux/Mac

# Check if environment variables are set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set."
    echo "Please set it using: export DATABASE_URL='your-database-url'"
    exit 1
fi

if [ -z "$SESSION_SECRET" ]; then
    echo "ERROR: SESSION_SECRET environment variable is not set."
    echo "Please set it using: export SESSION_SECRET='your-secret-key'"
    exit 1
fi

# Check if SSL certificates exist, generate if not
SSL_DIR="nginx/ssl"
if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
    echo "SSL certificates not found. Generating self-signed certificates..."

    # Run the certificate generation script
    if [ -f "generate-ssl-certs.sh" ]; then
        chmod +x generate-ssl-certs.sh
        ./generate-ssl-certs.sh
    else
        echo "Certificate generation script not found. Please run generate-ssl-certs.sh manually."
        echo "Continuing without SSL certificates..."
    fi
fi

# Stop any running containers
echo "Stopping any running containers..."
docker-compose down

# Build and start the containers
echo "Building and starting containers..."
docker-compose up -d --build

# Wait for the application to start
echo "Waiting for the application to start..."
sleep 10

# Check if the application is running
echo "Checking if the application is running..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 || echo "000")

if [ "$response" -eq 200 ]; then
    echo "Application is running successfully!"
    echo "You can access the application at:"
    echo "  - HTTP: http://localhost:5000"
    echo "  - HTTPS: https://localhost"
    echo "To create an admin account, visit: http://localhost:5000/setup-admin"
else
    echo "Could not connect to the application. Retrying..."
    sleep 5
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 || echo "000")

    if [ "$response" -eq 200 ]; then
        echo "Application is now running successfully!"
        echo "You can access the application at:"
        echo "  - HTTP: http://localhost:5000"
        echo "  - HTTPS: https://localhost"
        echo "To create an admin account, visit: http://localhost:5000/setup-admin"
    else
        echo "Application may not be running properly. Please check the logs."
        echo "You can view the logs with: docker-compose logs"
    fi
fi

# Display the environment variables being used
echo ""
echo "Environment Variables:"
echo "DATABASE_URL: [HIDDEN - Using NeonDB PostgreSQL]"
echo "SESSION_SECRET: [HIDDEN]"

echo ""
echo "Deployment completed!"
echo "For production deployment, make sure to:"
echo "1. Use a proper SSL certificate from a trusted CA"
echo "2. Configure proper firewall rules"
echo "3. Set up regular database backups"
