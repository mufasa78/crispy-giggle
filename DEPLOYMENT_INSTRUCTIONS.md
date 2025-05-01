# Shopee Data API - Deployment Instructions

## Requirements

Ensure your deployment environment has these dependencies installed:

```
# Core dependencies
flask==2.3.3
flask-jwt-extended==4.5.3
flask-sqlalchemy==3.1.1
gunicorn==23.0.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
werkzeug==2.3.7
urllib3==2.0.7

# Scraping and data extraction
beautifulsoup4==4.12.2
trafilatura==1.6.1
requests==2.31.0
requests-html==0.10.0
lxml==4.9.3

# Utilities
email-validator==2.1.0.post1
fake-useragent==1.4.0
python-dateutil==2.8.2
json-logging==1.3.0
python-dotenv==1.0.0

# Performance optimization
cachetools==5.3.2
```

## Deployment Options

### Option 1: Docker (Recommended)

#### 1. Create a Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Expose the port
EXPOSE 5000

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers=4", "main:app"]
```

#### 2. Build and Run the Docker Image

```bash
# Build the Docker image
docker build -t shopee-data-api .

# Run the container
docker run -d -p 5000:5000 \
  -e DATABASE_URL="postgresql://username:password@host:port/database" \
  -e SESSION_SECRET="your-secure-secret-key" \
  --name shopee-api shopee-data-api
```

### Option 2: VPS Deployment

#### 1. Set Up the Server

```bash
# Install Python and dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql nginx

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE shopee_api;
CREATE USER shopee_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE shopee_api TO shopee_user;
\q
```

#### 3. Create a Systemd Service

```bash
sudo nano /etc/systemd/system/shopee-api.service
```

Add the following content:

```
[Unit]
Description=Shopee Data API Service
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/shopee-api
Environment="PATH=/path/to/shopee-api/venv/bin"
Environment="DATABASE_URL=postgresql://shopee_user:your_secure_password@localhost/shopee_api"
Environment="SESSION_SECRET=your-secure-secret-key"
ExecStart=/path/to/shopee-api/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 4. Enable and Start the Service

```bash
sudo systemctl enable shopee-api
sudo systemctl start shopee-api
sudo systemctl status shopee-api
```

#### 5. Configure Nginx as a Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/shopee-api
```

Add the following content:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/shopee-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Set Up SSL with Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Option 3: Cloud Platform Deployment

#### AWS Elastic Beanstalk

1. Install the EB CLI
2. Initialize the EB CLI repository
3. Create an environment
4. Deploy the application

```bash
# Install the EB CLI
pip install awsebcli

# Initialize the repository
eb init -p python-3.9 shopee-api

# Create an environment
eb create shopee-api-prod

# Deploy
eb deploy
```

## Database Migration

If you're migrating from an existing database, export and import your data:

```bash
# Export from source
pg_dump -U username -d source_db > shopee_data.sql

# Import to target
psql -U username -d target_db < shopee_data.sql
```

## Environment Variables

The application requires these environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Secret key for session encryption
- `FLASK_ENV`: Set to "production" for production deployment

## Post-Deployment Verification

Verify API is working correctly:

```bash
# Test API status endpoint
curl https://your-domain.com/api/v1/

# Expected response
{"name":"Shopee Product Data API","status":"active","version":"v1"}
```

## Monitoring and Maintenance

### Logs

Check application logs:

```bash
# For systemd service
sudo journalctl -u shopee-api

# For Docker
docker logs shopee-api
```

### Database Maintenance

Perform regular database optimization:

```bash
sudo -u postgres psql -d shopee_api -c "VACUUM ANALYZE;"
```

### Backups

Set up automated backups:

```bash
# Create backup script
echo '#!/bin/bash
pg_dump -U shopee_user -d shopee_api > /path/to/backups/shopee_api_$(date +%Y%m%d).sql' > /usr/local/bin/backup-shopee-db.sh
chmod +x /usr/local/bin/backup-shopee-db.sh

# Set up cron job for daily backups
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup-shopee-db.sh") | crontab -
```

## Scaling

For handling 100,000-300,000 data points per day:

1. Increase `MAX_WORKER_THREADS` in config.py
2. Use a PostgreSQL connection pool (already configured)
3. Consider horizontal scaling with load balancing for very high volumes

## Support

If you encounter issues during deployment, please contact support at support@example.com.
