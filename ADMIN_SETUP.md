# Shopee Data API - Administrator Setup Guide

## System Requirements

- Python 3.9+
- PostgreSQL 12+
- 4+ CPU cores recommended
- 8GB+ RAM recommended
- Strong internet connection

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/shopee-data-api.git
cd shopee-data-api
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

1. Create a PostgreSQL database for the application

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE shopee_api;
CREATE USER shopee_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE shopee_api TO shopee_user;
\q
```

2. Set the database URI environment variable:

```bash
export DATABASE_URL=postgresql://shopee_user:your_secure_password@localhost/shopee_api
```

For production, add this to your environment configuration (e.g., in `.bashrc` or through your deployment platform).

### 4. Initialize the Database

```bash
python -c "from app import db; db.create_all()"
```

### 5. Create Admin Account

```bash
python -c "from main import setup_admin; setup_admin('admin', 'secure_admin_password')"
```

## Configuration

The application configuration is in `config.py`. Key parameters to adjust include:

- `MAX_WORKER_THREADS`: Number of concurrent worker threads (default: 10)
- `BATCH_SIZE`: Number of items to process in a single batch (default: 100)
- `JOB_TIMEOUT`: Maximum job runtime in seconds (default: 3600)
- `REQUEST_DELAY_MIN` and `REQUEST_DELAY_MAX`: Delay between requests to avoid rate limiting

For high-volume deployment, use the `ProductionConfig` class settings which are optimized for performance.

## Running the Server

### Development Mode

```bash
export FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5000
```

### Production Mode

Using Gunicorn (recommended for production):

```bash
gunicorn --bind 0.0.0.0:5000 --workers=4 --threads=2 --timeout=120 main:app
```

## Server Address Configuration

The API will be available at:

```
http://your-server-ip:5000/api/v1
```

For production deployment, you should:

1. Use a reverse proxy like Nginx to handle TLS/SSL
2. Set up a domain name for the API
3. Configure proper firewall rules

### Example Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name api.your-domain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring and Maintenance

### Log Files

Application logs are written to the console by default. For production, redirect to a file:

```bash
gunicorn --bind 0.0.0.0:5000 --workers=4 main:app --log-file=/var/log/shopee-api/app.log
```

### Database Maintenance

Perform regular database maintenance:

```bash
sudo -u postgres psql -d shopee_api -c "VACUUM ANALYZE;"
```

### Backup

Regularly backup the database:

```bash
pg_dump -U shopee_user -d shopee_api > backup_$(date +%Y%m%d).sql
```

## API Key Management

### Generate API Key for User

Using Python shell:

```python
from app import app, db
from models import User
from utils.helpers import generate_api_key, hash_password

with app.app_context():
    username = "client_name"
    password = "secure_password"
    
    # Check if user exists
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"User {username} already exists")
    else:
        api_key = generate_api_key()
        new_user = User(
            username=username,
            password_hash=hash_password(password),
            api_key=api_key
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"Created user {username} with API key: {api_key}")
```

Provide the generated API key to the client for use with the API.

## Troubleshooting

### Database Connection Issues

If the application cannot connect to the database:

1. Check the DATABASE_URL environment variable
2. Ensure PostgreSQL is running: `sudo systemctl status postgresql`
3. Verify the user has proper permissions

### Scraping Issues

If the API is failing to retrieve product data:

1. Check if Shopee has changed their website structure
2. Examine the logs for specific error messages
3. Test manual access to the Shopee website from the server
4. Update USER_AGENTS in config.py if needed

### Performance Issues

If the API is running slowly:

1. Increase MAX_WORKER_THREADS in config.py
2. Optimize database indexes
3. Consider scaling horizontally with multiple server instances
4. Check server CPU and memory usage during peak loads

## Contact Support

For additional assistance, contact the development team at developer@example.com.