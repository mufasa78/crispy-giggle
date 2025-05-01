# Shopee Data API - Client Guide

## Getting Started

This guide provides simple instructions for accessing the Shopee Data API to extract product information from Shopee Taiwan.

## API Address and Authentication

### Base URL

The API is hosted at:

```
http://your-server-domain:5000/api/v1
```

> **Important**: Replace `your-server-domain` with the actual server address provided to you.

### Authentication

All API requests require your unique API key for authentication. You must include your API key in one of the following ways:

#### Option 1: Using X-API-Key Header (Recommended)

```
X-API-Key: your_api_key_here
```

#### Option 2: Using Authorization Header

```
Authorization: Bearer your_api_key_here
```

## Quick Start Example

Here's a simple example to get you started with the API using Python:

```python
import requests

# Replace with your actual API key and server address
API_KEY = "your_api_key_here"
BASE_URL = "http://your-server-domain:5000/api/v1"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Example: Extract data for a single Shopee product
def get_product_data(shop_id, item_id):
    # Create a job with a single product
    deal_id = f"{shop_id}.{item_id}"
    
    # Step 1: Submit the job
    job_response = requests.post(
        f"{BASE_URL}/job/create",
        headers=headers,
        json={
            "deals": [
                {
                    "deal_id": deal_id,
                    "step_id": "step_1",
                    "priority": 1
                }
            ]
        }
    )
    
    if not job_response.ok:
        print(f"Error creating job: {job_response.text}")
        return None
    
    job_data = job_response.json()
    job_id = job_data["data"]["vendor_job_id"]
    print(f"Job created with ID: {job_id}")
    
    # Step 2: Poll for results (every 5 seconds)
    import time
    max_attempts = 12  # 1 minute timeout
    
    for attempt in range(max_attempts):
        print(f"Checking job status (attempt {attempt+1}/{max_attempts})...")
        
        result_response = requests.get(
            f"{BASE_URL}/job/result/{job_id}",
            headers=headers
        )
        
        if not result_response.ok:
            print(f"Error checking job: {result_response.text}")
            time.sleep(5)
            continue
        
        result_data = result_response.json()
        job_status = result_data["data"].get("status")
        
        if job_status in ["success", "failure", "cancelled"]:
            print(f"Job completed with status: {job_status}")
            
            # Return the first product in the results
            if "products" in result_data["data"] and len(result_data["data"]["products"]) > 0:
                return result_data["data"]["products"][0]
            else:
                print("No products found in results")
                return None
        
        print("Job still processing, waiting 5 seconds...")
        time.sleep(5)
    
    print("Timeout waiting for job to complete")
    return None

# Example usage
if __name__ == "__main__":
    # Example Shopee product from URL: https://shopee.tw/product-title-i.104581011.24901963692
    shop_id = "104581011"
    item_id = "24901963692"
    
    product = get_product_data(shop_id, item_id)
    
    if product:
        print("\nProduct Information:")
        print(f"Name: {product['name']}")
        print(f"Price: {product['price']} {product['currency']}")
        print(f"Brand: {product['brand']}")
        print(f"Rating: {product['rating']['rating_star']} ({product['rating']['rating_count']} reviews)")
        print(f"Images: {len(product['images'])} images available")
        
        # Print the first image URL
        if product['images']:
            print(f"First image: {product['images'][0]}")
```

## Extracting Product IDs from Shopee URLs

The API requires product IDs in the format `{shop_id}.{item_id}`, which can be extracted from Shopee URLs:

```
https://shopee.tw/product-title-i.104581011.24901963692
                                    ↑          ↑
                                shop_id     item_id
```

In this example, the `deal_id` would be `104581011.24901963692`.

## Batch Processing

For processing multiple products efficiently, submit them as a single job:

```python
def batch_process_products(product_list):
    """Process multiple products in a single job
    
    product_list format: [(shop_id, item_id), (shop_id, item_id), ...]
    """
    # Create deals list from product list
    deals = []
    for i, (shop_id, item_id) in enumerate(product_list):
        deals.append({
            "deal_id": f"{shop_id}.{item_id}",
            "step_id": f"step_{i}",
            "priority": 1
        })
    
    # Submit the job
    job_response = requests.post(
        f"{BASE_URL}/job/create",
        headers=headers,
        json={"deals": deals}
    )
    
    # Handle response and polling as in the earlier example
    # ...
```

## Next Steps

For more detailed information:

1. Refer to the full API documentation in `API_DOCUMENTATION.md`
2. See example code implementations in various languages
3. Contact your account manager for assistance or special requirements

## Support

If you encounter any issues or have questions about using the API, please contact support at support@example.com.