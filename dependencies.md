# Shopee Data API Dependencies

## Core Dependencies

| Package | Version | Purpose |
|---------|---------|--------|
| flask | 2.3.3 | Web framework for building the API endpoints and web interface |
| flask-jwt-extended | 4.5.3 | JWT authentication for securing API endpoints |
| flask-sqlalchemy | 3.1.1 | SQLAlchemy integration for Flask to simplify database operations |
| gunicorn | 23.0.0 | WSGI HTTP Server for production deployment |
| sqlalchemy | 2.0.23 | ORM for database interactions with PostgreSQL |
| psycopg2-binary | 2.9.9 | PostgreSQL database adapter for Python |
| werkzeug | 2.3.7 | WSGI utility library used by Flask |
| urllib3 | 2.0.7 | HTTP client for Python, used for reliable HTTP connections |

## Scraping and Data Extraction

| Package | Version | Purpose |
|---------|---------|--------|
| beautifulsoup4 | 4.12.2 | HTML parsing library for web scraping (fallback method) |
| trafilatura | 1.6.1 | Main content extraction library for clean web data extraction |
| requests | 2.31.0 | HTTP library for making API calls to Shopee |
| requests-html | 0.10.0 | HTML parsing with JavaScript support for dynamic content |
| lxml | 4.9.3 | XML/HTML processing library, used by BeautifulSoup |

## Utilities

| Package | Version | Purpose |
|---------|---------|--------|
| email-validator | 2.1.0.post1 | Validate email addresses in user registration |
| fake-useragent | 1.4.0 | Generate random user-agent strings to avoid detection |
| python-dateutil | 2.8.2 | Extensions to Python's datetime module |
| json-logging | 1.3.0 | JSON-formatted logging for better log processing |
| python-dotenv | 1.0.0 | Load environment variables from .env files |

## Performance Optimization

| Package | Version | Purpose |
|---------|---------|--------|
| cachetools | 5.3.2 | Caching decorators to reduce redundant API calls |

## System Requirements

- Python 3.9+
- PostgreSQL 12+
- 4+ CPU cores recommended for production
- 8GB+ RAM recommended for production
- Strong internet connection for reliable scraping

## Version Compatibility

These specific versions have been tested and confirmed to work together. The SQLAlchemy and Flask-SQLAlchemy versions are particularly important as they must be compatible with each other.

## High-Volume Processing

For processing the required 100,000-300,000 data points per day, the system is optimized with:

- Connection pooling for database efficiency
- Multi-threading for parallel processing
- Request throttling to avoid rate limits
- Caching to minimize redundant requests

## Installation

All dependencies can be installed using pip:

```bash
pip install -r requirements.txt
```

## Development vs. Production

For development environments, fewer worker threads and simplified configurations are used. For production, the system automatically scales up resources based on the configuration settings in config.py.
