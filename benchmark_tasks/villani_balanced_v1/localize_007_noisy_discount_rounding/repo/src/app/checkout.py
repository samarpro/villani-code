from app.pricing.base import subtotal
from app.pricing.discounts import apply_discount
from app.pricing.fees import service_fee

def total_after_discount(lines, pct: float) -> float:
    return apply_discount(subtotal(lines), pct)

def total_with_fee(lines, pct: float) -> float:
    discounted = total_after_discount(lines, pct)
    return discounted + service_fee(discounted)
