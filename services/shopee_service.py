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
from requests_html import HTMLSession

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
                logger.info(f"Successfully downloaded HTML for {shop_id}.{item_id}")
                
                # Try to extract product data from the HTML using multiple methods
                title = ""
                # Try different selectors for the title
                selectors = [
                    'div.YPqix5 > span',
                    'div.AttM6y > span',
                    'div[class*="product-title"] span',
                    'h1',
                    'meta[property="og:title"]',
                    'title'
                ]
                
                for selector in selectors:
                    try:
                        elem = soup.select_one(selector)
                        if elem:
                            if selector.startswith('meta'):
                                title = elem.get('content', '').strip()
                            else:
                                title = elem.text.strip()
                            if title:
                                logger.info(f"Found title using selector {selector}: {title[:30]}...")
                                break
                    except Exception as e:
                        logger.warning(f"Error extracting title with selector {selector}: {str(e)}")
                
                # If no title found, use product ID as fallback
                if not title:
                    title = f"Product {item_id}"
                    logger.warning(f"Could not extract title for {shop_id}.{item_id}, using fallback")
                
                # Extract product description from meta tags if available
                description = ""
                try:
                    desc_selectors = [
                        'meta[name="description"]',
                        'meta[property="og:description"]',
                        'div[class*="product-desc"]',
                        'div[class*="description"]'
                    ]
                    
                    for selector in desc_selectors:
                        elem = soup.select_one(selector)
                        if elem:
                            if selector.startswith('meta'):
                                description = elem.get('content', '').strip()
                            else:
                                description = elem.text.strip()
                            if description:
                                logger.info(f"Found description using selector {selector}: {description[:30]}...")
                                break
                except Exception as e:
                    logger.warning(f"Error extracting description: {str(e)}")
                
                # Try to extract price
                price = 0
                script_images = []
                try:
                    # Try to find the script tag with product data
                    scripts = soup.find_all('script')
                    for script in scripts:
                        script_content = script.string if script.string else ''
                        if script_content and ('__INITIAL_STATE__' in script_content or 'window._shopee' in script_content):
                            # Found a script with product data
                            logger.info("Found product data in script tag")
                            # Look for price in the script
                            import re
                            # Try to find price pattern
                            price_match = re.search(r'"price":\s*(\d+\.?\d*)', script_content)
                            if price_match:
                                try:
                                    price = float(price_match.group(1))
                                    logger.info(f"Found price in script: {price}")
                                except ValueError:
                                    pass
                            
                            # Try to find product name
                            if not title:
                                name_match = re.search(r'"name":\s*"([^"]+)"', script_content)
                                if name_match:
                                    title = name_match.group(1)
                                    logger.info(f"Found title in script: {title[:30]}...")
                            
                            # Try to find description
                            if not description:
                                desc_match = re.search(r'"description":\s*"([^"]+)"', script_content)
                                if desc_match:
                                    description = desc_match.group(1).replace('\\n', '\n')
                                    logger.info(f"Found description in script: {description[:30]}...")
                            
                            # Try to find images
                            img_matches = re.findall(r'"image":\s*"(https:[^"]+)"', script_content)
                            if img_matches:
                                # Store the images for later use
                                script_images = img_matches
                                logger.info(f"Found {len(script_images)} images in script")
                            break
                    
                    # If we didn't find price in scripts, try selectors as backup
                    if price == 0:
                        price_selectors = [
                            'div[class*="price"] span',
                            'meta[property="product:price:amount"]'
                        ]
                        
                        for selector in price_selectors:
                            elem = soup.select_one(selector)
                            if elem:
                                if selector.startswith('meta'):
                                    price_text = elem.get('content', '').strip()
                                else:
                                    price_text = elem.text.strip()
                                
                                if price_text:
                                    # Remove currency symbols and convert to number
                                    price_text = ''.join(c for c in price_text if c.isdigit() or c == '.')
                                    try:
                                        price = float(price_text)
                                        logger.info(f"Found price using selector {selector}: {price}")
                                        break
                                    except ValueError:
                                        continue
                except Exception as e:
                    logger.warning(f"Error extracting price: {str(e)}")
                
                # Look for images
                images = []
                try:
                    # First check if we already found images in scripts
                    if 'script_images' in locals() and script_images:
                        images.extend(script_images)
                        logger.info(f"Using {len(images)} images from script data")
                    else:
                        # Try to find image URLs in various places
                        img_selectors = [
                            'meta[property="og:image"]',
                            'img[class*="product-image"]',
                            'img[class*="main-image"]'
                        ]
                        
                        for selector in img_selectors:
                            elems = soup.select(selector)
                            if elems:
                                for elem in elems:
                                    if selector.startswith('meta'):
                                        img_url = elem.get('content', '')
                                    else:
                                        img_url = elem.get('src', '')
                                    if img_url and img_url not in images and img_url.startswith('http'):
                                        images.append(img_url)
                                if images:
                                    logger.info(f"Found {len(images)} images using selector {selector}")
                                    break
                except Exception as e:
                    logger.warning(f"Error extracting images: {str(e)}")
                
                # Structure the data to match the API response format as much as possible
                product_data = {
                    "data": {
                        "item": {
                            "itemid": int(item_id),
                            "shopid": int(shop_id),
                            "name": title,
                            "description": description,
                            "item_status": "normal",
                            "price": price,
                            "stock": 100,  # Default stock
                            "historical_sold": 0,  # Default historical sold
                            "shopee_verified": True,
                            "is_official_shop": False,
                            "brand": "Unknown",
                            "images": images
                        }
                    },
                    "scraped_html": str(soup.title)  # Just include title tag instead of entire HTML
                }
                
                logger.info(f"Successfully extracted product data for {shop_id}.{item_id}")
                return product_data
            
            return {"error": f"Unexpected status code: {response.status_code}"}
                
        except requests.RequestException as e:
            logger.error(f"Request error for {shop_id}.{item_id}: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Unexpected error for {shop_id}.{item_id}: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    @staticmethod
    def _fetch_product_data_api(shop_id, item_id):
        """
        Fetch product data using a direct API call to Shopee's API
        """
        api_url = f"https://shopee.tw/api/v4/item/get?itemid={item_id}&shopid={shop_id}"
        logger.info(f"Fetching product with direct API call for {shop_id}.{item_id}")
        
        try:
            # Add some randomness to the user agent to avoid blocking
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            ]
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Referer': f'https://shopee.tw/product/{shop_id}/{item_id}',
                'Origin': 'https://shopee.tw',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90"',
                'sec-ch-ua-mobile': '?0',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin'
            }
            
            cookies = {
                'SPC_F': 'your-random-id',  # This is just a placeholder
                'SPC_SI': 'mall.abcdefghijklmnopqrstuvwxyz',  # This is just a placeholder
                '_gcl_au': '1.1.123456789.1234567890',
                '_med': 'refer', 
                'language': 'en',
                'csrftoken': 'random-csrf-token'
            }
            
            response = session.get(api_url, headers=headers, cookies=cookies, timeout=30)
            logger.info(f"API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data and 'data' in data and 'item' in data['data']:
                        logger.info(f"Successfully extracted product data from API for {shop_id}.{item_id}")
                        
                        # Image processing - Shopee stores partial URLs that need to be completed
                        item_data = data['data']['item']
                        if 'images' in item_data and item_data['images']:
                            full_images = []
                            for img in item_data['images']:
                                if img:
                                    # Transform image URLs to full URLs if needed
                                    if img.startswith('http'):
                                        full_images.append(img)
                                    else:
                                        # Construct the full image URL based on Shopee's pattern
                                        full_url = f"https://cf.shopee.tw/file/{img}"
                                        full_images.append(full_url)
                            item_data['images'] = full_images
                            
                        return data
                except Exception as json_error:
                    logger.warning(f"JSON parsing error: {str(json_error)}")
                    return {"error": f"JSON parsing error: {str(json_error)}"}
            
            return {"error": f"API request failed with status code: {response.status_code}"}
        except Exception as e:
            logger.error(f"Error fetching product from API for {shop_id}.{item_id}: {str(e)}")
            return {"error": f"Failed to fetch product from API: {str(e)}"}
    
    @staticmethod
    def fetch_product_data(shop_id, item_id):
        """
        Fetch product data from Shopee with built-in caching and fallbacks
        """
        # Add jitter to avoid thundering herd problem if caching expires
        jitter = random.uniform(0, 0.5)  # Add up to 0.5 seconds of jitter
        time.sleep(jitter)
        
        # Try the standard method first
        data = ShopeeService._fetch_product_data_cached(shop_id, item_id)
        
        # Check if we got a valid response or need to try other methods
        if isinstance(data, dict):
            # Check if there was an error or if we got empty data
            item_data = data.get('data', {}).get('item', {})
            if "error" in data or not item_data.get('name'):
                # If failed, clear cache and try with JavaScript rendering
                logger.warning(f"Standard method failed for {shop_id}.{item_id}, trying JavaScript rendering")
                ShopeeService._fetch_product_data_cached.cache_clear()
                
                # Try with JavaScript rendering
                try:
                    js_data = ShopeeService._fetch_product_data_with_js(shop_id, item_id)
                    if isinstance(js_data, dict) and not "error" in js_data:
                        return js_data
                    else:
                        # If JavaScript rendering also failed, try standard method one more time
                        data = ShopeeService._fetch_product_data_cached(shop_id, item_id)
                except Exception as js_error:
                    logger.error(f"JavaScript rendering failed: {str(js_error)}")
                    # Try standard method one more time
                    data = ShopeeService._fetch_product_data_cached(shop_id, item_id)
        
        # If we still have an error, raise an exception
        if isinstance(data, dict) and "error" in data:
            raise Exception(f"Failed to fetch product data: {data.get('error')}")
        
        return data
