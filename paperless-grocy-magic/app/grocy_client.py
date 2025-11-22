"""Grocy API client for product and price management."""
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class GrocyProduct:
    """Represents a Grocy product."""

    def __init__(self, data: Dict):
        self.id = data.get('id')
        self.name = data.get('name', '')
        self.description = data.get('description', '')
        self.barcode = data.get('barcode', '')
        self.price = float(data.get('price', 0) or 0)
        self.location_id = data.get('location_id')
        self.qu_id_purchase = data.get('qu_id_purchase')
        self.qu_id_stock = data.get('qu_id_stock')

    def __repr__(self):
        return f"GrocyProduct(id={self.id}, name={self.name}, price={self.price}€)"


class GrocyClient:
    """Client for interacting with Grocy API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'GROCY-API-KEY': api_key,
            'Content-Type': 'application/json'
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make API request to Grocy."""
        url = f"{self.base_url}/api{endpoint}"

        try:
            logger.debug(f"Grocy API: {method} {url}")
            if 'json' in kwargs:
                logger.debug(f"Request data: {kwargs['json']}")

            response = self.session.request(method, url, timeout=10, **kwargs)

            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            logger.debug(f"Response text (first 500 chars): {response.text[:500]}")

            response.raise_for_status()

            if response.status_code == 204:  # No content
                logger.debug("Got 204 No Content, returning empty dict")
                return {}

            return response.json()

        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Grocy API JSON decode error ({method} {endpoint}): {e}")
            logger.error(f"Response was: {response.text[:1000]}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Grocy API request error ({method} {endpoint}): {e}")
            logger.error(f"Full URL: {url}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:1000]}")
            return None

    def test_connection(self) -> bool:
        """Test connection to Grocy API."""
        # Try /system/info first
        result = self._request('GET', '/system/info')
        if result:
            logger.info(f"Connected to Grocy {result.get('grocy_version', {}).get('Version', 'unknown')}")
            return True

        # Fallback: Try to get products as connection test
        logger.warning("/system/info failed, trying /objects/products as fallback...")
        result = self._request('GET', '/objects/products')
        if result is not None:  # Even empty list is success
            logger.info(f"Connected to Grocy (via /objects/products, {len(result)} products)")
            return True

        logger.error("Both connection tests failed")
        return False

    def get_all_products(self) -> List[GrocyProduct]:
        """Get all products from Grocy."""
        data = self._request('GET', '/objects/products')
        if data:
            products = [GrocyProduct(p) for p in data]
            logger.info(f"Retrieved {len(products)} products from Grocy")
            return products
        return []

    def search_products(self, query: str) -> List[GrocyProduct]:
        """Search for products by name."""
        all_products = self.get_all_products()
        query_lower = query.lower()

        # Simple substring search
        matches = [p for p in all_products if query_lower in p.name.lower()]
        logger.debug(f"Search '{query}': {len(matches)} matches")
        return matches

    def get_product(self, product_id: int) -> Optional[GrocyProduct]:
        """Get a specific product by ID."""
        data = self._request('GET', f'/objects/products/{product_id}')
        if data:
            return GrocyProduct(data)
        return None

    def update_product_price(self, product_id: int, price: float, store: str = None) -> tuple[bool, str]:
        """Update product price in Grocy. Returns (success, error_message)."""
        try:
            # Get current product data
            product = self.get_product(product_id)
            if not product:
                error_msg = f"Product {product_id} not found in Grocy"
                logger.error(error_msg)
                return False, error_msg

            # Grocy products table doesn't have a 'price' column
            # Prices are stored separately (via purchases/shopping_locations)
            # We'll store price info in the description field for reference
            update_data = {}

            # Add store to description if provided
            if store:
                desc = product.description or ""
                price_info = f"Preis: {price:.2f}€ ({store})"

                # Check if description already has price info
                if "Preis:" in desc:
                    # Replace existing price info
                    import re
                    desc = re.sub(r'Preis:.*?€\s*\([^)]+\)', price_info, desc)
                else:
                    # Append price info
                    desc = f"{desc}\n{price_info}".strip()

                update_data['description'] = desc

            result = self._request('PUT', f'/objects/products/{product_id}', json=update_data)

            if result:
                logger.info(f"Updated price for product {product_id} ({product.name}): {price:.2f}€")
                return True, ""

            error_msg = "Grocy API returned empty response"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Exception updating product: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def create_product(self, name: str, price: float = 0.0, barcode: str = None) -> tuple[Optional[GrocyProduct], str]:
        """Create a new product in Grocy. Returns (product, error_message)."""
        try:
            # Get default location and quantity unit
            logger.debug(f"Fetching locations and quantity units for new product '{name}'")
            locations = self._request('GET', '/objects/locations')
            qu_units = self._request('GET', '/objects/quantity_units')

            if not locations:
                error_msg = "Could not get locations from Grocy - API returned empty"
                logger.error(error_msg)
                return None, error_msg

            if not qu_units:
                error_msg = "Could not get quantity units from Grocy - API returned empty"
                logger.error(error_msg)
                return None, error_msg

            location_id = locations[0]['id']
            qu_id = qu_units[0]['id']

            logger.debug(f"Using location_id={location_id}, qu_id={qu_id}")

            # Grocy products table doesn't have a 'price' column
            # Store price in description for reference
            price_desc = f'Automatisch erstellt - Preis: {price:.2f}€' if price else 'Automatisch erstellt'

            product_data = {
                'name': name,
                'description': price_desc,
                'location_id': location_id,
                'qu_id_purchase': qu_id,
                'qu_id_stock': qu_id
            }

            if barcode:
                product_data['barcode'] = barcode

            logger.debug(f"Creating product with data: {product_data}")
            result = self._request('POST', '/objects/products', json=product_data)

            if result:
                new_product = GrocyProduct(result)
                logger.info(f"Created product: {new_product}")
                return new_product, ""

            error_msg = "Grocy API returned empty response for POST /objects/products"
            logger.error(error_msg)
            return None, error_msg

        except Exception as e:
            error_msg = f"Exception creating product '{name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg

    def add_to_stock(self, product_id: int, amount: float = 1.0, price: float = None,
                     best_before_days: int = 30) -> tuple[bool, str]:
        """
        Add product to stock (inventory).

        Args:
            product_id: Grocy product ID
            amount: Quantity to add (default: 1.0)
            price: Purchase price (optional, this is where Grocy stores prices!)
            best_before_days: Days until best before date (default: 30)

        Returns:
            (success, error_message) tuple
        """
        try:
            from datetime import datetime, timedelta

            # Calculate best before date
            best_before_date = (datetime.now() + timedelta(days=best_before_days)).strftime('%Y-%m-%d')

            stock_data = {
                'amount': amount,
                'best_before_date': best_before_date
            }

            # Add price if provided (this is where Grocy stores purchase prices!)
            if price is not None:
                stock_data['price'] = str(price)

            logger.debug(f"Adding to stock: product_id={product_id}, amount={amount}, price={price}")
            logger.debug(f"Stock data: {stock_data}")

            result = self._request('POST', f'/stock/products/{product_id}/add', json=stock_data)

            if result is not None:  # Empty dict {} is also success
                logger.info(f"Added {amount}x product {product_id} to stock (price: {price}€)")
                return True, ""

            error_msg = "Grocy API returned None for stock add"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Exception adding product {product_id} to stock: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
