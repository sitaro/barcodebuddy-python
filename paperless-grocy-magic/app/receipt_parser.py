"""Receipt text parser for extracting products and prices."""
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ReceiptItem:
    """Represents a single item from a receipt."""

    def __init__(self, name: str, price: float, quantity: float = 1.0, unit: str = "Stk"):
        self.name = name.strip()
        self.price = price
        self.quantity = quantity
        self.unit = unit
        self.price_per_unit = price / quantity if quantity > 0 else price

    def __repr__(self):
        if self.quantity != 1.0:
            return f"ReceiptItem({self.name}, {self.price}€, {self.quantity}{self.unit})"
        return f"ReceiptItem({self.name}, {self.price}€)"


class Receipt:
    """Represents a parsed receipt."""

    def __init__(self):
        self.store: Optional[str] = None
        self.date: Optional[datetime] = None
        self.items: List[ReceiptItem] = []
        self.total: Optional[float] = None
        self.raw_text: str = ""

    def __repr__(self):
        return f"Receipt(store={self.store}, date={self.date}, items={len(self.items)}, total={self.total}€)"


class ReweParser:
    """Parser for REWE receipts."""

    # Regex patterns for REWE receipts
    PRODUCT_PATTERN = re.compile(r'^(.+?)\s+(\d+[,\.]\d{2})\s+[AB]\s*\*?\s*$', re.MULTILINE)
    WEIGHT_PATTERN = re.compile(r'^\s*(\d+[,\.]\d+)\s*kg\s*x\s*(\d+[,\.]\d{2})\s*EUR/kg\s*$', re.MULTILINE)
    DATE_PATTERN = re.compile(r'Datum:\s*(\d{2})\.(\d{2})\.(\d{4})')
    TOTAL_PATTERN = re.compile(r'SUMME\s+EUR\s+(\d+[,\.]\d{2})')

    def parse(self, text: str) -> Optional[Receipt]:
        """Parse a REWE receipt from OCR text."""
        receipt = Receipt()
        receipt.raw_text = text

        # Detect store
        if 'REWE MARKT' in text or 'REWE' in text:
            receipt.store = 'REWE'
        else:
            logger.warning("Not a REWE receipt")
            return None

        # Extract date
        date_match = self.DATE_PATTERN.search(text)
        if date_match:
            day, month, year = date_match.groups()
            try:
                receipt.date = datetime(int(year), int(month), int(day))
            except ValueError as e:
                logger.error(f"Invalid date: {e}")

        # Extract total
        total_match = self.TOTAL_PATTERN.search(text)
        if total_match:
            receipt.total = self._parse_price(total_match.group(1))

        # Extract products
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]

            # Try to match product line
            product_match = self.PRODUCT_PATTERN.match(line)
            if product_match:
                name = product_match.group(1).strip()
                price = self._parse_price(product_match.group(2))

                # Check if next line has weight info
                quantity = 1.0
                unit = "Stk"
                if i + 1 < len(lines):
                    weight_match = self.WEIGHT_PATTERN.match(lines[i + 1])
                    if weight_match:
                        quantity = self._parse_price(weight_match.group(1))
                        unit = "kg"
                        i += 1  # Skip weight line

                # Clean up product name
                name = self._clean_product_name(name)

                item = ReceiptItem(name, price, quantity, unit)
                receipt.items.append(item)
                logger.debug(f"Found item: {item}")

            i += 1

        logger.info(f"Parsed REWE receipt: {len(receipt.items)} items, total {receipt.total}€")
        return receipt

    def _parse_price(self, price_str: str) -> float:
        """Convert German price format to float."""
        return float(price_str.replace(',', '.'))

    def _clean_product_name(self, name: str) -> str:
        """Clean up product name."""
        # Remove common prefixes/suffixes
        name = name.strip()

        # Remove leading codes (e.g., "SW-", "BW ", etc.)
        name = re.sub(r'^[A-Z]{1,3}[-\s]', '', name)

        # Capitalize first letter of each word
        name = ' '.join(word.capitalize() for word in name.split())

        return name


class ReceiptParserFactory:
    """Factory for creating appropriate parser based on store."""

    PARSERS = {
        'rewe': ReweParser,
        # Add more parsers later:
        # 'edeka': EdekaParser,
        # 'aldi': AldiParser,
        # 'lidl': LidlParser,
    }

    @classmethod
    def parse(cls, text: str, store_hint: Optional[str] = None) -> Optional[Receipt]:
        """Parse receipt text, auto-detecting store if needed."""

        # If store hint provided, try that parser first
        if store_hint:
            store_hint = store_hint.lower()
            if store_hint in cls.PARSERS:
                parser = cls.PARSERS[store_hint]()
                receipt = parser.parse(text)
                if receipt:
                    return receipt

        # Try all parsers
        for store_name, parser_class in cls.PARSERS.items():
            parser = parser_class()
            receipt = parser.parse(text)
            if receipt:
                logger.info(f"Detected store: {store_name}")
                return receipt

        logger.warning("Could not parse receipt with any known format")
        return None


# Convenience function
def parse_receipt(text: str, store_hint: Optional[str] = None) -> Optional[Receipt]:
    """Parse receipt text and return Receipt object."""
    return ReceiptParserFactory.parse(text, store_hint)
