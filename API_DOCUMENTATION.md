# Shopee Data API Documentation

## Base URL

The API is hosted at your server, with the base URL:

```
http://your-server-domain:5000/api/v1
```

## Authentication

All API requests require authentication using an API key. There are two methods to include your API key in requests:

### Method 1: Using X-API-Key Header

```
X-API-Key: your_api_key_here
```

### Method 2: Using Authorization Header

```
Authorization: Bearer your_api_key_here
```

If authentication fails, the API will return a 401 Unauthorized response.

## Error Handling

Errors are returned with appropriate HTTP status codes and a JSON response in the following format:

```json
{
    "success": false,
    "code": "error_code",
    "message": "Human-readable error message"
}
```

Common error codes include:
- `unauthorized`: Authentication failure
- `invalid_request`: Invalid request format
- `job_not_found`: The requested job does not exist
- `server_error`: Internal server error

## Endpoints

### 1. Get API Status

**Endpoint:** `GET /`

Check if the API is running and get version information.

**Response:**
```json
{
    "name": "Shopee Product Data API",
    "version": "v1",
    "status": "active"
}
```

### 2. Create a Data Extraction Job

**Endpoint:** `POST /job/create`

Submit a new data extraction job with multiple product IDs.

**Request Body:**
```json
{
    "job_id": "34c4e7623450",  // Optional, system will generate if not provided
    "deals": [
        {
            "deal_id": "1988776.7648272833", // Format: "{shop_id}.{item_id}"
            "step_id": "123546",           // Your reference ID (optional)
            "priority": 2                   // Processing priority (1-10)
        },
        {
            "deal_id": "1877554.6761418533",
            "step_id": "123893",
            "priority": 1
        }
    ]
}
```

**Response:**
```json
{
    "success": true,
    "code": null,
    "message": null,
    "data": {
        "vendor_job_id": "34c4e7623450"
    }
}
```

### 3. Get Job Results

**Endpoint:** `GET /job/result/{vendor_job_id}`

Retrieve the results of a previously submitted job.

**Response:**
```json
{
    "success": true,
    "code": null,
    "message": null,
    "data": {
        "job_id": "34c4e7623450",
        "status": "success",
        "completed": true,
        "total_deals": 2,
        "completed_deals": 2,
        "failed_deals": 0,
        "created_at": "2025-05-01T20:30:00Z",
        "completed_at": "2025-05-01T20:32:00Z",
        "products": [
            {
                "itemid": 7648272833,
                "shopid": 1988776,
                "name": "Product Name",
                "description": "Product description text...",
                "price": 299.0,
                "price_before_discount": 399.0,
                "currency": "TWD",
                "discount_percentage": 25,
                "stock": 100,
                "historical_sold": 500,
                "monthly_sales": 50,
                "images": [
                    "https://cf.shopee.tw/file/image1.jpg",
                    "https://cf.shopee.tw/file/image2.jpg"
                ],
                "brand": "Example Brand",
                "model": "EX-2023",
                "attributes": [
                    {"name": "Color", "value": "Red"},
                    {"name": "Size", "value": "XL"},
                    {"name": "Material", "value": "Cotton"}
                ],
                "categories": [
                    {"id": 123, "name": "Clothing"}, 
                    {"id": 456, "name": "Shirts"}
                ],
                "shipping_options": [
                    {"method": "Standard", "fee": 60.0, "min_days": 3, "max_days": 5}
                ],
                "rating": {
                    "rating_star": 4.8,
                    "rating_count": 250,
                    "five_star": 200,
                    "four_star": 35,
                    "three_star": 10,
                    "two_star": 3,
                    "one_star": 2
                },
                "seller": {
                    "shopid": 1988776,
                    "name": "Official Shop",
                    "location": "Taipei",
                    "rating": 4.9,
                    "is_official": true
                },
                "updated_at": "2025-05-01T20:31:00Z"
            },
            // Additional products...
        ]
    }
}
```

### 4. Cancel a Job

**Endpoint:** `POST /job/cancel/{vendor_job_id}`

Cancel a job that is currently in progress.

**Response:**
```json
{
    "success": true,
    "code": null,
    "message": null,
    "data": {
        "vendor_job_id": "34c4e7623450",
        "status": "cancelled"
    }
}
```

## Deal ID Format

The `deal_id` parameter in the Create Job endpoint should be in the format: `{shop_id}.{item_id}`

Example: `104581011.24901963692`

This format can be derived from Shopee product URLs:

From URL `https://shopee.tw/product-title-i.104581011.24901963692`:
- `shop_id` is `104581011`
- `item_id` is `24901963692`
- So the `deal_id` would be `104581011.24901963692`

## Rate Limits

To maintain system performance, the API has the following rate limits:
- 2,000 requests per hour per API key
- Maximum of 10,000 deals per job
- Maximum of 50 concurrent jobs per user

## Using the API with curl

### Example 1: Create a Job

```bash
curl -X POST \
  https://your-server-domain:5000/api/v1/job/create \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your_api_key_here' \
  -d '{
    "deals": [
        {
            "deal_id": "104581011.24901963692",
            "step_id": "123456",
            "priority": 1
        }
    ]
}'
```

### Example 2: Get Job Results

```bash
curl -X GET \
  https://your-server-domain:5000/api/v1/job/result/34c4e7623450 \
  -H 'X-API-Key: your_api_key_here'
```

### Example 3: Cancel a Job

```bash
curl -X POST \
  https://your-server-domain:5000/api/v1/job/cancel/34c4e7623450 \
  -H 'X-API-Key: your_api_key_here'
```

## Using the API with Python

```python
import requests
import json

API_KEY = "your_api_key_here"
BASE_URL = "https://your-server-domain:5000/api/v1"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Create a job
def create_job(deal_ids):
    deals = [
        {"deal_id": deal_id, "step_id": f"step_{i}", "priority": 1}
        for i, deal_id in enumerate(deal_ids)
    ]
    
    response = requests.post(
        f"{BASE_URL}/job/create",
        headers=headers,
        json={"deals": deals}
    )
    
    return response.json()

# Get job results
def get_job_results(job_id):
    response = requests.get(
        f"{BASE_URL}/job/result/{job_id}",
        headers=headers
    )
    
    return response.json()

# Example usage
deal_ids = ["104581011.24901963692", "104911467.5684470744"]
result = create_job(deal_ids)
print(json.dumps(result, indent=2))

job_id = result["data"]["vendor_job_id"]
print(f"Job created with ID: {job_id}")

# Poll for results (in a real application, add appropriate delay/retry logic)
import time
while True:
    job_result = get_job_results(job_id)
    if job_result["data"]["status"] in ["success", "failure", "cancelled"]:
        print(json.dumps(job_result, indent=2))
        break
    print("Job still processing, waiting...")
    time.sleep(5)
```

## Notes

1. Large jobs may take time to process. Always check the job status before accessing the data.
2. The API is optimized for high throughput and can handle 100,000-300,000 product requests per day.
3. Data is cached for 24 hours, so requesting the same product multiple times within this period will be faster.
4. For optimal performance, consider batching your requests into jobs with multiple deals rather than creating many small jobs.