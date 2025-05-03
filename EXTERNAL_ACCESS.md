# Setting Up External Access

This document provides instructions for setting up external access to your application.

## Option 1: Using Nginx as a Reverse Proxy (Recommended for Development)

### Prerequisites

- Docker and Docker Compose installed
- Basic understanding of networking

### Setup Steps

1. **Configure Nginx**

   The `nginx.conf` file is already created with a basic configuration. You can modify it if needed:

   ```nginx
   server {
       listen 80;
       server_name shopee-scraper.example.com;  # Replace with your actual domain

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

2. **Start Nginx**

   Run the following command to start Nginx:

   ```bash
   docker-compose -f docker-compose.nginx.yml up -d
   ```

3. **Update Your Hosts File**

   For local development, add an entry to your hosts file:

   - Windows: `C:\Windows\System32\drivers\etc\hosts`
   - Linux/Mac: `/etc/hosts`

   Add the following line:

   ```
   127.0.0.1 shopee-scraper.example.com
   ```

4. **Access Your Application**

   You can now access your application at:

   ```
   http://shopee-scraper.example.com
   ```

5. **Automated Setup**

   Alternatively, you can use the provided PowerShell script:

   ```powershell
   .\setup-external-access.ps1
   ```

## Option 2: Using a Domain with DNS (Production)

For production environments, you'll want to use a real domain with proper DNS configuration.

### Prerequisites

- A registered domain name
- Access to your domain's DNS settings
- A server with a public IP address

### Setup Steps

1. **Configure DNS**

   Add an A record in your domain's DNS settings pointing to your server's IP address:

   ```
   Type: A
   Name: shopee-scraper (or whatever subdomain you want)
   Value: YOUR_SERVER_IP
   TTL: 3600 (or as recommended)
   ```

2. **Configure Nginx for SSL (Recommended)**

   For production, you should use HTTPS. Create a new Nginx configuration:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;

       location / {
           proxy_pass http://api:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Set Up SSL Certificates**

   You can use Let's Encrypt to get free SSL certificates:

   ```bash
   # Install certbot
   apt-get update
   apt-get install certbot python3-certbot-nginx

   # Get certificates
   certbot --nginx -d your-domain.com
   ```

4. **Deploy Your Application**

   Update your docker-compose.yml file to include the Nginx service and deploy:

   ```bash
   docker-compose up -d
   ```

## Option 3: Using Kubernetes Ingress (For Kubernetes Deployment)

If you're using Kubernetes, you can use Ingress to expose your application.

### Prerequisites

- Kubernetes cluster
- Ingress controller installed (like Nginx Ingress Controller)
- Domain name (optional)

### Setup Steps

1. **Deploy the Ingress Resource**

   The `k8s/ingress.yaml` file is already created. Update it with your domain:

   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: shopee-scraper-ingress
     annotations:
       nginx.ingress.kubernetes.io/rewrite-target: /
   spec:
     rules:
     - host: your-domain.com  # Replace with your actual domain
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: shopee-scraper-api
               port:
                 number: 80
   ```

2. **Apply the Ingress Resource**

   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

3. **Get the Ingress IP or Hostname**

   ```bash
   kubectl get ingress
   ```

4. **Configure DNS**

   Add a DNS record pointing to the Ingress IP or hostname.

## Troubleshooting

### Connection Refused

If you see "Connection Refused" errors:

1. Check if your application is running:
   ```bash
   docker ps
   ```

2. Check if the ports are correctly mapped:
   ```bash
   docker-compose ps
   ```

3. Check if Nginx is running:
   ```bash
   docker-compose -f docker-compose.nginx.yml ps
   ```

### SSL Certificate Issues

If you have SSL certificate issues:

1. Check if your certificates are valid:
   ```bash
   certbot certificates
   ```

2. Renew certificates if needed:
   ```bash
   certbot renew
   ```

### DNS Issues

If your domain is not resolving:

1. Check your DNS settings with:
   ```bash
   nslookup your-domain.com
   ```

2. It may take up to 24-48 hours for DNS changes to propagate globally.
