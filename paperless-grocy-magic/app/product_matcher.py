"""Product matching between receipt items and Grocy products."""
import logging
from typing import List, Optional, Tuple
from fuzzywuzzy import fuzz
from receipt_parser import ReceiptItem
from grocy_client import GrocyProduct

logger = logging.getLogger(__name__)


class ProductMatch:
    """Represents a match between a receipt item and a Grocy product."""

    def __init__(self, receipt_item: ReceiptItem, grocy_product: Optional[GrocyProduct], score: int):
        self.receipt_item = receipt_item
        self.grocy_product = grocy_product
        self.score = score  # 0-100

    @property
    def is_match(self) -> bool:
        """Check if this is a valid match (has product and good score)."""
        return self.grocy_product is not None

    @property
    def is_new_product(self) -> bool:
        """Check if this is a new product (no match found)."""
        return self.grocy_product is None

    def __repr__(self):
        if self.is_match:
            return f"Match({self.receipt_item.name} → {self.grocy_product.name}, score={self.score})"
        return f"NoMatch({self.receipt_item.name})"


class ProductMatcher:
    """Matches receipt items to Grocy products using fuzzy matching."""

    def __init__(self, threshold: float = 0.8):
        """
        Initialize matcher.

        Args:
            threshold: Matching threshold (0.0-1.0). Higher = more strict.
        """
        self.threshold = int(threshold * 100)  # Convert to 0-100 scale

    def find_best_match(self, receipt_item: ReceiptItem, grocy_products: List[GrocyProduct]) -> ProductMatch:
        """
        Find the best matching Grocy product for a receipt item.

        Args:
            receipt_item: Item from receipt
            grocy_products: List of available Grocy products

        Returns:
            ProductMatch with best match or None if no good match found
        """
        if not grocy_products:
            logger.warning("No Grocy products available for matching")
            return ProductMatch(receipt_item, None, 0)

        best_product = None
        best_score = 0

        receipt_name = receipt_item.name.lower()

        for product in grocy_products:
            product_name = product.name.lower()

            # Try different fuzzy matching strategies
            ratio = fuzz.ratio(receipt_name, product_name)
            partial_ratio = fuzz.partial_ratio(receipt_name, product_name)
            token_sort_ratio = fuzz.token_sort_ratio(receipt_name, product_name)
            token_set_ratio = fuzz.token_set_ratio(receipt_name, product_name)

            # Use the best score from all strategies
            score = max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)

            if score > best_score:
                best_score = score
                best_product = product

        # Only return match if score exceeds threshold
        if best_score >= self.threshold:
            logger.info(f"Match: '{receipt_item.name}' → '{best_product.name}' (score: {best_score})")
            return ProductMatch(receipt_item, best_product, best_score)
        else:
            logger.warning(f"No match for '{receipt_item.name}' (best score: {best_score} < {self.threshold})")
            return ProductMatch(receipt_item, None, best_score)

    def match_all(self, receipt_items: List[ReceiptItem], grocy_products: List[GrocyProduct]) -> List[ProductMatch]:
        """
        Match all receipt items to Grocy products.

        Args:
            receipt_items: Items from receipt
            grocy_products: Available Grocy products

        Returns:
            List of ProductMatch objects
        """
        matches = []

        for item in receipt_items:
            match = self.find_best_match(item, grocy_products)
            matches.append(match)

        # Statistics
        matched_count = sum(1 for m in matches if m.is_match)
        logger.info(f"Matched {matched_count}/{len(receipt_items)} items")

        return matches

    def get_unmatched_items(self, matches: List[ProductMatch]) -> List[ReceiptItem]:
        """Get list of receipt items that didn't match any Grocy product."""
        return [m.receipt_item for m in matches if m.is_new_product]

    def get_matched_items(self, matches: List[ProductMatch]) -> List[ProductMatch]:
        """Get list of successfully matched items."""
        return [m for m in matches if m.is_match]
