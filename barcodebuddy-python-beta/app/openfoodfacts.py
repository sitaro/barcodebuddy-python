"""OpenFoodFacts API client for barcode lookup."""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OpenFoodFactsClient:
    """Client for OpenFoodFacts API."""

    BASE_URL = "https://world.openfoodfacts.org/api/v2"

    def lookup_barcode(self, barcode: str) -> Optional[Dict[Any, Any]]:
        """
        Look up a barcode in OpenFoodFacts database.

        Returns product info if found, None otherwise.
        """
        try:
            url = f"{self.BASE_URL}/product/{barcode}.json"
            logger.info(f"Looking up barcode in OpenFoodFacts: {barcode}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 1 and data.get('product'):
                product = data['product']

                # Extract relevant information
                product_info = {
                    'name': product.get('product_name', 'Unknown Product'),
                    'barcode': barcode,
                    'brand': product.get('brands', ''),
                    'quantity': product.get('quantity', ''),
                    'image_url': product.get('image_url', ''),
                    'categories': product.get('categories', ''),
                    'ingredients': product.get('ingredients_text', '')
                }

                logger.info(f"✅ Found in OpenFoodFacts: {product_info['name']}")
                return product_info
            else:
                logger.info(f"❌ Not found in OpenFoodFacts: {barcode}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenFoodFacts API error: {e}")
            return None
