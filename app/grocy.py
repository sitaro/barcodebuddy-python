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

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """Make API request."""
        url = f"{self.url}/api/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                timeout=10,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Grocy API error: {e}")
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
