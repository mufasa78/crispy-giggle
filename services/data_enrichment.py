import logging
import re
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class DataEnrichmentService:
    """
    Service for enhancing and enriching product data scraped from Shopee.
    This extracts more precise details from the raw data.
    """
    
    @staticmethod
    def extract_precise_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract precise product data from raw Shopee data.
        
        Args:
            raw_data: The raw data dictionary scraped from Shopee
            
        Returns:
            Enhanced and enriched product data dictionary with more fields
        """
        try:
            # Start with the original data
            item_data = raw_data.get('data', {}).get('item', {})
            
            if not item_data:
                logger.warning("No item data found in raw_data")
                return raw_data
            
            # Basic product information
            item_id = item_data.get('itemid')
            shop_id = item_data.get('shopid')
            
            # Create the enriched data structure
            enriched_data = {
                'data': {
                    'item': {
                        'itemid': item_id,
                        'shopid': shop_id,
                        'name': item_data.get('name', ''),
                        'description': item_data.get('description', ''),
                        'item_status': item_data.get('item_status', 'normal'),
                        
                        # Price information with more precision
                        'price': DataEnrichmentService._extract_price(item_data),
                        'price_before_discount': DataEnrichmentService._extract_original_price(item_data),
                        'currency': 'TWD',  # Taiwan currency
                        'discount_percentage': DataEnrichmentService._calculate_discount(item_data),
                        
                        # Stock and sales information
                        'stock': DataEnrichmentService._extract_stock(item_data),
                        'historical_sold': DataEnrichmentService._extract_historical_sold(item_data),
                        'monthly_sales': DataEnrichmentService._extract_monthly_sales(item_data),
                        
                        # Enhanced images with proper URLs
                        'images': DataEnrichmentService._process_images(item_data.get('images', [])),
                        'image_thumbnails': DataEnrichmentService._process_thumbnails(item_data),
                        'video_info': DataEnrichmentService._extract_video_info(item_data),
                        
                        # Product details
                        'categories': DataEnrichmentService._extract_categories(item_data),
                        'attributes': DataEnrichmentService._extract_attributes(item_data),
                        'brand': DataEnrichmentService._extract_brand(item_data),
                        'model': DataEnrichmentService._extract_model(item_data),
                        'variants': DataEnrichmentService._extract_variants(item_data),
                        
                        # Shipping information
                        'shipping_options': DataEnrichmentService._extract_shipping(item_data),
                        
                        # Seller information
                        'seller': {
                            'shopid': shop_id,
                            'name': DataEnrichmentService._extract_shop_name(item_data),
                            'location': DataEnrichmentService._extract_shop_location(item_data),
                            'rating': DataEnrichmentService._extract_shop_rating(item_data),
                            'followers': DataEnrichmentService._extract_shop_followers(item_data),
                            'response_rate': DataEnrichmentService._extract_response_rate(item_data),
                            'response_time': DataEnrichmentService._extract_response_time(item_data),
                            'is_official': DataEnrichmentService._is_official_shop(item_data),
                            'is_preferred': DataEnrichmentService._is_preferred_seller(item_data)
                        },
                        
                        # Ratings information
                        'rating': {
                            'rating_star': DataEnrichmentService._extract_rating(item_data),
                            'rating_count': DataEnrichmentService._extract_rating_count(item_data),
                            'one_star': DataEnrichmentService._extract_star_count(item_data, 1),
                            'two_star': DataEnrichmentService._extract_star_count(item_data, 2),
                            'three_star': DataEnrichmentService._extract_star_count(item_data, 3),
                            'four_star': DataEnrichmentService._extract_star_count(item_data, 4),
                            'five_star': DataEnrichmentService._extract_star_count(item_data, 5)
                        },
                        
                        # Enhanced metadata
                        'shopee_verified': item_data.get('shopee_verified', False),
                        'updated_at': datetime.utcnow().isoformat(),
                        
                        # Keep original raw data for reference
                        'raw_data': item_data
                    }
                }
            }
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Error enriching data: {str(e)}")
            # Return original data if enrichment fails
            return raw_data
    
    @staticmethod
    def _extract_price(item_data: Dict[str, Any]) -> float:
        """Extract the current price."""
        try:
            # Check for price and price_min fields
            if 'price' in item_data:
                # Convert from Shopee's price format (sometimes in smallest currency unit)
                price = float(item_data['price'])
                # If price seems to be in smallest unit (e.g., cents), convert to dollars
                if price > 10000 and 'currency' in item_data and item_data['currency'] != 'IDR':
                    price = price / 100000
                return price
            
            # Look for price in models
            if 'models' in item_data and item_data['models']:
                # Take average of all model prices
                prices = [float(model.get('price', 0)) for model in item_data['models']]
                if prices:
                    return sum(prices) / len(prices)
            
            return 0.0
        except Exception as e:
            logger.warning(f"Error extracting price: {str(e)}")
            return 0.0
    
    @staticmethod
    def _extract_original_price(item_data: Dict[str, Any]) -> float:
        """Extract the original price before discount."""
        try:
            if 'price_before_discount' in item_data:
                price = float(item_data['price_before_discount'])
                # If price seems to be in smallest unit (e.g., cents), convert to dollars
                if price > 10000 and 'currency' in item_data and item_data['currency'] != 'IDR':
                    price = price / 100000
                return price
            return DataEnrichmentService._extract_price(item_data)
        except Exception as e:
            logger.warning(f"Error extracting original price: {str(e)}")
            return DataEnrichmentService._extract_price(item_data)
    
    @staticmethod
    def _calculate_discount(item_data: Dict[str, Any]) -> int:
        """Calculate discount percentage."""
        try:
            if 'discount' in item_data:
                return int(item_data['discount'])
                
            current_price = DataEnrichmentService._extract_price(item_data)
            original_price = DataEnrichmentService._extract_original_price(item_data)
            
            if original_price > 0 and original_price > current_price:
                return int(round((1 - current_price / original_price) * 100))
            return 0
        except Exception as e:
            logger.warning(f"Error calculating discount: {str(e)}")
            return 0
    
    @staticmethod
    def _extract_stock(item_data: Dict[str, Any]) -> int:
        """Extract the available stock."""
        try:
            if 'stock' in item_data:
                return int(item_data['stock'])
                
            # Try to extract from models
            if 'models' in item_data and item_data['models']:
                return sum(int(model.get('stock', 0)) for model in item_data['models'])
                
            return 0
        except Exception as e:
            logger.warning(f"Error extracting stock: {str(e)}")
            return 0
    
    @staticmethod
    def _extract_historical_sold(item_data: Dict[str, Any]) -> int:
        """Extract historically sold quantity."""
        try:
            if 'historical_sold' in item_data:
                return int(item_data['historical_sold'])
            return 0
        except Exception as e:
            logger.warning(f"Error extracting historical sold: {str(e)}")
            return 0
    
    @staticmethod
    def _extract_monthly_sales(item_data: Dict[str, Any]) -> int:
        """Extract monthly sales if available."""
        try:
            if 'sold' in item_data:
                return int(item_data['sold'])
            return 0
        except Exception as e:
            logger.warning(f"Error extracting monthly sales: {str(e)}")
            return 0
    
    @staticmethod
    def _process_images(images: List[str]) -> List[str]:
        """Process and clean image URLs."""
        try:
            processed_images = []
            for img in images:
                if not img:
                    continue
                # Make sure image URL is complete
                if img.startswith('http'):
                    processed_images.append(img)
                else:
                    # Construct the full image URL based on Shopee's pattern
                    processed_images.append(f"https://cf.shopee.tw/file/{img}")
            return processed_images
        except Exception as e:
            logger.warning(f"Error processing images: {str(e)}")
            return []
    
    @staticmethod
    def _process_thumbnails(item_data: Dict[str, Any]) -> List[str]:
        """Extract thumbnail images."""
        try:
            thumbnails = []
            # Try various fields that might contain thumbnails
            if 'images_thumbnail' in item_data:
                thumbnails = item_data['images_thumbnail']
            elif 'image_thumbnail' in item_data:
                thumbnails = item_data['image_thumbnail']
            # Process the thumbnail URLs similar to main images
            return DataEnrichmentService._process_images(thumbnails)
        except Exception as e:
            logger.warning(f"Error processing thumbnails: {str(e)}")
            return []
    
    @staticmethod
    def _extract_video_info(item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract video information if available."""
        try:
            video_info = {}
            if 'video_info_list' in item_data and item_data['video_info_list']:
                video = item_data['video_info_list'][0]
                video_info = {
                    'url': video.get('video_url', ''),
                    'thumbnail': video.get('thumbnail_url', ''),
                    'duration': video.get('duration', 0)
                }
            return video_info
        except Exception as e:
            logger.warning(f"Error extracting video info: {str(e)}")
            return {}
    
    @staticmethod
    def _extract_categories(item_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract product categories."""
        try:
            categories = []
            if 'categories' in item_data and item_data['categories']:
                for category in item_data['categories']:
                    categories.append({
                        'id': category.get('catid', 0),
                        'name': category.get('display_name', ''),
                        'level': category.get('level', 0)
                    })
            return categories
        except Exception as e:
            logger.warning(f"Error extracting categories: {str(e)}")
            return []
    
    @staticmethod
    def _extract_attributes(item_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract product attributes."""
        try:
            attributes = []
            if 'attributes' in item_data and item_data['attributes']:
                for attr in item_data['attributes']:
                    attributes.append({
                        'name': attr.get('name', ''),
                        'value': attr.get('value', '')
                    })
            return attributes
        except Exception as e:
            logger.warning(f"Error extracting attributes: {str(e)}")
            return []
    
    @staticmethod
    def _extract_brand(item_data: Dict[str, Any]) -> str:
        """Extract product brand."""
        try:
            if 'brand' in item_data:
                return item_data['brand']
                
            # Try to find brand in attributes
            if 'attributes' in item_data and item_data['attributes']:
                for attr in item_data['attributes']:
                    if attr.get('name', '').lower() in ['brand', 'brands', '品牌']:
                        return attr.get('value', '')
            return ''
        except Exception as e:
            logger.warning(f"Error extracting brand: {str(e)}")
            return ''
    
    @staticmethod
    def _extract_model(item_data: Dict[str, Any]) -> str:
        """Extract product model."""
        try:
            # Try to find model in attributes
            if 'attributes' in item_data and item_data['attributes']:
                for attr in item_data['attributes']:
                    if attr.get('name', '').lower() in ['model', '型號', '型号']:
                        return attr.get('value', '')
            return ''
        except Exception as e:
            logger.warning(f"Error extracting model: {str(e)}")
            return ''
    
    @staticmethod
    def _extract_variants(item_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract product variants."""
        try:
            variants = []
            if 'models' in item_data and item_data['models']:
                # Get tier variations (variation types like color, size, etc.)
                tier_variations = []
                if 'tier_variations' in item_data and item_data['tier_variations']:
                    tier_variations = item_data['tier_variations']
                
                # Process each model/variant
                for model in item_data['models']:
                    variant = {
                        'model_id': model.get('modelid', 0),
                        'name': model.get('name', ''),
                        'price': float(model.get('price', 0)) / 100000 if int(model.get('price', 0)) > 10000 else float(model.get('price', 0)),
                        'stock': int(model.get('stock', 0)),
                        'options': {}
                    }
                    
                    # Add variation options (e.g., "Color": "Red", "Size": "XL")
                    if model.get('extinfo') and 'option_indexes' in model['extinfo'] and tier_variations:
                        option_indexes = model['extinfo']['option_indexes']
                        for i, index in enumerate(option_indexes):
                            if i < len(tier_variations):
                                variation = tier_variations[i]
                                name = variation.get('name', f'Option {i+1}')
                                if variation.get('options') and index < len(variation['options']):
                                    variant['options'][name] = variation['options'][index]
                    
                    variants.append(variant)
            return variants
        except Exception as e:
            logger.warning(f"Error extracting variants: {str(e)}")
            return []
    
    @staticmethod
    def _extract_shipping(item_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract shipping options."""
        try:
            shipping = []
            if 'shipping_fee_info' in item_data and item_data['shipping_fee_info']:
                for option in item_data['shipping_fee_info']:
                    shipping.append({
                        'method': option.get('name', ''),
                        'fee': float(option.get('shipping_fee', 0)),
                        'min_days': option.get('min_days', 0),
                        'max_days': option.get('max_days', 0)
                    })
            return shipping
        except Exception as e:
            logger.warning(f"Error extracting shipping: {str(e)}")
            return []
    
    @staticmethod
    def _extract_shop_name(item_data: Dict[str, Any]) -> str:
        """Extract seller shop name."""
        try:
            if 'shop_info' in item_data and item_data['shop_info']:
                return item_data['shop_info'].get('name', '')
            return ''
        except Exception as e:
            logger.warning(f"Error extracting shop name: {str(e)}")
            return ''
    
    @staticmethod
    def _extract_shop_location(item_data: Dict[str, Any]) -> str:
        """Extract seller location."""
        try:
            if 'shop_info' in item_data and item_data['shop_info']:
                return item_data['shop_info'].get('shop_location', '')
            return ''
        except Exception as e:
            logger.warning(f"Error extracting shop location: {str(e)}")
            return ''
    
    @staticmethod
    def _extract_shop_rating(item_data: Dict[str, Any]) -> float:
        """Extract seller rating."""
        try:
            if 'shop_info' in item_data and item_data['shop_info']:
                rating = item_data['shop_info'].get('shop_rating', 0)
                if isinstance(rating, dict) and 'rating_star' in rating:
                    return float(rating['rating_star'])
                return float(rating)
            return 0.0
        except Exception as e:
            logger.warning(f"Error extracting shop rating: {str(e)}")
            return 0.0
    
    @staticmethod
    def _extract_shop_followers(item_data: Dict[str, Any]) -> int:
        """Extract shop followers count."""
        try:
            if 'shop_info' in item_data and item_data['shop_info']:
                return int(item_data['shop_info'].get('follower_count', 0))
            return 0
        except Exception as e:
            logger.warning(f"Error extracting shop followers: {str(e)}")
            return 0
    
    @staticmethod
    def _extract_response_rate(item_data: Dict[str, Any]) -> float:
        """Extract seller response rate."""
        try:
            if 'shop_info' in item_data and item_data['shop_info']:
                return float(item_data['shop_info'].get('response_rate', 0))
            return 0.0
        except Exception as e:
            logger.warning(f"Error extracting response rate: {str(e)}")
            return 0.0
    
    @staticmethod
    def _extract_response_time(item_data: Dict[str, Any]) -> int:
        """Extract seller response time in hours."""
        try:
            if 'shop_info' in item_data and item_data['shop_info']:
                # Response time is usually in minutes or seconds, convert to hours
                time_val = item_data['shop_info'].get('response_time', 0)
                # If it's in seconds, convert to hours
                if time_val > 3600:
                    return round(time_val / 3600)
                # If it's in minutes, convert to hours
                elif time_val > 60:
                    return round(time_val / 60)
                return int(time_val)
            return 0
        except Exception as e:
            logger.warning(f"Error extracting response time: {str(e)}")
            return 0
    
    @staticmethod
    def _is_official_shop(item_data: Dict[str, Any]) -> bool:
        """Check if shop is official."""
        try:
            if 'shop_info' in item_data and item_data['shop_info']:
                return item_data['shop_info'].get('is_official_shop', False)
            if 'is_official_shop' in item_data:
                return item_data['is_official_shop']
            return False
        except Exception as e:
            logger.warning(f"Error checking official shop: {str(e)}")
            return False
    
    @staticmethod
    def _is_preferred_seller(item_data: Dict[str, Any]) -> bool:
        """Check if seller is preferred."""
        try:
            if 'shop_info' in item_data and item_data['shop_info']:
                return item_data['shop_info'].get('is_preferred_plus_seller', False)
            return False
        except Exception as e:
            logger.warning(f"Error checking preferred seller: {str(e)}")
            return False
    
    @staticmethod
    def _extract_rating(item_data: Dict[str, Any]) -> float:
        """Extract product rating."""
        try:
            if 'item_rating' in item_data and item_data['item_rating']:
                rating = item_data['item_rating']
                if 'rating_star' in rating:
                    return float(rating['rating_star'])
            return 0.0
        except Exception as e:
            logger.warning(f"Error extracting rating: {str(e)}")
            return 0.0
    
    @staticmethod
    def _extract_rating_count(item_data: Dict[str, Any]) -> int:
        """Extract product rating count."""
        try:
            if 'item_rating' in item_data and item_data['item_rating']:
                return int(item_data['item_rating'].get('rating_count', 0))
            return 0
        except Exception as e:
            logger.warning(f"Error extracting rating count: {str(e)}")
            return 0
    
    @staticmethod
    def _extract_star_count(item_data: Dict[str, Any], star_level: int) -> int:
        """Extract count for a specific star rating level."""
        try:
            key = f'rating_count_{star_level}'
            if 'item_rating' in item_data and item_data['item_rating'] and key in item_data['item_rating']:
                return int(item_data['item_rating'][key])
            return 0
        except Exception as e:
            logger.warning(f"Error extracting {star_level} star count: {str(e)}")
            return 0
