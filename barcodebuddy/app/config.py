"""Configuration management for Home Assistant Add-on."""
import json
import os
from typing import Optional


class Config:
    """Load and manage add-on configuration."""

    def __init__(self):
        self.config_path = "/data/options.json"
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from Home Assistant."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}

    @property
    def grocy_url(self) -> Optional[str]:
        """Get Grocy URL."""
        url = self._config.get('grocy_url', '').strip()
        return url if url else None

    @property
    def grocy_api_key(self) -> Optional[str]:
        """Get Grocy API key."""
        key = self._config.get('grocy_api_key', '').strip()
        return key if key else None

    @property
    def debug(self) -> bool:
        """Get debug mode."""
        return self._config.get('debug', False)

    @property
    def has_grocy(self) -> bool:
        """Check if Grocy is configured."""
        return self.grocy_url is not None and self.grocy_api_key is not None

    @property
    def barcode_add(self) -> str:
        """Get ADD mode barcode."""
        return self._config.get('barcode_add', 'BBUDDY-ADD')

    @property
    def barcode_consume(self) -> str:
        """Get CONSUME mode barcode."""
        return self._config.get('barcode_consume', 'BBUDDY-CONSUME')

    @property
    def barcode_quantity_prefix(self) -> str:
        """Get quantity barcode prefix."""
        return self._config.get('barcode_quantity_prefix', 'BBUDDY-Q-')

    @property
    def enable_openfoodfacts(self) -> bool:
        """Check if OpenFoodFacts database is enabled."""
        return self._config.get('enable_openfoodfacts', True)

    @property
    def enable_upcdatabase(self) -> bool:
        """Check if UPC Database is enabled."""
        return self._config.get('enable_upcdatabase', True)

    @property
    def language(self) -> str:
        """Get configured language."""
        lang = self._config.get('language', 'de').strip()
        # Validate language code
        if lang in ['en', 'de', 'fr', 'es']:
            return lang
        return 'de'  # Default fallback
