import requests
import logging
import json
import time
import random
import functools
import trafilatura
from urllib.parse import urlparse, parse_qs
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

from config import (SHOPEE_BASE_URL, REQUEST_TIMEOUT, RETRY_ATTEMPTS, 
                  RETRY_DELAY, MAX_CONCURRENT_REQUESTS)

# Create a session with connection pooling
session = requests.Session()

# Configure retry strategy with backoff
retry_strategy = Retry(
    total=RETRY_ATTEMPTS,
    backoff_factor=RETRY_DELAY,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

# Mount the adapter to the session
adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=MAX_CONCURRENT_REQUESTS,
    pool_maxsize=MAX_CONCURRENT_REQUESTS * 2
)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Configure logging
logger = logging.getLogger(__name__)

class ShopeeService:
    """Service for interacting with Shopee API"""
    
    @staticmethod
    def extract_item_id_and_shop_id(deal_id):
        """
        Extract item_id and shop_id from deal_id
        Format: "{shop_id}.{item_id}"
        """
        try:
            parts = deal_id.split('.')
            if len(parts) != 2:
                raise ValueError(f"Invalid deal_id format: {deal_id}")
            
            shop_id = parts[0]
            item_id = parts[1]
            
            return shop_id, item_id
        except Exception as e:
            logger.error(f"Error extracting IDs from deal_id {deal_id}: {str(e)}")
            raise ValueError(f"Invalid deal_id format: {deal_id}")
    
    @staticmethod
    def extract_ids_from_url(shopee_url):
        """
        Extract item_id and shop_id from Shopee URL
        Examples: 
        - https://shopee.tw/---i.104581011.24901963692
        - https://shopee.tw/---i.104911467.5684470744
        """
        try:
            # Log the URL for debugging
            logger.info(f"Extracting IDs from URL: {shopee_url}")
            
            # Parse URL
            parsed_url = urlparse(shopee_url)
            
            # Extract path
            path = parsed_url.path
            logger.debug(f"URL path: {path}")
            
            # Find the pattern -i.{shop_id}.{item_id}
            if '-i.' in path:
                parts = path.split('-i.')
                if len(parts) == 2:
                    id_parts = parts[1].split('.')
                    if len(id_parts) == 2:
                        shop_id = id_parts[0]
                        item_id = id_parts[1]
                        logger.info(f"Successfully extracted shop_id={shop_id}, item_id={item_id} from URL")
                        return shop_id, item_id
            
            # If we couldn't extract from path using -i. pattern, try other patterns
            # For example, some URLs might have pattern product-i{shop_id}.{item_id}
            if 'product-i' in path:
                parts = path.split('product-i')
                if len(parts) == 2 and '.' in parts[1]:
                    id_parts = parts[1].split('.')
                    if len(id_parts) == 2:
                        shop_id = id_parts[0]
                        item_id = id_parts[1]
                        logger.info(f"Successfully extracted shop_id={shop_id}, item_id={item_id} from URL using product-i pattern")
                        return shop_id, item_id
            
            # Try a different approach for URLs that don't match the standard format
            # Look for a pattern of numbers separated by a dot
            import re
            # Find all patterns of numbers.numbers in the URL
            matches = re.findall(r'(\d+)\.(\d+)', shopee_url)
            if matches:
                # Assume the last match is the one we want
                shop_id, item_id = matches[-1]
                logger.info(f"Using regex, extracted shop_id={shop_id}, item_id={item_id} from URL")
                return shop_id, item_id
            
            # If we couldn't extract from path, check query parameters
            query_params = parse_qs(parsed_url.query)
            if 'itemid' in query_params and 'shopid' in query_params:
                item_id = query_params['itemid'][0]
                shop_id = query_params['shopid'][0]
                logger.info(f"Successfully extracted shop_id={shop_id}, item_id={item_id} from URL query parameters")
                return shop_id, item_id
                
            raise ValueError(f"Could not extract shop_id and item_id from URL: {shopee_url}")
        except Exception as e:
            logger.error(f"Error extracting IDs from URL {shopee_url}: {str(e)}")
            raise ValueError(f"Invalid Shopee URL format: {shopee_url}")
    
    # Cache for product data to avoid redundant requests
    # Cache up to 1000 most recently used products
    @staticmethod
    @lru_cache(maxsize=1000)
    def _fetch_product_data_cached(shop_id, item_id):
        """
        Cached version of product data fetch using web scraping
        since the direct API gives 403 Forbidden errors
        """
        # Create product page URL
        product_url = f"https://shopee.tw/product/{shop_id}/{item_id}"
        
        # Add some randomness to the user agent to avoid blocking
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            # Try scraping with trafilatura first (best option)
            try:
                logger.info(f"Fetching product page for {shop_id}.{item_id} using trafilatura")
                downloaded = trafilatura.fetch_url(product_url)
                if downloaded:
                    page_content = trafilatura.extract(downloaded, include_comments=False, include_tables=True, output_format='json')
                    if page_content:
                        # Convert JSON string to dict and extract info
                        extracted_data = json.loads(page_content)
                        return {
                            "data": {
                                "item": {
                                    "itemid": int(item_id),
                                    "shopid": int(shop_id),
                                    "name": extracted_data.get("title", ""),
                                    "description": extracted_data.get("text", ""),
                                    "item_status": "normal",
                                    "price": 0,  # Will try to extract this later
                                    "stock": 0,  # Will try to extract this later
                                    "historical_sold": 0,  # Will try to extract this later
                                    "shopee_verified": True,
                                    "is_official_shop": False,
                                    "brand": "Unknown",
                                    "images": []  # Will try to extract these later
                                }
                            },
                            "scraped_content": extracted_data
                        }
            except Exception as trafilatura_error:
                logger.warning(f"Trafilatura extraction failed for {shop_id}.{item_id}: {str(trafilatura_error)}")
                # Fall back to BeautifulSoup if trafilatura fails
            
            # Fallback to direct request + BeautifulSoup if trafilatura failed
            logger.info(f"Falling back to BeautifulSoup for {shop_id}.{item_id}")
            response = session.get(product_url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # If we get a successful response, parse the HTML with BeautifulSoup
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to extract product data from the HTML
                title = ""
                title_elem = soup.select_one('div.YPqix5 > span')
                if title_elem:
                    title = title_elem.text.strip()
                
                # Extract product description from meta tags if available
                description = ""
                meta_desc = soup.select_one('meta[name="description"]')
                if meta_desc and meta_desc.get('content'):
                    description = meta_desc.get('content')
                
                # Structure the data to match the API response format as much as possible
                product_data = {
                    "data": {
                        "item": {
                            "itemid": int(item_id),
                            "shopid": int(shop_id),
                            "name": title,
                            "description": description,
                            "item_status": "normal",
                            "price": 0,  # We can't easily extract this from HTML
                            "stock": 0,  # We can't easily extract this from HTML
                            "historical_sold": 0,  # We can't easily extract this from HTML
                            "shopee_verified": True,
                            "is_official_shop": False,
                            "brand": "Unknown",
                            "images": []  # We can't easily extract these from HTML
                        }
                    },
                    "scraped_html": str(soup)[:5000]  # Include a portion of HTML for debugging
                }
                
                logger.info(f"Successfully extracted basic product data for {shop_id}.{item_id}")
                return product_data
            
            return {"error": f"Unexpected status code: {response.status_code}"}
                
        except requests.RequestException as e:
            logger.error(f"Request error for {shop_id}.{item_id}: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Unexpected error for {shop_id}.{item_id}: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    @staticmethod
    def fetch_product_data(shop_id, item_id):
        """
        Fetch product data from Shopee API with built-in caching
        """
        # Add jitter to avoid thundering herd problem if caching expires
        jitter = random.uniform(0, 0.5)  # Add up to 0.5 seconds of jitter
        time.sleep(jitter)
        
        # Call the cached version
        data = ShopeeService._fetch_product_data_cached(shop_id, item_id)
        
        # Check if we got an error response and handle appropriately
        if isinstance(data, dict) and "error" in data:
            logger.warning(f"Error in cached response for {shop_id}.{item_id}: {data.get('error')}")
            # If there's an error in the cached response, try clearing the cache entry
            ShopeeService._fetch_product_data_cached.cache_clear()
            # Make one more attempt without the cache
            data = ShopeeService._fetch_product_data_cached(shop_id, item_id)
            if isinstance(data, dict) and "error" in data:
                raise Exception(f"Failed to fetch product data: {data.get('error')}")
        
        return data
