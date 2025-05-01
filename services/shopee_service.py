import requests
import logging
import json
import time
from urllib.parse import urlparse, parse_qs

from config import SHOPEE_BASE_URL, REQUEST_TIMEOUT, RETRY_ATTEMPTS, RETRY_DELAY

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
        Example: https://shopee.tw/---i.104581011.24901963692
        """
        try:
            # Parse URL
            parsed_url = urlparse(shopee_url)
            
            # Extract path
            path = parsed_url.path
            
            # Find the pattern -i.{shop_id}.{item_id}
            if '-i.' in path:
                parts = path.split('-i.')
                if len(parts) == 2:
                    id_parts = parts[1].split('.')
                    if len(id_parts) == 2:
                        shop_id = id_parts[0]
                        item_id = id_parts[1]
                        return shop_id, item_id
            
            # If we couldn't extract from path, check query parameters
            query_params = parse_qs(parsed_url.query)
            if 'itemid' in query_params and 'shopid' in query_params:
                item_id = query_params['itemid'][0]
                shop_id = query_params['shopid'][0]
                return shop_id, item_id
                
            raise ValueError(f"Could not extract shop_id and item_id from URL: {shopee_url}")
        except Exception as e:
            logger.error(f"Error extracting IDs from URL {shopee_url}: {str(e)}")
            raise ValueError(f"Invalid Shopee URL format: {shopee_url}")
    
    @staticmethod
    def fetch_product_data(shop_id, item_id):
        """
        Fetch product data from Shopee API
        """
        url = f"{SHOPEE_BASE_URL}?itemid={item_id}&shopid={shop_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://shopee.tw/product/{shop_id}/{item_id}',
            'Origin': 'https://shopee.tw'
        }
        
        # Retry logic
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                
                # Check if response is successful
                if response.status_code == 200:
                    data = response.json()
                    return data
                
                # If rate limited or server error, retry after delay
                if response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(f"Rate limited or server error (attempt {attempt+1}): {response.status_code}")
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    continue
                
                # Other errors
                logger.error(f"Error fetching product data: HTTP {response.status_code}")
                response.raise_for_status()
                
            except requests.RequestException as e:
                logger.error(f"Request error (attempt {attempt+1}): {str(e)}")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    raise Exception(f"Failed to fetch product data after {RETRY_ATTEMPTS} attempts: {str(e)}")
        
        raise Exception(f"Failed to fetch product data after {RETRY_ATTEMPTS} attempts")
