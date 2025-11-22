"""UPC Database API client for barcode lookup."""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class UPCDatabaseClient:
    """Client for UPC Database API (free tier, no API key needed)."""

    BASE_URL = "https://api.upcdatabase.org/product"

    def lookup_barcode(self, barcode: str) -> Optional[Dict[Any, Any]]:
        """
        Look up a barcode in UPC Database.

        Returns product info if found, None otherwise.
        Note: Free tier has rate limits (~100 requests/day)
        """
        try:
            url = f"{self.BASE_URL}/{barcode}"
            logger.info(f"Looking up barcode in UPC Database: {barcode}")

            response = requests.get(url, timeout=10)

            # UPC Database returns 404 if not found
            if response.status_code == 404:
                logger.info(f"❌ Not found in UPC Database: {barcode}")
                return None

            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                # Extract relevant information
                product_info = {
                    'name': data.get('title', 'Unknown Product'),
                    'barcode': barcode,
                    'brand': data.get('brand', ''),
                    'quantity': '',
                    'image_url': '',
                    'categories': data.get('category', ''),
                    'description': data.get('description', '')
                }

                logger.info(f"✅ Found in UPC Database: {product_info['name']}")
                return product_info
            else:
                logger.info(f"❌ Not found in UPC Database: {barcode}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"UPC Database API error: {e}")
            return None
