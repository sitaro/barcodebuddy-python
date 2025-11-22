"""EAN-Search.org API client for barcode lookup."""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EANSearchClient:
    """Client for EAN-Search.org API."""

    BASE_URL = "https://api.ean-search.org/api"

    def lookup_barcode(self, barcode: str) -> Optional[Dict[Any, Any]]:
        """
        Look up a barcode in EAN-Search.org database.

        Returns product info if found, None otherwise.
        """
        try:
            params = {
                'op': 'barcode-lookup',
                'barcode': barcode,
                'format': 'json'
            }

            logger.info(f"Looking up barcode in EAN-Search: {barcode}")

            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # EAN-Search returns a list with one item if found
            if isinstance(data, list) and len(data) > 0:
                product = data[0]

                # Extract relevant information
                product_info = {
                    'name': product.get('name', 'Unknown Product'),
                    'barcode': barcode,
                    'brand': '',  # EAN-Search doesn't always provide brand
                    'quantity': '',
                    'image_url': '',
                    'categories': product.get('categoryName', ''),
                    'description': product.get('description', '')
                }

                logger.info(f"✅ Found in EAN-Search: {product_info['name']}")
                return product_info
            else:
                logger.info(f"❌ Not found in EAN-Search: {barcode}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"EAN-Search API error: {e}")
            return None
