"""Grocy API client."""
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GrocyClient:
    """Client for Grocy API."""

    def __init__(self, url: str, api_key: str):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'GROCY-API-KEY': api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        # Use a session to persist cookies/connection
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """Make API request."""
        url = f"{self.url}/api/{endpoint.lstrip('/')}"
        logger.debug(f"Grocy API call: {method} {url}")
        try:
            # Don't follow redirects - API should respond directly
            response = self.session.request(
                method,
                url,
                timeout=10,
                allow_redirects=False,
                **kwargs
            )
            logger.debug(f"Grocy response: Status {response.status_code}, Content-Type: {response.headers.get('Content-Type', 'unknown')}")

            # Check for redirects (means auth failed)
            if response.status_code in (301, 302, 303, 307, 308):
                logger.error(f"Grocy returned redirect (status {response.status_code}) - API key may be invalid")
                logger.error(f"Redirect location: {response.headers.get('Location', 'unknown')}")
                return None

            response.raise_for_status()

            if not response.text:
                logger.warning("Grocy returned empty response")
                return {}

            return response.json()
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Grocy API returned invalid JSON: {e}")
            logger.error(f"Response text: {response.text[:200]}")  # First 200 chars
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Grocy API request failed: {e}")
            return None

    def test_connection(self) -> bool:
        """Test Grocy connection."""
        result = self._request('GET', 'system/info')
        return result is not None

    def find_product_by_barcode(self, barcode: str) -> Optional[Dict[Any, Any]]:
        """Find product by barcode."""
        result = self._request('GET', f'stock/products/by-barcode/{barcode}')
        return result

    def add_product(self, product_id: int, amount: float = 1.0) -> bool:
        """Add product to stock."""
        data = {
            'amount': amount,
            'transaction_type': 'purchase'
        }
        result = self._request('POST', f'stock/products/{product_id}/add', json=data)
        return result is not None

    def consume_product(self, product_id: int, amount: float = 1.0) -> bool:
        """Consume product from stock."""
        data = {
            'amount': amount,
            'transaction_type': 'consume'
        }
        result = self._request('POST', f'stock/products/{product_id}/consume', json=data)
        return result is not None

    def get_product_info(self, product_id: int) -> Optional[Dict[Any, Any]]:
        """Get product information."""
        return self._request('GET', f'objects/products/{product_id}')
