from decimal import Decimal
from app.checkout import total_after_discount, total_with_fee

def test_discount_rounds_half_up_at_cents():
    # 10.05 * 0.9 = 9.045 -> should become 9.05, not 9.04
    total = total_after_discount([(10.05, 1)], 0.10)
    assert total == 9.05

def test_unrelated_fee_calculation_still_works():
    total = total_with_fee([(20.0, 1)], 0.10)
    assert total == 18.9
