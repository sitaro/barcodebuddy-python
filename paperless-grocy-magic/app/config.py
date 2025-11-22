"""Configuration management for Paperless Grocy Magic."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the add-on."""

    def __init__(self, config_path="/data/options.json"):
        """Initialize configuration from Home Assistant options."""
        self.config_path = Path(config_path)
        self._config = {}
        self.load()

    def load(self):
        """Load configuration from options.json."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._config = json.load(f)
                logger.info("Configuration loaded successfully")
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                self._config = {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._config = {}

    @property
    def paperless_url(self) -> str:
        """Get Paperless URL."""
        return self._config.get('paperless_url', '').strip()

    @property
    def paperless_api_key(self) -> str:
        """Get Paperless API key."""
        return self._config.get('paperless_api_key', '').strip()

    @property
    def paperless_tag(self) -> str:
        """Get Paperless tag for receipts."""
        return self._config.get('paperless_tag', 'kassenbon').strip()

    @property
    def grocy_url(self) -> str:
        """Get Grocy URL."""
        return self._config.get('grocy_url', '').strip()

    @property
    def grocy_api_key(self) -> str:
        """Get Grocy API key."""
        return self._config.get('grocy_api_key', '').strip()

    @property
    def auto_process_receipts(self) -> bool:
        """Check if automatic receipt processing is enabled."""
        return self._config.get('auto_process_receipts', True)

    @property
    def process_interval_hours(self) -> int:
        """Get processing interval in hours."""
        return self._config.get('process_interval_hours', 1)

    @property
    def fuzzy_match_threshold(self) -> float:
        """Get fuzzy matching threshold (0.0-1.0)."""
        return self._config.get('fuzzy_match_threshold', 0.8)

    @property
    def supported_stores(self) -> list:
        """Get list of supported store names."""
        return self._config.get('supported_stores', ['rewe', 'edeka', 'aldi', 'lidl', 'penny'])

    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config.get('debug', False)


# Global config instance
config = Config()
