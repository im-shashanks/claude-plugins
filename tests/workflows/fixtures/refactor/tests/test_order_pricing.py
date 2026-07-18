"""Behavior-pinning tests for order_pricing.calculate_total.

Full-branch coverage so the refactoring FORTIFY phase finds the safety
threshold already met and TRANSFORM can proceed without many new tests.
These tests must stay green after refactoring (behavior preservation).
"""

from src.order_pricing import calculate_total


def _items(*pairs):
    return [{"price": p, "qty": q} for p, q in pairs]


def test_gold_high_subtotal_free_shipping_us():
    # subtotal 200 -> gold 20% -> 160 discounted -> free shipping, 8% tax
    total = calculate_total(_items((100, 2)), "gold", "US")
    assert total == round(160 + 0 + 160 * 0.08, 2)


def test_gold_mid_subtotal():
    # subtotal 60 -> gold 15% -> 51 -> US shipping 5, tax 8%
    total = calculate_total(_items((60, 1)), "gold", "US")
    assert total == round(51 + 5 + 51 * 0.08, 2)


def test_gold_low_subtotal():
    total = calculate_total(_items((40, 1)), "gold", "US")
    assert total == round(36 + 5 + 36 * 0.08, 2)


def test_silver_tiers():
    assert calculate_total(_items((100, 2)), "silver", "US") == round(180 + 0 + 180 * 0.08, 2)
    assert calculate_total(_items((60, 1)), "silver", "US") == round(55.8 + 5 + 55.8 * 0.08, 2)
    assert calculate_total(_items((40, 1)), "silver", "US") == round(38 + 5 + 38 * 0.08, 2)


def test_bronze_tiers_and_zero_discount():
    assert calculate_total(_items((100, 2)), "bronze", "US") == round(190 + 0 + 190 * 0.08, 2)
    assert calculate_total(_items((60, 1)), "bronze", "US") == round(58.2 + 5 + 58.2 * 0.08, 2)
    # low bronze -> 0 discount
    assert calculate_total(_items((40, 1)), "bronze", "US") == round(40 + 5 + 40 * 0.08, 2)


def test_country_shipping_and_tax():
    # DE, discounted 36 (<75) -> non-US shipping 15, DE tax 19%
    total = calculate_total(_items((40, 1)), "gold", "DE")
    assert total == round(36 + 15 + 36 * 0.19, 2)
    # other country -> 10% tax, 15 shipping
    total = calculate_total(_items((40, 1)), "gold", "FR")
    assert total == round(36 + 15 + 36 * 0.10, 2)


def test_unknown_tier_defaults_to_bronze():
    assert calculate_total(_items((100, 2)), "platinum", "US") == calculate_total(
        _items((100, 2)), "bronze", "US"
    )
