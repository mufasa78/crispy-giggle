# Shopee Taiwan Data Scraper API

## Overview

This enterprise-level API service extracts detailed product information from Shopee Taiwan (shopee.tw). It's designed for high-throughput data extraction with robust fallback mechanisms to ensure reliable data retrieval even when facing anti-scraping measures.

## Features

- **High-Volume Processing**: Optimized for 100,000-300,000 daily data entries
- **Multi-Method Extraction**: Uses a 3-tier approach for maximum data availability
- **Robust Error Handling**: Multiple fallback mechanisms ensure data retrieval
- **Anti-Bot Protection Bypass**: Sophisticated request patterns to avoid detection
- **CSV Batch Processing**: Import thousands of product IDs via CSV upload
- **Single URL Processing**: Extract data from any Shopee Taiwan product URL
- **Admin Dashboard**: Monitor job progress and data extraction statistics
- **REST API**: Programmatically submit jobs and retrieve results

## API Endpoints

### Create a New Job

```
POST /api/jobs
```

Request body example:
```json
{
    "job_id": "34c4e7623450",  # Optional
    "deals": [
        {
            "deal_id": "1988776.7648272833",
            "step_id": "123546",
            "priority": 2
        },
        {
            "deal_id": "1877554.6761418533",
            "step_id": "123893",
            "priority": 1
        }
    ]
}
```

### Get Job Results

```
GET /api/jobs/{job_id}/results
```

Response example:
```json
{
    "status": "success",
    "job_id": "34c4e7623450",
    "completed": true,
    "products": [
        {
            "itemid": 7648272833,
            "shopid": 1988776,
            "name": "Product Name",
            "description": "Product description text...",
            "price": 299.0,
            "stock": 100,
            "historical_sold": 500,
            "images": [
                "https://cf.shopee.tw/file/image1.jpg",
                "https://cf.shopee.tw/file/image2.jpg"
            ],
            "raw_data": {...}  // Full API response data
        }
    ]
}
```

### Cancel a Running Job

```
POST /api/jobs/{job_id}/cancel
```

## Installation & Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure PostgreSQL database in config.py
4. Run the application: `gunicorn --bind 0.0.0.0:5000 main:app`

## Architecture

The service follows a multi-tier architecture to maximize data extraction success:

1. **Tier 1**: HTML scraping with Trafilatura for clean content extraction
2. **Tier 2**: Direct API calls to Shopee's internal API endpoints
3. **Tier 3**: Direct HTML parsing with BeautifulSoup and custom selectors

Each tier has sophisticated error handling and anti-detection measures, including:
- Randomized request delays
- Rotating user agents
- Realistic cookie generation
- Request throttling to avoid rate limits

## Performance Optimization

- Connection pooling for database efficiency
- LRU caching to minimize redundant requests
- Multi-threading for parallel processing
- Proper application context handling for threaded operations

## Administration

The system includes an admin dashboard for:
- Monitoring job progress
- Viewing detailed job statistics
- Managing user accounts
- Adjusting system configuration

## Security

- API Key authentication
- Rate limiting
- Input validation and sanitization
- Secure password hashing

## Requirements

See requirements.txt for detailed dependencies.

## License

Proprietary - All rights reserved