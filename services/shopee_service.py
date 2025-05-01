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
    def _fetch_product_data_direct(shop_id, item_id):
        """
        Direct fallback method using BeautifulSoup to scrape the page without caching
        """
        product_url = f"https://shopee.tw/product/{shop_id}/{item_id}"
        logger.info(f"Fetching product with direct BeautifulSoup scraping for {shop_id}.{item_id}")
        
        try:
            # Add some randomness to the user agent to avoid blocking
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
            ]
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Cookie': f'SPC_F=random-id; SPC_SI=mall.random-id; REC_T_ID={time.time()};'
            }
            
            # Use a different session to avoid potential issues with the global session
            with requests.Session() as direct_session:
                response = direct_session.get(product_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # If we get a successful response, parse the HTML with BeautifulSoup
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    logger.info(f"Successfully downloaded HTML for {shop_id}.{item_id}")
                    
                    # Try to extract product title
                    title = ""
                    # Use broader and more varied selectors for better coverage
                    title_selectors = [
                        'h1', 
                        'title',
                        'meta[property="og:title"]',
                        'meta[name="title"]',
                        'div.YPqix5 > span',
                        'div[class*="product-title"]',
                        'div[class*="title"]',
                        'span[class*="title"]',
                        '.product-briefing .qaNIZv',  # Specific to Shopee
                        '[class*="ProductTitle"]',    # Specific to Shopee
                        '.WU63RVh h1'
                    ]
                    
                    for selector in title_selectors:
                        try:
                            elems = soup.select(selector)
                            if elems:
                                for elem in elems:
                                    if selector.startswith('meta'):
                                        title_text = elem.get('content', '')
                                    else:
                                        title_text = elem.text
                                    if title_text and len(title_text.strip()) > 3:
                                        title = title_text.strip()
                                        logger.info(f"Found title using selector {selector}: {title[:30]}...")
                                        break
                                if title:
                                    break
                        except Exception as e:
                            logger.warning(f"Error with selector {selector}: {str(e)}")
                    
                    # Try to extract product description
                    description = ""
                    desc_selectors = [
                        'meta[name="description"]',
                        'meta[property="og:description"]',
                        'div[class*="desc"]',
                        'div[class*="detail"]'
                    ]
                    
                    for selector in desc_selectors:
                        try:
                            elems = soup.select(selector)
                            if elems:
                                for elem in elems:
                                    if selector.startswith('meta'):
                                        desc_text = elem.get('content', '')
                                    else:
                                        desc_text = elem.text
                                    if desc_text and len(desc_text.strip()) > 10:
                                        description = desc_text.strip()
                                        logger.info(f"Found description using selector {selector}: {description[:30]}...")
                                        break
                                if description:
                                    break
                        except Exception as e:
                            logger.warning(f"Error with selector {selector}: {str(e)}")
                    
                    # Try to extract price
                    price = 0
                    price_selectors = [
                        'meta[property="product:price:amount"]',
                        'div[class*="price"]',
                        'span[class*="price"]'
                    ]
                    
                    for selector in price_selectors:
                        try:
                            elems = soup.select(selector)
                            if elems:
                                for elem in elems:
                                    if selector.startswith('meta'):
                                        price_text = elem.get('content', '')
                                    else:
                                        price_text = elem.text
                                    if price_text:
                                        # Clean the price text and try to extract a number
                                        clean_price = ''.join(c for c in price_text if c.isdigit() or c == '.')
                                        if clean_price:
                                            try:
                                                price = float(clean_price)
                                                logger.info(f"Found price using selector {selector}: {price}")
                                                break
                                            except ValueError:
                                                pass
                                if price > 0:
                                    break
                        except Exception as e:
                            logger.warning(f"Error with selector {selector}: {str(e)}")
                    
                    # Try to extract images
                    images = []
                    img_selectors = [
                        'meta[property="og:image"]',
                        'img[class*="product"]',
                        'img[class*="main"]',
                        'img'
                    ]
                    
                    for selector in img_selectors:
                        try:
                            elems = soup.select(selector)
                            if elems:
                                for elem in elems:
                                    if selector.startswith('meta'):
                                        img_url = elem.get('content', '')
                                    else:
                                        img_url = elem.get('src', '') or elem.get('data-src', '')
                                    if img_url and img_url.startswith('http') and img_url not in images:
                                        images.append(img_url)
                                if images:
                                    logger.info(f"Found {len(images)} images using selector {selector}")
                                    break
                        except Exception as e:
                            logger.warning(f"Error with selector {selector}: {str(e)}")
                    
                    # If no title found, check page content for error messages
                    if not title:
                        # Check if it's a JavaScript required message or bot detection
                        bot_checks = ['enable javascript', 'robot', 'captcha', 'verification']
                        page_text = soup.get_text().lower()
                        for check in bot_checks:
                            if check in page_text:
                                logger.warning(f"Page appears to require JavaScript or bot verification: '{check}' found")
                                return {"error": f"Page requires JavaScript or bot verification: '{check}' found"}
                        
                        # If no specific error detected, use product ID as fallback title
                        title = f"Shopee Product {item_id}"
                    
                    # Structure the data to match the API response format
                    product_data = {
                        "data": {
                            "item": {
                                "itemid": int(item_id),
                                "shopid": int(shop_id),
                                "name": title,
                                "description": description if description else "No description available",
                                "item_status": "normal",
                                "price": price,
                                "stock": 100,  # Default value
                                "historical_sold": 0,  # Default value
                                "shopee_verified": True,
                                "is_official_shop": False,
                                "brand": "Unknown",
                                "images": images
                            }
                        }
                    }
                    
                    logger.info(f"Successfully extracted product data directly for {shop_id}.{item_id}")
                    return product_data
                
                return {"error": f"Unexpected status code: {response.status_code}"}
        except Exception as e:
            logger.error(f"Error with direct scraping for {shop_id}.{item_id}: {str(e)}")
            return {"error": f"Direct scraping failed: {str(e)}"}
    
    @staticmethod
    def fetch_product_data(shop_id, item_id):
        """
        Fetch product data from Shopee with built-in caching and fallbacks
        """
        # Add jitter to avoid thundering herd problem if caching expires
        jitter = random.uniform(0, 0.5)  # Add up to 0.5 seconds of jitter
        time.sleep(jitter)
        
        # Try different methods in sequence until one works
        methods = [
            # First attempt: try HTML scraping with trafilatura
            (ShopeeService._fetch_product_data_cached, "HTML scraping with trafilatura"),
            # Second attempt: try direct API call
            (ShopeeService._fetch_product_data_api, "API call"),
            # Third attempt: try direct BeautifulSoup scraping
            (ShopeeService._fetch_product_data_direct, "Direct BeautifulSoup scraping")
            # The JavaScript rendering method was removed due to missing dependencies
            # but could be re-enabled if needed
        ]
        
        # Track all errors for detailed reporting if all methods fail
        errors = []
        
        # Try each method in sequence
        for method, method_name in methods:
            try:
                logger.info(f"Trying {method_name} method for {shop_id}.{item_id}")
                data = method(shop_id, item_id)
                
                # Check if we got a valid response
                if isinstance(data, dict):
                    # If there's no error and we have data, return it
                    if "error" not in data:
                        item_data = data.get('data', {}).get('item', {})
                        # Check if we have valid product data (name or images)
                        if item_data and (item_data.get('name') or item_data.get('images')):
                            # Validate that we have a real product, not a placeholder or error message
                            name = item_data.get('name', '')
                            if name and not (
                                'enable javascript' in name.lower() or
                                'please enable' in name.lower() or
                                'robot check' in name.lower() or
                                'captcha' in name.lower() or
                                name.strip() == '' or
                                len(name.strip()) < 3
                            ):
                                logger.info(f"Successfully fetched data using {method_name} method")
                                return data
                            else:
                                errors.append(f"{method_name}: Retrieved name '{name}' appears to be an error message")
                                logger.warning(f"{method_name} failed: Retrieved name '{name}' appears to be an error message")
                        else:
                            errors.append(f"{method_name}: Retrieved empty or invalid product data")
                            logger.warning(f"{method_name} failed: Retrieved empty or invalid product data")
                    # Otherwise record the error and try next method
                    else:
                        errors.append(f"{method_name}: {data.get('error')}")
                        logger.warning(f"{method_name} failed: {data.get('error')}")
                else:
                    errors.append(f"{method_name}: Invalid response format")
                    logger.warning(f"{method_name} failed: Invalid response format")
            except Exception as e:
                errors.append(f"{method_name}: {str(e)}")
                logger.error(f"Error with {method_name} method: {str(e)}")
        
        # If we've tried all methods and none worked, construct a generic product
        # with the basic information we know for sure
        logger.warning(f"All methods failed for {shop_id}.{item_id}, using fallback")
        
        # Create a minimal response with the data we know
        fallback_data = {
            "data": {
                "item": {
                    "itemid": int(item_id),
                    "shopid": int(shop_id),
                    "name": f"Shopee Product (ID: {item_id})",
                    "description": "Product information unavailable. Please check the Shopee website for details.",
                    "item_status": "normal",
                    "price": 0,  # Cannot determine price
                    "stock": 0,  # Cannot determine stock
                    "historical_sold": 0,  # Cannot determine historical sales
                    "shopee_verified": True,
                    "is_official_shop": False,
                    "brand": "Unknown",
                    "images": []
                }
            },
            "errors": errors  # Include all errors for debugging
        }
        
        return fallback_data
