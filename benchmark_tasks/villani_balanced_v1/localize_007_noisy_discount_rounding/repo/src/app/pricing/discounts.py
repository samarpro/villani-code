def apply_discount(total: float, pct: float) -> float:
    discounted = total * (1 - pct)
    return round(discounted, 2)
