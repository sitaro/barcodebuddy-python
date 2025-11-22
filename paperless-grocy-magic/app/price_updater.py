"""Service for updating Grocy prices from receipts."""
import logging
from typing import List, Dict
from datetime import datetime
from receipt_parser import Receipt, parse_receipt
from grocy_client import GrocyClient
from product_matcher import ProductMatcher, ProductMatch

logger = logging.getLogger(__name__)


class PriceUpdateResult:
    """Result of a price update operation."""

    def __init__(self):
        self.success = False
        self.receipt: Receipt = None
        self.matches: List[ProductMatch] = []
        self.updated_count = 0
        self.failed_count = 0
        self.unmatched_count = 0
        self.created_count = 0
        self.errors: List[str] = []

    def to_dict(self) -> Dict:
        """Convert result to dictionary for API response."""
        return {
            'success': self.success,
            'store': self.receipt.store if self.receipt else None,
            'date': self.receipt.date.isoformat() if self.receipt and self.receipt.date else None,
            'total_items': len(self.matches),
            'updated': self.updated_count,
            'created': self.created_count,
            'failed': self.failed_count,
            'unmatched': self.unmatched_count,
            'matches': [
                {
                    'receipt_item': m.receipt_item.name,
                    'grocy_product': m.grocy_product.name if m.grocy_product else None,
                    'price': m.receipt_item.price,
                    'score': m.score,
                    'matched': m.is_match,
                    'created': getattr(m, 'was_created', False)
                }
                for m in self.matches
            ],
            'errors': self.errors
        }


class PriceUpdateService:
    """Service for processing receipts and updating Grocy prices."""

    def __init__(self, grocy_client: GrocyClient, matcher_threshold: float = 0.8):
        self.grocy = grocy_client
        self.matcher = ProductMatcher(threshold=matcher_threshold)

    def process_receipt_text(self, text: str, store_hint: str = None) -> PriceUpdateResult:
        """
        Process receipt text and update Grocy prices.

        Args:
            text: Receipt OCR text
            store_hint: Optional store name hint (e.g., 'rewe')

        Returns:
            PriceUpdateResult with details of the operation
        """
        result = PriceUpdateResult()

        # Step 1: Parse receipt
        logger.info("Step 1: Parsing receipt...")
        receipt = parse_receipt(text, store_hint)

        if not receipt:
            result.errors.append("Could not parse receipt")
            logger.error("Receipt parsing failed")
            return result

        result.receipt = receipt
        logger.info(f"Parsed {len(receipt.items)} items from {receipt.store} receipt")

        # Step 2: Get Grocy products
        logger.info("Step 2: Fetching Grocy products...")
        grocy_products = self.grocy.get_all_products()

        if not grocy_products:
            result.errors.append("Could not fetch Grocy products")
            logger.error("Failed to fetch Grocy products")
            return result

        logger.info(f"Found {len(grocy_products)} products in Grocy")

        # Step 3: Match receipt items to Grocy products
        logger.info("Step 3: Matching products...")
        matches = self.matcher.match_all(receipt.items, grocy_products)
        result.matches = matches

        matched = self.matcher.get_matched_items(matches)
        unmatched = self.matcher.get_unmatched_items(matches)

        logger.info(f"Matched: {len(matched)}, Unmatched: {len(unmatched)}")

        # Step 4: Update prices in Grocy
        logger.info("Step 4: Updating prices in Grocy...")
        for match in matched:
            product_id = match.grocy_product.id
            new_price = match.receipt_item.price

            # Update price
            success, error = self.grocy.update_product_price(
                product_id=product_id,
                price=new_price,
                store=receipt.store
            )

            if success:
                # Add to stock with the new price
                stock_success, stock_error = self.grocy.add_to_stock(
                    product_id=product_id,
                    amount=1.0,
                    price=new_price
                )

                if stock_success:
                    result.updated_count += 1
                    logger.info(f"✅ Updated & added to stock: {match.grocy_product.name} → {new_price:.2f}€")
                else:
                    result.failed_count += 1
                    error_msg = f"Updated {match.grocy_product.name} but failed to add to stock: {stock_error}"
                    result.errors.append(error_msg)
                    logger.error(f"⚠️  {error_msg}")
            else:
                result.failed_count += 1
                error_msg = f"Failed to update {match.grocy_product.name}: {error}"
                result.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")

        # Step 5: Create new products for unmatched items
        logger.info(f"Step 5: Creating {len(unmatched)} new products in Grocy...")
        for item in unmatched:
            # Create product in Grocy
            new_product, error = self.grocy.create_product(
                name=item.name,
                price=item.price
            )

            if new_product:
                # Add to stock with price
                stock_success, stock_error = self.grocy.add_to_stock(
                    product_id=new_product.id,
                    amount=1.0,
                    price=item.price
                )

                if stock_success:
                    result.created_count += 1
                    logger.info(f"✨ Created & added to stock: {new_product.name} ({item.price:.2f}€)")

                    # Update the match object to reflect creation
                    for match in matches:
                        if match.receipt_item == item:
                            match.grocy_product = new_product
                            match.was_created = True
                            break
                else:
                    result.unmatched_count += 1
                    error_msg = f"Created {item.name} but failed to add to stock: {stock_error}"
                    result.errors.append(error_msg)
                    logger.error(f"⚠️  {error_msg}")
            else:
                result.unmatched_count += 1
                error_msg = f"Failed to create {item.name}: {error}"
                result.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")

        # Count remaining unmatched (those that couldn't be created)
        final_unmatched = [item for item in unmatched
                          if not any(m.receipt_item == item and getattr(m, 'was_created', False)
                                   for m in matches)]

        if final_unmatched:
            logger.warning(f"⚠️  Still unmatched: {', '.join(item.name for item in final_unmatched)}")

        # Mark as successful if at least some items were updated or created
        result.success = (result.updated_count > 0) or (result.created_count > 0)

        logger.info(
            f"Finished: {result.updated_count} updated, "
            f"{result.created_count} created, "
            f"{result.failed_count} failed, {result.unmatched_count} unmatched"
        )

        return result

    def process_receipt(self, receipt: Receipt) -> PriceUpdateResult:
        """
        Process a parsed receipt object and update Grocy prices.

        Args:
            receipt: Parsed Receipt object

        Returns:
            PriceUpdateResult with details of the operation
        """
        result = PriceUpdateResult()
        result.receipt = receipt

        # Get Grocy products
        grocy_products = self.grocy.get_all_products()

        if not grocy_products:
            result.errors.append("Could not fetch Grocy products")
            return result

        # Match and update
        matches = self.matcher.match_all(receipt.items, grocy_products)
        result.matches = matches

        matched = self.matcher.get_matched_items(matches)

        for match in matched:
            success = self.grocy.update_product_price(
                product_id=match.grocy_product.id,
                price=match.receipt_item.price,
                store=receipt.store
            )

            if success:
                result.updated_count += 1
            else:
                result.failed_count += 1

        result.unmatched_count = len(self.matcher.get_unmatched_items(matches))
        result.success = result.updated_count > 0

        return result
