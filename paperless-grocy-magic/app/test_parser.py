"""Test receipt parser with real Rewe receipt."""
import logging
from receipt_parser import parse_receipt

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Real Rewe receipt text (extracted from PDF)
REWE_RECEIPT = """
REWE MARKT
Homburger Landstr. 340-352
60433 Frankfurter-Berg
UID Nr.: DE812706034
EUR
SW-VORDERHAXE 7,98 B
BIERSCHINKEN 1,29 B
SCHUPFNUDELN 1,79 B
KARTOFFEL FESTK 1,99 B
GELBE ZWIEBELN 1,09 B
Deutschland / Hk 0,44 B
 0,340 kg x 1,29 EUR/kg
BW SENFK 2,79 B
GAULOISES ROT 23,00 A *
--------------------------------------
SUMME EUR 40,37
======================================
Geg. Mastercard EUR 40,37

** Kundenbeleg **
Datum: 22.11.2025
Uhrzeit: 18:26:23 Uhr
"""

def main():
    """Test the parser."""
    print("=" * 60)
    print("Testing REWE Receipt Parser")
    print("=" * 60)
    print()

    receipt = parse_receipt(REWE_RECEIPT)

    if receipt:
        print(f"✅ Successfully parsed receipt!")
        print()
        print(f"📍 Store: {receipt.store}")
        print(f"📅 Date: {receipt.date.strftime('%d.%m.%Y') if receipt.date else 'N/A'}")
        print(f"💰 Total: {receipt.total:.2f} €")
        print()
        print(f"🛒 Products ({len(receipt.items)} items):")
        print("-" * 60)

        for i, item in enumerate(receipt.items, 1):
            if item.quantity != 1.0:
                print(f"{i}. {item.name:<30} {item.quantity:.3f} {item.unit} × {item.price_per_unit:.2f} €/{ item.unit} = {item.price:.2f} €")
            else:
                print(f"{i}. {item.name:<30} {item.price:.2f} €")

        print("-" * 60)
        print(f"{'SUMME':<30} {receipt.total:.2f} €")
        print()

        # Verify total matches sum of items
        calculated_total = sum(item.price for item in receipt.items)
        print(f"Calculated total: {calculated_total:.2f} €")
        if abs(calculated_total - receipt.total) < 0.01:
            print("✅ Total matches!")
        else:
            print(f"⚠️  Total mismatch: {calculated_total:.2f} vs {receipt.total:.2f}")

    else:
        print("❌ Failed to parse receipt")

    print()
    print("=" * 60)


if __name__ == '__main__':
    main()
