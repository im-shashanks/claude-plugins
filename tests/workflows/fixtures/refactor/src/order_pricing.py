"""Order pricing with deliberate code smells for the refactoring E2E test.

Smells present (targeted-tier refactoring candidates):
  - Duplicated discount-calculation blocks across three customer tiers.
  - A long function (calculate_total) doing tier resolution, discounts,
    shipping, and tax inline.
  - Magic numbers scattered through the logic.

Behavior is fully pinned by tests/test_order_pricing.py so a refactor can
preserve it while extracting helpers and removing duplication.
"""


def calculate_total(items, customer_tier, country):
    subtotal = 0
    for item in items:
        subtotal += item["price"] * item["qty"]

    # Duplicated discount logic per tier (the smell).
    if customer_tier == "gold":
        if subtotal > 100:
            discount = subtotal * 0.20
        elif subtotal > 50:
            discount = subtotal * 0.15
        else:
            discount = subtotal * 0.10
    elif customer_tier == "silver":
        if subtotal > 100:
            discount = subtotal * 0.10
        elif subtotal > 50:
            discount = subtotal * 0.07
        else:
            discount = subtotal * 0.05
    else:  # bronze / default
        if subtotal > 100:
            discount = subtotal * 0.05
        elif subtotal > 50:
            discount = subtotal * 0.03
        else:
            discount = 0.0

    discounted = subtotal - discount

    # Shipping (magic numbers).
    if discounted > 75:
        shipping = 0.0
    elif country == "US":
        shipping = 5.0
    else:
        shipping = 15.0

    # Tax (magic numbers).
    if country == "US":
        tax = discounted * 0.08
    elif country == "DE":
        tax = discounted * 0.19
    else:
        tax = discounted * 0.10

    return round(discounted + shipping + tax, 2)
